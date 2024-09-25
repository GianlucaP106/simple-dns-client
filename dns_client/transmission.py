import socket

from configuration import Configuration
from packet import Packet, RecordType


class Transmitter:
    def __init__(self, config: Configuration):
        self.config = config

    def transmit(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect((self.config.server, self.config.port))
        sock.settimeout(self.config.timeout)

        request = Packet.build_request(
            self.config.name, mx=self.config.mx, ns=self.config.ns
        )

        print(f"sending query to {self.config.server} for hostname {self.config.name}")
        packet = request.pack()
        sock.send(packet)
        res = sock.recv(512)
        print("unpacking response...")
        response = Packet.build_response(res, request)

        print(
            f"response code: {response.header.response_code}  answer count: {response.header.answer_count}"
        )

        for answer in response.get_answers():
            print("----------- answer -----------")
            print("hostname: ", answer.name)
            print("type: ", answer.get_type_str())
            print("class: ", answer.clazz)
            print("data length: ", answer.data_length)
            print(f"{answer.get_type_title_str()}: {answer.data}")
            if answer.data_type == RecordType.MX:
                print("preference: ", answer.preference)

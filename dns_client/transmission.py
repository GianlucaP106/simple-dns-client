import socket

from configuration import Configuration
from packet import Packet


class Transmitter:
    def __init__(self, config: Configuration):
        self.config = config

    def transmit(self):
        print("connecting to dns server: ", self.config.server)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect((self.config.server, self.config.port))
        sock.settimeout(self.config.timeout)

        print("querying for hostname: ", self.config.name)
        request = Packet.build_request(
            self.config.name, mx=self.config.mx, ns=self.config.ns
        )

        print("packing request...")
        packet = request.pack()
        print("packed: ", packet)
        sock.send(packet)
        res = sock.recv(512)
        print("recieved packet: ", res)

        print("unpacking response...")
        response = Packet.build_response(res, request)
        print("answer count in response: ", response.header.answer_count)
        print("response code", response.header.response_code)
        print("recusive supported: ", response.header.recursive_supported)

        if response.answers:
            for answer in response.answers:
                print("answer:")
                print("hostname: ", answer.name)
                print("type: ", answer.data_type)
                print("class: ", answer.clazz)
                print("data length: ", answer.data_length)
                print("data: ", answer.data)
                print("preference: ", answer.preference)
                print("exchange (mail): ", answer.exchange)

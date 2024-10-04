import socket
import time

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
        packet = request.pack()

        retries = 0

        print(f"DnsClient sending request for {request.question.name}")
        print(f"Server: {self.config.server}")
        print("Request type: ", request.question.qtype.to_str())

        startTime = time.time()
        while True:
            try:
                sock.send(packet)
                res = sock.recv(512)
                if res:
                    break
            except socket.timeout:
                if retries >= self.config.retries:
                    print(
                        f"ERROR \t Maximum number of retries [{self.config.retries}] exceeded"
                    )
                    return 0
                retries += 1

        endTime = time.time()
        responseTime = endTime - startTime
        print(f"Response received after {responseTime} seconds ({retries} retries)\n")
        response = Packet.build_response(res, request)

        self.display_records(response, "answers", "Answer Section")
        self.display_records(response, "authoritative_records", "Authoritative Section")
        self.display_records(response, "additional_records", "Additional Section")

    @classmethod
    def display_records(cls, response: Packet, record_section: str, title: str):
        responses = response.get_records(record_section)
        count = len(responses)
        print(f"***{title} ({count} records)***")
        if count == 0:
            print("NOTFOUND")
            return

        isAuth = "auth" if response.header.authoritative else "nonauth"
        for record in responses:
            data = [
                record.get_type_str(),
                str(record.data),
                str(record.ttl),
                isAuth,
            ]

            if record.data_type == RecordType.MX.value:
                data.insert(2, str(record.preference))

            output = " \t ".join(data)
            print(output)

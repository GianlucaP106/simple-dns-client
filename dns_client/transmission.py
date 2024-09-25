import socket

from configuration import Configuration
from packet import Packet, PacketHeader, PacketQuestion


class Transmitter:
    def __init__(self, config: Configuration):
        self.config = config

    def transmit(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect((self.config.server, self.config.port))
        sock.settimeout(self.config.timeout)
        request = Packet.build_request_packet(
            self.config.name, mx=self.config.mx, ns=self.config.ns
        )
        packet = request.pack()

        print("Sending: ", packet)
        sock.send(packet)
        res = sock.recv(512)
        print("Recieved: ", res)

        response = Packet.build_response_packet(res, request.question)
        print("Built response packet: ", response.question.name)

import socket
import time

from configuration import Configuration
from packet import Packet, RecordType, PacketAnswer


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
        if request.question.mx:
            print(f"Request type: MX\n")
        elif request.question.ns:
            print(f"Request type: NS\n")
        else:
            print(f"Request type: A\n")

        startTime = time.time()
        while (True):
            try:                
                sock.send(packet)
                res = sock.recv(512)
                if res: 
                    break
            except socket.timeout:
                if retries >= self.config.retries:
                    print(f"ERROR \t Maximum number of retries [{self.config.retries}] exceeded")
                    return 0 
                retries += 1

        endTime = time.time()
        responseTime = endTime - startTime
        print(f"Response received after {responseTime} seconds ({retries} retries)\n")  
        response = Packet.build_response(res, request)

        if response.header.answer_count != 0:
            print(f"***Answer Section ({response.header.answer_count} records)***")
            self.display_records(response, 'answers')

        if response.header.additional_records_count != 0:
            print(f"***Additional Section ({response.header.additional_records_count} records)***")
            self.display_records(response, 'additional_records')
        
        if response.header.answer_count == 0 and response.header.additional_records_count == 0:
            print(f"NOTFOUND")

    @classmethod
    def display_records(cls, response: Packet, record_section: str):
        if response.header.authoritative:
            isAuth = 'auth'
        else:
            isAuth = 'nonauth'

        for record in response.get_records(record_section):
            if record.data_type == RecordType.MX:
                print(f"{cls.get_type_str(record)} \t {record.data} \t {record.preference} \t {record.ttl} \t {isAuth}")
            else:
                print(f"{cls.get_type_str(record)} \t {record.data} \t {record.ttl} \t {isAuth}")

    @staticmethod
    def get_type_str(record: PacketAnswer) -> str:
        match record.data_type:
            case RecordType.CNAME:
                return "CNAME"
            case RecordType.NS:
                return "NS"
            case RecordType.A:
                return "A"
            case RecordType.MX:
                return "MX"
            case _:
                return str(record.data_type)
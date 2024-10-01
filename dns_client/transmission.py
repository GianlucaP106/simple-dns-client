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
        
        responseNotRecieved = True
        retries = 0

        while (responseNotRecieved):
            try:
                while (True):
                    if retries == 0:
                        print(f"sending query to {self.config.server} for hostname {self.config.name}")
                    else:
                        print(f"retry sending query to {self.config.server} for hostname {self.config.name}")
                    startTime = time.time()
                    sock.send(packet)
                
                    res = sock.recv(512)
                    endTime = time.time()
                    responseTime = endTime - startTime
                    
                    if not res: 
                        continue
                    else:
                        print(f"Response received after {responseTime} seconds ({retries} retries)\n")
                        responseNotRecieved = False
                        break

            except socket.timeout:
                if retries >= self.config.retries:
                    print(f"ERROR \t Maximum number of retries [{self.config.retries}] exceeded")
                    return 0 
                else:
                    retries += 1
                    continue

        print("unpacking response...")
        response = Packet.build_response(res, request)

        print(f"response code: {response.header.response_code}  answer count: {response.header.answer_count}")

        for answer in response.get_answers():
            print("----------- answer -----------")
            print("hostname: ", answer.name)
            print("type: ", answer.get_type_str())
            print("class: ", answer.clazz)
            print("data length: ", answer.data_length)
            print(f"{answer.get_type_title_str()}: {answer.data}")
            if answer.data_type == RecordType.MX:
                print("preference: ", answer.preference)

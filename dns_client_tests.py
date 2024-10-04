import unittest
import struct

from dns_client.packet import Packet, PacketHeader, PacketQuestion, PacketAnswer, RecordType

class TestPacketHeader(unittest.TestCase):
    header = PacketHeader(
            id=1234,
            response=True,
            opcode=0,
            authoritative=False,
            truncated=False,
            recursive=True,
            recursive_supported=True,
            response_code=0,
            question_count=1,
            answer_count=2,
            name_server_records_count=3,
            additional_records_count=4
        )

    def test_pack(self):
        packed_data = self.header.pack()
        expected_data = struct.pack("!HHHHHH", 1234, self.header._PacketHeader__pack_flag(), 1, 2, 3, 4)
        self.assertEqual(packed_data, expected_data)

    def test_unpack_flag(self):
        flag = 0b1000011110000001
        self.header._unpack_flag(flag)

        self.assertTrue(self.header.response)
        self.assertEqual(self.header.opcode, 0)
        self.assertTrue(self.header.authoritative)
        self.assertTrue(self.header.truncated)
        self.assertTrue(self.header.recursive)
        self.assertTrue(self.header.recursive_supported)
        self.assertEqual(self.header.z, 0)
        self.assertEqual(self.header.response_code, 1)

    def test_build_request(self):
        method_header = PacketHeader.build_request(2)
        self.assertEqual(method_header.question_count, 2)
        self.assertTrue(method_header.recursive)

    def test_build_response(self):
        raw_data = struct.pack("!HHHHHH", 1234, 0b1000101010100001, 2, 3, 4, 5)
        method_header = PacketHeader.build_response(raw_data)

        self.assertEqual(method_header.id, 1234)
        self.assertEqual(method_header.question_count, 2)
        self.assertEqual(method_header.answer_count, 3)

class TestPacketQuestion(unittest.TestCase):
    def test_pack_question(self):
        question = PacketQuestion(name="example.com")
        packed_data = question.pack()

        expected_name = b"\x07example\x03com\x00"
        expected_data = expected_name + struct.pack("!HH", RecordType.A.value, PacketQuestion.QCLASS)

        self.assertEqual(packed_data, expected_data)

    def test_build_question(self):
        question = PacketQuestion.build_question(b"\x03\x77\x77\x77\x06\x6d\x63\x67\x69\x6c\x6c\x02\x63\x61\x00\x00\x01\x00\x01")
        self.assertEqual(question.name, "\x03www\x06mcgill\x02ca\x00")
        self.assertEqual(question.qtype, RecordType.A)

class TestPacketAnswer(unittest.TestCase):
    def test_build_answer(self):
        # Raw answer to test extraction
        raw_response = b"\x82\x7a\x81\x00\x00\x01\x00\x01\x00\x00\x00\x00\x03\x77\x77\x77\x06\x6d\x63\x67\x69\x6c\x6c\x02\x63\x61\x00\x00\x01\x00\x01\xc0\x0c\x00\x01\x00\x01\x00\x00\x04\x13\x00\x04\x84\xd8\xb1\xa0"
        answers, _ = PacketAnswer.build_answer(raw_response, 31, 1)

        self.assertEqual(answers[0].name, "www.mcgill.ca")
        self.assertEqual(answers[0].data_type, RecordType.A.value)
        self.assertEqual(answers[0].ttl, 1043)
        self.assertEqual(answers[0].data_length, 4)
        self.assertEqual(answers[0].data, "132.216.177.160")

class TestPacket(unittest.TestCase):
    def test_build_request_packet(self):
        packet = Packet.build_request(name="example.com")
        packed_data = packet.pack()

        # Check if packed data is correctly formed
        expected_name = b"\x07example\x03com\x00"
        expected_question = expected_name + struct.pack("!HH", RecordType.A.value, PacketQuestion.QCLASS)
        expected_header = struct.pack("!HHHHHH", packet.header.id, packet.header._PacketHeader__pack_flag(), 1, 0, 0, 0)

        self.assertEqual(packed_data, expected_header + expected_question)

    def test_build_response_packet(self):
        request_packet = Packet.build_request(name="example.com")
        raw_response = b"\x12\x34\x81\x80\x00\x01\x00\x01\x00\x00\x00\x00" + b"\x07example\x03com\x00\x00\x01\x00\x01" + b"\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04\xc0\xa8\x00\x01"
        response_packet = Packet.build_response(raw_response, request_packet)

        self.assertEqual(response_packet.header.id, 0x1234)
        self.assertEqual(response_packet.answers[0].data, "192.168.0.1")

if __name__ == '__main__':
    unittest.main()

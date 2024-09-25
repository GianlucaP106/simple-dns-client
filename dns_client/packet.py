import random
import struct
from typing import Optional


class PacketHeader:
    def __init__(
        self,
        id: int,
        response: bool = False,
        opcode: int = 0,
        authoritative: bool = False,
        truncated: bool = False,
        recursive: bool = False,
        recursive_supported: bool = False,
        response_code: int = 0,
        question_count: int = 0,
        answer_count: int = 0,
        nameserver_records_count: int = 0,
        additional_records_count: int = 0,
    ):
        self.id = id
        self.response = response
        self.opcode = opcode
        self.authoritative = authoritative
        self.truncated = truncated
        self.recursive = recursive
        self.recursive_supported = recursive_supported
        self.response_code = response_code
        self.question_count = question_count
        self.answer_count = answer_count
        self.authoritative_records_count = nameserver_records_count
        self.additional_records_count = additional_records_count
        self.z = 0

    def pack(self) -> bytes:
        return struct.pack(
            "!HHHHHH",
            self.id,
            self.__pack_flag(),
            self.question_count,
            self.answer_count,
            self.authoritative_records_count,
            self.additional_records_count,
        )

    @classmethod
    def build_request_header(cls, question_count: int):
        header = cls(
            id=cls.__generate_id(),
            recursive=True,
            question_count=question_count,
        )

        return header

    @classmethod
    def build_response_header(cls, raw: bytes):
        id, flag, qcount, acount, nscount, arcount = struct.unpack("!HHHHHH", raw)
        header = PacketHeader(
            id=id,
            question_count=qcount,
            answer_count=acount,
            nameserver_records_count=nscount,
            additional_records_count=arcount,
        )
        header.__unpack_flag(flag)
        return header

    def __pack_flag(self) -> int:
        qr = self.to_bit(self.response)
        opcode = self.opcode
        aa = self.to_bit(self.authoritative)
        tc = self.to_bit(self.truncated)
        rd = self.to_bit(self.recursive)
        ra = self.to_bit(self.recursive_supported)
        z = self.z
        rcode = self.response_code
        flag = (
            (qr << 15)
            | (opcode << 11)
            | (aa << 10)
            | (tc << 9)
            | (rd << 8)
            | (ra << 7)
            | (z << 4)
            | (rcode)
        )

        return flag

    def __unpack_flag(self, flag: int) -> None:
        def mask(position: int, m: int) -> int:
            return (flag >> position) & m

        qr = mask(15, 0x01)
        opcode = mask(11, 0x0F)
        aa = mask(10, 0x01)
        tc = mask(9, 0x01)
        rd = mask(8, 0x01)
        ra = mask(7, 0x01)
        z = mask(4, 0x07)
        rcode = mask(0, 0x0F)

        self.response = self.from_bit(qr)
        self.opcode = opcode
        self.authoritative = self.from_bit(aa)
        self.truncated = self.from_bit(tc)
        self.recursive = self.from_bit(rd)
        self.recursive_supported = self.from_bit(ra)
        self.z = z
        self.response_code = rcode

    @staticmethod
    def to_bit(b: bool) -> int:
        return 1 if b else 0

    @staticmethod
    def from_bit(b: int) -> bool:
        return False if b == 0 else True

    @staticmethod
    def __generate_id() -> int:
        return random.randint(0, 65535)


class PacketQuestion:
    A = 0x0001
    NS = 0x0002
    MX = 0x000F
    QCLASS = 0x0001

    def __init__(self, name: str, mx: Optional[bool] = None, ns: Optional[bool] = None):
        self.name = name
        self.mx = mx
        self.ns = ns

    def pack(self) -> bytes:
        qname = self.__pack_host_name()
        if self.mx:
            qtype = self.MX
        elif self.ns:
            qtype = self.NS
        else:
            qtype = self.A

        packet = qname + struct.pack("!HH", qtype, self.QCLASS)
        return packet

    def get_packed_length(self) -> int:
        return len(self.pack())

    def __pack_host_name(self) -> bytes:
        parts = []
        labels = self.name.split(".")
        for label in labels:
            length = bytes([len(label)])
            ascii_label = label.encode("ascii")
            parts.append(length + ascii_label)

        parts.append(bytes([0]))
        return b"".join(parts)

    @classmethod
    def build_question(cls, raw: bytes):
        data = raw[:-4]
        # TODO: decode name
        name = data.decode()

        end = raw[-4:]
        qtype, _ = struct.unpack("HH", end)
        mx = qtype == cls.MX
        ns = qtype == cls.NS

        return PacketQuestion(name=name, mx=mx, ns=ns)


class PacketAnwser:
    def pack(self) -> bytes:
        return b""


class Packet:
    def __init__(
        self,
        header: PacketHeader,
        question: PacketQuestion,
        answer: Optional[PacketAnwser] = None,
    ):
        self.header = header
        self.question = question
        self.answer = answer

    def pack(self) -> bytes:
        parts = [self.header.pack(), self.question.pack()]
        if self.answer:
            parts.append(self.answer.pack())

        return b"".join(parts)

    @staticmethod
    def build_request_packet(
        name: str,
        mx: Optional[bool] = None,
        ns: Optional[bool] = None,
    ):
        header = PacketHeader.build_request_header(1)
        question = PacketQuestion(name, mx, ns)
        return Packet(header=header, question=question)

    @staticmethod
    def build_response_packet(response: bytes, question: PacketQuestion):
        header_cutoff = 12
        header = PacketHeader.build_response_header(response[:header_cutoff])
        q = PacketQuestion.build_question(
            response[header_cutoff : header_cutoff + question.get_packed_length()]
        )

        return Packet(header=header, question=q)

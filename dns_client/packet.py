import random
import struct
from types import prepare_class
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
    def build_request(cls, question_count: int):
        return cls(
            id=cls.__generate_id(),
            recursive=True,
            question_count=question_count,
        )

    @classmethod
    def build_response(cls, header: bytes):
        id, flag, qcount, acount, nscount, arcount = struct.unpack("!HHHHHH", header)
        h = PacketHeader(
            id=id,
            question_count=qcount,
            answer_count=acount,
            nameserver_records_count=nscount,
            additional_records_count=arcount,
        )
        h.__unpack_flag(flag)
        return h

    def __pack_flag(self) -> int:
        qr = self.__to_bit(self.response)
        opcode = self.opcode
        aa = self.__to_bit(self.authoritative)
        tc = self.__to_bit(self.truncated)
        rd = self.__to_bit(self.recursive)
        ra = self.__to_bit(self.recursive_supported)
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

        self.response = self.__from_bit(qr)
        self.opcode = opcode
        self.authoritative = self.__from_bit(aa)
        self.truncated = self.__from_bit(tc)
        self.recursive = self.__from_bit(rd)
        self.recursive_supported = self.__from_bit(ra)
        self.z = z
        self.response_code = rcode

    @staticmethod
    def __to_bit(b: bool) -> int:
        return 1 if b else 0

    @staticmethod
    def __from_bit(b: int) -> bool:
        return False if b == 0 else True

    @staticmethod
    def __generate_id() -> int:
        return random.randint(0, 65535)


class RecordType:
    A = 0x0001
    NS = 0x0002
    MX = 0x000F
    CNAME = 0x0005


class PacketQuestion:
    QCLASS = 0x0001

    def __init__(self, name: str, mx: Optional[bool] = None, ns: Optional[bool] = None):
        self.name = name
        self.mx = mx
        self.ns = ns

    def pack(self) -> bytes:
        qname = self.__pack_host_name()
        if self.mx:
            qtype = RecordType.MX
        elif self.ns:
            qtype = RecordType.NS
        else:
            qtype = RecordType.A

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
    def build_question(cls, question: bytes):
        data = question[:-4]
        name = data.decode()

        end = question[-4:]
        qtype, _ = struct.unpack("HH", end)
        mx = qtype == RecordType.MX
        ns = qtype == RecordType.NS

        return PacketQuestion(name=name, mx=mx, ns=ns)


class PacketAnwser:
    def __init__(
        self,
        name: str,
        data_type: int,
        clazz: int,
        ttl: int,
        data_length: int,
        data: bytes,
        preference: int,
        exchange: str,
    ):
        self.name: str = name
        self.data_type: int = data_type
        self.clazz: int = clazz
        self.ttl: int = ttl
        self.data_length: int = data_length
        self.data: bytes = data
        self.preference: int = preference
        self.exchange: str = exchange

    @classmethod
    def build_answer(
        cls, response: bytes, pointer: int, header: PacketHeader
    ) -> "list[PacketAnwser] | None":
        answers = []
        for answer_idx in range(header.answer_count):
            name, pointer = cls.__extract_name(response, pointer)
            data_start = pointer + 10
            meta = response[pointer:data_start]
            data_type, clazz, ttl, data_length = struct.unpack("!HHIH", meta)

            preference_start = data_start + data_length
            rdata = response[data_start:preference_start]
            # TODO: check the type and decode it

            exchange_start = preference_start + 2
            (preference,) = struct.unpack(
                "!H", response[preference_start:exchange_start]
            )

            exchange, pointer = cls.__extract_name(response, exchange_start)

            a = PacketAnwser(
                name=name,
                data_type=data_type,
                clazz=clazz,
                ttl=ttl,
                data_length=data_length,
                data=rdata,
                preference=preference,
                exchange=exchange,
            )

            print(
                name,
                data_type,
                clazz,
                ttl,
                data_length,
                rdata,
                preference,
                exchange,
            )

            answers.append(a)

        return answers

    @classmethod
    def __extract_name(cls, response: bytes, start: int) -> tuple[str, int]:
        labels = []
        out_pointer = start + 1
        while True:
            length = response[start]
            if length == 0:
                break

            if cls.__is_label_pointer(length):
                pointer = cls.__decode_pointer(length, response[start + 1])
                out_pointer = start + 2
                start = pointer
                continue

            label_start = start + 1
            label = response[label_start : label_start + length]
            label_str = label.decode("ascii")
            labels.append(label_str)
            start = label_start + length

        return (".".join(labels), out_pointer)

    @staticmethod
    def __is_label_pointer(first_byte: int) -> bool:
        return first_byte & 0b11000000 == 0b11000000

    @staticmethod
    def __decode_pointer(first_byte: int, second_byte: int) -> int:
        return ((first_byte & 0x3F) << 8) + second_byte


class Packet:
    def __init__(
        self,
        header: PacketHeader,
        question: PacketQuestion,
        answers: Optional[list[PacketAnwser]] = None,
    ):
        self.header = header
        self.question = question
        self.answers = answers

    def pack(self) -> bytes:
        return b"".join([self.header.pack(), self.question.pack()])

    @staticmethod
    def build_request(
        name: str,
        mx: Optional[bool] = None,
        ns: Optional[bool] = None,
    ) -> "Packet":
        header = PacketHeader.build_request(1)
        question = PacketQuestion(name, mx, ns)
        return Packet(header=header, question=question)

    @staticmethod
    def build_response(raw: bytes, request: "Packet") -> "Packet":
        question_pointer = 12
        answer_pointer = question_pointer + request.question.get_packed_length()
        header = PacketHeader.build_response(raw[:question_pointer])
        q = PacketQuestion.build_question(raw[question_pointer:answer_pointer])
        answers = PacketAnwser.build_answer(raw, answer_pointer, header)
        return Packet(header=header, question=q, answers=answers)

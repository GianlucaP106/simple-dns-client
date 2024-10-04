import random
import struct
import enum


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
        name_server_records_count: int = 0,
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
        self.authoritative_records_count = name_server_records_count
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
            name_server_records_count=nscount,
            additional_records_count=arcount,
        )
        h._unpack_flag(flag)
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

    def _unpack_flag(self, flag: int) -> None:
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

    def validateHeaderErrors(self) -> None:
        if not self.recursive_supported:
            print(
                "ERROR \t Not recursive: the name server does not support recursive queries"
            )
            exit(1)

        if self.response_code == 0:
            return

        errors = {
            1: "ERROR \t Format error: the name server was unable to interpret the query",
            2: "ERROR \t Server failure: the name server was unable to process this query due to a problem with the name server",
            3: "NOTFOUND \t Name error: the domain name referenced in the query does not exist",
            4: "ERROR \t Not implemented: the name server does not support the requested kind of query",
            5: "ERROR \t Refused: the name server refuses to perform the requested operation for policy reasons",
        }

        err = errors.get(self.response_code)
        msg = "ERROR \t Unexpected error: an unexpected error has occured"
        if err:
            msg = err

        print(msg)
        exit(1)

    @staticmethod
    def __to_bit(b: bool) -> int:
        return 1 if b else 0

    @staticmethod
    def __from_bit(b: int) -> bool:
        return False if b == 0 else True

    @staticmethod
    def __generate_id() -> int:
        return random.randint(0, 65535)


class RecordType(enum.Enum):
    CNAME = 0x0005
    NS = 0x0002
    A = 0x0001
    MX = 0x000F

    __to_str = {
        CNAME: "CNAME",
        NS: "NS",
        A: "A",
        MX: "MX",
    }

    @classmethod
    def is_supported(cls, code: int) -> bool:
        for c in cls:
            if c.value == code:
                return True

        return False

    def to_str(self) -> str:
        s = self.__to_str.get(self.value)
        if not s:
            return ""

        return s


class PacketQuestion:
    QCLASS = 0x0001

    def __init__(self, name: str, mx: bool = False, ns: bool = False):
        self.name = name
        if mx:
            self.qtype = RecordType.MX
        elif ns:
            self.qtype = RecordType.NS
        else:
            self.qtype = RecordType.A

    def pack(self) -> bytes:
        qname = self.__pack_host_name()
        packet = qname + struct.pack("!HH", self.qtype.value, self.QCLASS)
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
        mx = qtype == RecordType.MX.value
        ns = qtype == RecordType.NS.value

        return PacketQuestion(name=name, mx=mx, ns=ns)


class PacketAnswer:
    def __init__(
        self,
        name: str,
        data_type: int,
        clazz: int,
        ttl: int,
        data_length: int,
        raw: bytes = b"",
        data: str = "",
        preference: int = 0,
    ):
        self.name = name
        self.data_type = data_type
        self.clazz = clazz
        self.ttl = ttl
        self.data_length = data_length
        self.raw = raw
        self.data = data
        self.preference = preference

    def is_supported_type(self) -> bool:
        return RecordType.is_supported(self.data_type)

    def get_type_str(self) -> str:
        return RecordType(self.data_type).to_str()

    @classmethod
    def build_answer(
        cls, response: bytes, pointer: int, count: int
    ) -> tuple[list["PacketAnswer"], int]:
        answers = []
        for _ in range(count):
            answer, pointer = cls.__unpack_answer(response, pointer)
            answers.append(answer)
            if answer.clazz != 1:
                print(
                    "ERROR \t Unexpected class: an unexpected class code value in the records was encountered"
                )
                exit(1)

        return answers, pointer

    @classmethod
    def __unpack_answer(
        cls, response: bytes, pointer: int
    ) -> tuple["PacketAnswer", int]:
        name, pointer = cls.__extract_name(response, pointer)

        data_start = pointer + 10
        meta = response[pointer:data_start]
        data_type, clazz, ttl, data_length = struct.unpack("!HHIH", meta)

        data_end = data_start + data_length
        a = PacketAnswer(
            name=name,
            data_type=data_type,
            clazz=clazz,
            ttl=ttl,
            data_length=data_length,
        )

        a.__extract_data(response, data_start, data_end)

        return a, data_end

    def __extract_data(self, response: bytes, start: int, end: int):
        self.raw = response[start:end]
        match self.data_type:
            case RecordType.CNAME.value:
                self.data, _ = self.__extract_name(response, start)
            case RecordType.NS.value:
                self.data, _ = self.__extract_name(response, start)
            case RecordType.A.value:
                octets = []
                for octet in self.raw:
                    octets.append(str(octet))
                self.data = ".".join(octets)
            case RecordType.MX.value:
                (preference,) = struct.unpack("!H", self.raw[0:2])
                self.preference = preference
                self.data, _ = self.__extract_name(response, start + 2)

    @classmethod
    def __extract_name(cls, response: bytes, start: int) -> tuple[str, int]:
        labels = []
        out_pointer = start + 1
        label_found = False
        while True:
            length = response[start]
            if length == 0:
                break

            if cls.__is_label_pointer(length):
                pointer = cls.__decode_pointer(length, response[start + 1])

                if not label_found:
                    out_pointer = start + 2
                    label_found = True

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
        answers: list[PacketAnswer] = [],
        authoritative_records: list[PacketAnswer] = [],
        additional_records: list[PacketAnswer] = [],
    ):
        self.header = header
        self.question = question
        self.answers = answers
        self.authoritative_records = authoritative_records
        self.additional_records = additional_records

    def pack(self) -> bytes:
        return b"".join([self.header.pack(), self.question.pack()])

    def get_records(self, record_section: str) -> list[PacketAnswer]:
        out = []
        record_list: list[PacketAnswer] = getattr(self, record_section, [])
        for a in record_list:
            if a.is_supported_type():
                out.append(a)
        return out

    @staticmethod
    def build_request(
        name: str,
        mx: bool = False,
        ns: bool = False,
    ) -> "Packet":
        header = PacketHeader.build_request(1)
        question = PacketQuestion(name, mx, ns)
        return Packet(header=header, question=question)

    @staticmethod
    def build_response(raw: bytes, request: "Packet") -> "Packet":
        question_pointer = 12
        answer_pointer = question_pointer + request.question.get_packed_length()
        header = PacketHeader.build_response(raw[:question_pointer])
        header.validateHeaderErrors()

        q = PacketQuestion.build_question(raw[question_pointer:answer_pointer])
        answers, next_pointer = PacketAnswer.build_answer(
            raw, answer_pointer, header.answer_count
        )

        authoritative_records, next_pointer = PacketAnswer.build_answer(
            raw, next_pointer, header.authoritative_records_count
        )

        additional_records, _ = PacketAnswer.build_answer(
            raw, next_pointer, header.additional_records_count
        )
        return Packet(
            header=header,
            question=q,
            answers=answers,
            authoritative_records=authoritative_records,
            additional_records=additional_records,
        )

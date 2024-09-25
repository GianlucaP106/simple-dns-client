import argparse


class Configuration:
    def __init__(self):
        args = self.__parse_args()
        self.timeout = int(args.t)
        self.retries = int(args.r)
        self.port = int(args.p)
        self.mx = bool(args.mx)
        self.ns = bool(args.ns)
        self.server = str(args.server).strip("@")
        self.name = str(args.name)

    def __parse_args(self):
        parser = argparse.ArgumentParser(description="Simple DNS Client")
        group = parser.add_mutually_exclusive_group()
        parser.add_argument(
            "-t",
            type=int,
            help="Timeout, in seconds, before retransmitting an unanswered query",
            default=5,
        )
        parser.add_argument(
            "-r",
            type=int,
            help="Maximum number of times to retransmit an unanswered query before giving up",
            default=3,
        )
        parser.add_argument(
            "-p", type=int, help="UDP port number of the DNS server", default=53
        )
        group.add_argument(
            "-mx", action="store_true", help="Send a MX (mail server) query"
        )
        group.add_argument(
            "-ns", action="store_true", help="Send a NS (name server) query"
        )
        parser.add_argument(
            "server", help="IPv4 address of the DNS server, in a.b.c.d format"
        )
        parser.add_argument("name", help="Domain name to query for")
        args = parser.parse_args()
        return args

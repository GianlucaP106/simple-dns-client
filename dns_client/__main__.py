from dns_client.configuration import Configuration
from dns_client.transmission import Transmitter


def main():
    config = Configuration()
    transmitter = Transmitter(config)
    transmitter.transmit()


if __name__ == "__main__":
    main()

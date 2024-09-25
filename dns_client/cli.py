from configuration import Configuration
from transmission import Transmitter


def main():
    config = Configuration()
    transmitter = Transmitter(config)
    transmitter.transmit()


if __name__ == "__main__":
    main()

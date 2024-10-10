# A Simple DNS Client

A simple DNS client implementation written in python. It is lightweight, simple and user friendly.

![dns_client_demo](https://github.com/user-attachments/assets/2671a970-8d85-4500-980e-10cec4234187)

## Installation (optional)

```bash
pip install git+https://github.com/GianlucaP106/simple-dns-client
```

## Usage

#### Example query

```bash
python -m dns_client 8.8.8.8 google.com
```

#### See usage information

```bash
python -m dns_client -h
# usage: __main__.py [-h] [-t T] [-r R] [-p P] [-mx | -ns] server name
#
# Simple DNS Client
#
# positional arguments:
#   server      IPv4 address of the DNS server, in a.b.c.d format
#   name        Domain name to query for
#
# options:
#   -h, --help  show this help message and exit
#   -t T        Timeout, in seconds, before retransmitting an unanswered query
#   -r R        Maximum number of times to retransmit an unanswered query before giving up
#   -p P        UDP port number of the DNS server
#   -mx         Send a MX (mail server) query
#   -ns         Send a NS (name server) query
```

import zmq
import argparse
import ChordClient
import os
import hashlib
import sys

def arg_parser():
    parser = argparse.ArgumentParser(description='Run a chord client')
    parser.add_argument('known_ip')
    return parser.parse_args()


def main():
    known_ip = arg_parser().known_ip

    cn = ChordClient.ChordClient(known_ip)
    while True:
        n = input()

        id_sha = hashlib.sha256()
        id_sha.update(n.encode())
        id = int.from_bytes(id_sha.digest(), sys.byteorder)

        id = int(n)

        print(cn.askKeyPosition(id))

if __name__ == '__main__':
    main()
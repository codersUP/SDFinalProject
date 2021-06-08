import zmq
import argparse
import ChordNode
import hashlib
import sys

def arg_parser():
    parser = argparse.ArgumentParser(description='Run a chord server node')
    parser.add_argument('ip')
    parser.add_argument('known_ip')
    return parser.parse_args()


def main():
    id_sha = hashlib.sha256()

    ip = arg_parser().ip

    id_sha.update(ip.encode())
    id = int.from_bytes(id_sha.digest(), sys.byteorder)

    bits = 256
    known_ip = arg_parser().known_ip

    cn = ChordNode.ChordNode(ip, id, bits, known_ip)
    cn.run()
    cn.join()

if __name__ == '__main__':
    main()
import zmq
import argparse
import ChordClient
import os
import sys

def arg_parser():
    parser = argparse.ArgumentParser(description='Run a chord client')
    parser.add_argument('known_ip')
    return parser.parse_args()


def main():
    known_ip = arg_parser().known_ip

    cn = ChordClient.ChordClient(known_ip)
    while True:
        url = input()

        print(cn.askKeyPosition(url))

if __name__ == '__main__':
    main()
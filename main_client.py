import zmq
import argparse
import ChordClient
import os
import sys

def arg_parser():
    parser = argparse.ArgumentParser(description='Run a chord client')
    parser.add_argument('ip')
    parser.add_argument('port')
    parser.add_argument('known_ip')
    return parser.parse_args()


def main():
    ip = arg_parser().ip
    port = arg_parser().port
    known_ip = arg_parser().known_ip

    cn = ChordClient.ChordClient(ip, port, known_ip)
    if cn.join() == 0:
        print('Client connected')
    else:
        print('Error conecting')
        return

    cn.run()

    while True:
        url = input()

        print(cn.askUrl(url))

if __name__ == '__main__':
    main()
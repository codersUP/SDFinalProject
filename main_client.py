import zmq
import argparse
import ChordClient
import os
import sys
from pprint import pprint

def arg_parser():
    parser = argparse.ArgumentParser(description='Run a chord client')
    parser.add_argument('known_ip')
    return parser.parse_args()


def main():
    known_ip = arg_parser().known_ip

    cn = ChordClient.ChordClient(known_ip)
    if cn.join() == 0:
        print('Client connected')
    else:
        print('Error conecting')
        return

    # cn.run()

    while True:
        url = input('Enter url: ')
        d = int(input('Enter depth: '))

        htmls = cn.askUrl(url, depth=d)
        for u, h in htmls.items():
            f = open(u.replace('/', ' '), "x")
            f.write(h)
            f.close()

if __name__ == '__main__':
    main()
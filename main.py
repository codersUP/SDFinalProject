import zmq
import argparse
import ChordNode

def arg_parser():
    parser = argparse.ArgumentParser(description='Run a chord client')
    parser.add_argument('ip')
    parser.add_argument('id')
    parser.add_argument('bits')
    parser.add_argument('known_ip')
    return parser.parse_args()


def main():
    ip = arg_parser().ip
    id = arg_parser().id
    bits = arg_parser().bits
    known_ip = arg_parser().known_ip

    cn = ChordNode.ChordNode(ip, id, bits, known_ip)
    cn.run()
    cn.join()

if __name__ == '__main__':
    main()
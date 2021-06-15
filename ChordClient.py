import zmq
from parser import isAskUrlClientRep, jsonToDict, dictToJson, isClientJoinRep
import macros

class ChordClient:
    def __init__(self, ip, port, know_ip):
        self.ip = ip
        self.port = port
        self.know_ip = know_ip

        self.chord_nodes_ip = [know_ip]

    
    def join(self):
        context = zmq.Context()

        socket = context.socket(zmq.REQ)
        socket.connect(f'tcp://{self.know_ip}:5555')

        socket.setsockopt( zmq.LINGER, 0)
        socket.setsockopt( zmq.RCVTIMEO, macros.TIME_LIMIT )

        try:
            client_join_req = {macros.action: macros.client_join_req}

            socket.send_string(dictToJson(client_join_req))

            message = socket.recv()

            message_dict = jsonToDict(message)
            if isClientJoinRep(message_dict):
                self.chord_nodes_ip = message_dict[macros.answer]['ip']
                # print(self.chord_nodes_ip)
                return 0

        except Exception as e:
            print(e, f'Error join to IP: {self.know_ip}')
            socket.close()
            return -1



    def askKeyPosition(self, key_url):
        context = zmq.Context()

        socket = context.socket(zmq.REQ)
        socket.connect(f'tcp://{self.know_ip}:5555')

        ask_url_client_req = {macros.action: macros.ask_url_client_req, macros.query: {'url': key_url}}
        socket.send_string(dictToJson(ask_url_client_req))

        message = socket.recv()
        print(message)

        message_dict = jsonToDict(message)
        if isAskUrlClientRep(message_dict):
            return message_dict[macros.answer]["html"]

            
import zmq
from parser import isAskUrlClientRep, jsonToDict, dictToJson
import macros

class ChordClient:
    def __init__(self, know_ip):
        self.know_ip = know_ip

    def askKeyPosition(self, key_url):
        context = zmq.Context()

        socket = context.socket(zmq.REQ)
        socket.connect(f'tcp://{self.know_ip}:5555')

        ask_url_client_req = {macros.action: macros.ask_url_client_req , macros.query: {'url': key_url}}
        socket.send_string(dictToJson(ask_url_client_req))

        message = socket.recv()
        print(message)

        message_dict = jsonToDict(message)
        if isAskUrlClientRep(message_dict):
            return message_dict[macros.answer]["html"]

            
import zmq
from parser import isAskKeyPositionRep, jsonToDict, dictToJson
import macros

class ChordClient:
    def __init__(self, know_ip):
        self.know_ip = know_ip

    def askKeyPosition(self, key_id):
        context = zmq.Context()

        socket = context.socket(zmq.REQ)
        socket.connect(f'tcp://{self.know_ip}:5555')

        ask_key_position_req = {macros.action: macros.ask_key_position_req , macros.query: {'id': key_id}}
        print(ask_key_position_req)
        socket.send_string(dictToJson(ask_key_position_req))

        message = socket.recv()
        print(message)

        message_dict = jsonToDict(message)
        if isAskKeyPositionRep(message_dict):
                return (message_dict[macros.answer]["id"], message_dict[macros.answer]["ip"])

            
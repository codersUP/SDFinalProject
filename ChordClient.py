import zmq
from parser import isAskUrlClientRep, jsonToDict, dictToJson, isClientJoinRep, isSendHtmlReq, isAskUrlEndReq
import macros
import threading


class ChordClient:
    def __init__(self, ip, port, know_ip):
        self.ip = ip
        self.port = port
        self.know_ip = know_ip

        self.chord_nodes_ip = [know_ip]
        self.query_id = 1

        self.jobs = {}

    
    def recieveMessages(self):
        context = zmq.Context()

        socket = context.socket(zmq.REP)
        socket.bind(f'tcp://*:{self.port}')

        while True:
            message = socket.recv()
            # print(message)

            message_dict = jsonToDict(message)

            if isSendHtmlReq(message_dict):
                self.ansSendHTML(socket, message_dict)

            if isAskUrlEndReq(message_dict):
                self.ansAskUrlEnd(socket, message_dict)



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


    def askUrl(self, key_url, depth=5):
        for ip in self.chord_nodes_ip:
            context = zmq.Context()

            socket = context.socket(zmq.REQ)
            socket.connect(f'tcp://{ip}:5555')

            socket.setsockopt( zmq.LINGER, 0)
            socket.setsockopt( zmq.RCVTIMEO, macros.TIME_LIMIT )

            try:
                ask_url_client_req = {macros.action: macros.ask_url_client_req, macros.query: {'url': key_url, 'depth': depth}, macros.client_ip: self.ip, macros.client_port: self.port, macros.client_query_id: self.query_id}
                socket.send_string(dictToJson(ask_url_client_req))

                message = socket.recv()
                # print(message)

                message_dict = jsonToDict(message)
                if isAskUrlClientRep(message_dict):
                    self.jobs[self.query_id] = True
                    return 0
            
            except Exception as e:
                print(e, f'Error asking for url to IP: {ip}')
                self.chord_nodes_ip = self.chord_nodes_ip[1:]
                self.chord_nodes_ip.append(ip)
                socket.close()
        
        return -1


    def ansSendHTML(self, socket, message_dict):
        html = message_dict[macros.html]
        query_id = message_dict[macros.client_query_id]

        # guardar el html
        print(f'QUERY_ID: {query_id} \n HTML: {html}')

        send_html_rep = {macros.action: macros.send_html_rep}
        socket.send_string(dictToJson(send_html_rep))


    def ansAskUrlEnd(self, socket, message_dict):
        query_id = message_dict[macros.client_query_id]

        print(f'QUERY_ID: {query_id} END')
        self.jobs.pop(self.query_id)
        self.query_id += 1

        ask_url_end_rep = {macros.action: macros.ask_url_end_rep}
        socket.send_string(dictToJson(ask_url_end_rep))


    def run(self):
        threading.Thread(target=self.recieveMessages, args=()).start()

            
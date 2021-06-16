import zmq
from parser import isAskUrlClientRep, jsonToDict, dictToJson, isClientJoinRep, isSendHtmlReq, isAskUrlEndReq
import macros
import threading
from scrapper import get_url_from_html, get_html_from_url


class ChordClient:
    def __init__(self, ip, port, know_ip):
        self.ip = ip
        self.port = port
        self.know_ip = know_ip

        self.chord_nodes_ip = [know_ip]
        # variable to iterate through chord_nodes_ip
        self.pos = 0


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

    # bfs-like algorithm
    def askUrl(self, key_url, depth=0):
        response = {}

        # queue of urls to request
        q = [{macros.url : key_url, macros.depth : depth}]
        # set of visited url to avoid graph cycles
        visited = { key_url }

        while len(q) > 0:
            current_req = q[0]
            q = q[1:]

            cur_url = current_req[macros.url]
            cur_depth = current_req[macros.depth]
            data, status = self.ask_html_from_url(cur_url)
            response[cur_url] = data

            if cur_depth > 0:
                children_url = get_url_from_html(data, cur_url)
                for child_url in children_url:
                    if child_url not in visited:
                        visited.add(child_url)
                        new_req = {macros.url : child_url, macros.depth : cur_depth - 1}
                        q.append(new_req)

        return response

    def ask_html_from_url(self, key_url):
        while True:
            ip = self.chord_nodes_ip[self.pos]
            self.increase_pos()
            
            context = zmq.Context()

            socket = context.socket(zmq.REQ)
            socket.connect(f'tcp://{ip}:5555')

            socket.setsockopt( zmq.LINGER, 0)
            socket.setsockopt( zmq.RCVTIMEO, macros.TIME_LIMIT )

            try:
                ask_url_client_req = {
                    macros.action: macros.ask_url_client_req,
                    macros.query: {macros.url: key_url}
                }
                socket.send_string(dictToJson(ask_url_client_req))

                message = socket.recv()
                # print(message)

                message_dict = jsonToDict(message)
                if isAskUrlClientRep(message_dict):
                    return message_dict[macros.answer][macros.html], message_dict[macros.answer][macros.status]
            
            except Exception as e:
                print(e, f'Error asking for url to IP: {ip}')
            
            socket.close()
        
        return '', -1

    
    def increase_pos(self):
        self.pos += 1
        if self.pos >= len(self.chord_nodes_ip):
            self.pos = 0


            
import zmq
import threading
import macros
import time
from parser import *
import random
import hashlib
import sys
from scrapper import get_html_from_url

class SubFinger:
    def __init__(self):
        self.start = -1
        self.node = -1


class ChordNode:
    def __init__(self, ip, id, bits, known_ip):
        self.id = int(id)
        self.ip = ip 
        self.bits = int(bits)
        self.known_ip = known_ip

        self.finger = [SubFinger() for _ in range(self.bits + 1)]
        for i in range(1, self.bits + 1):
            self.finger[i].start = (self.id + 2**(i - 1)) % (2**self.bits)

        self.predecessor = self.id

        self.id_ip = {self.id: self.ip}

        self.successors = []

        self.keys = {}
        self.keys_replic = {}

        self.works = {}

    def getSuccessor(self):
        return self.finger[1].node


    def recieveMessages(self, port):
        context = zmq.Context()

        socket = context.socket(zmq.REP)
        socket.bind(f"tcp://*:{port}")

        while True:
            message = socket.recv()
            # print(message)

            message_dict = jsonToDict(message)

            if isAliveReq(message_dict):
                self.ansAlive(socket, message_dict)

            if isAskSuccessorReq(message_dict):
                self.ansSuccessor(socket, self.getSuccessor())

            if isFindSuccessorReq(message_dict):
                self.ansFindSuccessor(socket, message_dict)

            if isAskPredecessorReq(message_dict):
                self.ansPredecessor(socket, self.predecessor)

            if isSetPredecessorReq(message_dict):
                self.ansSetPredecessor(socket, message_dict)

            if isUpdateFingerTableReq(message_dict):
                self.ansUpdateFingerTable(socket, message_dict)

            if isAksClosestPrecedingFingerReq(message_dict):
                self.ansClosestPrecedingFinger(socket, message_dict)

            if isAskUrlServerReq(message_dict):
                self.ansUrlServer(socket, message_dict)

            if isAskUrlClientReq(message_dict):
                self.ansUrlClient(socket, message_dict)

            if isNotifyReq(message_dict):
                self.ansNotify(socket, message_dict)

            if isClientJoinReq(message_dict):
                self.ansJoin(socket, message_dict)

            # self.printFingerTable()


    def findSuccessor(self, id):
        findPredecessor_id = self.findPredecessor(id)
        if findPredecessor_id != -1:
            n_prima = findPredecessor_id
        # nunca findPredecessor debe retornar -1
        else:
            pass

        if n_prima == id:
            return n_prima
        askSuccessor_id = self.askSuccessor(n_prima)
        if askSuccessor_id != -1:
            return askSuccessor_id
        # n_prima is down
        else:
            while(True):
                askFindSuccessor_id = self.askFindSuccessor(self.successors[0], id)
                if askFindSuccessor_id != -1:
                    return askFindSuccessor_id
                # self.successors[0] is down
                else:
                    self.updateFingerOldId(self.successors[0], self.successors[1])
                    self.successors = self.successors[1:]

    def findPredecessor(self, id):
        n_prima = self.id

        askSuccessor_id = self.askSuccessor(n_prima)
        if askSuccessor_id != -1:
            n_prima_s = askSuccessor_id
        # n_prima is down aunque no debe haber error nunca aquí
        else:
            pass

        while not self.inRange(id, n_prima, False, n_prima_s, True):
            n_prima_temp = n_prima

            askClosestPrecedingFinger_id = self.askClosestPrecedingFinger(n_prima, id)
            if askClosestPrecedingFinger_id != -1:
                n_prima = askClosestPrecedingFinger_id
            # n_prima is down
            else:
                break


            askSuccessor_id2 = self.askSuccessor(n_prima)
            if askSuccessor_id2 != -1:
                n_prima_s = askSuccessor_id2
            # n_prima is down
            else:
                n_prima = n_prima_temp
                break

        if id == n_prima_s:
            return n_prima_s
        return n_prima

    def closestPrecedingFinger(self, id):
        for i in range(self.bits, 0, -1):
            if self.inRange(self.finger[i].node, self.id, False, id, False):
                return self.finger[i].node
        return self.id

    def notify(self, id, keys):
        # print(f'NOTIFY {id}')
        if id != self.predecessor:
            askAlive_id = self.askAlive(self.id_ip[self.predecessor])
        else:
            askAlive_id = 0

        if askAlive_id == -1:
            self.updateReplicKeys()

        if askAlive_id == -1 or self.inRange(id, self.predecessor, False, self.id, False) or id == self.predecessor:
            self.predecessor = id
            self.keys_replic = keys

    def stabilize(self):
        while(True):
            while(True):
                askPredecessor_id = self.askPredecessor(self.getSuccessor())
                if askPredecessor_id != -1:
                    x = askPredecessor_id
                    break
                # self.getSuccessor() is down
                else:
                    self.updateFingerOldId(self.successors[0], self.successors[1])
                    self.successors = self.successors[1:]

            if self.inRange(x, self.id, False, self.getSuccessor(), False) and x != self.id:
                self.finger[1].node = x

            while(True):
                askNotify_id = self.askNotify(self.getSuccessor(), self.id)
                # self.getSuccessor() is down
                if askNotify_id != -1:
                    break
                else:
                    self.updateFingerOldId(self.successors[0], self.successors[1])
                    self.successors = self.successors[1:]

            # self.printFingerTable()
            time.sleep(macros.TIME_STABILIZE)

    def fixFingers(self):
        while(True):
            i = random.randint(1, self.bits)
            findSuccessor_id = self.findSuccessor(self.finger[i].start)
            if findSuccessor_id != -1:
                self.finger[i].node = findSuccessor_id
            #TODO fixFingers Error aunque nunca debe dar error

            time.sleep(macros.TIME_FIXFINGERS)

    def updateSuccessors(self):
        while(True):
            len_s = len(self.successors)
            while len_s < macros.SUCCESSORS_NUMBER:
                askSuccessor_id = self.askSuccessor(self.successors[-1])
                if askSuccessor_id != -1:
                    self.successors.insert(len_s, askSuccessor_id)
                # successors[-1] is down
                else:
                    self.updateFingerOldId(self.successors[-1], self.successors[-2])
                    self.successors = self.successors[:-1]
                len_s = len(self.successors)

            # print(f'Successors {self.successors}')
            
            time.sleep(macros.TIME_SUCCESSORS_REFRESH) 


    def join(self):
        if self.known_ip != self.ip:
            id = self.askAlive(self.known_ip)

            if id != -1:
                self.initFingerTable(id)
                self.update_others()
                return

        print('Im the only node in the network')

        for i in range(1, self.bits + 1):
            self.finger[i].node = self.id
            self.finger[i].node_successor = self.id
        self.predecessor = self.id
        self.successors.insert(0, self.id)

        return


    def initFingerTable(self, node_id):
        # print('init finger table')

        find_successor_id = self.askFindSuccessor(node_id, self.finger[1].start)
        if find_successor_id != -1:
            self.finger[1].node = find_successor_id
            self.successors.insert(0, find_successor_id)
        else:
            raise Exception('ERROR joining')

        ask_predecessor_id = self.askPredecessor(self.getSuccessor())
        if ask_predecessor_id != -1:
            self.predecessor = ask_predecessor_id
        else:
            raise Exception('ERROR joining')

        ask_setPredecessor_ret = self.askSetPredecessor(self.getSuccessor(), self.id)
        if ask_setPredecessor_ret == -1:
            raise Exception('ERROR joining')

        for i in range(1, self.bits):
            if self.inRange(self.finger[i + 1].start, self.id, True, self.finger[i].node, False):
                self.finger[i + 1].node = self.finger[i].node
            else:
                ask_findSuccessor_id = self.askFindSuccessor(node_id, self.finger[i + 1].start)
                if ask_findSuccessor_id != -1:
                    self.finger[i + 1].node = ask_findSuccessor_id
                else:
                    raise Exception('ERROR joining')


    def update_others(self):
        # print('init update_others')
        for i in range(1, self.bits + 1):
            find_predecessor_id = self.findPredecessor((self.id - 2**(i - 1)) % (2**self.bits))
            if find_predecessor_id != -1:
                p = find_predecessor_id
            else:
                raise Exception('ERROR joining')

            if p == self.id:
                continue

            askUpdateFingerTable_id = self.askUpdateFingerTable(p, self.id, i)
            if askUpdateFingerTable_id == -1:
                raise Exception('ERROR joining')


    def updateFingerTable(self, s, i):
        if self.inRange(s, self.id, True, self.finger[i].node, False):
            self.finger[i].node = s
            p = self.predecessor

            if(p != s):
                askUpdateFingerTable_id = self.askUpdateFingerTable(p, s, i)
                # predecessor is down
                if askUpdateFingerTable_id == -1:
                    # TODO
                    pass
    

    def askAlive(self, ip):
        context = zmq.Context()

        socket = context.socket(zmq.REQ)
        socket.connect(f'tcp://{ip}:5555')

        socket.setsockopt( zmq.LINGER, 0)
        socket.setsockopt( zmq.RCVTIMEO, macros.TIME_LIMIT )
        try:
            alive_req_dict = {
                macros.action: macros.alive_req, 
                macros.id: self.id, 
                macros.ip: self.ip
            }
            socket.send_string(dictToJson(alive_req_dict))

            message = socket.recv()
            # print(message)

            message_dict = jsonToDict(message)

            if isAliveRep(message_dict):
                self.id_ip[message_dict[macros.id]] = message_dict[macros.ip]
                return message_dict[macros.id]

        except Exception as e:
            print(e, f'Error AskAlive to {ip}')
            socket.close()
            return -1

    def ansAlive(self, socket, message_dict):
        self.id_ip[message_dict[macros.id]] = message_dict[macros.ip]
        alive_rep_dict = {
            macros.action: macros.alive_rep, 
            macros.id: self.id, 
            macros.ip: self.ip
        }
        socket.send_string(dictToJson(alive_rep_dict))


    def askSuccessor(self, node_id):
        if node_id == self.id:
            return self.getSuccessor()

        context = zmq.Context()
        
        socket = context.socket(zmq.REQ)
        socket.connect(f'tcp://{self.id_ip[node_id]}:5555')

        socket.setsockopt( zmq.LINGER, 0)
        socket.setsockopt( zmq.RCVTIMEO, macros.TIME_LIMIT )

        try:
            ask_successor_req = {macros.action: macros.ask_successor_req}
            # print(ask_successor_req, node_id)
            socket.send_string(dictToJson(ask_successor_req))

            message = socket.recv()
            # print(message)

            message_dict = jsonToDict(message)
            if isAskSuccessorRep(message_dict):
                self.id_ip[message_dict[macros.answer][macros.id]] = message_dict[macros.answer][macros.ip]
                return message_dict[macros.answer][macros.id]
            
        except Exception as e:
            print(e, f'Error askSuccessor to: ID: {node_id}, IP: {self.id_ip[node_id]}')
            socket.close()
            return -1

    def ansSuccessor(self, socket, id):
        ask_successor_rep = {
            macros.action: macros.ask_successor_rep, 
            macros.answer: {
                macros.id: id,
                macros.ip: self.id_ip[id]
            }
        }
        socket.send_string(dictToJson(ask_successor_rep))


    def askFindSuccessor(self, node_id, successor_id):
        context = zmq.Context()

        socket = context.socket(zmq.REQ)
        socket.connect(f'tcp://{self.id_ip[node_id]}:5555')

        socket.setsockopt( zmq.LINGER, 0)
        socket.setsockopt( zmq.RCVTIMEO, macros.TIME_LIMIT )

        try:
            find_successor_req = {
                macros.action: macros.find_successor_req, 
                macros.query: {macros.id: successor_id}
            }
            # print(find_successor_req)
            socket.send_string(dictToJson(find_successor_req))

            message = socket.recv()
            # print(message)

            message_dict = jsonToDict(message)
            if isFindSuccessorRep(message_dict):
                self.id_ip[message_dict[macros.answer][macros.id]] = message_dict[macros.answer][macros.ip]
                return message_dict[macros.answer][macros.id]
        
        except Exception as e:
            print(e, f'Error askFindSuccessor to: ID: {node_id}, IP: {self.id_ip[node_id]}')
            socket.close()
            return -1

    def ansFindSuccessor(self, socket, message_dict):
        id = self.findSuccessor(message_dict[macros.query][macros.id])
        find_successor_rep = {
            macros.action: macros.find_successor_rep, 
            macros.answer: {
                macros.id: id, 
                macros.ip: self.id_ip[id]
            }
        }
        # print(find_successor_rep)
        socket.send_string(dictToJson(find_successor_rep))


    def askPredecessor(self, node_id):
        if node_id == self.id:
            return self.predecessor

        context = zmq.Context()

        socket = context.socket(zmq.REQ)
        socket.connect(f'tcp://{self.id_ip[node_id]}:5555')

        socket.setsockopt( zmq.LINGER, 0)
        socket.setsockopt( zmq.RCVTIMEO, macros.TIME_LIMIT )

        try:
            ask_predecessor_req = {macros.action: macros.ask_predecessor_req}
            socket.send_string(dictToJson(ask_predecessor_req))

            message = socket.recv()
            # print(message)

            message_dict = jsonToDict(message)
            if isAskPredecessorRep(message_dict):
                self.id_ip[message_dict[macros.answer][macros.id]] = message_dict[macros.answer][macros.ip]
                return message_dict[macros.answer][macros.id]

        except Exception as e:
            print(e, f'Error askPredecessor to: ID: {node_id}, IP: {self.id_ip[node_id]}')
            socket.close()
            return -1

    def ansPredecessor(self, socket, id):
        ask_predecessor_rep = {
            macros.action: macros.ask_predecessor_rep, 
            macros.answer: {
                macros.id: id, 
                macros.ip: self.id_ip[id]
            }
        }
        socket.send_string(dictToJson(ask_predecessor_rep))


    def askSetPredecessor(self, node_id, predecessor_id):
        context = zmq.Context()

        socket = context.socket(zmq.REQ)
        socket.connect(f'tcp://{self.id_ip[node_id]}:5555')

        socket.setsockopt( zmq.LINGER, 0)
        socket.setsockopt( zmq.RCVTIMEO, macros.TIME_LIMIT )

        try:
            set_predecessor_req = {
                macros.action: macros.set_predecessor_req, 
                macros.query: {
                    macros.id: predecessor_id, 
                    macros.ip: self.id_ip[predecessor_id]
                }
            }
            socket.send_string(dictToJson(set_predecessor_req))

            message = socket.recv()
            # print(message)

            message_dict = jsonToDict(message)
            if isSetPredecessorRep(message_dict):
                self.keys = message_dict[macros.keys]
                self.keys_replic = message_dict[macros.keys_replic]
                return 0
            
        except Exception as e:
            print(e, f'Error askSetPredecessor to: ID: {node_id}, IP: {self.id_ip[node_id]}')
            socket.close()
            return -1

    def ansSetPredecessor(self, socket, message_dict):
        id = message_dict[macros.query][macros.id]

        keys_replic_ret = self.keys_replic.copy()
        keys_ret = {}
        for url, html in self.keys.items():
            url_id = self.getIdFromUrl(url)
            if self.predecessor < url_id and url_id <= id:
                keys_ret[url] = html

        self.keys_replic = keys_ret

        self.predecessor = id
        self.id_ip[id] = message_dict[macros.query][macros.ip]

        set_predecessor_rep = {
            macros.action: macros.set_predecessor_rep, 
            macros.keys: keys_ret, 
            macros.keys_replic: keys_replic_ret
        }
        socket.send_string(dictToJson(set_predecessor_rep))


    def askUpdateFingerTable(self, node_id, s, i):
        if node_id == self.id:
            self.updateFingerTable(s, i)
            return

        context = zmq.Context()

        socket = context.socket(zmq.REQ)
        socket.connect(f'tcp://{self.id_ip[node_id]}:5555')

        socket.setsockopt( zmq.LINGER, 0)
        socket.setsockopt( zmq.RCVTIMEO, macros.TIME_LIMIT )

        try:
            update_finger_table_req = {
                macros.action: macros.update_finger_table_req, 
                macros.query: {
                    macros.id: s,
                    macros.i: i, 
                    macros.ip: self.id_ip[s]
                }
            }
            socket.send_string(dictToJson(update_finger_table_req))

            message = socket.recv()
            # print(message)

            message_dict = jsonToDict(message)
            if isUpdateFingerTableRep(message_dict):
                return 0
        
        except Exception as e:
            print(e, f'Error askUpdateFingerTable to: ID: {node_id}, IP: {self.id_ip[node_id]}')
            socket.close()
            return -1
    
    def ansUpdateFingerTable(self, socket, message_dict):
        self.id_ip[message_dict[macros.query][macros.id]] = message_dict[macros.query][macros.ip]
        self.updateFingerTable(message_dict[macros.query][macros.id], message_dict[macros.query][macros.i])
        update_finger_table_rep = {macros.action: macros.update_finger_table_rep}
        socket.send_string(dictToJson(update_finger_table_rep))


    def askClosestPrecedingFinger(self, node_id, id):
        if node_id == self.id:
            return self.closestPrecedingFinger(id)

        context = zmq.Context()

        socket = context.socket(zmq.REQ)
        socket.connect(f'tcp://{self.id_ip[node_id]}:5555')

        socket.setsockopt( zmq.LINGER, 0)
        socket.setsockopt( zmq.RCVTIMEO, macros.TIME_LIMIT )

        try:
            ask_closest_preceding_finger_req = {
                macros.action: macros.ask_closest_preceding_finger_req, 
                macros.query: {macros.id: id}
            }
            # print(ask_closest_preceding_finger_req, node_id)
            socket.send_string(dictToJson(ask_closest_preceding_finger_req))

            message = socket.recv()
            # print(message)

            message_dict = jsonToDict(message)
            if isAksClosestPrecedingFingerRep(message_dict):
                self.id_ip[message_dict[macros.answer][macros.id]] = message_dict[macros.answer][macros.ip]
                return message_dict[macros.answer][macros.id]

        except Exception as e:
            print(e, f'Error askClosestPrecedingFinger to: ID: {node_id}, IP: {self.id_ip[node_id]}')
            socket.close()
            return -1

    def ansClosestPrecedingFinger(self, socket, message_dict):
        id = self.closestPrecedingFinger(message_dict[macros.query][macros.id])
        ip = self.id_ip[id]
        ask_closest_preceding_finger_rep = {
            macros.action: macros.ask_closest_preceding_finger_rep, 
            macros.answer: {
                macros.id: id, 
                macros.ip: ip
            }
        }
        socket.send_string(dictToJson(ask_closest_preceding_finger_rep))


    def askUrlServer(self, node_id, key_url):
        if node_id == self.id:
            # print(key_url)
            status = self.upd_url(key_url)
            return self.keys[key_url], status

        context = zmq.Context()

        socket = context.socket(zmq.REQ)
        socket.connect(f'tcp://{self.id_ip[node_id]}:5556')

        socket.setsockopt( zmq.LINGER, 0)
        socket.setsockopt( zmq.RCVTIMEO, macros.URL_TIME_LIMIT )

        try:
            ask_url_server_req = {
                macros.action: macros.ask_url_server_req, 
                macros.query: {macros.url: key_url}
            }
            # print(ask_key_position_req)
            socket.send_string(dictToJson(ask_url_server_req))

            message = socket.recv()
            # print(message)

            message_dict = jsonToDict(message)
            if isAskUrlServerRep(message_dict):
                self.id_ip[message_dict[macros.answer][macros.id]] = message_dict[macros.answer][macros.ip]
                return message_dict[macros.answer][macros.html], message_dict[macros.answer][macros.status]

        except Exception as e:
            print(e, f'Error askKeyPosition to: ID: {node_id}, IP: {self.id_ip[node_id]}')
            socket.close()
            return '' , -1
    
    def upd_url(self, key_url):
        if key_url not in self.keys or self.keys[key_url] == '':
            data, status = get_html_from_url(key_url)
            self.keys[key_url] = data
            return status
        return 0

    def ansUrlServer(self, socket, message_dict):
        key_url = message_dict[macros.query][macros.url]

        status = self.upd_url(key_url)

        ask_url_server_rep = {  
            macros.action: macros.ask_url_server_rep, 
            macros.answer: {
                macros.id: self.id,
                macros.ip: self.ip, 
                macros.html: self.keys[key_url],
                macros.status: status
            }
        }
        socket.send_string(dictToJson(ask_url_server_rep))


    def ansUrlClient(self, socket, message_dict):
        key_url = message_dict[macros.query][macros.url]
        
        url_id = self.getIdFromUrl(key_url)
        node_id = self.findSuccessor(url_id)

        # print(f'NODE IF: {node_id}')
        data, status = self.askUrlServer(node_id, key_url)
        # print(f'DATA: {data}')

        ask_url_client_rep = {
            macros.action: macros.ask_url_client_rep,
            macros.answer:{
                macros.html: data,
                macros.status: status
            }
        }
        socket.send_string(dictToJson(ask_url_client_rep))


    def askNotify(self, node_id, id):
        if node_id == self.id:
            return self.notify(id, self.keys)

        context = zmq.Context()

        socket = context.socket(zmq.REQ)
        socket.connect(f'tcp://{self.id_ip[node_id]}:5555')

        socket.setsockopt( zmq.LINGER, 0)
        socket.setsockopt( zmq.RCVTIMEO, macros.TIME_LIMIT )

        try:
            ask_notify_req = {
                macros.action: macros.notify_req, 
                macros.query: {
                    macros.id: id, 
                    macros.ip: self.id_ip[id]}, 
                macros.keys: self.keys
            }
            socket.send_string(dictToJson(ask_notify_req))

            message = socket.recv()

            message_dict = jsonToDict(message)
            if isNotifyRep(message_dict):
                return 0

        except Exception as e:
            print(e, f'Error askNotify to: ID: {node_id}, IP: {self.id_ip[node_id]}')
            socket.close()
            return -1

    def ansNotify(self, socket, message_dict):
        id = message_dict[macros.query][macros.id]
        keys = message_dict[macros.keys]
        self.id_ip[id] = message_dict[macros.query][macros.ip]
        self.notify(id, keys)
        ask_notify_rep = {macros.action: macros.notify_rep}
        socket.send_string(dictToJson(ask_notify_rep))


    def ansJoin(self, socket, message_dict):
        ips = {self.ip: 1}
        for f in self.finger[1:]:
            ips[self.id_ip[f.node]] = 1
        ips_list = [i for i in ips.keys()]

        client_join_rep = {
            macros.action: macros.client_join_rep, 
            macros.answer: {macros.ip: ips_list}
        }
        socket.send_string(dictToJson(client_join_rep))


    def stabilizationStuff(self):
        threading.Thread(target=self.updateSuccessors, args=()).start()
        time.sleep(macros.TIME_INIT_STABLIZE_STUFF)
        threading.Thread(target=self.stabilize, args=()).start()
        threading.Thread(target=self.fixFingers, args=()).start()


    def run(self):
        threading.Thread(target=self.recieveMessages, args=('5555', )).start()
        threading.Thread(target=self.recieveMessages, args=('5556', )).start()
        threading.Thread(target=self.stabilizationStuff, args=()).start()


    def printFingerTable(self):
        print('Finger table:')
        print(f'Predecessor: {self.predecessor}')
        for i in range(1, self.bits + 1):
            print(f'{self.finger[i].start} {self.finger[i].node}')
        print(self.keys)
        print(self.keys_replic)
        print('---------')

    def inRange(self, key, lwb, lequal, upb, requal):
        l = False
        r = False

        if not lequal:
            lwb += 1
            lwb %= (2**self.bits)
        if not requal:
            upb -= 1
            upb %= (2**self.bits)
        
        if lwb <= upb:
            return lwb <= key and key <= upb 
        else:
            return (lwb <= key and key <= upb + (2**self.bits)) or (lwb <= key + (2**self.bits) and key <= upb)


    def updateFingerOldId(self, id_old, id_new):
        for f in self.finger:
            if f.node == id_old:
                f.node = id_new

    def updateReplicKeys(self):
        for url, html in self.keys_replic.items():
            self.keys[url] = html

    def getIdFromUrl(self, url):
        id_sha = hashlib.sha256()
        id_sha.update(url.encode())
        id = int.from_bytes(id_sha.digest(), sys.byteorder)

        # id %= 2**self.bits

        return id
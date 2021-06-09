import zmq
import threading
import macros
import time
from parser import *
import random

class SubFinger:
    def __init__(self):
        self.start = 0
        self.node = 0
        self.node_succesor = 0


class ChordNode:
    def __init__(self, ip, id, bits, know_ip):
        self.id = int(id)
        self.ip = ip 
        self.bits = int(bits)
        self.know_ip = know_ip

        self.finger = [SubFinger() for _ in range(self.bits + 1)]
        for i in range(1, self.bits + 1):
            self.finger[i].start = (self.id + 2**(i - 1)) % (2**self.bits)

        self.predecesor = self.id

        self.id_ip = {self.id: self.ip}

    def getSuccesor(self):
        return self.finger[1].node


    def recieveMessages(self):
        context = zmq.Context()

        socket = context.socket(zmq.REP)
        socket.bind("tcp://*:5555")

        while True:
            message = socket.recv()
            # print(message)

            message_dict = jsonToDict(message)

            if isAliveReq(message_dict):
                self.ansAlive(socket, message_dict)

            if isAskSuccesorReq(message_dict):
                self.ansSuccesor(socket, self.getSuccesor())

            if isFindSuccesorReq(message_dict):
                self.ansFindSuccesor(socket, message_dict)

            if isAskPredecesorReq(message_dict):
                self.ansPredecesor(socket, self.predecesor)

            if isSetPredecesorReq(message_dict):
                self.ansSetPredecesor(socket, message_dict)

            if isUpdateFingerTableReq(message_dict):
                self.ansUpdateFingerTable(socket, message_dict)

            if isAksClosestPrecedingFingerReq(message_dict):
                self.ansClosesPrecedingFinger(socket, message_dict)

            if isAskKeyPositionReq(message_dict):
                self.ansAskKeyPosition(socket, message_dict)

            if isNotifyReq(message_dict):
                self.ansNotify(socket, message_dict)

            # self.printFingerTable()


    def findSuccesor(self, id):
        n_prima = self.findPredecesor(id)
        if n_prima == id:
            return n_prima
        return self.askSuccesor(n_prima)

    def findPredecesor(self, id):
        n_prima = self.id
        n_prima_s = self.askSuccesor(n_prima)
        while not self.inRange(id, n_prima, False, n_prima_s, True):
            n_prima_temp = n_prima
            n_prima = self.askClosestPrecedingFinger(n_prima, id)
            n_prima_s = self.askSuccesor(n_prima)
        if id == n_prima_s:
            return n_prima_s
        return n_prima

    def closestPrecedingFinger(self, id):
        for i in range(self.bits, 0, -1):
            if self.inRange(self.finger[i].node, self.id, False, id, False):
                return self.finger[i].node
        return self.id

    def notify(self, id):
        if self.inRange(id, self.predecesor, False, self.id, False):
            self.predecesor = id  

    def stabilize(self):
        x = self.askPredecesor(self.getSuccesor())
        if self.inRange(x, self.id, False, self.getSuccesor(), False) and x != self.id:
            self.finger[1].node = x
        self.askNotify(self.getSuccesor(), self.id)
        # self.printFingerTable()

        time.sleep(10)
        threading.Thread(target=self.stabilize, args=()).start()

    def fixFingers(self):
        i = random.randint(1, self.bits)
        self.finger[i].node = self.findSuccesor(self.finger[i].start)
        # self.printFingerTable()

        time.sleep(10)
        threading.Thread(target=self.fixFingers, args=()).start()


    def join(self):
        if self.know_ip == self.ip:
            for i in range(1, self.bits + 1):
                self.finger[i].node = self.id
            self.predecesor = self.id
            return

        id = self.askAlive(self.know_ip)
        if id != -1:
            self.initFingerTable(id)
            self.update_others()

        else:
            print('Im the only node in the network')

            for i in range(1, self.bits + 1):
                self.finger[i].node = self.id
            self.predecesor = self.id


    def initFingerTable(self, node_id):
        # print('init finger table')
        self.finger[1].node = self.askFindSuccesor(node_id, self.finger[1].start)
        self.predecesor = self.askPredecesor(self.getSuccesor())
        self.askSetPredecesor(self.getSuccesor(), self.id)

        for i in range(1, self.bits):
            if self.inRange(self.finger[i + 1].start, self.id, True, self.finger[i].node, False):
                self.finger[i + 1].node = self.finger[i].node
            else:
                self.finger[i + 1].node = self.askFindSuccesor(node_id, self.finger[i + 1].start)


    def update_others(self):
        # print('init update_others')
        for i in range(1, self.bits + 1):
            p = self.findPredecesor((self.id - 2**(i - 1)) % (2**self.bits))

            if p == self.id:
                continue
            self.askUpdateFingerTable(p, self.id, i)


    def updateFingerTable(self, s, i):
        if self.inRange(s, self.id, True, self.finger[i].node, False):
            self.finger[i].node = s
            p = self.predecesor

            if(p != s):
                self.askUpdateFingerTable(p, s, i)


    def askAlive(self, ip):
        context = zmq.Context()

        socket = context.socket(zmq.REQ)
        socket.connect(f'tcp://{ip}:5555')

        socket.setsockopt( zmq.LINGER, 0)
        socket.setsockopt( zmq.RCVTIMEO, macros.TIME_LIMIT )
        try:
            alive_req_dict = {macros.action: macros.alive_req, macros.id: self.id, macros.ip: self.ip}
            socket.send_string(dictToJson(alive_req_dict))

            message = socket.recv()
            print(message)

            message_dict = jsonToDict(message)

            if isAliveRep(message_dict):
                self.id_ip[message_dict[macros.id]] = message_dict[macros.ip]
                return message_dict[macros.id]

        except Exception as e:
            print(e)
            socket.close()
            return -1

    
    def ansAlive(self, socket, message_dict):
        self.id_ip[message_dict[macros.id]] = message_dict[macros.ip]
        alive_rep_dict = {macros.action: macros.alive_rep, macros.id: self.id, macros.ip: self.ip}
        socket.send_string(dictToJson(alive_rep_dict))


    def askSuccesor(self, node_id):
        if node_id == self.id:
            return self.getSuccesor()

        context = zmq.Context()

        socket = context.socket(zmq.REQ)

        socket.connect(f'tcp://{self.id_ip[node_id]}:5555')
        ask_succesor_req = {macros.action: macros.ask_succesor_req}
        # print(ask_succesor_req, node_id)
        socket.send_string(dictToJson(ask_succesor_req))

        message = socket.recv()
        # print(message)

        message_dict = jsonToDict(message)
        if isAskSuccesorRep(message_dict):
            self.id_ip[message_dict[macros.answer]['id']] = message_dict[macros.answer]['ip']
            return message_dict[macros.answer]['id']

    def ansSuccesor(self, socket, id):
        ask_succesor_rep = {macros.action: macros.ask_succesor_rep, macros.answer: {'id': id, 'ip': self.id_ip[id]}}
        socket.send_string(dictToJson(ask_succesor_rep))


    def askFindSuccesor(self, node_id, succesor_id):
        context = zmq.Context()

        socket = context.socket(zmq.REQ)
        socket.connect(f'tcp://{self.id_ip[node_id]}:5555')

        find_succesor_req = {macros.action: macros.find_succesor_req, macros.query: {'id': succesor_id}}
        # print(find_succesor_req)
        socket.send_string(dictToJson(find_succesor_req))

        message = socket.recv()
        # print(message)

        message_dict = jsonToDict(message)
        if isFindSuccesorRep(message_dict):
            self.id_ip[message_dict[macros.answer]['id']] = message_dict[macros.answer]['ip']
            return message_dict[macros.answer]['id']

    def ansFindSuccesor(self, socket, message_dict):
        id = self.findSuccesor(message_dict[macros.query]['id'])
        find_succesor_rep = {macros.action: macros.find_succesor_rep, macros.answer: {'id': id, 'ip': self.id_ip[id]}}
        # print(find_succesor_rep)
        socket.send_string(dictToJson(find_succesor_rep))


    def askPredecesor(self, node_id):
        if node_id == self.id:
            return self.predecesor

        context = zmq.Context()

        socket = context.socket(zmq.REQ)
        socket.connect(f'tcp://{self.id_ip[node_id]}:5555')

        ask_predecesor_req = {macros.action: macros.ask_predecesor_req}
        socket.send_string(dictToJson(ask_predecesor_req))

        message = socket.recv()
        # print(message)

        message_dict = jsonToDict(message)
        if isAskPredecesorRep(message_dict):
            self.id_ip[message_dict[macros.answer]['id']] = message_dict[macros.answer]['ip']
            return message_dict[macros.answer]['id']

    def ansPredecesor(self, socket, id):
        ask_predecesor_rep = {macros.action: macros.ask_predecesor_rep, macros.answer: {'id': id, 'ip': self.id_ip[id]}}
        socket.send_string(dictToJson(ask_predecesor_rep))


    def askSetPredecesor(self, node_id, predecesor_id):
        context = zmq.Context()

        socket = context.socket(zmq.REQ)
        socket.connect(f'tcp://{self.id_ip[node_id]}:5555')

        set_predecesor_req = {macros.action: macros.set_predecesor_req, macros.query: {'id': predecesor_id, 'ip': self.id_ip[predecesor_id]}}
        socket.send_string(dictToJson(set_predecesor_req))

        message = socket.recv()
        # print(message)

        message_dict = jsonToDict(message)
        if isSetPredecesorRep(message_dict):
            return

    def ansSetPredecesor(self, socket, message_dict):
        self.predecesor = message_dict[macros.query]['id']
        self.id_ip[message_dict[macros.query]['id']] = message_dict[macros.query]['ip']
        set_predecesor_rep = {macros.action: macros.set_predecesor_rep}
        socket.send_string(dictToJson(set_predecesor_rep))


    def askUpdateFingerTable(self, node_id, s, i):
        if node_id == self.id:
            self.updateFingerTable(s, i)
            return

        context = zmq.Context()

        socket = context.socket(zmq.REQ)
        socket.connect(f'tcp://{self.id_ip[node_id]}:5555')

        update_finger_table_req = {macros.action: macros.update_finger_table_req, macros.query: {'s': s, 'i': i, 'ip': self.id_ip[s]}}
        socket.send_string(dictToJson(update_finger_table_req))

        message = socket.recv()
        # print(message)

        message_dict = jsonToDict(message)
        if isUpdateFingerTableRep(message_dict):
            return
    
    def ansUpdateFingerTable(self, socket, message_dict):
        self.id_ip[message_dict[macros.query]['s']] = message_dict[macros.query]['ip']
        self.updateFingerTable(message_dict[macros.query]['s'], message_dict[macros.query]['i'])
        update_finger_table_rep = {macros.action: macros.update_finger_table_rep}
        socket.send_string(dictToJson(update_finger_table_rep))


    def askClosestPrecedingFinger(self, node_id, id):
        if node_id == self.id:
            return self.closestPrecedingFinger(id)

        context = zmq.Context()

        socket = context.socket(zmq.REQ)
        socket.connect(f'tcp://{self.id_ip[node_id]}:5555')

        ask_closest_preceding_finger_req = {macros.action: macros.ask_closest_preceding_finger_req, macros.query: {'id': id}}
        # print(ask_closest_preceding_finger_req, node_id)
        socket.send_string(dictToJson(ask_closest_preceding_finger_req))

        message = socket.recv()
        # print(message)

        message_dict = jsonToDict(message)
        if isAksClosestPrecedingFingerRep(message_dict):
            self.id_ip[message_dict[macros.answer]['id']] = message_dict[macros.answer]['ip']
            return message_dict[macros.answer]['id']

    def ansClosesPrecedingFinger(self, socket, message_dict):
        id = self.closestPrecedingFinger(message_dict[macros.query]['id'])
        ip = self.id_ip[id]
        ask_closest_preceding_finger_rep = {macros.action: macros.ask_closest_preceding_finger_rep, macros.answer: {'id': id, 'ip': ip}}
        socket.send_string(dictToJson(ask_closest_preceding_finger_rep))

    
    def ansAskKeyPosition(self, socket, message_dict):
        id = message_dict[macros.query]['id']
        ans_id = self.findSuccesor(id)

        ans_ask_key_position_rep = {macros.action: macros.ask_key_position_rep, macros.answer: {'id': ans_id, 'ip': self.id_ip[ans_id]}}
        socket.send_string(dictToJson(ans_ask_key_position_rep))


    def askNotify(self, node_id, id):
        if node_id == self.id:
            return self.notify(id)

        context = zmq.Context()

        socket = context.socket(zmq.REQ)
        socket.connect(f'tcp://{self.id_ip[node_id]}:5555')

        ask_notify_req = {macros.action: macros.notify_req, macros.query: {'id': id, 'ip': self.id_ip[id]}}
        socket.send_string(dictToJson(ask_notify_req))

        message = socket.recv()

        message_dict = jsonToDict(message)
        if isNotifyRep(message_dict):
            return

    def ansNotify(self, socket, message_dict):
        id = message_dict[macros.query]['id']
        self.id_ip[id] = message_dict[macros.query]['ip']
        self.notify(id)
        ask_notify_rep = {macros.action: macros.notify_rep}
        socket.send_string(dictToJson(ask_notify_rep))


    def stabilizationStuff(self):
        time.sleep(30)
        threading.Thread(target=self.stabilize, args=()).start()
        threading.Thread(target=self.fixFingers, args=()).start()


    def run(self):
        threading.Thread(target=self.recieveMessages, args=()).start()
        threading.Thread(target=self.stabilizationStuff, args=()).start()


    def printFingerTable(self):
        print('Finger table:')
        print(f'Predecesor: {self.predecesor}')
        for i in range(1, self.bits + 1):
            print(f'{self.finger[i].start} {self.finger[i].interval} {self.finger[i].node}')
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

    def searchNodeSuccesorInFinger(self, id):
        for f in self.finger:
            if f.node == id:
                return f.node_succesor

    def assingSuccesorNodeToNode(self, id):
        for f in self.finger:
            if f.node == id:
                f.node = f.node_succesor
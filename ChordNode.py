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

        self.succesors = []

        self.keys = {}
        self.keys_replic = {}

        self.works = {}

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

            if isAskUrlServerReq(message_dict):
                self.ansUrlServer(socket, message_dict)

            if isAskUrlClientReq(message_dict):
                self.ansUrlClient(socket, message_dict)

            if isNotifyReq(message_dict):
                self.ansNotify(socket, message_dict)

            if isClientJoinReq(message_dict):
                self.ansJoin(socket, message_dict)

            # self.printFingerTable()


    def findSuccesor(self, id):
        findPredecesor_id = self.findPredecesor(id)
        if findPredecesor_id != -1:
            n_prima = findPredecesor_id
        # nunca findPredecesor debe retornar -1
        else:
            pass

        if n_prima == id:
            return n_prima
        askSuccesor_id = self.askSuccesor(n_prima)
        if askSuccesor_id != -1:
            return askSuccesor_id
        # n_prima is down
        else:
            while(True):
                askFindSuccesor_id = self.askFindSuccesor(self.succesors[0], id)
                if askFindSuccesor_id != -1:
                    return askFindSuccesor_id
                # self.succesors[0] is down
                else:
                    self.updateFingerOldId(self.succesors[0], self.succesors[1])
                    self.succesors = self.succesors[1:]

    def findPredecesor(self, id):
        n_prima = self.id

        askSuccesor_id = self.askSuccesor(n_prima)
        if askSuccesor_id != -1:
            n_prima_s = askSuccesor_id
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


            askSuccesor_id2 = self.askSuccesor(n_prima)
            if askSuccesor_id2 != -1:
                n_prima_s = askSuccesor_id2
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
        if id != self.predecesor:
            askAlive_id = self.askAlive(self.id_ip[self.predecesor])
        else:
            askAlive_id = 0

        if askAlive_id == -1:
            self.updateReplicKeys()

        if askAlive_id == -1 or self.inRange(id, self.predecesor, False, self.id, False) or id == self.predecesor:
            self.predecesor = id
            self.keys_replic = keys

    def stabilize(self):
        while(True):
            while(True):
                askPredecesor_id = self.askPredecesor(self.getSuccesor())
                if askPredecesor_id != -1:
                    x = askPredecesor_id
                    break
                # self.getSuccesor() is down
                else:
                    self.updateFingerOldId(self.succesors[0], self.succesors[1])
                    self.succesors = self.succesors[1:]

            if self.inRange(x, self.id, False, self.getSuccesor(), False) and x != self.id:
                self.finger[1].node = x

            while(True):
                askNotify_id = self.askNotify(self.getSuccesor(), self.id)
                # self.getSuccesor() is down
                if askNotify_id != -1:
                    break
                else:
                    self.updateFingerOldId(self.succesors[0], self.succesors[1])
                    self.succesors = self.succesors[1:]

            self.printFingerTable()
            time.sleep(macros.TIME_STABILIZE)

    def fixFingers(self):
        while(True):
            i = random.randint(1, self.bits)
            findSuccesor_id = self.findSuccesor(self.finger[i].start)
            if findSuccesor_id != -1:
                self.finger[i].node = findSuccesor_id
            #TODO fixFingers Error aunque nunca debe dar error

            time.sleep(macros.TIME_FIXFINGERS)

    def updateSuccesors(self):
        while(True):
            len_s = len(self.succesors)
            while len_s < macros.SUCCESORS_NUMBER:
                askSuccesor_id = self.askSuccesor(self.succesors[-1])
                if askSuccesor_id != -1:
                    self.succesors.insert(len_s, askSuccesor_id)
                # succesors[-1] is down
                else:
                    self.updateFingerOldId(self.succesors[-1], self.succesors[-2])
                    self.succesors = self.succesors[:-1]
                len_s = len(self.succesors)

            # print(f'Succesors {self.succesors}')
            
            time.sleep(macros.TIME_SUCCESORS_REFRESH) 


    def join(self):
        if self.know_ip != self.ip:
            id = self.askAlive(self.know_ip)

            if id != -1:
                self.initFingerTable(id)
                self.update_others()
                return

        print('Im the only node in the network')

        for i in range(1, self.bits + 1):
            self.finger[i].node = self.id
            self.finger[i].node_succesor = self.id
        self.predecesor = self.id
        self.succesors.insert(0, self.id)

        return


    def initFingerTable(self, node_id):
        # print('init finger table')

        find_succesor_id = self.askFindSuccesor(node_id, self.finger[1].start)
        if find_succesor_id != -1:
            self.finger[1].node = find_succesor_id
            self.succesors.insert(0, find_succesor_id)
        else:
            raise Exception('ERROR joining')

        ask_predecesor_id = self.askPredecesor(self.getSuccesor())
        if ask_predecesor_id != -1:
            self.predecesor = ask_predecesor_id
        else:
            raise Exception('ERROR joining')

        ask_setPredecesor_ret = self.askSetPredecesor(self.getSuccesor(), self.id)
        if ask_setPredecesor_ret == -1:
            raise Exception('ERROR joining')

        for i in range(1, self.bits):
            if self.inRange(self.finger[i + 1].start, self.id, True, self.finger[i].node, False):
                self.finger[i + 1].node = self.finger[i].node
            else:
                ask_findSuccesor_id = self.askFindSuccesor(node_id, self.finger[i + 1].start)
                if ask_findSuccesor_id != -1:
                    self.finger[i + 1].node = ask_findSuccesor_id
                else:
                    raise Exception('ERROR joining')


    def update_others(self):
        # print('init update_others')
        for i in range(1, self.bits + 1):
            find_predecesor_id = self.findPredecesor((self.id - 2**(i - 1)) % (2**self.bits))
            if find_predecesor_id != -1:
                p = find_predecesor_id
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
            p = self.predecesor

            if(p != s):
                askUpdateFingerTable_id = self.askUpdateFingerTable(p, s, i)
                # predecesor is down
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
            alive_req_dict = {macros.action: macros.alive_req, macros.id: self.id, macros.ip: self.ip}
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
        alive_rep_dict = {macros.action: macros.alive_rep, macros.id: self.id, macros.ip: self.ip}
        socket.send_string(dictToJson(alive_rep_dict))


    def askSuccesor(self, node_id):
        if node_id == self.id:
            return self.getSuccesor()

        context = zmq.Context()
        
        socket = context.socket(zmq.REQ)
        socket.connect(f'tcp://{self.id_ip[node_id]}:5555')

        socket.setsockopt( zmq.LINGER, 0)
        socket.setsockopt( zmq.RCVTIMEO, macros.TIME_LIMIT )

        try:
            ask_succesor_req = {macros.action: macros.ask_succesor_req}
            # print(ask_succesor_req, node_id)
            socket.send_string(dictToJson(ask_succesor_req))

            message = socket.recv()
            # print(message)

            message_dict = jsonToDict(message)
            if isAskSuccesorRep(message_dict):
                self.id_ip[message_dict[macros.answer]['id']] = message_dict[macros.answer]['ip']
                return message_dict[macros.answer]['id']
            
        except Exception as e:
            print(e, f'Error askSuccesor to: ID: {node_id}, IP: {self.id_ip[node_id]}')
            socket.close()
            return -1

    def ansSuccesor(self, socket, id):
        ask_succesor_rep = {macros.action: macros.ask_succesor_rep, macros.answer: {'id': id, 'ip': self.id_ip[id]}}
        socket.send_string(dictToJson(ask_succesor_rep))


    def askFindSuccesor(self, node_id, succesor_id):
        context = zmq.Context()

        socket = context.socket(zmq.REQ)
        socket.connect(f'tcp://{self.id_ip[node_id]}:5555')

        socket.setsockopt( zmq.LINGER, 0)
        socket.setsockopt( zmq.RCVTIMEO, macros.TIME_LIMIT )

        try:
            find_succesor_req = {macros.action: macros.find_succesor_req, macros.query: {'id': succesor_id}}
            # print(find_succesor_req)
            socket.send_string(dictToJson(find_succesor_req))

            message = socket.recv()
            # print(message)

            message_dict = jsonToDict(message)
            if isFindSuccesorRep(message_dict):
                self.id_ip[message_dict[macros.answer]['id']] = message_dict[macros.answer]['ip']
                return message_dict[macros.answer]['id']
        
        except Exception as e:
            print(e, f'Error askFindSuccesor to: ID: {node_id}, IP: {self.id_ip[node_id]}')
            socket.close()
            return -1

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

        socket.setsockopt( zmq.LINGER, 0)
        socket.setsockopt( zmq.RCVTIMEO, macros.TIME_LIMIT )

        try:
            ask_predecesor_req = {macros.action: macros.ask_predecesor_req}
            socket.send_string(dictToJson(ask_predecesor_req))

            message = socket.recv()
            # print(message)

            message_dict = jsonToDict(message)
            if isAskPredecesorRep(message_dict):
                self.id_ip[message_dict[macros.answer]['id']] = message_dict[macros.answer]['ip']
                return message_dict[macros.answer]['id']

        except Exception as e:
            print(e, f'Error askPredecesor to: ID: {node_id}, IP: {self.id_ip[node_id]}')
            socket.close()
            return -1

    def ansPredecesor(self, socket, id):
        ask_predecesor_rep = {macros.action: macros.ask_predecesor_rep, macros.answer: {'id': id, 'ip': self.id_ip[id]}}
        socket.send_string(dictToJson(ask_predecesor_rep))


    def askSetPredecesor(self, node_id, predecesor_id):
        context = zmq.Context()

        socket = context.socket(zmq.REQ)
        socket.connect(f'tcp://{self.id_ip[node_id]}:5555')

        socket.setsockopt( zmq.LINGER, 0)
        socket.setsockopt( zmq.RCVTIMEO, macros.TIME_LIMIT )

        try:
            set_predecesor_req = {macros.action: macros.set_predecesor_req, macros.query: {'id': predecesor_id, 'ip': self.id_ip[predecesor_id]}}
            socket.send_string(dictToJson(set_predecesor_req))

            message = socket.recv()
            # print(message)

            message_dict = jsonToDict(message)
            if isSetPredecesorRep(message_dict):
                self.keys = message_dict[macros.keys]
                self.keys_replic = message_dict[macros.keys_replic]
                return 0
            
        except Exception as e:
            print(e, f'Error askSetPredecesor to: ID: {node_id}, IP: {self.id_ip[node_id]}')
            socket.close()
            return -1

    def ansSetPredecesor(self, socket, message_dict):
        id = message_dict[macros.query]['id']

        keys_replic_ret = self.keys_replic.copy()
        keys_ret = {}
        for url, html in self.keys.items():
            url_id = self.getIdFromUrl(url)
            if self.predecesor < url_id and url_id <= id:
                keys_ret[url] = html

        self.keys_replic = keys_ret

        self.predecesor = id
        self.id_ip[id] = message_dict[macros.query]['ip']

        set_predecesor_rep = {macros.action: macros.set_predecesor_rep, macros.keys: keys_ret, macros.keys_replic: keys_replic_ret}
        socket.send_string(dictToJson(set_predecesor_rep))


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
            update_finger_table_req = {macros.action: macros.update_finger_table_req, macros.query: {'s': s, 'i': i, 'ip': self.id_ip[s]}}
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

        socket.setsockopt( zmq.LINGER, 0)
        socket.setsockopt( zmq.RCVTIMEO, macros.TIME_LIMIT )

        try:
            ask_closest_preceding_finger_req = {macros.action: macros.ask_closest_preceding_finger_req, macros.query: {'id': id}}
            # print(ask_closest_preceding_finger_req, node_id)
            socket.send_string(dictToJson(ask_closest_preceding_finger_req))

            message = socket.recv()
            # print(message)

            message_dict = jsonToDict(message)
            if isAksClosestPrecedingFingerRep(message_dict):
                self.id_ip[message_dict[macros.answer]['id']] = message_dict[macros.answer]['ip']
                return message_dict[macros.answer]['id']

        except Exception as e:
            print(e, f'Error askClosestPrecedingFinger to: ID: {node_id}, IP: {self.id_ip[node_id]}')
            socket.close()
            return -1

    def ansClosesPrecedingFinger(self, socket, message_dict):
        id = self.closestPrecedingFinger(message_dict[macros.query]['id'])
        ip = self.id_ip[id]
        ask_closest_preceding_finger_rep = {macros.action: macros.ask_closest_preceding_finger_rep, macros.answer: {'id': id, 'ip': ip}}
        socket.send_string(dictToJson(ask_closest_preceding_finger_rep))


    def askUrlServer(self, node_id, key_url):
        if node_id == self.id:
            status = self.upd_url(key_url)
            return self.keys[key_url], status

        context = zmq.Context()

        socket = context.socket(zmq.REQ)
        socket.connect(f'tcp://{self.id_ip[node_id]}:5555')

        socket.setsockopt( zmq.LINGER, 0)
        socket.setsockopt( zmq.RCVTIMEO, macros.TIME_LIMIT )

        try:
            ask_url_server_req = {
                macros.action: macros.ask_url_server_req, 
                macros.query: {'url': key_url}
            }
            # print(ask_key_position_req)
            socket.send_string(dictToJson(ask_url_server_req))

            message = socket.recv()
            print(message)

            message_dict = jsonToDict(message)
            if isAskUrlServerRep(message_dict):
                self.id_ip[message_dict[macros.answer]['id']] = message_dict[macros.answer]['ip']
                return message_dict[macros.answer]['html'], message_dict[macros.status]

        except Exception as e:
            print(e, f'Error askKeyPosition to: ID: {node_id}, IP: {self.id_ip[node_id]}')
            socket.close()
            return '' , -1
    
    def upd_url(self, key_url):
        if key_url not in self.keys:
            data, status = get_html_from_url(key_url)
            self.keys[key_url] = data
            return status
        return 0

    def ansUrlServer(self, socket, message_dict):
        key_url = message_dict[macros.query]['url']

        status = self.upd_url(key_url)

        ask_url_server_rep = {  
            macros.action: macros.ask_url_server_rep, 
            macros.answer: {'id': self.id,
                            'ip': self.ip, 
                            'html': self.keys[key_url],
                            macros.status: status},
        }
        socket.send_string(dictToJson(ask_url_server_rep))


    def ansUrlClient(self, socket, message_dict):
        key_url = message_dict[macros.query]['url']
        
        url_id = self.getIdFromUrl(key_url)
        node_id = self.findSuccesor(url_id)

        data, status = self.askUrlServer(node_id, key_url)

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
            ask_notify_req = {macros.action: macros.notify_req, macros.query: {'id': id, 'ip': self.id_ip[id]}, macros.keys: self.keys}
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
        id = message_dict[macros.query]['id']
        keys = message_dict[macros.keys]
        self.id_ip[id] = message_dict[macros.query]['ip']
        self.notify(id, keys)
        ask_notify_rep = {macros.action: macros.notify_rep}
        socket.send_string(dictToJson(ask_notify_rep))


    def ansJoin(self, socket, message_dict):
        ips = {self.ip: 1}
        for f in self.finger[1:]:
            ips[self.id_ip[f.node]] = 1
        ips_list = [i for i in ips.keys()]

        client_join_rep = {macros.action: macros.client_join_rep, macros.answer: {macros.ip: ips_list}}
        socket.send_string(dictToJson(client_join_rep))


    def stabilizationStuff(self):
        threading.Thread(target=self.updateSuccesors, args=()).start()
        time.sleep(macros.TIME_INIT_STABLIZE_STUFF)
        threading.Thread(target=self.stabilize, args=()).start()
        threading.Thread(target=self.fixFingers, args=()).start()


    def run(self):
        threading.Thread(target=self.recieveMessages, args=()).start()
        threading.Thread(target=self.stabilizationStuff, args=()).start()


    def printFingerTable(self):
        print('Finger table:')
        print(f'Predecesor: {self.predecesor}')
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
        # id_sha = hashlib.sha256()
        # id_sha.update(url.encode())
        # id = int.from_bytes(id_sha.digest(), sys.byteorder)

        id = len(url)
        id %= 2**self.bits

        return id
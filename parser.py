import json
import macros

def jsonToDict(json_text):
    return json.loads(json_text)

def dictToJson(dict):
    return json.dumps(dict)


def isAliveReq(message_dict):
    return message_dict[macros.action] == macros.alive_req

def isAliveRep(message_dict):
    return message_dict[macros.action] == macros.alive_rep


def isAskSuccessorReq(message_dict):
    return message_dict[macros.action] == macros.ask_successor_req

def isAskSuccessorRep(message_dict):
    return message_dict[macros.action] == macros.ask_successor_rep


def isFindSuccessorReq(message_dict):
    return message_dict[macros.action] == macros.find_successor_req

def isFindSuccessorRep(message_dict):
    return message_dict[macros.action] == macros.find_successor_rep


def isAskPredecessorReq(message_dict):
    return message_dict[macros.action] == macros.ask_predecessor_req

def isAskPredecessorRep(message_dict):
    return message_dict[macros.action] == macros.ask_predecessor_rep


def isSetPredecessorReq(message_dict):
    return message_dict[macros.action] == macros.set_predecessor_req

def isSetPredecessorRep(message_dict):
    return message_dict[macros.action] == macros.set_predecessor_rep


def isUpdateFingerTableReq(message_dict):
    return message_dict[macros.action] == macros.update_finger_table_req

def isUpdateFingerTableRep(message_dict):
    return message_dict[macros.action] == macros.update_finger_table_rep


def isAksClosestPrecedingFingerReq(message_dict):
    return message_dict[macros.action] == macros.ask_closest_preceding_finger_req

def isAksClosestPrecedingFingerRep(message_dict):
    return message_dict[macros.action] == macros.ask_closest_preceding_finger_rep


def isAskUrlClientReq(message_dict):
    return message_dict[macros.action] == macros.ask_url_client_req

def isAskUrlClientRep(message_dict):
    return message_dict[macros.action] == macros.ask_url_client_rep


def isAskUrlServerReq(message_dict):
    return message_dict[macros.action] == macros.ask_url_server_req

def isAskUrlServerRep(message_dict):
    return message_dict[macros.action] == macros.ask_url_server_rep


def isNotifyReq(message_dict):
    return message_dict[macros.action] == macros.notify_req

def isNotifyRep(message_dict):
    return message_dict[macros.action] == macros.notify_rep


def isClientJoinReq(message_dict):
    return message_dict[macros.action] == macros.client_join_req

def isClientJoinRep(message_dict):
    return message_dict[macros.action] == macros.client_join_rep
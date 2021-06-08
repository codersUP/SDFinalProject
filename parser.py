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


def isAskSuccesorReq(message_dict):
    return message_dict[macros.action] == macros.ask_succesor_req

def isAskSuccesorRep(message_dict):
    return message_dict[macros.action] == macros.ask_succesor_rep


def isFindSuccesorReq(message_dict):
    return message_dict[macros.action] == macros.find_succesor_req

def isFindSuccesorRep(message_dict):
    return message_dict[macros.action] == macros.find_succesor_rep


def isAskPredecesorReq(message_dict):
    return message_dict[macros.action] == macros.ask_predecesor_req

def isAskPredecesorRep(message_dict):
    return message_dict[macros.action] == macros.ask_predecesor_rep


def isSetPredecesorReq(message_dict):
    return message_dict[macros.action] == macros.set_predecesor_req

def isSetPredecesorRep(message_dict):
    return message_dict[macros.action] == macros.set_predecesor_rep


def isUpdateFingerTableReq(message_dict):
    return message_dict[macros.action] == macros.update_finger_table_req

def isUpdateFingerTableRep(message_dict):
    return message_dict[macros.action] == macros.update_finger_table_rep


def isAksClosestPrecedingFingerReq(message_dict):
    return message_dict[macros.action] == macros.ask_closest_preceding_finger_req

def isAksClosestPrecedingFingerRep(message_dict):
    return message_dict[macros.action] == macros.ask_closest_preceding_finger_rep


def isAskKeyPositionReq(message_dict):
    return message_dict[macros.action] == macros.ask_key_position_req

def isAskKeyPositionRep(message_dict):
    return message_dict[macros.action] == macros.ask_key_position_rep

def isNotifyReq(message_dict):
    return message_dict[macros.action] == macros.notify_req

def isNotifyRep(message_dict):
    return message_dict[macros.action] == macros.notify_rep
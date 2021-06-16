action = 'action'

i = 'i'
id = 'id'
ip = 'ip'
query = 'query'
answer = 'answer'
keys = 'keys'
keys_replic = 'keys_replic'
url = 'url'
html = 'html'
depth = 'depth'
status = 'status'

client_ip = 'client_ip'
client_port = 'client_port'
client_query_id = 'client_query_id'

alive_req = 'alive_req'
alive_rep = 'alive_rep'

ask_successor_req = 'ask_successor_req'
ask_successor_rep = 'ask_successor_rep'

find_successor_req = 'find_successor_req'
find_successor_rep = 'find_successor_rep'

ask_predecessor_req = 'ask_predecessor_req'
ask_predecessor_rep = 'ask_predecessor_rep'

set_predecessor_req = 'set_predecessor_req'
set_predecessor_rep = 'set_predecessor_rep'

update_finger_table_req = 'update_finger_table_req'
update_finger_table_rep = 'update_finger_table_rep'

ask_closest_preceding_finger_req = 'ask_closest_preceding_finger_req'
ask_closest_preceding_finger_rep = 'ask_closest_preceding_finger_rep'

ask_url_client_req = 'ask_url_client_req'
ask_url_client_rep = 'ask_url_client_rep'

ask_url_server_req = 'ask_url_server_req'
ask_url_server_rep = 'ask_url_server_rep'

notify_req = 'notify_req'
notify_rep = 'notify_rep'

client_join_req = 'client_join_req'
client_join_rep = 'client_join_rep'

send_html_req = 'send_html_req'
send_html_rep = 'send_html_rep'

ask_url_end_req = 'ask_url_end_req'
ask_url_end_rep = 'ask_url_end_rep'

TIME_LIMIT = 5000 # ms
URL_TIME_LIMIT = 100000 # ms
TIME_FIXFINGERS = 1 # s
TIME_STABILIZE = 1 # s
TIME_SUCCESSORS_REFRESH = 1
TIME_INIT_STABLIZE_STUFF = 5 # s

SUCCESSORS_NUMBER = 20
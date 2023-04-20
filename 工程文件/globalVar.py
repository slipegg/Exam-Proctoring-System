import threading
from get_conf import get_conf
from DBhelper import *

# {
#     'monitor_id': {
#         'client_id': {
#             'camera': {'fd':fd, 'force_close':False},
#             'screen': {'fd':fd, 'force_close':False}
#         },
#         'client_id': {
#             'camera': fd,
#             'screen': fd
#         },
#     }
# }
monitors = {}

# {
#     'client_id': {
#         'username': str,
#         'screen': {'fd': fd, 'audio': True},
#         'camera': {'fd': fd, 'audio': True},
#         'monitor_id': []
#     },
# }
clients = {}

client_lock = threading.Lock()
monitor_lock = threading.Lock()


config = {}
def loadConfig(config_path):
    f = open(config_path, 'r', encoding='gbk')
    txt = f.read()
    global config
    config = get_conf(txt)
    print(config)


def getRootDir():
    if 'root-dir' not in config:
        print("can't find root directory")
        exit(-1)
    root_dir = config['root-dir']
    if not root_dir.endswith('/'):
        root_dir += '/'
    return root_dir


loadConfig('webrtc-hkl.conf')


login_user_lock = threading.Lock()
login_user = {}
for client in db_helper.getAllClients():
    login_user[client['id']] = {'camera': False, 'screen': False, 'username':client['username']}

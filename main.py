from BlocksFunc.blocks import BlockManager
from SocketServer.socket_connections import Server, StartConnection, USERLIST, get_file_data, NetworkFunc
from ClientFunc.interface import Interface
import threading
import hashlib
import re
import sys
from matplotlib import pyplot as plt

def start_listen(chain, addr):
    return Server(chain, addr).open_server()


def start_interface(chain, login):
    return Interface(chain, login)

IP_ADDR = 'XXX.XXX.XXX.XXX' # You're local IP-address
SUBNET = re.match(r'\d+.\d+.\d+.', IP_ADDR).group() + '0/24'

login = input('Введите ваш логин: ')
password = input('Введите ваш пароль: ')
hash_log = hashlib.sha256(bytes(login.encode())).hexdigest()
hash_passwd = hashlib.sha256(bytes(password.encode())).hexdigest()
login_pkt = ['cv_acc', {hash_log: hash_passwd}]

chain = BlockManager('blockchain')
th1 = threading.Thread(target=start_listen, args=(chain, IP_ADDR,))
th1.start()


if StartConnection(IP_ADDR, login_pkt, SUBNET).find_hosts():
    print('Вы ввели неверный логин или пароль')
    Interface.exit()
    sys.exit(0)
else:
    chain.create_manager()
    NetworkFunc.send_to_all([USERLIST[:-4], get_file_data(USERLIST)])
    th2 = threading.Thread(target=start_interface, args=(chain, login))
    th2.start()

import socket
import threading
import json
from dataclasses import dataclass, field
from ipaddress import IPv4Network
import os, time
import hashlib

USERLIST = 'userlist.txt'
PASSFILE = 'accounts.txt'
BALANCE_FILE = 'balance.txt'

class Server:
    PORT = 20137
    def __init__(self, bm, addr):
        self.__addr = addr
        Server.MY_ADDR = addr
        self.__port = Server.PORT
        Server.BlockManager = bm

    def __get_client(self, sock, addr):
        #print('Получено соединение', addr)
        try:
            with open(USERLIST, 'r') as userlist:
                users = json.load(userlist)
        except:
            NetworkFunc.listen_data(sock, addr)
            sock.close()
            return 0


        if addr[0] in users.keys(): # Если пользователь уже онлайн
            NetworkFunc.listen_data(sock, addr)

        else: # Если не онлайн
            NetworkFunc.listen_data(sock, addr)
            
            with open(USERLIST, 'r') as userlist:
                users = json.load(userlist)
                
            if addr[0] in users.keys():
                sock.close()
                return 0
                
            while True:
                if NetworkFunc.SEND_MARKER == True:
                    #print('Отправка разрешена')
                    users[addr[0]] = time.asctime()
                    with open(USERLIST, 'w') as userlist:
                        json.dump(users, userlist, indent=1)
                    sock.close()
                    sock = socket.socket()
                    sock.connect((addr[0], StartConnection.PORT))
                    self.__send_file_data(sock)
                    break
                elif NetworkFunc.SEND_MARKER == 'denied':
                    #print('Отправка запрещена')
                    sock.close()
                    break
                else:
                    continue
            else:
                pass
            NetworkFunc.SEND_MARKER = False
        sock.close()
            
    def __send_file_data(self, sock):
        balance_list = [BALANCE_FILE[:-4], get_file_data(BALANCE_FILE)]
        acc_list = [PASSFILE[:-4], get_file_data(PASSFILE)]
        u_list = [USERLIST[:-4], get_file_data(USERLIST)]
        
        for block in Server.BlockManager.get_all_blocks():
            NetworkFunc.send_to_addr(sock, block)
        
        NetworkFunc.send_to_addr(sock, balance_list, acc_list, u_list)
        NetworkFunc.send_exitcode(sock)
        sock.close()
        


    def open_server(self):
        Server.SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        Server.SERVER.bind((self.__addr, self.__port))
        Server.SERVER.listen()

        Server.object_list = []
        try:
            while True:
                obj = self.Connection(Server.SERVER.accept())
                Server.object_list.append(obj)
                th = threading.Thread(target=(self.__get_client), args=(obj.conn, obj.addr,))
                th.start()
        except:
            for o in Server.object_list:
                o.close_connection()
                print('Off')
            Server.SERVER.close()

        Server.SERVER.close()

    @classmethod
    def close_server(cls):
        for o in Server.object_list:
            o.close_connection()
            print('Object was disconnected')

        Server.SERVER.close()

    class Connection:
        def __init__(self, accept):
            self.conn = accept[0]
            self.addr = accept[1]
        
        def close_connection(self):
            self.conn.close()
@dataclass
class StartConnection:
    PORT = 20137
    UPDATE_STATUS = False

    hostaddr: str
    login_data : list
    net: str = field(default='192.168.1.0/24')

    def __post_init__(self):
        StartConnection.MY_ADDR = self.hostaddr

    def __go_conn(self, addr_tup):
        if self.UPDATE_STATUS:
            return 0
        else:
            cl = socket.socket()
            try:
                cl.connect(addr_tup)
                self.UPDATE_STATUS = True
                NetworkFunc.send_to_addr(cl, self.login_data)
                NetworkFunc.send_exitcode(cl)
                cl.close()
            except:
                cl.close()
                return 0

    @staticmethod
    def get_files(split_data):
        #print('Получаем файлы')
        for element in split_data:
            obj = json.loads(element.replace('\'', '\"'))
            if obj[0] in [BALANCE_FILE[:-4], PASSFILE[:-4], USERLIST[:-4]]:
                with open(obj[0] + '.txt', 'w') as file:
                    json.dump(obj[1], file, indent=1)
            else:
                with open(os.path.join('blockchain', obj[0] + '.txt'), 'w') as file:
                    json.dump(obj[1], file, indent=1)
        #print('Загрузка файлов завершена')
        
    def find_hosts(self):
        with open(USERLIST, 'w') as userlist:
            json.dump({self.hostaddr: time.asctime()}, userlist, indent=1)

        for addr in IPv4Network(self.net):
            if str(addr) == self.hostaddr:
                continue
            else:
                th = threading.Thread(target=(self.__go_conn), args=((str(addr), self.PORT),))
                th.start()

        time.sleep(5)

        if not self.UPDATE_STATUS:
            for key in self.login_data[1].keys():
                try:
                    if get_file_data(PASSFILE)[key] == self.login_data[1][key]:
                        return 0
                    else:
                        return 1
                except:
                    return 1
        else:
            if len(get_file_data(USERLIST)) == 1:
                return 1
            else:
                return 0

@dataclass
class NetworkFunc:
    VALID_COUNTER = 0
    REPLY_NUMS = 0
    SEND_MARKER = False

    @classmethod
    def listen_data(cls, sock, cl_addr):
        COMMAND_DICT = {
            'cv_acc': cls.cv_account,
            'cv_bl' : cls.cv_block,
            'cv_tr' : cls.cv_transaction,
            'c_valid' : cls.count_valid,
            'cv_sign_in' : cls.cv_sign_in,
            'add_tr' : cls.add_tr,
            'add_bl' : cls.add_block,
            'exit' : cls.user_exit
        }
        data = ''
        while True:
            data += sock.recv(65565).decode()
            if data:
                if 'EXITCODE' == data[-8:]:
                    split_data = data.split('ENDMARK')
                    split_data.pop(-1)
                    #print(split_data)
                    for element in split_data:
                        obj = json.loads(element.replace('\'', '\"'))
                        if obj[0] in ['0.0', BALANCE_FILE[:-4], PASSFILE[:-4], USERLIST[:-4]]:
                            StartConnection.get_files(split_data)
                            sock.close()
                            break

                        command_dict_code = COMMAND_DICT[obj[0]](obj[1])
                        if not command_dict_code or command_dict_code == 2:
                            s_reply = socket.socket()
                            s_reply.connect((cl_addr[0], StartConnection.PORT))
                            NetworkFunc.send_to_addr(s_reply, ['c_valid', [sock.getsockname()[0], command_dict_code]])
                            NetworkFunc.send_exitcode(s_reply)
                        else:
                            pass
                    break
            else:
                continue
        #sock.close()

    @classmethod
    def add_block(cls, block):
        num = block[0]
        cl_str = block[1]
        return Server.BlockManager.GoMine(num, cl_str, Server.BlockManager).go_close()

    @classmethod
    def cv_block(cls, block):
        num = block[0]
        cl_str = block[1]
        return Server.BlockManager.GoMine(num, cl_str, Server.BlockManager).check_valid()

    @classmethod
    def add_tr(cls, transaction):
        sender = transaction[0]
        to = transaction[1]
        money = float(transaction[2])
        date = transaction[3]
        Server.BlockManager.transaction.add_transaction(sender, to, money, date)
        return 1

    @classmethod
    def cv_transaction(cls, transaction):
        sender = transaction[0]
        to = transaction[1]
        try:
            money = float(transaction[2])
            if money <= 0:
                raise Exception
        except:
            return 2
        balances = get_file_data(BALANCE_FILE)

        sender_mark = to_mark = None
        if sender == to:
            return 2
        try:
            if balances[hashlib.sha256(bytes(sender.encode())).hexdigest()] >= money:
                sender_mark = True
        except:
            pass
        try:
            if balances[hashlib.sha256(bytes(to.encode())).hexdigest()]:
                to_mark = True
        except:
            pass
        return 0 if sender_mark and to_mark else 2


    @classmethod
    def cv_account(cls, pass_data):
        try:
            for key in pass_data.keys():
                if len(get_file_data(USERLIST)) == 1:
                    try:
                        if get_file_data(PASSFILE)[key] == pass_data[key]:
                            cls.SEND_MARKER = True
                        else:
                            cls.SEND_MARKER = 'denied'
                            return 1
                    except:
                        cls.SEND_MARKER = 'denied'
                        return 1
                else:
                    if get_file_data(PASSFILE)[key] == pass_data[key]:
                        NetworkFunc.VALID_COUNTER += 1

                    NetworkFunc.send_to_all(['cv_sign_in', pass_data])
            return 1
        except:
            return 1

    @classmethod
    def cv_sign_in(cls, pass_data):
        for key in pass_data.keys():
            try:
                if get_file_data(PASSFILE)[key] == pass_data[key]:
                    return 0
                else:
                    return 2
            except:
                return 2

    @classmethod
    def user_exit(cls, addr):
        with open(USERLIST, 'r') as userlist:
            users = json.load(userlist)

        users.pop(addr)
        #print('Пользователь', addr, 'вышел')

        with open(USERLIST, 'w') as userlist:
            json.dump(users, userlist)

        return 1

    @classmethod
    def count_valid(cls, reply):
        cls.REPLY_NUMS += 1

        if not reply[1]:
            #print(reply[0], 'подтвердил валидность ваших данных!')
            cls.VALID_COUNTER += 1
        else:
            pass
            #print(reply[0], 'отклонил валидность ваших данных!')
        try:
            if cls.REPLY_NUMS ==  len(cls.ONLINE_USERS):
                if cls.VALID_COUNTER >= int((len(get_file_data(USERLIST)) / 2)):
                    #print('Данные подтверждены большинством', cls.VALID_COUNTER)
                    cls.SEND_MARKER = True
                else:
                    cls.SEND_MARKER = 'denied'
                    #print('Данные не подтверждены')

                cls.VALID_COUNTER = 0
                cls.REPLY_NUMS = 0
            return 1
        except:
            return 1


    @classmethod
    def send_to_all(cls, *args):
        offline_users = []
        cls.ONLINE_USERS = get_file_data(USERLIST)
        cls.ONLINE_USERS.pop(Server.MY_ADDR)

        if not cls.ONLINE_USERS:
            return 3

        for user_addr in cls.ONLINE_USERS:
            s = socket.socket()
            s.settimeout(2)
            try:
                s.connect((user_addr, StartConnection.PORT))
                for data in args:
                    NetworkFunc.send_to_addr(s, data)
                NetworkFunc.send_exitcode(s)
            except ConnectionRefusedError or socket.timeout:
                offline_users.append(user_addr)
                continue

        if offline_users:
            new_userlist = get_file_data(USERLIST)
            [new_userlist.pop(off_i) for off_i in offline_users]

            with open(USERLIST, 'w') as f:
                json.dump(new_userlist, f)

            cls.send_to_all([USERLIST[:-4], new_userlist])

            if len(new_userlist) == 1:
                return 3
            elif cls.VALID_COUNTER >= int((len(new_userlist) / 2)):
                #print('Данные подтверждены большинством', cls.VALID_COUNTER)
                cls.SEND_MARKER = True
            else:
                cls.SEND_MARKER = 'denied'
                #print('Данные не подтверждены')
                cls.VALID_COUNTER = 0
            return 1

    @classmethod
    def send_to_addr(cls, sock, *args):
        try:
            for msg in args:
                msg = str(list(msg))
                msg += 'ENDMARK'
                sock.send(bytes(msg.encode()))
            return 0
        except:
            return 1

    @classmethod
    def send_exitcode(cls, sock):
        sock.send(bytes('EXITCODE'.encode()))
        sock.close()


def get_file_data(filepath):  # Используется и для нахождения баланса
    with open(filepath, 'r') as pass_file:
        return json.load(pass_file)









from dataclasses import dataclass
from SocketServer.socket_connections import NetworkFunc, Server, BALANCE_FILE, USERLIST, get_file_data
import hashlib
import json
import sys
import time

@dataclass
class Interface:
  __blockfunc : object
  __username : str

  def __post_init__(self):
    self.__log_in = Autorize(self.__username)
    command_list = {'help': Interface.help,
                    'all': self.__show_all,
                    'open': self.__show_open,
                    'begin': self.__begin,
                    'exit': Interface.exit,
                    'send': self.__transaction,
                    'stat': self.__go_stat}

    print("Напишите help если хотите посмотреть все доступные програмы\n")
    print("Если хотите выйти напишите exit\n")

    while True:
      answer = input('Введите команду: ')
      try:
        command_list[answer]()
      except KeyError:
        print('Такой команды не существует')
        continue

  def __sign_out(self):
    if not self.__log_in:
      print('Вы не заходили в аккаунт')
      return 1

    print('Прощай,', self.__log_in.accname)
    self.__log_in = None
    return 0

  def __sign_in(self):
    if self.__log_in:
      return 0
    else:
      self.__log_in = Autorize(self.__username)
      self.__log_in.autorize()
      
  def __go_stat(self):
      return self.__log_in.statistics()
      
  @classmethod
  def help(cls):
    print("Введите команду all для просмотра всех блоков")
    print("Введите команду open для просмотра открытых блоков")
    print("Введите команду begin для начала ХЭШирования")
    print("Введите команду send для создания транзакции")
    print("Введите команду stat для просмотра статистики")
    return 0

  def __show_all(self):
    for block in self.__blockfunc.get_all_blocks():
      print(block)
    return 0

  def __show_open(self):
    for block in self.__blockfunc.get_open_blocks():
      print(block)
    return 0

  def __begin(self):
    print('Выберите номер блока, который хотите майнить')
    self.__show_open()
    num = input('Введите номер блока: ')
    cl_str = input('Введите вашу строку nonce: ')
    cl_block = [num, cl_str]
    
    go_mine_obj = self.__blockfunc.GoMine(num, cl_str, self.__blockfunc)
    if not go_mine_obj.check_valid():
      NetworkFunc.VALID_COUNTER += 1
    
    
    if NetworkFunc.send_to_all(['cv_bl', cl_block]) == 3:
      print('Никого нет в сети, закрытие блока отклонено')
      return 0

    while True:
      if NetworkFunc.SEND_MARKER == True:
        print('Закрытие блока разрешено!')
        go_mine_obj.go_close()
        NetworkFunc.send_to_all(['add_bl', cl_block])

        self.__get_awards()
        break
      elif NetworkFunc.SEND_MARKER == 'denied':
        print('Закрытие блока отклонено!')
        break
      else:
        continue

    NetworkFunc.SEND_MARKER = False

  def __get_awards(self):
    online_num = int(len(get_file_data(USERLIST)))
    award = 1 / online_num
    balances = get_file_data(BALANCE_FILE)

    balances[hashlib.sha256(bytes(self.__log_in.accname.encode())).hexdigest()] += award

    self.__blockfunc.transaction.ValidBalance.upload_file(balances)
    NetworkFunc.send_to_all([BALANCE_FILE[:-4], balances])

  def __transaction(self):
    print('Вас приветствует метод создания транзации')
    self.__sign_in()
    to = input('Введите логин получателя: ')
    money = input('Введите сумму транзакции: ')
    date = time.asctime()
    sender = self.__log_in.accname
    trans_list = ['cv_tr', [sender, to, money, date]]
    print(trans_list)
    print('Проверьте валидность данных')
    print('От:', sender)
    print('Кому:', to)
    print('Сумма:', money)
    print('Дата:', date)
    print('\n')
    transaction = [sender, to, money, date]

    if not NetworkFunc.cv_transaction(transaction):
      NetworkFunc.VALID_COUNTER += 1

    if NetworkFunc.send_to_all(['cv_tr', transaction]) == 3:
      print('Никого нет в сети, транзакция отклонена')
      return 0

    while True:
      if NetworkFunc.SEND_MARKER == True:
        print('Транзакция разрешена!')
        self.__blockfunc.transaction.add_transaction(sender, to, money, date)
        NetworkFunc.send_to_all(['add_tr', transaction])
        break
      elif NetworkFunc.SEND_MARKER == 'denied':
        print('Транзакция отклонена')
        break
      else:
        continue

    NetworkFunc.SEND_MARKER = False
    return 0

  @classmethod
  def exit(cls):
    try:
      NetworkFunc.send_to_all(['exit', Server.MY_ADDR])
    except:
      pass
    Server.close_server()
    print('Bye.')
    sys.exit(0)

class Autorize:
  PASSFILE = 'accounts.txt'

  def __init__(self, login):
    self.__accname = login
    self.__welcome_alert()

  def autorize(self):
    pass
        
  def __welcome_alert(self):
     print('Привет,', self.__accname)

  def statistics(self):
      balances = self.get_accounts(BALANCE_FILE)
      try:
          print('Имя аккаунта:', self.__accname)
          print('Количество монет:', balances[hashlib.sha256(bytes(self.__accname.encode())).hexdigest()])
      except:
          return 'Error'
      
  @property
  def accname(self):
    return self.__accname

  def get_accounts(self, filepath=None): # Используется и для нахождения баланса
    if not filepath:
      filepath = self.PASSFILE
      
    with open(filepath, 'r') as pass_file:
      return json.load(pass_file)




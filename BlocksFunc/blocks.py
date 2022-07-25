import os
import json
import hashlib
import random
from decimal import Decimal
from dataclasses import dataclass
from collections import namedtuple


@dataclass
class BlockManager:
    STRUCTURE = { 'header' : { 'previous_hash' : 0, 'nonce' : 0 }, 'transactions' : [] }
    __dirpath : str
    
    def __post_init__(self):
        if not self.__is_create():
            #print('Блока инициализации не существует, создаём')
            first_block_structure = { 'header' : { 'previous_hash' : 0, 'nonce' : str(random.random()) }, 'transactions' : [] }
            self.add_block(0.0, first_block_structure)
            self.create_block()

    def create_manager(self):
        main_num, main_block = self.__find_empty_block(TransactionManager.MAX_LENGTH)
        self.transaction = TransactionManager(self, main_num, main_block)
        return 0

    def __is_create(self):
        return 1 if os.listdir(self.__dirpath) else 0

    def get_all_blocks(self, nums=True):
        all_blocks = []
        
        for filename in sorted(os.listdir(self.__dirpath)):
            with open(os.path.join(self.__dirpath, filename), 'r') as file:
                if not nums:
                      all_blocks.append(json.load(file))
                else:
                    all_blocks.append((filename[:-4], json.load(file)))
                      
        return all_blocks
    
    def get_last_block(self):
        filename = sorted(os.listdir(self.__dirpath))[-1]
        num = filename[:-4]
        with open(os.path.join(self.__dirpath, filename), 'r') as last_file:
            block = json.load(last_file)            
        return (num, block)
    
    def get_open_blocks(self):
        open_blocks = []
        for block in self.get_all_blocks():
            if len(block[1]['transactions']) == TransactionManager.MAX_LENGTH and not block[1]['header']['nonce']:
                open_blocks.append(block)
        return open_blocks


    def add_block(self, number, block):
        filename = str(number) + '.txt'
        with open(os.path.join(self.__dirpath, filename), 'w') as file:
            json.dump(block, file, indent=1)
            
        return 0 
    
    def create_block(self, previous_num=False, previous_block=False, structure=STRUCTURE):
        if not previous_block:
            previous_num, previous_block = self.get_last_block()
            
        if previous_block['header']['nonce']: # Если предыдущий блок закрыт
            new_number = float(Decimal(str(previous_num)) + Decimal('1'))
            prev_valid = hashlib.sha256((str(previous_block['header']['nonce']) + str(self.GoMine.get_transactions(previous_block)) + previous_block['header']['nonce']).encode()).hexdigest()
        else:
            new_number = float(Decimal(str(previous_num)) + Decimal('0.1'))
            prev_valid = previous_block['header']['previous_hash']

        structure['header']['previous_hash'] = prev_valid
        
        return self.add_block(new_number, structure)

    def close_block(self, number, nonce_str):
        filename = str(number) + '.txt'
        
        num_tr, block_for_transactions = self.get_last_block() # Определение следующего блока для ввода данных
        
        self.transaction.MainNum = num_tr
        self.transaction.MainBlock = block_for_transactions
    
        with open(os.path.join(self.__dirpath, filename), 'r') as file:
            block = json.load(file)
            block['header']['nonce'] = nonce_str
            parent_block = block
        
        self.add_block(number, block)
        return self.create_block(number, parent_block) if int(float(number)) == int(float(num_tr)) else 0     

    def __find_empty_block(self, size):
        for block in self.get_all_blocks():
            if not float(block[0]):
                continue
            if len(block[1]['transactions']) < size:
                return block

    @dataclass
    class GoMine:
        DIRPATH = 'blockchain'
        DIFFICULT = 1
        __num : str
        __client_str : str
        __client_obj : object

        def __post_init__(self):
            if self.__num in [num for num, _ in self.__client_obj.get_open_blocks()]:
                with open(os.path.join(self.DIRPATH, self.__num + '.txt'), 'r') as file:
                    self.__block = json.load(file)

                #print(self.__block)
                prev_hash = self.__block['header']['previous_hash']
                tr = self.get_transactions(self.__block)
                self.__client_hash = hashlib.sha256((prev_hash + tr + self.__client_str).encode()).hexdigest()
                #print(prev_hash + tr + self.__client_str)
                #print(prev_hash, tr, self.__client_str)
            else:
                self.__client_hash = 0

        def go_close(self):
            self.__client_obj.close_block(self.__num, self.__client_str)
            return 1

        @staticmethod
        def get_transactions(block):
            res_str = ''
            for tr in block['transactions']:
                for attr in tr:
                    res_str += str(attr)
            return res_str

        def check_valid(self):
            if self.__client_hash:
                if 'a' * self.DIFFICULT in self.__client_hash:
                    #print('Хэш верный!')
                    return 0
                else:
                    #print('Хэш ошибочный')
                    return 2
            else:
                #print('Блок не открыт!')
                return 2




@dataclass
class TransactionManager:
    MAX_LENGTH = 10
    __Transaction = namedtuple('Transaction', 'sender, to, money, date')
    __bm : object
    __MainNum : str
    __MainBlock : dict

    def add_transaction(self, sender, to, money, date):
        #print(self.__MainNum, self.__MainBlock)
        self.ValidBalance.go_send(sender, to, money, self.ValidBalance.get_balance())
        tr = self.__Transaction(sender, to, money, date)
        self.__MainBlock['transactions'].append(tr)
        self.__bm.add_block(self.__MainNum, self.__MainBlock)

        self.__check_length()

    def __check_length(self):
        if len(self.__MainBlock['transactions']) == self.MAX_LENGTH:
            if self.__MainNum == self.__bm.get_last_block()[0]:
                self.__bm.create_block()

            self.__MainNum, self.__MainBlock = self.__bm.get_last_block()
            
    @property
    def MainBlock(self):
        return self.__MainBlock

    @MainBlock.setter
    def MainBlock(self, new_block):
        self.__MainBlock = new_block
        
    @property
    def MainNum(self):
        return self.__MainNum
    
    @MainNum.setter
    def MainNum(self, new_num):
        self.__MainNum = new_num

    class ValidBalance:
        BALANCE_FILE = 'balance.txt'

        @classmethod
        def go_send(cls, sender, to, money, balances):
            new_list = cls.send_valid(sender, to, money, balances)
            if new_list:
                cls.upload_file(new_list)
                #print('Транзакция отправлена успешно!')
                return 0
            else:
                return 1

        @classmethod
        def upload_file(cls, new_list):
            with open(cls.BALANCE_FILE, 'w') as file_b:
                json.dump(new_list, file_b, indent=1)

        @staticmethod
        def send_valid(sender, to, money, balances):
            balances[hashlib.sha256(bytes(sender.encode())).hexdigest()] -= float(money)
            balances[hashlib.sha256(bytes(to.encode())).hexdigest()] += float(money)
            return balances

        @classmethod
        def get_balance(cls, filepath=None):  # Используется и для нахождения баланса
            if not filepath:
                filepath = cls.BALANCE_FILE

            with open(filepath, 'r') as pass_file:
                return json.load(pass_file)

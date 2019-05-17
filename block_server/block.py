import hashlib
import time
import json

class Block(object):
    def __init__(self, index, previous_hash, nonce, difficult, transactions, timestamp=None):
        self.index = index
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.difficult = difficult
        self.transactions = transactions
        self.timestamp = timestamp or time.time()

    def compute_hash(self):

        block_string = json.dumps(self.__dict__, sort_keys=True)

        return hashlib.sha256(block_string.encode()).hexdigest()

    @staticmethod
    def from_dict(data_block):
        block = Block(data_block['index'], data_block['previous_hash'], data_block['nonce'], 
                      data_block['difficult'], data_block['transactions'], data_block['timestamp'])
        block.hash = data_block['hash']
        return block

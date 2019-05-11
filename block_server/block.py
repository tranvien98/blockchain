import hashlib
import time


class Block(object):
    def __init__(self, index, previous_hash, nonce, transaction_counter, difficult, transactions, timestamp=None):
        self.index = index
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.transaction_counter = transaction_counter
        self.difficult = difficult
        self.transactions = transactions
        self.timestamp = timestamp or time.time()

    def compute_hash(self):
        block_string = "{}{}{}{}{}{}{}".format(
            self.index, self.previous_hash, self.nonce,
            self.transaction_counter, self.difficult,
            self.transactions, self.timestamp,
        )

        return hashlib.sha256(block_string.encode()).hexdigest()

    @staticmethod
    def from_dict(data_block):
        block = Block(data_block['index'], data_block['previous_hash'], data_block['nonce'], 
                      data_block['transaction_counter'], data_block['difficult'],
                      data_block['transactions'], data_block['timestamp'],)
        
        return block

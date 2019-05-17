from block import Block
import time

class Blockchain(object):
    difficulty = 2
    def __init__(self):
        self.chain = []
        self.create_genesis_block()
        self.unconfirmed_transactions = []
        self.open_auctions = []
        self.chain_code = {'chain': self.chain, 'open_auctions': self.open_auctions,
                           'unconfirmed_transactions': self.unconfirmed_transactions}
    def from_list(data_chain):
        blockchain = Blockchain()
        blockchain.chain = []
        blockchain.unconfirmed_transactions = []
        for data_block in data_chain:
            block = Block.from_dict(data_block)
            blockchain.chain.append(block)

        return blockchain

    def make_json(self):
        chain_data = []

        for block in self.chain:
            chain_data.append(block.__dict__)
        
        return chain_data

    def create_genesis_block(self):
        """
        Tạo khối genesis và gắn nó vào chuỗi.
      
        """
        genesis_block = Block(0, 0, 0, 2, [])

        self.proof_of_work(genesis_block)

        genesis_block.hash = genesis_block.compute_hash()

        self.chain.append(genesis_block)
    @property
    def last_block(self):
        return self.chain[-1]

    def add_block(self, block, proof):
        """
        Thêm khối vào chuỗi sau khi xác minh.
        Xác minh bao gồm:
        * Kiểm tra proof là hợp lệ.
        * previous_hash đã tham chiếu trong khối và hàm băm của khối mới nhất
          trong chuỗi.
        """
        previous_hash = self.last_block.hash

        if previous_hash != block.previous_hash:
            return False

        if not Blockchain.is_valid_proof(block, proof):
            return False

        block.hash = proof
        self.chain.append(block)
        return True

    def proof_of_work(self, block):
       
        block.nonce = 0

        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    @classmethod
    def is_valid_proof(cls, block, block_hash):
        """

        """

        return (block_hash.startswith('0' * Blockchain.difficulty) and
                block_hash == block.compute_hash())

    @classmethod
    def check_chain_validity(cls, chain):
        result = True
        previous_hash = "0"

        for block in chain:
            block_hash = block.hash
          
            delattr(block, "hash")

            if not cls.is_valid_proof(block, block_hash) or \
                    previous_hash != block.previous_hash:
                result = False
                break

            block.hash, previous_hash = block_hash, block_hash

        return result

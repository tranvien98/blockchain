from block import Block


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.create_genesis_block()
        self.unconfirmed_transactions = []

    def create_genesis_block(self):
        genesis_block = Block(0, 0, 0, 0, 2, [])
        self.chain.append(genesis_block)

    @staticmethod
    def from_list(data_chain):
        blockchain = Blockchain()
        blockchain.chain = []

        for data_block in data_chain:
            block = Block.from_dict(data_block)
            blockchain.chain.append(block)

        return blockchain

    def make_json(self):
        chain_data = []

        for block in self.chain:
            chain_data.append(block.__dict__)
        
        return chain_data

    @staticmethod
    def proof_of_work(block):
        difficult = block.difficult
        block.nonce = 0

        hash = block.compute_hash()

        while not hash.startswith('0'*difficult):
            block.nonce += 1
            hash = block.compute_hash()

        return hash

    def get_last_block(self):
        return self.chain[-1]

    @staticmethod
    def is_valid_block(block, previous_block):
        difficult = block.difficult

        if block.index - previous_block.index != 1:
            print("index error")
            return False
        elif previous_block.compute_hash() != block.previous_hash:
            print("chain error")
            return False
        elif not block.compute_hash().startswith('0'*difficult):
            print("invalid proof of work")
            return False
        elif block.timestamp <= previous_block.timestamp:
            # print(block.block_header.timestamp)
            # print(previous_block.block_header.timestamp)
            print("cannot chain 2 block same time")
            return False

        return True

    def add_block(self, block):
        previous_block = self.get_last_block()

        if self.is_valid_block(block, previous_block):
            self.chain.append(block)
            return True
        else:
            return False

    def is_valid_chain(self):
        """
        Check if given blockchain is valid
        """
        previous_block = self.chain[0]
        current_index = 1

        while current_index < len(self.chain):

            block = self.chain[current_index]

            if not self.is_valid_block(block, previous_block):
                return False

            previous_block = block
            current_index += 1

        return True
    #add transaction
    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

"""
Chưa làm các service liên quan đến transaction 
- Định nghĩa tran
- Validate
- Xử lý
- Truy xuất dữ liệu từ block chain 
- Định nghĩa chain-code (smart contract)
"""
import time
import requests
from flask import Flask, jsonify, request

from block import Block
from blockchain import Blockchain

app = Flask(__name__)
anchors = set()  # <ip>:<port>
anchors.add('127.0.0.1:5001')
orders = set()
orders.add('127.0.0.1:5002')
blockchain = Blockchain()

orderIp = "127.0.0.1:5002"
anchorsIp = "127.0.0.1:5001"
myAddress = "127.0.0.1:5000"

@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    """
    them transaction
    """
    tx_data = request.get_json()
    required_fields = ["type", "content"]

    for field in required_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 404

    tx_data["timestamp"] = time.time()

    blockchain.add_new_transaction(tx_data)

    url = 'http://{}/broadcast_transaction'.format(orderIp)
    response = requests.post(url, json=tx_data)

    return "Success", 201


@app.route('/get_transaction', methods=['POST'])
def get_transaction():
    """
    lấy giao dịch từ các nút khác
    """
    tx_data = request.get_json()
    required_fields = ["type", "content", "timestamp"]

    for field in required_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 404

    blockchain.add_new_transaction(tx_data)

    return "Success", 201


"""
Lấy nút cuối của chuỗi
"""
@app.route('/open_auctions', methods=['GET'])
def get_open_auctions():
    
    global blockchain

    url = 'http://{}/consensus'.format(orderIp)
    response = requests.get(url)

    length = response.json()['length']
    chain = response.json()['chain']
    longest_chain = Blockchain.fromList(chain)

    if len(blockchain.chain) < length and blockchain.check_chain_validity(longest_chain.chain):

        longest_chain.open_auctions = {}

        for block in longest_chain.chain:
            if not compute_open_auctions(block, longest_chain.open_auctions, longest_chain.chain_code):
                return "Invalid Blockchain", 400

        blockchain = longest_chain

    auctions = []
    for _, auction in blockchain.open_auctions.items():
        auctions.append(auction)

    return jsonify({"length": len(blockchain.open_auctions),
                    "auctions": list(auctions)})


@app.route('/chain', methods=['GET'])
def get_chain():
    global blockchain

    url = 'http://{}/consensus'.format(orderIp)
    response = requests.get(url)

    length = response.json()['length']
    chain = response.json()['chain']
    longest_chain = Blockchain.fromList(chain)

    if len(blockchain.chain) < length and blockchain.check_chain_validity(longest_chain.chain):
        # recompute open_auctions
        longest_chain.open_auctions = {}

        for block in longest_chain.chain:
            if not compute_open_auctions(block, longest_chain.open_auctions, longest_chain.chain_code):
                return "Invalid Blockchain", 400

        blockchain = longest_chain

    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    return jsonify({"length": len(chain_data),
                    "chain": chain_data})


@app.route('/local_chain', methods=['GET'])
def get_local_chain():
    chain_data = []

    for block in blockchain.chain:
        chain_data.append(block.__dict__)

    return jsonify({"length": len(chain_data),
                    "chain": chain_data})

@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
    """
   
    """

    if not blockchain.unconfirmed_transactions:
        return jsonify({"response": "None transactions 0x001"})

    last_block = blockchain.last_block

    new_block = Block(index=last_block.index + 1,
                      transactions=[],
                      timestamp=time.time(),
                      previous_hash=last_block.hash)

    for transaction in blockchain.unconfirmed_transactions:
     
        if not validate_transaction(transaction):
            continue

        new_block.transactions.append(transaction)

    blockchain.unconfirmed_transactions = []

    if (len(new_block.transactions) == 0):
        return jsonify({"response": "None transactions 0x002"})

    proof = blockchain.proof_of_work(new_block)
    blockchain.add_block(new_block, proof)


    url = 'http://{}/broadcast_block'.format(orderIp)
    response = requests.post(url, json=new_block.__dict__)

    result = new_block.index

    if not result:
        return jsonify({"response": "None transactions to mine 0x002"})
    return jsonify({"response": "Block #{} is mined.".format(result)})



@app.route('/add_block', methods=['POST'])
def validate_and_add_block():
    global blockchain

    block_data = request.get_json()

    block = Block(block_data["index"],
                  block_data["transactions"],
                  block_data["timestamp"],
                  block_data["previous_hash"],
                  block_data["nonce"])

    tmp_open_auctions = blockchain.open_auctions
    tmp_chain_code = blockchain.chain_code

    if not compute_open_auctions(block, tmp_open_auctions, tmp_chain_code):
        return "The block was discarded by the node", 400

    blockchain.open_auctions = tmp_open_auctions
    blockchain.chain_code = tmp_chain_code

    proof = block_data['hash']
    added = blockchain.add_block(block, proof)

    if not added:
        return "The block was discarded by the node", 400

    return "Block added to the chain", 201


@app.route('/pending_tx')
def get_pending_tx():
    return jsonify(blockchain.unconfirmed_transactions)


@app.route('/list_nodes', methods=['GET', 'POST'])
def list_node():
    url = 'http://{}/list_nodes'.format(orderIp)
    response = requests.get(url)

    data = response.json()

    return jsonify(data)


def validate_transaction(transaction):
    global blockchain
    #Kiểm tra quyền của giao dịch
    author = transaction['content']['author']
    url = 'http://{}/validate_permission'.format(caIP + ':' + caPort)
    response = requests.post(
        url, json={'peer': author, 'action': transaction['type']})

    if response.json()['decision'] != 'accept':
        print("Reject from server")
        return False

    #check validate transaction and compute open_auctions
    if transaction['type'].lower() == 'open':
        questionid = transaction['content']['questionid']
        if questionid in blockchain.open_auctions:
            return False
        blockchain.open_auctions[questionid] = transaction['content']
        return True
    elif transaction['type'].lower() == 'close':
        questionid = transaction['content']['questionid']
        if questionid in blockchain.open_auctions and blockchain.open_auctions[questionid]['author'] == transaction['content']['author'] and blockchain.open_auctions[questionid]['status'] == 'opening':
            blockchain.open_auctions[questionid]['status'] = 'closed'
            return True
        return False
    elif transaction['type'].lower() == 'vote':
        questionid = transaction['content']['questionid']
        if questionid in blockchain.open_auctions and blockchain.open_auctions[questionid]['status'] == 'opening':
            vote = transaction['content']['vote']
            author = transaction['content']['author']
            if author not in blockchain.open_auctions[questionid]['answers'][vote]:
                blockchain.open_auctions[questionid]['answers'][vote].append(
                    author)
                return True
            return False
    elif transaction['type'].lower() == 'smartcontract':
        try:
            exec(transaction['content']['code'],
                 blockchain.chain_code, blockchain.chain_code)
            return True
        except:
            print('Error when create new contract')
            return False
    elif transaction['type'].lower() == 'execute':
        try:
            thread = threading.Thread(
                target=blockchain.chain_code[transaction['content']['contract']], args=transaction['content']['arguments'])
            thread.start()
            return True
        except:
            print('Error when execute chain_code {}'.format(
                transaction['content']['contract']))
            return False


def compute_open_auctions(block, open_auctions, chain_code):
    for transaction in block.transactions:
        author = transaction['content']['author']
        url = 'http://{}/validate_permission'.format(anchorsIp)
        response = requests.post(
            url, json={'peer': author, 'action': transaction['type']})

        if response.json()['decision'] != 'accept':
            print("Reject from server")
            return False

        #check validate transaction and compute open_auctions

        if transaction['type'].lower() == 'open':
            questionid = transaction['content']['questionid']
            if questionid not in open_auctions:
                open_auctions[questionid] = transaction['content']
                return True
        elif transaction['type'].lower() == 'close':
            questionid = transaction['content']['questionid']
            if questionid in open_auctions and open_auctions[questionid]['author'] == transaction['content']['author'] and open_auctions[questionid]['status'] == 'opening':
                open_auctions[questionid]['status'] = 'closed'
                return True
        elif transaction['type'].lower() == 'vote':
            questionid = transaction['content']['questionid']
            if questionid in open_auctions and open_auctions[questionid]['status'] == 'opening':
                vote = transaction['content']['vote']
                author = transaction['content']['author']
                if author not in open_auctions[questionid]['answers'][vote]:
                    open_auctions[questionid]['answers'][vote].append(author)
                    return True
        elif transaction['type'].lower() == 'smartcontract':
            try:
                exec(transaction['content']['code'], chain_code)
                return True
            except:
                print('Error when create new contract')
                return False
        else:
            return True
        return False
    return True


def join_to_network(anchorsIp, myAddress):
    try:
        url = 'http://{}/add_node'.format(anchorsIp)
        response = requests.post(url, json={myAddress})
        print('Connection successfull')
        return True
    except:
        print("Connection refused by the server..")

        return False


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000,
                        type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port



  
    while not join_to_network(anchorsIp):
        print("Let me sleep for 5 seconds")
        time.sleep(5)

    app.run(port=port, debug=True, threaded=True)

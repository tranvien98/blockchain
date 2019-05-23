"""
Chưa làm các service liên quan đến transaction 
- Định nghĩa tran
- Validate
- Xử lý
- Truy xuất dữ liệu từ block chain 
- Định nghĩa chain-code (smart contract)
"""
import sys
import time
import requests
from flask import Flask, jsonify, request
import threading
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
    longest_chain = Blockchain.from_list(chain)

    print(len(blockchain.chain), length)
    if len(blockchain.chain) < length and blockchain.check_chain_validity(longest_chain.chain):
        longest_chain.open_auctions = {}

        for block in longest_chain.chain:
            if not compute_open_auctions(block, longest_chain.open_auctions, longest_chain.chain_code):
                return "Invalid Blockchain", 400

        blockchain = longest_chain

    auctions = []
    for _ , auction in blockchain.open_auctions.items():
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
    longest_chain = Blockchain.from_list(chain)

    if len(blockchain.chain) < length and blockchain.check_chain_validity(longest_chain.chain):
        # kiem tra lai open_auction
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
def mine():
    """
   
    """
    if not blockchain.unconfirmed_transactions:
        return jsonify({"response": "None transactions 0x01"})

    last_block = blockchain.last_block

    new_block = Block(last_block.index + 1, last_block.hash, 0, blockchain.difficulty, [])

    
    for transaction in blockchain.unconfirmed_transactions:
        if not validate_transaction(transaction):
            continue
        new_block.transactions.append(transaction)


    blockchain.unconfirmed_transactions = []

    if (len(new_block.transactions) == 0):
        return jsonify({"response": "Error none transactions x02"})

    proof = blockchain.proof_of_work(new_block)
    blockchain.add_block(new_block, proof)


    url = 'http://{}/broadcast_block'.format(orderIp)
    response = requests.post(url, json=new_block.__dict__)

    result = new_block.index

    if not result:
        return jsonify({"response": " Error none transactions x02"})
    return jsonify({"response": "Block #{} is mined.".format(result)})



@app.route('/add_block', methods=['POST'])
def validate_and_add_block():
    global blockchain

    block_data = request.get_json()

    block = Block(data_block['index'], data_block['previous_hash'], data_block['nonce'],
                  data_block['difficult'], data_block['transactions'], data_block['timestamp'])

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
    print(author)
    url = 'http://{}/validate_permission'.format(anchorsIp)
    response = requests.post(
        url, json={'peer': author, 'action': transaction['type']})

    if response.json()['decision'] != 'accept':
        print("Reject from server")
        return False

    if transaction['type'].lower() == 'open':
        id_auctioneer = transaction['content']['id_auctioneer']
        if id_auctioneer in blockchain.open_auctions:
            return False
        if transaction['content']['price_bidder'] < 0:
            return False
        blockchain.open_auctions[id_auctioneer] = transaction['content']
        blockchain.timeout[id_auctioneer] = True
        try:
            thread = threading.Thread(target=blockchain.chain_code[transaction['content']['contract']], args=(
                lambda: blockchain.timeout[id_auctioneer], transaction['content']['author'], transaction['content']['id_auctioneer'], transaction['content']['connect'], ))
            thread.start()
        except :
            print('Error contract x02')
        return True
    elif transaction['type'].lower() == 'auctioning':
        id_auctioneer = transaction['content']['id_auctioneer']
        if transaction['content']['price_bidder'] < 0:
            return False
        if id_auctioneer in blockchain.open_auctions and blockchain.open_auctions[id_auctioneer]['status'] == 'opening':
            price_bidder = transaction['content']['price_bidder']
            try:
                blockchain.open_auctions[id_auctioneer]['id_bidder']
            except KeyError:
                blockchain.open_auctions[id_auctioneer]['id_bidder'] = None
            if blockchain.open_auctions[id_auctioneer]['id_bidder'] is not None:
               if (blockchain.open_auctions[id_auctioneer]['id_bidder'] != transaction['content']['id_bidder']):
                   return False
            if float(blockchain.open_auctions[id_auctioneer]['price_bidder']) < price_bidder :
                blockchain.open_auctions[id_auctioneer]['price_bidder'] = price_bidder
                blockchain.open_auctions[id_auctioneer]['id_bidder'] = transaction['content']['id_bidder']
                return True
            return False
        return False
        
    elif transaction['type'].lower() == 'close':
        id_auctioneer = transaction['content']['id_auctioneer']
        if id_auctioneer in blockchain.open_auctions and blockchain.open_auctions[id_auctioneer]['author'] == transaction['content']['author'] and blockchain.open_auctions[id_auctioneer]['status'] == 'opening':
            blockchain.open_auctions[id_auctioneer]['status'] = 'closed'
            return True
        return False
    elif transaction['type'].lower() == 'smartcontract':
       

        try:
            exec(transaction['content']['code'],blockchain.chain_code, blockchain.chain_code)
            return True
        except:
            print('Error contract x01')
            return False
    elif transaction['type'].lower() == 'execute':
        id_auctioneer = transaction['content']['id_auctioneer']
        try:
            blockchain.timeout[id_auctioneer] = False
            time.sleep(0.6)
            blockchain.timeout[id_auctioneer] = True
            thread = threading.Thread(target=blockchain.chain_code[transaction['content']['contract']], args=(
                lambda: blockchain.timeout[id_auctioneer], transaction['content']['author'], transaction['content']['id_auctioneer'], transaction['content']['connect'], ))
            thread.start()
            return True
        except:
            print('Error contract x03')
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
        if transaction['type'].lower() == 'open':
            id_auctioneer = transaction['content']['id_auctioneer']
            if id_auctioneer not in open_auctions:
                open_auctions[id_auctioneer] = transaction['content']
                return True
        else:
            return True
    return True


def join_network(anchorsIp):
    data = {
        'port' : "5000"
    }
    try:
        url = 'http://{}/add_node'.format(anchorsIp)
        response = requests.post(url, json=data)
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
    parser.add_argument('-a', '--anchorsIp', default='127.0.0.1',
                        type=str, help='port to listen on')
    args = parser.parse_args()
    port = args.port
    anchorsIp = args.anchorsIp
    anchorsIp = anchorsIp + ":5001"

  
    while not join_network(anchorsIp):
        print("Let me sleep for 10 seconds")
        time.sleep(1)

    app.run(host='127.0.0.1',port=port, debug=True, threaded=True)

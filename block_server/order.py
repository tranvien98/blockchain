import requests
from flask import Flask, jsonify, request

from block import Block
from blockchain import Blockchain

app = Flask(__name__)


anchors = set()
anchors.add('127.0.0.1:5001')


@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    tx_data = request.get_json()
    required_fields = ["auctioneer", "item", "price", "bidder"]

    for field in required_fields:
        if not tx_data.get(field):
            return "Invlaid transaction data", 404

    tx_data["timestamp"] = time.time()

    blockchain.add_new_transaction(tx_data)

    return "Success", 201


@app.route('/get_transaction', methods=['POST'])
def get_transaction():
    tx_data = request.get_json()
    required_fields = ["auctioneer", "item", "price", "bidder", "timestamp"]

    for field in required_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 404

    blockchain.add_new_transaction(tx_data)

    return "Success", 201
@app.route('/mine', methods=['GET', 'POST'])
def mine():
    """
    Tạo block mới từ uncomfirmed_transactions

    """
    result = -1
    global uncomfirmed_transactions
    for anchor in anchors:
        try:
            url = 'http://{}/concensus'.format(anchor)
            http_response = requests.get(url)
            last_block = http_response.json()['last_block']
            last_hash = http_response.json()['last_hash']
            difficult = last_block['difficult']
            transaction_counter = len(uncomfirmed_transactions)
            index = last_block['index'] + 1
            result = index
            new_block = Block(
                index, last_hash, 0, transaction_counter, difficult, uncomfirmed_transactions
            )
            
            Blockchain.proof_of_work(new_block)
            url = 'http://{}/broadcast_block'.format(anchor)
            http_response = requests.post(url, json=new_block.__dict__)
        except:
            print("cannot connect anchor {}". format(anchor))

    uncomfirmed_transactions = []


    if result == -1:
        return jsonify({"No transaction to mine"})
    return jsonify({"response": "Block #{} is mined.".format(result)})


@app.route('/order', methods=['GET', 'POST'])
def line_up():
    """
    Nhận yêu cầu thêm transaction từ general node và thêm vào hàng đợi

    """
    pass


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5002,
                        type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(port=port, debug=True, threaded=True)



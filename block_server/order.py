import requests
from flask import Flask, jsonify, request

from block import Block
from blockchain import Blockchain

app = Flask(__name__)


anchors = set()


@app.route('/add_node', methods=['POST'])
def register_new_anchors():
    data = request.get_json()

    if not data:
        return 'Invalid data', 400

    request_addr = data['ipaddress']
    port = data['port']
    node = request_addr + ':' + str(port)

    if not node:
        return "Invalid data", 400

    anchors.add(node)

    return "Success", 201


@app.route('/broadcast_block', methods=['POST'])
def announce_new_block():
    """

    """
    block = Block.from_dict(request.get_json())
    if not block:
    	return "Invalid data at announce_new_block", 400

    request_addr = request.remote_addr

    offline_node = []

    for peer in anchors:
        try:
            if peer.find(request_addr) != -1:
                continue
            url = "http://{}/add_block".format(peer)
            requests.post(url, json=block.__dict__)
        except requests.exceptions.ConnectionError:
            print('Cant connect to node {}. Remove it from peer list'.format(peer))
            offline_node.append(peer)

    for peer in offline_node:
        anchors.remove(peer)

    return "Success", 201


@app.route('/broadcast_transaction', methods=['POST'])
def announce_new_transaction():
    """

    """
    data = request.get_json()
    if not data:
        return "Invalid data at announce_new_block", 400

    request_addr = request.remote_addr

    offline_node = []

    for peer in anchors:
        try:
            if peer.find(request_addr) != -1:
                continue
            url = "http://{}/get_transaction".format(peer)
            requests.post(url, json=data)
        except requests.exceptions.ConnectionError:
            print('Cant connect to node {}. Remove it from peer list'.format(peer))
            offline_node.append(peer)

    for peer in offline_node:
        anchors.remove(peer)

    return "Success", 201


@app.route('/consensus', methods=['GET'])
def consensus():
    """

    """
    longest_chain = Blockchain()
    current_len = len(longest_chain.chain)

    offline_node = []

    for peer in anchors:
        try:
            response = requests.get('http://{}/local_chain'.format(peer))
            length = response.json()['length']
            chain = response.json()['chain']
            new_blockchain = Blockchain.fromList(chain)

            if length > current_len and longest_chain.check_chain_validity(new_blockchain.chain):
                current_len = length
                longest_chain = new_blockchain
        except requests.exceptions.ConnectionError:
            print('Cant connect to node {}. Remove it from anchors list'.format(peer))
            offline_node.append(peer)

    for peer in offline_node:
        anchors.remove(peer)

    chain_data = []

    for block in longest_chain.chain:
        chain_data.append(block.__dict__)

    return jsonify({"length": len(chain_data),
                    "chain": chain_data})

# in ra số lượng node
@app.route('/list_nodes', methods=['GET', 'POST'])
def get_node():
    result = {
        'Nodes in System': list(anchors),
        'Count of Nodes': len(anchors)
    }
    return jsonify(result)


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5002,
                        type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(port=port, debug=True, threaded=True)





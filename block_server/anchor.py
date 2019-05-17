import requests
from flask import Flask, jsonify, request
from block import Block

app = Flask(__name__)
general_nodes = set()


groups = {}

# O : Open | C : Close | A : Auction
permission = {'admin': 'OCASE', 'peer': 'OCSSE', 'guest': 'S'}

groups['127.0.0.1:5000'] = 'admin'


@app.route('/add_node', methods=['GET', 'POST'])
def validate_connection():
	print("connect....")
	data = request.get_json()
	request_addr = request.remote_addr
	print(request_addr)
	if not data:
		return 'Invalid data', 400


	node = request_addr + ':' + str(data['port'])
	if not node:
		return 'Invalid data', 400

	general_nodes.add(node)

	if node not in groups:
		groups[node] = 'peer'

	url = 'http://{}:5002/add_node'.format(request_addr)
	response = requests.post(
		url, json={'ipaddress': request_addr, 'port': data['port']})

	if response.status_code >= 400:
		return 'Error to connect to order', 400

	return "Success", 201


@app.route('/validate_permission', methods=['POST'])
def validate_permission():

	data = request.get_json()
	if not data:
		return 'Invalid data', 400

	node = data["peer"]
	action = data["action"]

	if not node in groups:
		groups[node] = 'guest'

	if permission[groups[node]].find(action[0].upper()) != -1:
		return jsonify({'decision': 'accept'})

	return jsonify({'decision': 'reject'})



if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5001, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port


    app.run(port=port, debug = True, threaded = True)



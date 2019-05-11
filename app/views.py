import datetime
import json
import os
import requests
from flask import Flask
from flask import render_template, redirect, request, jsonify

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

app = Flask(__name__)


# The node with which our application interacts, there can be multiple
# such nodes as well.
CONNECTED_NODE_ADDRESS = "http://127.0.0.1:5000"

posts = []


def fetch_posts():
    """
    Function to fetch the chain from a blockchain node, parse the
    data and store it locally.
    """
    get_chain_address = "{}/local_chain".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)
    if response.status_code == 200:
        content = []
        chain = json.loads(response.content)
        for block in chain["chain"]:
            for tx in block["transactions"]:
                tx["index"] = block["index"]
                tx["hash"] = block["previous_hash"]
                content.append(tx)

        global posts
        posts = sorted(content, key=lambda k: k['timestamp'],
                       reverse=True)


@app.route('/')
def index():
    fetch_posts()
    return render_template('index.html',
                           title='system auction',
                           posts=posts,
                           node_address=CONNECTED_NODE_ADDRESS,
                           readable_time=timestamp_to_string)


@app.route('/submit', methods=['POST'])
def submit_textarea():
    """
    Endpoint to create a new transaction via our application.
    """
    auctioneer = request.form["auctioneer"]
    post_item = request.form["item"]
    post_price = request.form["price"]
    bidder = request.form["bidder"]
    

    post_object = {
        'auctioneer':auctioneer,
        'item':post_item,
        'price':post_price,
        'bidder':bidder
    }

    # Submit a transaction
    new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)

    requests.post(new_tx_address,
                  json=post_object,
                  headers={'Content-type': 'application/json'})

    return redirect('/')


def timestamp_to_string(epoch_time):
    return datetime.datetime.fromtimestamp(epoch_time).strftime('%H:%M')


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=8080,
                        type=int, help='port to listen on')
    parser.add_argument('--host', default='127.0.0.1',
                        type=str, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    CONNECTED_NODE_ADDRESS = 'http://{}:5000'.format(args.host)

    app.run(host='127.0.0.1', port=port, debug=True, threaded=True)

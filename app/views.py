import datetime
import json
import os
import requests
from flask import Flask
from flask import render_template, redirect, request, jsonify
import time
__location__ = os.path.realpath(os.path.join(
    os.getcwd(), os.path.dirname(__file__)))

app = Flask(__name__)


# The node with which our application interacts, there can be multiple
# such nodes as well.
CONNECTED_NODE_ADDRESS = "http://127.0.0.1:5000"
CONNECTED_NODE_MINE = "http://127.0.0.1:5002"

posts = []


def fetch_posts():
    """
    lấy chuỗi từ peer và phân tích dữ liệu
    """
    get_chain_address = "{}/open_auctions".format(CONNECTED_NODE_ADDRESS)
    """
    response = requests.get(get_chain_address)
    if response.status_code == 200:
        content = []
        data = json.loads(response.content)
        surveys = data['auctions']

        global posts
        posts = sorted(auction, key=lambda k: k['timestamp'],
                       reverse=True)
                       """


@app.route('/')
def index():
    fetch_posts()
    return render_template('index.html',
                           title='System auction based blockchain',
                           posts=posts,
                           node_address=CONNECTED_NODE_ADDRESS,
                           readable_time=timestamp_to_string)


@app.route('/mine', methods=['GET', 'POST'])
def mine():
# dao block moi de luu tru thong tin
    url = '{}/mine'.format(CONNECTED_NODE_ADDRESS)
    response = requests.get(url)

    data = response.json()['response']
    print(data)
    return data

@app.route('/submit', methods=['POST'])
def submit_textarea():
    """
    tạo giao dịch mới khi ấn post
    """
    id_author = int(request.form['id'])
    item = request.form['item']
    opening_time = request.form['opening_time']
    author = request.form['author']

    post_object = {
        'type': 'open',
        'content': {
            'id_author': id_author,
            'item': item,
            'opening_time': opening_time,
            'author': author,
            'status': 'opening',
            'timestamp': time.time()
        }
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

import threading
import time
from threading import Timer
import sys
import requests


def run(times, author, id_auctioneer, CONNECTED_NODE_ADDRESS):
    def close_auction(author, id_auctioneer, CONNECTED_NODE_ADDRESS):

        post_object = {
            'type': 'close',
            'content': {
                'id_auctioneer': id_auctioneer,
                'author': author,
                'timestamp': time.time()
            }
        }

        new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)

        requests.post(new_tx_address,
                      json=post_object,
                      headers={'Content-type': 'application/json'})

        print(author, id_auctioneer, CONNECTED_NODE_ADDRESS)

    def mine():
        # dao block moi de luu tru thong tin
        url = '{}/mine'.format(CONNECTED_NODE_ADDRESS)
        response = requests.get(url)

        data = response.json()['response']
        print(data)

    start = time.perf_counter()
    while True:
        if times() and time.perf_counter()-start > 60:
            t = Timer(0, close_auction, args=[
                      author, id_auctioneer, CONNECTED_NODE_ADDRESS])
            t.start()
            f = Timer(0.6, mine)
            f.start()
            break
        if not times():
            break

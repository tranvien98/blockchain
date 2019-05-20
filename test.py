
import threading
import time
from threading import Timer
import sys

def run(times, author, id_auctioneer, CONNECTED_NODE_ADDRESS):
    def close_auction(author, id_auctioneer, CONNECTED_NODE_ADDRESS):
        
        
        post_object = {
            'type': 'close',
            'content': {
                'id_auctioneer': id_auctioneer,
                'author': author + ':5000',
                'timestamp': time.time()
            }
        }

        new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)

        requests.post(new_tx_address,
                    json=post_object,
                    headers={'Content-type': 'application/json'})
        
        print(author, id_auctioneer, CONNECTED_NODE_ADDRESS)
    stp = 1
    start = time.perf_counter()
    while True:
        if times() and time.perf_counter()-start > 5:
            t = Timer(0, close_auction, args=[author, id_auctioneer, CONNECTED_NODE_ADDRESS])
            t.start()
            break
        if not times():
            break
        


def main():
    author = 1
    id_auctioneer = 2
    CONNECTED_NODE_ADDRESS = 3
    stop_threads = {}
    stop_threads['22'] = True
    t1 = threading.Thread(target=run, args=(lambda: stop_threads['22'], author, id_auctioneer, CONNECTED_NODE_ADDRESS,))
    t1.start()


main()

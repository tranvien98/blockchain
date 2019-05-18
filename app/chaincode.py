from threading import Timer

import time
import requests


def count_down_opening_time(opening_time, author, id_auctioneer, CONNECTED_NODE_ADDRESS):
	def close_survey(author, id_auctioneer, CONNECTED_NODE_ADDRESS):
	    post_object = {
	        'type': 'close',
	        'content': {
	            'id_auctioneer': id_auctioneer,
                'author' : author
	            'timestamp': time.time()
	        }
	    }
	    # them transaction mới
	    new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)

	    print(new_tx_address)

	    requests.post(new_tx_address,
	                  json=post_object,
	                  headers={'Content-type': 'application/json'})

	print(opening_time, author, id_auctioneer)
	t = Timer(opening_time, close_auctions, args=[
	          author, id_auctioneer, CONNECTED_NODE_ADDRESS])
	t.start()

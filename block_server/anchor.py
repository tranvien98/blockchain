import requests
from flask import Flask, jsonify, request
from block import Block

app = Flask(__name__)
general_nodes = set()


def concensus():
    """
    lấy chuỗi local chain của tất cả các general node được quản lý bởi anchor
    chịn ra chuỗi dài nhất trả lại chuỗi đó và độ dài của chuỗi 
    """
    longest_data_chain = []
    longest_lenth = 0

    for peer in general_nodes:
        try:
            print("conect to peer {}".format(peer))
            http_response = requests.get('http://{}/local_chain'.format(peer))
            response = http_response.json()  # {'chain':chain, 'len': len}
            data_chain = response['chain']
            print('local chain of peer {}: {}'.format(peer, response))
            lenth = response['len']

            if lenth > longest_lenth:
                longest_data_chain = data_chain
                longest_lenth = lenth

        except requests.exceptions.ConnectionError:
            print('Cant connect to node {}. Remove it from peers list'.format(peer))
            general_nodes.remove(peer)

    return {'chain': longest_data_chain, 'len': longest_lenth}


@app.route('/add_node', methods=['POST'])
def validate_connection():
    """
    nhận yêu cầu thêm 1 general node (request: <port>)
    thêm node mới vào danh sách node (ip: port)
    tìm kiếm đồng thuận giữa các list node
    trả lại kết quả đồng thuận cho node yêu cầu để thực hiện đồng bộ hóa với các node còn lại trong mạng
    """
    data = request.get_json()
    print("receive data: {}".format(data))
    request_addr = request.remote_addr
    node = str(request_addr) + ':' + str(data['port'])
    print(node)
    general_nodes.add(node)

    print("consensusing...")
    result_chain = concensus()
    print("result chain: {}".format(result_chain))

    # general_nodes.add(node)
    print("current list node {}".format(general_nodes))

    return jsonify(result_chain)


@app.route('/concensus', methods=['GET','POST'])
def reach_concensus():
    """
    thực hiện đồng thuận trong mạng
    B1: tìm kiếm đồng thuận bằng func concensus() đã mô tả ở trên
    B2: yêu cầu thay mới local_chain của tất cả các node trong list node
    B3: trả về kết quả đồng thuận + block cuối cùng (để sử dụng cho mine sau này)
    """
    result_chain = concensus()
    print("send concensus data: {}".format(result_chain))

    for peer in general_nodes:
        try:
            url = 'http://{}/syn_chain'.format(peer)
            requests.post(url, json=result_chain)
        except:
            print('Cant connect to node {}. Remove it from peers list'.format(peer))
            general_nodes.remove(peer)
        
    last_block = result_chain['chain'][-1]
    block = Block.from_dict(last_block)
    hash = block.compute_hash()

    result_chain['last_block'] = last_block
    result_chain['last_hash'] = hash
    
    return jsonify(result_chain)



@app.route('/broadcast_block', methods=['GET','POST'])
def broadcast_block():
    """
    Broadcash bock mới đến các node trong list node
    """
    data = request.get_json()
    # print("send concensus data: {}".format(result_chain))

    for peer in general_nodes:
        try:
            url = 'http://{}/add_block'.format(peer)
            requests.post(url, json=data)
        except:
            print('Cant connect to node {}. Remove it from peers list'.format(peer))
            general_nodes.remove(peer)
        
    return 'success', 200


@app.route('/broadcast_transaction', methods=['POST'])
def announce_new_transaction():
    """
    thông báo cho mạng sau khi giao dịch được thêm vào.
    """
    data = request.get_json()
    if not data:
        return "Invalid data at announce_new_block", 400

    offline_node = []

    for peer in general_nodes:
        try:
            url = "http://{}/get_transaction".format(peer)
            requests.post(url, json=data)
        except requests.exceptions.ConnectionError:
            print('Cant connect to node {}. Remove it from peers list'.format(peer))
            offline_node.append(peer)

    for peer in offline_node:
        general_nodes.remove(peer)

    return "Success", 201

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5001, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    # print('My ip address : ' + get_ip())

    app.run(port=port, debug = True, threaded = True)



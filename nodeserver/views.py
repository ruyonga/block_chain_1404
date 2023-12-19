from .block import Block
from .blockchain import Blockchain
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
import json
import time
import requests

# Create your views here.

# the nodes copy of the block chain
blockchain = Blockchain()
blockchain.create_genesis_block()

# The address to other participating members of the network
peers = set()

# endpoint to submit a new transaction. This will be used by our application to add new data(posts)
# to the blockchain

@csrf_exempt
def new_transaction(request):
    tx_data = json.loads(request.body.decode('utf-8'))
    required_fields = ["author", "content"]

    print(tx_data)

    for field in required_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 400

    tx_data["timestamp"] = time.time()

    blockchain.add_new_transaction(tx_data)

    return "success", 201


# View to return the current chain
def get_chain(request):
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)

    content = {"length": len(chain_data),
               "chain": chain_data, "peers": list(peers)}
    return JsonResponse(content)


# endpoint to request the node to mine the unconfirmed transactions(if any)
# We'll be using it to intiate a command to mine from our application itself
def mine_unconfirmed_transactions(request):
    result = blockchain.mine()

    if not result:
        return "No transactions to mine"
    else:
        # Making sure we have the longest chain before anouncing to the network
        chain_length = len(blockchain.chain)
        consensus()
        if chain_length == len(blockchain.chain):
            # announce the recently mined block to the netwrork
            announce_new_block(blockchain.last_block)
        return "Block #{} is mined".format(blockchain.last_block.index)


def register_new_peers(request):

    node_address = request.get_json()["node_address"]

    if not node_address:
        return "Invalid data", 400

    # Add the node to the peer list
    peers.add(node_address)
    # Return the consensus blockchain to the newly registered node
    # so the he can sync
    return get_chain()


def register_with_existing_node(request):
    """
    Internally calls the 'register_node' endpoint to
    register current node with the node specified in the
    request, and sync the blockchain as well as peer data
    """
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    data = {"node_address": request.host_url}
    headers = {'Content-Type': "application/json"}

    # Make a request to register with remode node and obtain information
    response = request.post(node_address + "/register_node",
                            data=json.dumps(data), headers=headers)

    if response.status_code == 200:
        global blockchain
        global peers
        # update chain and the peers
        chain_dump = response.json()['chain']
        blockchain = create_chain_from_dump(chain_dump)
        peers.update(response.json()['peers'])
        return "Registration successful", 200
    else:
        # if something goes wrong, pass it on to the API response
        return response.content, response.status_code


def create_chain_from_dump(chain_dump):
    generated_blockchain = Blockchain()
    generated_blockchain.create_genesis_block()
    for idx, block_data in enumerate(chain_dump):
        if idx == 0:
            continue
        block = Block(block_data["index"],
                      block_data["transactions"],
                      block_data["timestamp"],
                      block_data["previous_hash"],
                      block_data["nonce"])
        proof = block_data['hash']
        added = generated_blockchain.add_block(block, proof)
        if not added:
            raise Exception("The chain dump is tampered")
    return generated_blockchain


def verify_and_add_block(request):
    block_data = request.get_json()
    block = Block(block_data["index"],
                  block_data["transactions"],
                  block_data["timestamp"],
                  block_data["previous_hash"],
                  block_data["nonce"])
    proof = block_data['hash']
    added = blockchain.add_block(block, proof)

    if not added:
        return "The block was discarded by the node", 400
    return "Block added to the chain", 201

# endpoint to query unconfirmed transactions


def get_pending_txns(request):
    return json.dumps(blockchain.unconfirmed_transactions)


def consensus():
    """
    Our naive consensus algorithm. if a longer valid chain is found out chain is replaced with it
    """
    global blockchain
    longest_chain = None
    current_len = len(blockchain.chain)

    for node in peers:

        responses = redirect("{}chain".format(node))

        length = responses.json()["length"]
        chain = responses.json()["chain"]

        if length > current_len and blockchain.check_chain_validity(chain):
            current_len = length
            longest_chain = chain

    if longest_chain:
        blockchain = longest_chain
        return True
    return False


def announce_new_block(block):
    """
    A function to announce to the network once a block has been minded.
    Other nodes can simply verify the proof of work and add it to their respective chain
    """
    for peer in peers:
        url = "{}add_block".format(peer)
        headers = {'Content-Type': "application/json"}
        try:
            # Make the POST request
            response = requests.posts(url, data=json.dumps(
                block.__dict__, sort_keys=True), headers=headers)
            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                content = response.text
                return HttpResponse(f"POST request successful. Response: {content}")
            else:
                return HttpResponse(f"POST request failed. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            # Handle exceptions (e.g., connection error, timeout)
            return HttpResponse(f"An error occurred: {e}")

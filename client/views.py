from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from .block import Block
from .blockchain import Blockchain
import requests
import datetime
import time
import json


# The node with which our application interacts, there can be mulitple such nodes aswell
CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"

posts = []
blockchain = Blockchain()
blockchain.create_genesis_block()
peers = set()

def fetch_posts():
    """
    This functions to fetch the chain from the blockchain node, parse the data and stores it locally

    """
    get_chain_address = f"{CONNECTED_NODE_ADDRESS}/chain"
    response = requests.get(get_chain_address)

    if response.status_code == 200:
        content = []
        chain = json.loads(response.content)
        for block in chain["chain"]:
            for tx in block["transcations"]:
                tx["index"] = block["index"]
                tx["hash"] = block["previous_hash"]
                tx['timestamp'] = timestamp_to_string(tx['timestamp'])
                content.append(tx)

        global posts
        posts = sorted(content, key=lambda k: k['timestamp'], reverse=True)
        
    
def index(request):
    """
    Home page of the application
    """
    print(fetch_posts())
    context = {"title": 'YourNet: Decenteralised content shaing',
               "posts": posts,
               "node_address": CONNECTED_NODE_ADDRESS}
    return render(request, "client/index.html", context)


def create_transaction(request):
    """
    Endpoint to create a new transaction via our application
    """
    post_content = request.POST["content"]
    author = request.POST["author"]
    post_object = {
        'author': author,
        'content': post_content,
    }

    # submit a transaction
    new_tx_address = "{}/new_transaction/".format(CONNECTED_NODE_ADDRESS)
    response = requests.post(new_tx_address, json=post_object, headers={
                  'Content-type': 'application/json'})
    if response.status_code == 200:
        messages.add_message(request, messages.SUCCESS,
                         "Transaction added successfully")
    else:
        messages.add_message(request, messages.ERROR,
                         "Error while creating transaction")
    return HttpResponseRedirect(reverse("client:index"))



# endpoint to submit a new transaction. This will be used by our application to add new data(posts)
# to the blockchain
@csrf_exempt
def new_transaction(request):
    tx_data = json.loads(request.body.decode('utf-8'))
    required_fields = ["author", "content"]

    for field in required_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 400

    tx_data["timestamp"] = time.time()
    blockchain.add_new_transaction(tx_data)

    return JsonResponse({"massage": "Transaction added successfuly", "status_code": 201})


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
        return HttpResponse("No transactions to mine")
    else:
        # Making sure we have the longest chain before anouncing to the network
        chain_length = len(blockchain.chain)
        consensus()
        if chain_length == len(blockchain.chain):
            # announce the recently mined block to the netwrork
            announce_new_block(blockchain.last_block)
        return HttpResponse("Block #{} is mined".format(blockchain.last_block.index))
    

@csrf_exempt
def register_new_peers(request):
    node_address = request.POST['node_address']

    if not node_address:
        return HttpResponseNotFound("Missing peer node address")

    # Add the node to the peer list
    peers.add(node_address)
    # Return the consensus blockchain to the newly registered node
    # so the he can sync

    #Build url to get chain view

    redirect_url = reverse("client:get-chain")
    return HttpResponseRedirect(redirect_url)

@csrf_exempt
def register_with_existing_node(request):
    """
    Internally calls the 'register_node' endpoint to
    register current node with the node specified in the
    request, and sync the blockchain as well as peer data
    """
    node_address = request.POST['node_address']

    if not node_address:
        return HttpResponseNotFound("Node address is missing")

    data = {"node_address": "http://"+request.META['HTTP_HOST']}
    headers = {'Content-Type': "application/json"}

    # Make a request to register with remode node and obtain information
    response = requests.post(node_address + "/register_node",
                             data=data, headers=headers)
    
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
    block_data = request.POST
    block = Block(block_data["index"],
                  block_data["transactions"],
                  block_data["timestamp"],
                  block_data["previous_hash"],
                  block_data["nonce"])
    proof = block_data['hash']
    added = blockchain.add_block(block, proof)

    if not added:
        return HttpResponseNotFound("The block was discarded by the node", 400)
    return HttpResponse("Block added to the chain", 201)

# endpoint to query unconfirmed transactions
def get_pending_txns(request):
    return JsonResponse(blockchain.unconfirmed_transactions, safe=False)


def consensus():
    """
    Our naive consensus algorithm. if a longer valid chain is found out chain is replaced with it
    """
    global blockchain
    longest_chain = None
    current_len = len(blockchain.chain)

    for node in peers:

        responses = HttpResponseRedirect(f"{node}/chain")

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
        url = "{}/add_block".format(peer)
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
        except requests.RequestException as e:
            # Handle exceptions (e.g., connection error, timeout)
            return HttpResponse(f"Anerror occurred: {e}")


def timestamp_to_string(epoc_itme):
    return datetime.datetime.fromtimestamp(epoc_itme).strftime('%H:%M')

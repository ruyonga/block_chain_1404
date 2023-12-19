from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
import requests
import datetime
import json


# The node with which our application interacts, there can be mulitple such nodes aswell
CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"

posts = []

def fetch_posts():
    """
    This functions to fetch the chain from the blockchain node, parse the data and stores it locally

    """
    get_chain_address = "{}/api/chain".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)
       
    if response.status_code == 200:
        content = []

        chain = json.loads(response.content)
        print(chain)

        for block in chain["chain"]:
            for tx in block["transcations"]:
                tx["index"] = block["index"]
                tx["hash"] = block["previous_hash"]
                content.append(tx)

        global posts
        posts = sorted(content, key=lambda k: k['timestamp'], reverse=True)


def index(request):
    fetch_posts()
    context = {"title": 'YourNet: Decenteralised content shaing',  "posts": posts, "node_address": CONNECTED_NODE_ADDRESS, "readable_time": timestamp_to_string}
    return render(request, "client/index.html", context)

#view to handle creating of transactions from the web
def create_transaction(request):
    """
    Endpoint to create a new transaction via our application
    """
    post_content = request.POST["content"]
    author = request.POST["author"]
    post_object = {
        'author' : author,
        'content' : post_content,
        }

    #submit a transaction
    new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)
    requests.post(new_tx_address, json=post_object, headers={'Content-type' : 'application/json'})

    return HttpResponseRedirect(reverse("index"))



def timestamp_to_string(epoc_itme):
    return datetime.datetime.fromtimestamp(epoc_itme).strftime('%H:%M')


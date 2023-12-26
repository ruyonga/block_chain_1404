from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
import requests
import datetime
import json


# The node with which our application interacts, there can be mulitple such nodes aswell
CONNECTED_NODE_ADDRESS = "http://192.168.1.20:8000"

posts = []


def fetch_posts():
    """
    This functions to fetch the chain from the blockchain node, parse the data and stores it locally

    """
    get_chain_address = f"{CONNECTED_NODE_ADDRESS}/api/chain"
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
    """
    Home page of the application
    """
    fetch_posts()
    context = {"title": 'YourNet: Decenteralised content shaing',  "posts": posts,
               "node_address": CONNECTED_NODE_ADDRESS, "readable_time": timestamp_to_string}
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
    new_tx_address = "{}/api/new_transaction/".format(CONNECTED_NODE_ADDRESS)
    response = requests.post(new_tx_address, json=post_object, headers={
                  'Content-type': 'application/json'})
    if response.status_code == 200:
        messages.add_message(request, messages.SUCCESS,
                         "Transaction added successfully")
    else:
        messages.add_message(request, messages.ERROR,
                         "Error while creating transaction")
    return HttpResponseRedirect(reverse("client:index"))


def timestamp_to_string(epoc_itme):
    return datetime.datetime.fromtimestamp(epoc_itme).strftime('%H:%M')

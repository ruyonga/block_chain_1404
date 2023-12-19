from hashlib import sha256
import json

class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
       """
       Constructor for the Block class
       :param index:            Unique ID of the block
       :param transactions:     list of transactions
       :param timestamp:        Time of the gerneration of the block
       :param previous_hash:    Hash of the previous  block in the chain which this block is part of
       """

       self.index = index
       self.transcations = transactions
       self.timestamp = timestamp
       self.previous_hash = previous_hash
       self.nonce = nonce

    def compute_hash(self):
        """
        A function that returns the hash of block content
        """
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()

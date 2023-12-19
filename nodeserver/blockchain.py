import time
from .block import Block

class Blockchain:
    #difficulty of proof of work algorithm
    difficulty = 2

    def __init__(self):
        """
        This is the constructor for the blockchain class
        """
        self.unconfirmed_transactions = []
        self.chain = []

    def create_genesis_block(self):
        """
        A function to generate a genesis bloc and append it to the chain.
        The block has index 0, previous_hash as 0, and a valid had
        """
        genesis_block = Block(0, [], 0, '0')
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)


    @property
    def last_block(self):
        return self.chain[-1]
    
    def add_block(self, block, proof):
        """
        A function that adds a vlock to the chain after verification.
        Verification includes;
        * Checking if the proof is valid
        * The previous_hash referred in the block and the hash of the latest block in the chain match
        """

        previous_hash = self.last_block.hash

        if previous_hash != block.previous_hash:
            return False
        
        if not Blockchain.is_valid_proof(block, proof):
            return False
        
        block.hash = proof
        self.chain.append(block)
        return True

    @staticmethod
    def proof_of_work(block):
        """
        Function that tries different values of nonce to get hash that statisifies our difficulty
        """

        block.nonce = 0
        computed_hash = block.compute_hash()

        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash
    

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)
        
        
    @classmethod
    def is_valid_proof(cls, block, block_hash):
    
        """" 
        Check of the block has is valid hash of the 
        block and satififies the difficulty creteria. """

        return (block_hash.startswith('0'* Blockchain.difficulty) and block_hash == block.compute_hash())
        
    
    @classmethod
    def check_chain_validity(cls, chain):
        result  = True
        
        previous_hash = '0'
        for block in chain:
            block_hash = block.hash
            #remove the has field to recompute the hash again
            #using compute_hash method
        
            delattr(block, "hash")
            if not cls.is_valid_proof(block, block_hash) or previous_hash != block.previous_hash:
                result = False
                break
            block.hash, previous_hash = block_hash, block_hash
        return result
        
        
        
    def mine(self):
        """
        This function services as an interface to add the pending transactions to the blockchain by adding
        them to the block and figuring out the prood of work
        """
        if not self.unconfirmed_transactions:
            return False
        
        last_block = self.last_block
        new_block = Block(index=last_block.index+1, transactions=self.unconfirmed_transactions, 
                          timestamp=time.time(), previous_hash=last_block.hash)
        
        proof = self.proof_of_work(new_block)
        
        self.add_block(new_block, proof)
        
        self.unconfirmed_transactions = []
    
        return True
        
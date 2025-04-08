import hashlib
import json
import time
from datetime import datetime


class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        """
        Initialize a new block in the blockchain
        
        Args:
            index (int): Position of the block in the chain
            timestamp (float): Time when the block was created
            data (dict): Academic record data stored in the block
            previous_hash (str): Hash of the previous block in the chain
        """
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()
    
    def calculate_hash(self):
        """
        Calculate the hash of the block using SHA-256
        
        Returns:
            str: Hexadecimal hash of the block
        """
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True).encode()
        
        return hashlib.sha256(block_string).hexdigest()
    
    def mine_block(self, difficulty=2):
        """
        Mine a new block (find a hash with a given difficulty)
        
        Args:
            difficulty (int): Number of leading zeros required in the hash
        """
        target = '0' * difficulty
        
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        
        print(f"Block mined: {self.hash}")
    
    def to_dict(self):
        """
        Convert block to dictionary for serialization
        
        Returns:
            dict: Block data in dictionary format
        """
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash
        }


class Blockchain:
    def __init__(self):
        """Initialize a new blockchain with a genesis block"""
        self.chain = [self.create_genesis_block()]
        self.difficulty = 2  # Difficulty of mining (number of leading zeros)
    
    def create_genesis_block(self):
        """
        Create the first block in the chain (genesis block)
        
        Returns:
            Block: The genesis block
        """
        return Block(0, time.time(), {"message": "Genesis Block"}, "0")
    
    def get_latest_block(self):
        """
        Get the most recent block in the chain
        
        Returns:
            Block: The latest block in the chain
        """
        return self.chain[-1]
    
    def add_block(self, data):
        """
        Add a new block to the chain with the given data
        
        Args:
            data (dict): Academic record data to be stored in the block
            
        Returns:
            Block: The newly created and added block
        """
        previous_block = self.get_latest_block()
        new_index = previous_block.index + 1
        new_timestamp = time.time()
        new_block = Block(new_index, new_timestamp, data, previous_block.hash)
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)
        return new_block
    
    def is_chain_valid(self):
        """
        Verify the integrity of the blockchain
        
        Returns:
            bool: True if the chain is valid, False otherwise
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            # Check if the current block's hash is valid
            if current_block.hash != current_block.calculate_hash():
                print("Invalid hash")
                return False
            
            # Check if the current block points to the correct previous hash
            if current_block.previous_hash != previous_block.hash:
                print("Invalid previous hash reference")
                return False
        
        return True
    
    def get_block_by_hash(self, hash_value):
        """
        Find a block by its hash value
        
        Args:
            hash_value (str): Hash of the block to find
            
        Returns:
            Block or None: The block with the given hash, or None if not found
        """
        for block in self.chain:
            if block.hash == hash_value:
                return block
        return None
    
    def get_block_by_index(self, index):
        """
        Find a block by its index
        
        Args:
            index (int): Index of the block to find
            
        Returns:
            Block or None: The block with the given index, or None if not found
        """
        if 0 <= index < len(self.chain):
            return self.chain[index]
        return None
    
    def to_dict(self):
        """
        Convert the entire blockchain to a dictionary for serialization
        
        Returns:
            dict: Blockchain data in dictionary format
        """
        return {
            'chain': [block.to_dict() for block in self.chain],
            'difficulty': self.difficulty,
            'length': len(self.chain)
        }
    
    @classmethod
    def from_dict(cls, blockchain_dict):
        """
        Create a blockchain instance from a dictionary
        
        Args:
            blockchain_dict (dict): Dictionary representation of a blockchain
            
        Returns:
            Blockchain: A new blockchain instance with the data from the dictionary
        """
        blockchain = cls()
        blockchain.chain = []
        
        for block_dict in blockchain_dict['chain']:
            block = Block(
                block_dict['index'],
                block_dict['timestamp'],
                block_dict['data'],
                block_dict['previous_hash']
            )
            block.nonce = block_dict['nonce']
            block.hash = block_dict['hash']
            blockchain.chain.append(block)
        
        blockchain.difficulty = blockchain_dict['difficulty']
        return blockchain

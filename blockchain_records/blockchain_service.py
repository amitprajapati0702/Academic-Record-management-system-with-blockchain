from .blockchain import Blockchain
from .models import BlockchainInstance, AcademicRecord
import json


class BlockchainService:
    """Service class to handle blockchain operations"""
    
    @classmethod
    def get_blockchain(cls):
        """
        Get the current blockchain instance or create a new one if none exists
        
        Returns:
            Blockchain: The current blockchain instance
        """
        try:
            instance = BlockchainInstance.objects.latest('last_updated')
            return instance.load_blockchain()
        except BlockchainInstance.DoesNotExist:
            # Create a new blockchain if none exists
            return Blockchain()
    
    @classmethod
    def save_blockchain(cls, blockchain):
        """
        Save the current state of the blockchain
        
        Args:
            blockchain (Blockchain): The blockchain to save
        """
        instance = BlockchainInstance()
        instance.save_blockchain(blockchain)
    
    @classmethod
    def add_record_to_blockchain(cls, record):
        """
        Add an academic record to the blockchain
        
        Args:
            record (AcademicRecord): The academic record to add
            
        Returns:
            str: The hash of the block containing the record
        """
        blockchain = cls.get_blockchain()
        
        # Convert the record to blockchain data format
        data = record.to_blockchain_data()
        
        # Add the record to the blockchain
        new_block = blockchain.add_block(data)
        
        # Save the updated blockchain
        cls.save_blockchain(blockchain)
        
        # Update the record with the block hash
        record.block_hash = new_block.hash
        record.save(update_fields=['block_hash'])
        
        return new_block.hash
    
    @classmethod
    def verify_record(cls, record):
        """
        Verify if a record exists in the blockchain and has not been tampered with
        
        Args:
            record (AcademicRecord): The academic record to verify
            
        Returns:
            dict: Verification result with status and message
        """
        if not record.block_hash:
            return {
                'verified': False,
                'message': 'Record is not on the blockchain'
            }
        
        blockchain = cls.get_blockchain()
        
        # Check if the blockchain is valid
        if not blockchain.is_chain_valid():
            return {
                'verified': False,
                'message': 'Blockchain integrity is compromised'
            }
        
        # Find the block containing the record
        block = blockchain.get_block_by_hash(record.block_hash)
        
        if not block:
            return {
                'verified': False,
                'message': 'Block not found in the blockchain'
            }
        
        # Verify the record data matches the data in the block
        block_data = block.data
        if block_data.get('record_id') != record.id:
            return {
                'verified': False,
                'message': 'Record ID mismatch'
            }
        
        if block_data.get('student_id') != record.student.student_id:
            return {
                'verified': False,
                'message': 'Student ID mismatch'
            }
        
        # Record is verified
        return {
            'verified': True,
            'message': 'Record verified successfully',
            'block_index': block.index,
            'timestamp': block.timestamp
        }
    
    @classmethod
    def get_blockchain_stats(cls):
        """
        Get statistics about the blockchain
        
        Returns:
            dict: Statistics about the blockchain
        """
        blockchain = cls.get_blockchain()
        
        return {
            'total_blocks': len(blockchain.chain),
            'is_valid': blockchain.is_chain_valid(),
            'difficulty': blockchain.difficulty,
            'genesis_block_time': blockchain.chain[0].timestamp
        }
    
    @classmethod
    def get_record_history(cls, student_id):
        """
        Get all blockchain records for a specific student
        
        Args:
            student_id (str): ID of the student
            
        Returns:
            list: List of blocks containing records for the student
        """
        blockchain = cls.get_blockchain()
        student_blocks = []
        
        for block in blockchain.chain[1:]:  # Skip genesis block
            if block.data.get('student_id') == student_id:
                student_blocks.append(block)
        
        return student_blocks

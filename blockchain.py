"""
Blockchain implementation for Entekhablock voting system
Provides immutable ledger for storing votes with SHA-256 hashing
"""

import hashlib
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional


class Block:
    """
    Represents a single block in the blockchain
    Each block contains vote data and links to previous block via hash
    """
    
    def __init__(self, index: int, timestamp: str, data: Dict[str, Any], previous_hash: str):
        """
        Initialize a new block
        
        Args:
            index: Position of block in chain (starts at 0 for genesis)
            timestamp: ISO format timestamp of block creation
            data: Dictionary containing vote information
            previous_hash: Hash of the previous block (ensures chain integrity)
        """
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = 0  # For simple proof of work
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """
        Generate SHA-256 hash of block contents
        Hash includes all block data to ensure immutability
        
        Returns:
            64-character hexadecimal hash string
        """
        # Combine all block data into single string
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True, ensure_ascii=False)
        
        # Return SHA-256 hash
        return hashlib.sha256(block_string.encode('utf-8')).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert block to dictionary for JSON serialization
        
        Returns:
            Dictionary representation of block
        """
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash
        }


class Blockchain:
    """
    Main blockchain class managing the chain of blocks
    Ensures integrity and provides methods for adding/validating blocks
    """
    
    def __init__(self, storage_path: Optional[str] = None, difficulty: int = 4):
        """
        Initialize blockchain with genesis block or load from file
        
        Args:
            storage_path: Path to JSON file for persistence
            difficulty: Number of leading zeros required for PoW
        """
        self.chain: List[Block] = []
        self.storage_path = storage_path
        self.difficulty = difficulty
        
        if storage_path and os.path.exists(storage_path):
            self.load_from_file()
        else:
            self.create_genesis_block()
            if storage_path:
                self.save_to_file()
    
    def create_genesis_block(self) -> None:
        """
        Create the first block in the chain (Genesis Block)
        This block has previous_hash of "0" and contains initialization data
        """
        genesis_data = {
            "message": "انتخابِلاک - Genesis Block",
            "system": "Entekhablock Voting Platform",
            "version": "1.0.0"
        }
        
        genesis_block = Block(
            index=0,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data=genesis_data,
            previous_hash="0"
        )
        
        # Mine the genesis block
        self.proof_of_work(genesis_block)

        self.chain.append(genesis_block)

    def save_to_file(self) -> bool:
        """Save blockchain to JSON file"""
        if not self.storage_path:
            return False
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump([b.to_dict() for b in self.chain], f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving blockchain: {e}")
            return False

    def load_from_file(self) -> bool:
        """Load blockchain from JSON file"""
        if not self.storage_path or not os.path.exists(self.storage_path):
            return False
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.chain = []
                for b_dict in data:
                    block = Block(
                        index=b_dict['index'],
                        timestamp=b_dict['timestamp'],
                        data=b_dict['data'],
                        previous_hash=b_dict['previous_hash']
                    )
                    block.nonce = b_dict.get('nonce', 0)
                    block.hash = b_dict['hash']
                    self.chain.append(block)
            return True
        except Exception as e:
            print(f"Error loading blockchain: {e}")
            self.create_genesis_block()
            return False
    
    def get_latest_block(self) -> Block:
        """
        Get the most recent block in the chain
        
        Returns:
            Last block in the chain
        """
        return self.chain[-1]
    
    def proof_of_work(self, block: Block) -> str:
        """
        Perform Proof of Work mining
        Find a nonce that produces a hash starting with the required number of zeros
        """
        block.nonce = 0
        computed_hash = block.calculate_hash()
        while not computed_hash.startswith('0' * self.difficulty):
            block.nonce += 1
            computed_hash = block.calculate_hash()
        block.hash = computed_hash
        return computed_hash

    def add_block(self, data: Dict[str, Any]) -> Block:
        """
        Add a new block to the chain with vote data
        
        Args:
            data: Dictionary containing vote information
                  Expected keys: voter_hash, poll_id, choice, timestamp
        
        Returns:
            The newly created and added block
        """
        latest_block = self.get_latest_block()
        
        new_block = Block(
            index=len(self.chain),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data=data,
            previous_hash=latest_block.hash
        )
        
        # Mine the block
        self.proof_of_work(new_block)

        self.chain.append(new_block)
        self.save_to_file()
        return new_block
    
    def is_chain_valid(self) -> bool:
        """
        Validate the entire blockchain
        Checks:
        1. Each block's hash is correct
        2. Each block's previous_hash matches the actual previous block's hash
        
        Returns:
            True if chain is valid, False if tampered
        """
        # Start from block 1 (skip genesis block)
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Check if current block's hash is correct
            if current_block.hash != current_block.calculate_hash():
                return False
            
            # Check if hash meets difficulty requirements
            if not current_block.hash.startswith('0' * self.difficulty):
                return False

            # Check if previous_hash matches
            if current_block.previous_hash != previous_block.hash:
                return False
        
        return True
    
    def get_blocks_by_poll(self, poll_id: str) -> List[Dict[str, Any]]:
        """
        Get all blocks (votes) for a specific poll
        
        Args:
            poll_id: Unique identifier of the poll
        
        Returns:
            List of block dictionaries containing votes for the poll
        """
        poll_blocks = []
        
        for block in self.chain:
            # Skip genesis block
            if block.index == 0:
                continue
            
            # Check if block contains vote for this poll
            if block.data.get("poll_id") == poll_id:
                poll_blocks.append(block.to_dict())
        
        return poll_blocks
    
    def get_all_blocks(self) -> List[Dict[str, Any]]:
        """
        Get all blocks in the chain as dictionaries
        
        Returns:
            List of all blocks in dictionary format
        """
        return [block.to_dict() for block in self.chain]
    
    def get_chain_info(self) -> Dict[str, Any]:
        """
        Get summary information about the blockchain
        
        Returns:
            Dictionary with chain statistics
        """
        return {
            "total_blocks": len(self.chain),
            "total_votes": len(self.chain) - 1,  # Exclude genesis block
            "is_valid": self.is_chain_valid(),
            "latest_block_hash": self.get_latest_block().hash,
            "genesis_timestamp": self.chain[0].timestamp
        }
    
    def simulate_tampering(self, block_index: int, new_data: Dict[str, Any]) -> Dict[str, bool]:
        """
        DEMO FUNCTION: Simulate tampering with a block to show immutability
        This will break the chain integrity
        
        Args:
            block_index: Index of block to tamper with
            new_data: New data to replace original block data
        
        Returns:
            Dictionary showing before/after validity status
        """
        if block_index >= len(self.chain) or block_index == 0:
            return {"error": "Invalid block index or cannot tamper genesis block"}
        
        # Check validity before tampering
        before_valid = self.is_chain_valid()
        
        # Tamper with the block
        self.chain[block_index].data = new_data
        # NOTE: We DON'T recalculate hash - this simulates malicious tampering
        
        # Check validity after tampering
        after_valid = self.is_chain_valid()
        
        return {
            "before_tampering": before_valid,
            "after_tampering": after_valid,
            "tampered_block": block_index,
            "integrity_broken": before_valid and not after_valid
        }


from utils.auth import hash_voter_identity as hash_national_code


# Demo/Testing
if __name__ == "__main__":
    # Create blockchain instance
    bc = Blockchain()
    
    print("=== Entekhablock Blockchain Demo ===\n")
    
    # Add sample votes
    vote1 = {
        "voter_hash": hash_national_code("0012345678"),
        "poll_id": "poll_001",
        "choice": "گزینه ۱",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    vote2 = {
        "voter_hash": hash_national_code("0023456789"),
        "poll_id": "poll_001",
        "choice": "گزینه ۲",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    block1 = bc.add_block(vote1)
    block2 = bc.add_block(vote2)
    
    print(f"Block 1 Hash: {block1.hash}")
    print(f"Block 2 Hash: {block2.hash}")
    print(f"\nChain Valid: {bc.is_chain_valid()}")
    
    # Show chain info
    print(f"\nChain Info: {json.dumps(bc.get_chain_info(), indent=2, ensure_ascii=False)}")
    
    # Demonstrate tampering
    print("\n=== Simulating Tampering ===")
    tamper_result = bc.simulate_tampering(1, {"fake": "data"})
    print(json.dumps(tamper_result, indent=2, ensure_ascii=False))

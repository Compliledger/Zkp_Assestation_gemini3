"""
Merkle Tree Implementation
For creating cryptographic commitments to evidence bundles
"""

import hashlib
from typing import List, Dict, Optional, Any
import json
import logging

logger = logging.getLogger(__name__)


class MerkleNode:
    """
    A node in the Merkle tree
    """
    def __init__(self, hash_value: str, left: Optional['MerkleNode'] = None, right: Optional['MerkleNode'] = None):
        self.hash = hash_value
        self.left = left
        self.right = right
    
    def is_leaf(self) -> bool:
        return self.left is None and self.right is None


class MerkleTree:
    """
    Merkle tree for evidence commitment
    
    Creates a binary tree of hashes where:
    - Leaf nodes contain hashes of evidence items
    - Internal nodes contain hashes of their children
    - Root node is the commitment to all evidence
    """
    
    def __init__(self, hash_algorithm: str = "SHA256"):
        """
        Initialize Merkle tree
        
        Args:
            hash_algorithm: Hash algorithm to use (SHA256, SHA512, etc.)
        """
        self.hash_algorithm = hash_algorithm.upper()
        self.root: Optional[MerkleNode] = None
        self.leaves: List[str] = []
        self._validate_algorithm()
    
    def _validate_algorithm(self):
        """Validate hash algorithm is supported"""
        supported = ["SHA256", "SHA512", "SHA384", "SHA224", "SHA1"]
        if self.hash_algorithm not in supported:
            raise ValueError(f"Unsupported hash algorithm: {self.hash_algorithm}. Supported: {supported}")
    
    def _hash(self, data: bytes) -> str:
        """
        Hash data using configured algorithm
        
        Args:
            data: Data to hash
            
        Returns:
            Hex-encoded hash
        """
        if self.hash_algorithm == "SHA256":
            return hashlib.sha256(data).hexdigest()
        elif self.hash_algorithm == "SHA512":
            return hashlib.sha512(data).hexdigest()
        elif self.hash_algorithm == "SHA384":
            return hashlib.sha384(data).hexdigest()
        elif self.hash_algorithm == "SHA224":
            return hashlib.sha224(data).hexdigest()
        elif self.hash_algorithm == "SHA1":
            return hashlib.sha1(data).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm: {self.hash_algorithm}")
    
    def _hash_pair(self, left: str, right: str) -> str:
        """
        Hash two values together (for internal nodes)
        
        Args:
            left: Left child hash
            right: Right child hash
            
        Returns:
            Combined hash
        """
        combined = (left + right).encode('utf-8')
        return self._hash(combined)
    
    def add_leaf(self, data: bytes) -> str:
        """
        Add a leaf to the tree
        
        Args:
            data: Data for the leaf node
            
        Returns:
            Hash of the leaf
        """
        leaf_hash = self._hash(data)
        self.leaves.append(leaf_hash)
        return leaf_hash
    
    def add_leaves(self, data_list: List[bytes]) -> List[str]:
        """
        Add multiple leaves to the tree
        
        Args:
            data_list: List of data items
            
        Returns:
            List of leaf hashes
        """
        return [self.add_leaf(data) for data in data_list]
    
    def build(self) -> str:
        """
        Build the Merkle tree from leaves
        
        Returns:
            Root hash (Merkle root)
            
        Raises:
            ValueError: If no leaves have been added
        """
        if not self.leaves:
            raise ValueError("Cannot build tree with no leaves")
        
        # Start with leaf nodes
        nodes = [MerkleNode(leaf_hash) for leaf_hash in self.leaves]
        
        # Build tree bottom-up
        while len(nodes) > 1:
            next_level = []
            
            # Process pairs of nodes
            for i in range(0, len(nodes), 2):
                left = nodes[i]
                
                # If odd number of nodes, duplicate the last one
                if i + 1 < len(nodes):
                    right = nodes[i + 1]
                else:
                    right = nodes[i]
                
                # Create parent node
                parent_hash = self._hash_pair(left.hash, right.hash)
                parent = MerkleNode(parent_hash, left, right)
                next_level.append(parent)
            
            nodes = next_level
        
        self.root = nodes[0]
        logger.info(f"Built Merkle tree with {len(self.leaves)} leaves, root: {self.root.hash[:16]}...")
        return self.root.hash
    
    def get_root(self) -> Optional[str]:
        """
        Get the Merkle root
        
        Returns:
            Root hash or None if tree not built
        """
        return self.root.hash if self.root else None
    
    def get_proof(self, leaf_index: int) -> List[Dict[str, Any]]:
        """
        Get Merkle proof for a specific leaf
        
        Args:
            leaf_index: Index of the leaf
            
        Returns:
            List of proof elements (sibling hashes and positions)
            
        Raises:
            ValueError: If tree not built or invalid index
        """
        if not self.root:
            raise ValueError("Tree must be built before generating proofs")
        
        if leaf_index < 0 or leaf_index >= len(self.leaves):
            raise ValueError(f"Invalid leaf index: {leaf_index}")
        
        proof = []
        nodes = [MerkleNode(leaf_hash) for leaf_hash in self.leaves]
        current_index = leaf_index
        
        # Build proof bottom-up
        while len(nodes) > 1:
            next_level = []
            
            for i in range(0, len(nodes), 2):
                left = nodes[i]
                right = nodes[i + 1] if i + 1 < len(nodes) else nodes[i]
                
                # If this is the path we're proving
                if i == current_index or i + 1 == current_index:
                    if current_index == i:
                        # We're on the left, record right sibling
                        proof.append({
                            "position": "right",
                            "hash": right.hash
                        })
                    else:
                        # We're on the right, record left sibling
                        proof.append({
                            "position": "left",
                            "hash": left.hash
                        })
                
                parent_hash = self._hash_pair(left.hash, right.hash)
                parent = MerkleNode(parent_hash, left, right)
                next_level.append(parent)
            
            # Move up to parent level
            current_index = current_index // 2
            nodes = next_level
        
        return proof
    
    def verify_proof(self, leaf_hash: str, proof: List[Dict[str, Any]], root_hash: str) -> bool:
        """
        Verify a Merkle proof
        
        Args:
            leaf_hash: Hash of the leaf to verify
            proof: Proof elements
            root_hash: Expected root hash
            
        Returns:
            True if proof is valid, False otherwise
        """
        current_hash = leaf_hash
        
        for element in proof:
            sibling_hash = element["hash"]
            position = element["position"]
            
            if position == "left":
                current_hash = self._hash_pair(sibling_hash, current_hash)
            else:
                current_hash = self._hash_pair(current_hash, sibling_hash)
        
        return current_hash == root_hash
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert tree to dictionary for storage
        
        Returns:
            Dictionary representation
        """
        return {
            "hash_algorithm": self.hash_algorithm,
            "root": self.get_root(),
            "leaves": self.leaves,
            "leaf_count": len(self.leaves)
        }
    
    def to_json(self) -> str:
        """
        Convert tree to JSON string
        
        Returns:
            JSON representation
        """
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MerkleTree':
        """
        Create tree from dictionary
        
        Args:
            data: Dictionary representation
            
        Returns:
            MerkleTree instance
        """
        tree = cls(hash_algorithm=data["hash_algorithm"])
        tree.leaves = data["leaves"]
        if data["root"]:
            tree.build()
        return tree
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MerkleTree':
        """
        Create tree from JSON string
        
        Args:
            json_str: JSON representation
            
        Returns:
            MerkleTree instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)


def create_merkle_tree_from_hashes(hashes: List[str], hash_algorithm: str = "SHA256") -> MerkleTree:
    """
    Create a Merkle tree from a list of hashes
    
    Args:
        hashes: List of hash strings
        hash_algorithm: Hash algorithm to use
        
    Returns:
        Built MerkleTree
    """
    tree = MerkleTree(hash_algorithm=hash_algorithm)
    tree.leaves = hashes
    tree.build()
    return tree


def create_merkle_tree_from_evidence(evidence_items: List[Dict[str, Any]], hash_algorithm: str = "SHA256") -> MerkleTree:
    """
    Create a Merkle tree from evidence items
    
    Args:
        evidence_items: List of evidence dictionaries with 'hash' key
        hash_algorithm: Hash algorithm to use
        
    Returns:
        Built MerkleTree
    """
    hashes = [item["hash"] for item in evidence_items]
    return create_merkle_tree_from_hashes(hashes, hash_algorithm)


def verify_evidence_integrity(evidence_hash: str, proof: List[Dict[str, Any]], merkle_root: str, 
                              hash_algorithm: str = "SHA256") -> bool:
    """
    Verify that an evidence item is part of a Merkle tree
    
    Args:
        evidence_hash: Hash of the evidence to verify
        proof: Merkle proof
        merkle_root: Expected Merkle root
        hash_algorithm: Hash algorithm used
        
    Returns:
        True if evidence is part of the tree, False otherwise
    """
    tree = MerkleTree(hash_algorithm=hash_algorithm)
    return tree.verify_proof(evidence_hash, proof, merkle_root)

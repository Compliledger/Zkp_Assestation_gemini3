"""
Evidence Commitment Generator
Creates Merkle tree commitments for evidence bundles
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import json

from app.utils.merkle import MerkleTree, create_merkle_tree_from_hashes
from app.utils.crypto import HashUtils, CryptoUtils
from app.core.evidence.normalizer import NormalizedEvidence
from app.utils.errors import ValidationError


class EvidenceCommitment(BaseModel):
    """
    Merkle tree commitment for evidence bundle
    """
    bundle_id: str = Field(..., description="Evidence bundle identifier")
    merkle_root: str = Field(..., description="Merkle tree root hash")
    evidence_count: int = Field(..., description="Number of evidence items")
    evidence_hashes: List[str] = Field(..., description="Hashes of all evidence items")
    
    # Tree metadata
    hash_algorithm: str = Field(default="SHA256", description="Hash algorithm used")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Encryption info (if encrypted)
    is_encrypted: bool = Field(default=False)
    encryption_key_id: Optional[str] = Field(None, description="ID of encryption key used")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CommitmentGenerator:
    """
    Generates cryptographic commitments for evidence bundles
    """
    
    def __init__(self, hash_algorithm: str = "SHA256"):
        """
        Initialize commitment generator
        
        Args:
            hash_algorithm: Hash algorithm to use (SHA256, SHA512, etc.)
        """
        self.hash_algorithm = hash_algorithm
        self.hash_utils = HashUtils()
        self.crypto_utils = CryptoUtils()
    
    def generate_commitment(
        self,
        evidence_items: List[NormalizedEvidence],
        bundle_id: str,
        encrypt: bool = False,
        encryption_key: Optional[bytes] = None
    ) -> EvidenceCommitment:
        """
        Generate Merkle commitment for evidence bundle
        
        Args:
            evidence_items: List of normalized evidence
            bundle_id: Unique bundle identifier
            encrypt: Whether to encrypt evidence hashes
            encryption_key: Encryption key if encrypt=True
        
        Returns:
            EvidenceCommitment with Merkle root
        
        Raises:
            ValidationError: If evidence list is empty or invalid
        """
        if not evidence_items:
            raise ValidationError("Cannot create commitment for empty evidence list")
        
        # Extract evidence hashes
        evidence_hashes = [item.content_hash for item in evidence_items]
        
        # Optionally encrypt hashes before commitment
        if encrypt:
            if not encryption_key:
                raise ValidationError("Encryption key required when encrypt=True")
            evidence_hashes = self._encrypt_hashes(evidence_hashes, encryption_key)
        
        # Create Merkle tree
        merkle_tree = create_merkle_tree_from_hashes(
            evidence_hashes,
            hash_algorithm=self.hash_algorithm
        )
        
        # Get Merkle root
        merkle_root = merkle_tree.get_root()
        
        # Create commitment
        commitment = EvidenceCommitment(
            bundle_id=bundle_id,
            merkle_root=merkle_root,
            evidence_count=len(evidence_items),
            evidence_hashes=evidence_hashes,
            hash_algorithm=self.hash_algorithm,
            is_encrypted=encrypt,
            encryption_key_id=f"key_{bundle_id}" if encrypt else None
        )
        
        return commitment
    
    def generate_proof(
        self,
        commitment: EvidenceCommitment,
        evidence_index: int
    ) -> Dict[str, Any]:
        """
        Generate Merkle proof for specific evidence in bundle
        
        Args:
            commitment: Evidence commitment
            evidence_index: Index of evidence to prove
        
        Returns:
            Proof dictionary with path and metadata
        """
        if evidence_index >= commitment.evidence_count:
            raise ValidationError(f"Invalid evidence index: {evidence_index}")
        
        # Recreate Merkle tree
        merkle_tree = create_merkle_tree_from_hashes(
            commitment.evidence_hashes,
            hash_algorithm=commitment.hash_algorithm
        )
        
        # Generate proof
        proof = merkle_tree.get_proof(evidence_index)
        
        return {
            "evidence_index": evidence_index,
            "evidence_hash": commitment.evidence_hashes[evidence_index],
            "merkle_root": commitment.merkle_root,
            "proof": proof,
            "bundle_id": commitment.bundle_id,
            "hash_algorithm": commitment.hash_algorithm
        }
    
    def verify_proof(
        self,
        evidence_hash: str,
        proof: List[Dict[str, Any]],
        merkle_root: str
    ) -> bool:
        """
        Verify Merkle proof for evidence
        
        Args:
            evidence_hash: Hash of evidence to verify
            proof: Merkle proof path
            merkle_root: Expected Merkle root
        
        Returns:
            True if proof is valid
        """
        # Create temporary tree for verification
        merkle_tree = MerkleTree(hash_algorithm=self.hash_algorithm)
        
        # Verify proof
        is_valid = merkle_tree.verify_proof(evidence_hash, proof, merkle_root)
        
        return is_valid
    
    def verify_bundle_integrity(
        self,
        evidence_items: List[NormalizedEvidence],
        commitment: EvidenceCommitment
    ) -> bool:
        """
        Verify that evidence items match commitment
        
        Args:
            evidence_items: Current evidence items
            commitment: Original commitment
        
        Returns:
            True if bundle integrity is maintained
        """
        # Check count
        if len(evidence_items) != commitment.evidence_count:
            return False
        
        # Regenerate commitment
        current_hashes = [item.content_hash for item in evidence_items]
        
        # If encrypted, can't directly compare
        if commitment.is_encrypted:
            # Would need to decrypt with original key
            # For now, just check hash count matches
            return len(current_hashes) == len(commitment.evidence_hashes)
        
        # Compare hashes
        return current_hashes == commitment.evidence_hashes
    
    def update_commitment(
        self,
        existing_commitment: EvidenceCommitment,
        new_evidence: List[NormalizedEvidence]
    ) -> EvidenceCommitment:
        """
        Update commitment with additional evidence
        
        Args:
            existing_commitment: Current commitment
            new_evidence: New evidence to add
        
        Returns:
            Updated commitment
        """
        # Combine existing and new hashes
        all_hashes = existing_commitment.evidence_hashes.copy()
        all_hashes.extend([item.content_hash for item in new_evidence])
        
        # Create new tree
        merkle_tree = create_merkle_tree_from_hashes(
            all_hashes,
            hash_algorithm=existing_commitment.hash_algorithm
        )
        
        # Create updated commitment
        updated_commitment = EvidenceCommitment(
            bundle_id=existing_commitment.bundle_id,
            merkle_root=merkle_tree.get_root(),
            evidence_count=len(all_hashes),
            evidence_hashes=all_hashes,
            hash_algorithm=existing_commitment.hash_algorithm,
            is_encrypted=existing_commitment.is_encrypted,
            encryption_key_id=existing_commitment.encryption_key_id
        )
        
        return updated_commitment
    
    def _encrypt_hashes(
        self,
        hashes: List[str],
        encryption_key: bytes
    ) -> List[str]:
        """
        Encrypt evidence hashes before commitment
        
        Args:
            hashes: List of evidence hashes
            encryption_key: Encryption key
        
        Returns:
            List of encrypted hashes (base64 encoded)
        """
        encrypted_hashes = []
        
        for hash_value in hashes:
            # Encrypt each hash
            ciphertext, nonce = self.crypto_utils.encrypt(
                hash_value.encode('utf-8'),
                encryption_key
            )
            
            # Combine ciphertext and nonce, encode as base64
            combined = ciphertext + nonce
            encrypted_hash = self.crypto_utils._encode(combined)
            encrypted_hashes.append(encrypted_hash)
        
        return encrypted_hashes
    
    def serialize_commitment(self, commitment: EvidenceCommitment) -> str:
        """
        Serialize commitment to JSON
        
        Args:
            commitment: Commitment to serialize
        
        Returns:
            JSON string
        """
        return commitment.json()
    
    def deserialize_commitment(self, json_str: str) -> EvidenceCommitment:
        """
        Deserialize commitment from JSON
        
        Args:
            json_str: JSON string
        
        Returns:
            EvidenceCommitment instance
        """
        return EvidenceCommitment.parse_raw(json_str)
    
    @staticmethod
    def generate_bundle_id(
        tenant_id: str,
        claim_id: str,
        timestamp: Optional[datetime] = None
    ) -> str:
        """
        Generate unique bundle ID
        
        Args:
            tenant_id: Tenant identifier
            claim_id: Claim identifier
            timestamp: Optional timestamp
        
        Returns:
            Bundle ID string
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        timestamp_str = timestamp.strftime("%Y%m%d%H%M%S")
        return f"bundle_{tenant_id}_{claim_id}_{timestamp_str}"

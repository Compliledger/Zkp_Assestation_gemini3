"""
Mock Anchor Service
Simulates blockchain anchoring for judge mode demos
"""

from typing import Dict, Any
from datetime import datetime
import hashlib
import random


class MockAnchorService:
    """
    Mock blockchain anchoring service for fast demos
    
    Returns realistic-looking anchor data instantly
    """
    
    @staticmethod
    def anchor_attestation(
        attestation_id: str,
        merkle_root: str,
        package_hash: str
    ) -> Dict[str, Any]:
        """
        Simulate blockchain anchoring
        
        Returns instant anchor data that looks realistic
        """
        # Generate mock transaction hash
        tx_data = f"{attestation_id}{merkle_root}{package_hash}{datetime.utcnow().isoformat()}"
        tx_hash = hashlib.sha256(tx_data.encode()).hexdigest()
        
        # Generate mock block info
        block_number = random.randint(15000000, 16000000)
        
        # Mock chains
        chains = ["algorand", "ethereum", "polygon", "avalanche"]
        selected_chain = random.choice(chains)
        
        return {
            "chain": selected_chain,
            "network": "testnet",
            "transaction_hash": tx_hash,
            "block_number": block_number,
            "block_hash": hashlib.sha256(f"block_{block_number}".encode()).hexdigest(),
            "timestamp": datetime.utcnow().isoformat(),
            "confirmation_count": 12,
            "status": "confirmed",
            "explorer_url": f"https://{selected_chain}-testnet.explorer.io/tx/{tx_hash}",
            "gas_used": random.randint(21000, 50000),
            "data": {
                "attestation_id": attestation_id,
                "merkle_root": merkle_root,
                "package_hash": package_hash
            },
            "mock": True,  # Indicate this is mock data
            "message": "⚡ Mock anchoring (instant for demo)"
        }
    
    @staticmethod
    def create_mock_anchor(
        claim_id: str,
        merkle_root: str,
        package_hash: str
    ) -> Dict[str, Any]:
        """Alias for anchor_attestation (used by attestations.py)"""
        return MockAnchorService.anchor_attestation(claim_id, merkle_root, package_hash)

    @staticmethod
    def verify_anchor(transaction_hash: str) -> Dict[str, Any]:
        """
        Simulate anchor verification
        """
        return {
            "transaction_hash": transaction_hash,
            "exists": True,
            "confirmations": 12,
            "status": "confirmed",
            "verified_at": datetime.utcnow().isoformat(),
            "mock": True
        }


# Singleton instance for easy import
mock_anchor_service = MockAnchorService()

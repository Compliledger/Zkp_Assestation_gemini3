"""
In-Memory Storage for Demo Mode
No database required - perfect for hackathon demos
"""

from datetime import datetime
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class MemoryStore:
    """In-memory storage for hackathon demo - no DB required"""
    
    def __init__(self):
        self.attestations: Dict[str, dict] = {}
        self.verifications: Dict[str, dict] = {}
        self.idempotency_keys: Dict[str, dict] = {}
        logger.info("MemoryStore initialized (demo mode)")
    
    # Attestations
    def create_attestation(
        self, 
        attestation_id: str, 
        data: dict, 
        idempotency_key: Optional[str] = None
    ) -> str:
        """Create new attestation"""
        self.attestations[attestation_id] = {
            **data,
            "created_at": datetime.utcnow().isoformat()
        }
        
        if idempotency_key:
            self.idempotency_keys[idempotency_key] = {
                "attestation_id": attestation_id,
                "created_at": datetime.utcnow()
            }
        
        logger.info(f"Created attestation: {attestation_id}")
        return attestation_id
    
    def get_attestation(self, attestation_id: str) -> Optional[dict]:
        """Get attestation by ID"""
        return self.attestations.get(attestation_id)
    
    def update_attestation(self, attestation_id: str, data: dict):
        """Update attestation data"""
        if attestation_id in self.attestations:
            self.attestations[attestation_id].update(data)
            logger.debug(f"Updated attestation: {attestation_id}")
    
    def list_attestations(self, limit: int = 100, offset: int = 0) -> List[dict]:
        """List attestations with pagination"""
        items = list(self.attestations.values())
        return items[offset:offset + limit]
    
    def count_attestations(self) -> int:
        """Count total attestations"""
        return len(self.attestations)
    
    # Idempotency
    def get_by_idempotency_key(self, key: str) -> Optional[str]:
        """Get attestation ID by idempotency key"""
        if key in self.idempotency_keys:
            return self.idempotency_keys[key]["attestation_id"]
        return None
    
    def has_idempotency_key(self, key: str) -> bool:
        """Check if idempotency key exists"""
        return key in self.idempotency_keys
    
    # Verifications
    def create_verification(self, verification_id: str, data: dict) -> str:
        """Create verification receipt"""
        self.verifications[verification_id] = {
            **data,
            "created_at": datetime.utcnow().isoformat()
        }
        logger.info(f"Created verification receipt: {verification_id}")
        return verification_id
    
    def get_verification(self, verification_id: str) -> Optional[dict]:
        """Get verification receipt by ID"""
        return self.verifications.get(verification_id)
    
    def list_verifications(self, limit: int = 100) -> List[dict]:
        """List verification receipts"""
        return list(self.verifications.values())[:limit]
    
    # Utility
    def clear_all(self):
        """Clear all data (for testing)"""
        self.attestations.clear()
        self.verifications.clear()
        self.idempotency_keys.clear()
        logger.warning("MemoryStore cleared")
    
    def get_stats(self) -> dict:
        """Get storage statistics"""
        return {
            "attestations_count": len(self.attestations),
            "verifications_count": len(self.verifications),
            "idempotency_keys_count": len(self.idempotency_keys)
        }


# Global instance
memory_store = MemoryStore()

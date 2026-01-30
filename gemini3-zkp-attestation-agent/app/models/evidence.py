"""
Evidence Models
Evidence bundles and items with Merkle commitments
"""

from sqlalchemy import Column, String, Integer, BigInteger, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.models.base import BaseModel, TimestampMixin


class EvidenceBundle(BaseModel, TimestampMixin):
    """
    Evidence bundles with Merkle commitments
    """
    __tablename__ = "evidence_bundles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bundle_id = Column(String(100), unique=True, nullable=False, index=True)
    claim_id = Column(String(100), ForeignKey('claims.claim_id', ondelete='CASCADE'), nullable=False, index=True)
    merkle_root = Column(String(128), nullable=False, index=True)
    merkle_tree_json = Column(JSONB)
    storage_uri = Column(String, nullable=False)
    encryption_key_ref = Column(String(255), nullable=False)
    encryption_algorithm = Column(String(50), default='AES-256-GCM')
    evidence_count = Column(Integer, nullable=False, default=0)
    total_size_bytes = Column(BigInteger)
    hash_algorithm = Column(String(50), default='SHA256')
    meta_data = Column(JSONB)
    
    # Relationships
    claim = relationship("Claim", back_populates="evidence_bundles")
    evidence_items = relationship("EvidenceItem", back_populates="bundle", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint('evidence_count >= 0', name='positive_evidence_count'),
    )
    
    def __repr__(self):
        return f"<EvidenceBundle(bundle_id='{self.bundle_id}', count={self.evidence_count})>"


class EvidenceItem(BaseModel, TimestampMixin):
    """
    Individual evidence artifacts within bundles
    """
    __tablename__ = "evidence_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bundle_id = Column(String(100), ForeignKey('evidence_bundles.bundle_id', ondelete='CASCADE'), nullable=False, index=True)
    item_hash = Column(String(128), nullable=False, index=True)
    item_type = Column(String(50))
    source_agent = Column(String(100))
    source_uri = Column(String)
    size_bytes = Column(BigInteger)
    meta_data = Column(JSONB)
    
    # Relationships
    bundle = relationship("EvidenceBundle", back_populates="evidence_items")
    
    def __repr__(self):
        return f"<EvidenceItem(hash='{self.item_hash[:16]}...', type='{self.item_type}')>"

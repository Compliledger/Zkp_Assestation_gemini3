"""
Anchoring Models
Blockchain anchoring and IPFS storage records
"""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.models.base import BaseModel, TimestampMixin


class AnchorRecord(BaseModel, TimestampMixin):
    """
    Blockchain anchor records
    """
    __tablename__ = "anchor_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    anchor_id = Column(String(100), unique=True, nullable=False, index=True)
    package_id = Column(String(100), ForeignKey('attestation_packages.package_id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Blockchain details
    blockchain = Column(String(50), nullable=False)
    transaction_hash = Column(String(256), nullable=False, index=True)
    block_number = Column(Integer)
    block_hash = Column(String(256))
    contract_address = Column(String(256))
    
    # Content
    package_hash = Column(String(64), nullable=False)
    merkle_root = Column(String(64))
    
    # Status
    status = Column(String(50), default='pending')
    confirmations = Column(Integer, default=0)
    
    # Metadata
    anchored_by = Column(String(100), nullable=False)
    anchored_at = Column(DateTime, nullable=False)
    confirmed_at = Column(DateTime)
    
    # Transaction details
    gas_used = Column(Integer)
    transaction_fee = Column(String(100))
    
    # Additional data
    meta_data = Column(JSONB)
    
    # Relationships
    package = relationship("AttestationPackage", back_populates="anchor_records")
    
    def __repr__(self):
        return f"<AnchorRecord(anchor_id='{self.anchor_id}', blockchain='{self.blockchain}')>"


class IPFSRecord(BaseModel, TimestampMixin):
    """
    IPFS storage records
    """
    __tablename__ = "ipfs_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cid = Column(String(100), unique=True, nullable=False, index=True)
    package_id = Column(String(100), ForeignKey('attestation_packages.package_id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Content details
    content_type = Column(String(100), nullable=False)
    size = Column(Integer, nullable=False)
    content_hash = Column(String(64), nullable=False)
    
    # IPFS details
    ipfs_gateway = Column(String(256), nullable=False)
    pinned = Column(Boolean, default=False)
    pin_service = Column(String(100))
    
    # Metadata
    uploaded_by = Column(String(100), nullable=False)
    uploaded_at = Column(DateTime, nullable=False)
    
    # Additional data
    meta_data = Column(JSONB)
    
    # Relationships
    package = relationship("AttestationPackage", back_populates="ipfs_records")
    
    def __repr__(self):
        return f"<IPFSRecord(cid='{self.cid}', package_id='{self.package_id}')>"

"""
Attestation Package Model
Final attestation outputs in multiple formats
"""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.models.base import BaseModel, TimestampMixin


class AttestationPackage(BaseModel, TimestampMixin):
    """
    Final attestation outputs in multiple formats
    """
    __tablename__ = "attestation_packages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    package_id = Column(String(100), unique=True, nullable=False, index=True)
    claim_id = Column(String(100), ForeignKey('claims.claim_id', ondelete='CASCADE'), nullable=False, index=True)
    tenant_id = Column(String(100), nullable=False, index=True)
    
    # Package information
    title = Column(String(255), nullable=False)
    description = Column(String)
    status = Column(String(50), default='draft')
    attestation_type = Column(String(100))
    compliance_framework = Column(String(100))
    
    # Package data and metadata
    package_data = Column(JSONB)
    package_hash = Column(String(64))
    
    # Legacy fields
    attestation_statement = Column(String)
    package_format = Column(String(50), default='JSON')
    package_uri = Column(String)
    oscal_json = Column(JSONB)
    human_readable_uri = Column(String)
    pdf_uri = Column(String)
    
    # Signature fields
    signature = Column(String(512))
    signature_algorithm = Column(String(50))
    signed_by = Column(String(255))
    signed_at = Column(DateTime)
    
    # Version and timestamps
    version = Column(Integer, default=1)
    assembled_at = Column(DateTime)
    published_at = Column(DateTime)
    
    # Relationships
    claim = relationship("Claim", back_populates="attestation_packages")
    anchor_records = relationship("AnchorRecord", back_populates="package", cascade="all, delete-orphan")
    ipfs_records = relationship("IPFSRecord", back_populates="package", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AttestationPackage(package_id='{self.package_id}', status='{self.status}')>"

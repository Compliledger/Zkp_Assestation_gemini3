"""
Proof Models
ZKP proof artifacts and circuit templates
"""

from sqlalchemy import Column, String, BigInteger, ForeignKey, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.models.base import BaseModel, TimestampMixin


class ProofArtifact(BaseModel, TimestampMixin):
    """
    Generated zero-knowledge proofs with metadata
    """
    __tablename__ = "proof_artifacts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proof_id = Column(String(100), unique=True, nullable=False, index=True)
    claim_id = Column(String(100), ForeignKey('claims.claim_id', ondelete='CASCADE'), nullable=False, index=True)
    proof_blob_uri = Column(String, nullable=False)
    proof_hash = Column(String(128), nullable=False, index=True)
    proof_size_bytes = Column(BigInteger)
    circuit_id = Column(String(100), nullable=False, index=True)
    circuit_version = Column(String(50), nullable=False)
    verification_key_id = Column(String(100), nullable=False)
    public_inputs = Column(JSONB)
    generation_time_seconds = Column(Numeric(10, 3))
    prover_version = Column(String(50))
    meta_data = Column(JSONB)
    
    # Relationships
    claim = relationship("Claim", back_populates="proof_artifacts")
    
    def __repr__(self):
        return f"<ProofArtifact(proof_id='{self.proof_id}', circuit='{self.circuit_id}')>"


class CircuitTemplate(BaseModel, TimestampMixin):
    """
    ZKP circuit definitions and templates
    """
    __tablename__ = "circuit_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    circuit_id = Column(String(100), nullable=False, index=True)
    circuit_name = Column(String(255), nullable=False)
    circuit_version = Column(String(50), nullable=False)
    claim_type = Column(String(50), nullable=False, index=True)
    circuit_file_uri = Column(String)
    verification_key_uri = Column(String)
    description = Column(String)
    parameters = Column(JSONB)
    is_active = Column(Boolean, default=True, index=True)
    
    __table_args__ = (
        {'schema': None},
    )
    
    def __repr__(self):
        return f"<CircuitTemplate(circuit_id='{self.circuit_id}', version='{self.circuit_version}')>"

"""
Claim Model
Core attestation claims with lifecycle status
"""

from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from app.models.base import BaseModel, TimestampMixin


class ClaimType(str, enum.Enum):
    """Claim types"""
    EVIDENCE_INTEGRITY = "evidence_integrity"
    CONTROL_EFFECTIVENESS = "control_effectiveness"
    THRESHOLD = "threshold"
    CONTINUOUS_VALIDITY = "continuous_validity"


class ClaimStatus(str, enum.Enum):
    """Claim status values"""
    PENDING = "pending"
    GENERATING = "generating"
    GENERATED = "generated"
    ANCHORING = "anchoring"
    ANCHORED = "anchored"
    VALID = "valid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    FAILED = "failed"


class Claim(BaseModel, TimestampMixin):
    """
    Core attestation claims table
    """
    __tablename__ = "claims"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(String(100), unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    system_id = Column(String(100), nullable=False, index=True)
    framework = Column(String(50))
    control_id = Column(String(50))
    claim_type = Column(SQLEnum(ClaimType), nullable=False)
    status = Column(SQLEnum(ClaimStatus), nullable=False, default=ClaimStatus.PENDING, index=True)
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime, nullable=False)
    
    # Relationships
    evidence_bundles = relationship("EvidenceBundle", back_populates="claim", cascade="all, delete-orphan")
    proof_artifacts = relationship("ProofArtifact", back_populates="claim", cascade="all, delete-orphan")
    anchors = relationship("Anchor", back_populates="claim", cascade="all, delete-orphan")
    verification_receipts = relationship("VerificationReceipt", back_populates="claim", cascade="all, delete-orphan")
    lifecycle_events = relationship("LifecycleEvent", back_populates="claim", cascade="all, delete-orphan")
    attestation_packages = relationship("AttestationPackage", back_populates="claim", cascade="all, delete-orphan")
    revocations = relationship("Revocation", back_populates="claim", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint('valid_to > valid_from', name='valid_time_range'),
    )
    
    def __repr__(self):
        return f"<Claim(claim_id='{self.claim_id}', type='{self.claim_type}', status='{self.status}')>"

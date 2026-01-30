"""
Revocation Model
Revoked attestations with audit trail
"""

from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from app.models.base import BaseModel, TimestampMixin


class RevocationType(str, enum.Enum):
    """Revocation types"""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    POLICY_VIOLATION = "policy_violation"
    EVIDENCE_COMPROMISED = "evidence_compromised"
    EXPIRED = "expired"


class Revocation(BaseModel, TimestampMixin):
    """
    Revoked attestations with reasons and audit trail
    """
    __tablename__ = "revocations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    revocation_id = Column(String(100), unique=True, nullable=False, index=True)
    claim_id = Column(String(100), ForeignKey('claims.claim_id', ondelete='CASCADE'), nullable=False, index=True)
    reason = Column(String, nullable=False)
    revoked_by = Column(String(255), nullable=False)
    revoked_by_role = Column(String(100))
    revocation_type = Column(SQLEnum(RevocationType))
    effective_at = Column(DateTime, nullable=False, index=True)
    meta_data = Column(JSONB)
    
    # Relationships
    claim = relationship("Claim", back_populates="revocations")
    
    def __repr__(self):
        return f"<Revocation(revocation_id='{self.revocation_id}', type='{self.revocation_type}')>"

"""
Verification Model
Proof verification records and receipts
"""

from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from app.models.base import BaseModel


class VerificationResult(str, enum.Enum):
    """Verification result values"""
    VALID = "valid"
    INVALID = "invalid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ERROR = "error"


class VerificationReceipt(BaseModel):
    """
    Proof verification audit trail
    """
    __tablename__ = "verification_receipts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_id = Column(String(100), unique=True, nullable=False, index=True)
    claim_id = Column(String(100), ForeignKey('claims.claim_id', ondelete='CASCADE'), nullable=False, index=True)
    verifier_id = Column(String(100), nullable=False)
    verifier_type = Column(String(50))
    result = Column(SQLEnum(VerificationResult), nullable=False, index=True)
    checks_passed = Column(JSONB)
    details = Column(JSONB)
    verification_time_seconds = Column(Numeric(10, 3))
    verified_at = Column(DateTime, nullable=False, index=True)
    
    # Relationships
    claim = relationship("Claim", back_populates="verification_receipts")
    
    def __repr__(self):
        return f"<VerificationReceipt(receipt_id='{self.receipt_id}', result='{self.result}')>"

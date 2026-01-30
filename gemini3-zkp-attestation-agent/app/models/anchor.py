"""
Anchor Model
Blockchain anchoring records
"""

from sqlalchemy import Column, String, Integer, BigInteger, ForeignKey, Enum as SQLEnum, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from app.models.base import BaseModel, TimestampMixin


class AnchorStatus(str, enum.Enum):
    """Anchor status values"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class Anchor(BaseModel, TimestampMixin):
    """
    Blockchain anchoring records for immutable proof commitments
    """
    __tablename__ = "anchors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    anchor_id = Column(String(100), unique=True, nullable=False, index=True)
    claim_id = Column(String(100), ForeignKey('claims.claim_id', ondelete='CASCADE'), nullable=False, index=True)
    chain = Column(String(50), nullable=False, index=True)
    network = Column(String(50))
    transaction_id = Column(String(255), index=True)
    block_height = Column(BigInteger)
    block_hash = Column(String(128))
    commitment_hash = Column(String(128), nullable=False)
    status = Column(SQLEnum(AnchorStatus), nullable=False, default=AnchorStatus.PENDING, index=True)
    confirmation_count = Column(Integer, default=0)
    gas_used = Column(BigInteger)
    transaction_fee = Column(Numeric(20, 8))
    anchored_at = Column(DateTime)
    confirmed_at = Column(DateTime)
    meta_data = Column(JSONB)
    
    # Relationships
    claim = relationship("Claim", back_populates="anchors")
    
    def __repr__(self):
        return f"<Anchor(anchor_id='{self.anchor_id}', chain='{self.chain}', status='{self.status}')>"

"""
Lifecycle Event Model
Attestation state transitions and audit log
"""

from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from app.models.base import BaseModel, TimestampMixin


class EventType(str, enum.Enum):
    """Lifecycle event types"""
    CREATED = "created"
    EVIDENCE_COMMITTED = "evidence_committed"
    PROOF_GENERATED = "proof_generated"
    ANCHOR_SUBMITTED = "anchor_submitted"
    ANCHOR_CONFIRMED = "anchor_confirmed"
    VERIFIED = "verified"
    EXPIRED = "expired"
    REVOKED = "revoked"
    RENEWED = "renewed"
    FAILED = "failed"


class LifecycleEvent(BaseModel, TimestampMixin):
    """
    Immutable audit log of all attestation state changes
    """
    __tablename__ = "lifecycle_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(String(100), unique=True, nullable=False, index=True)
    claim_id = Column(String(100), ForeignKey('claims.claim_id', ondelete='CASCADE'), nullable=False, index=True)
    event_type = Column(SQLEnum(EventType), nullable=False, index=True)
    from_status = Column(String(50))
    to_status = Column(String(50))
    triggered_by = Column(String(255))
    trigger_source = Column(String(100))
    reason = Column(String)
    meta_data = Column(JSONB)
    
    # Relationships
    claim = relationship("Claim", back_populates="lifecycle_events")
    
    def __repr__(self):
        return f"<LifecycleEvent(event_id='{self.event_id}', type='{self.event_type}')>"

"""
Tenant and API Key Models
Multi-tenant support and authentication
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.models.base import BaseModel, TimestampMixin


class Tenant(BaseModel, TimestampMixin):
    """
    Multi-tenant support
    """
    __tablename__ = "tenants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True, default=uuid.uuid4)
    tenant_name = Column(String(255), nullable=False)
    tenant_type = Column(String(50))
    status = Column(String(50), default='active', index=True)
    settings = Column(JSONB)
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="tenant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tenant(tenant_id='{self.tenant_id}', name='{self.tenant_name}')>"


class APIKey(BaseModel, TimestampMixin):
    """
    API authentication tokens
    """
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_id = Column(String(100), unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.tenant_id', ondelete='CASCADE'), nullable=False, index=True)
    key_hash = Column(String(255), nullable=False)
    key_name = Column(String(255))
    permissions = Column(JSONB)
    rate_limit_per_minute = Column(Integer, default=60)
    last_used_at = Column(DateTime)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True, index=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="api_keys")
    
    def __repr__(self):
        return f"<APIKey(key_id='{self.key_id}', tenant_id='{self.tenant_id}')>"

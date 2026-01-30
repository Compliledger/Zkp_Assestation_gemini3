"""
Response Schemas
Pydantic models for API responses
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ClaimStatus(str, Enum):
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


class AttestationResponse(BaseModel):
    """Response after attestation generation request"""
    claim_id: str
    proof_id: Optional[str] = None
    status: ClaimStatus
    attestation_uri: str
    anchor_status: str
    estimated_completion: Optional[datetime] = None
    created_at: datetime
    valid_from: datetime
    valid_to: datetime


class EvidenceBundleResponse(BaseModel):
    """Evidence bundle information"""
    bundle_id: str
    merkle_root: str
    evidence_count: int
    total_size_bytes: int
    hash_algorithm: str


class ProofResponse(BaseModel):
    """Proof artifact information"""
    proof_id: str
    circuit_id: str
    circuit_version: str
    proof_hash: str
    verification_key_id: str
    public_inputs: Dict[str, Any]
    generation_time_seconds: float


class AnchorResponse(BaseModel):
    """Blockchain anchor information"""
    anchor_id: str
    chain: str
    network: Optional[str] = None
    transaction_id: Optional[str] = None
    block_height: Optional[int] = None
    block_hash: Optional[str] = None
    status: str
    confirmation_count: int = 0
    anchored_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None


class AttestationDetailResponse(BaseModel):
    """Complete attestation details"""
    claim_id: str
    system_id: str
    tenant_id: str
    claim_type: str
    framework: Optional[str] = None
    control_id: Optional[str] = None
    status: ClaimStatus
    evidence_bundle: Optional[EvidenceBundleResponse] = None
    proof: Optional[ProofResponse] = None
    anchor: Optional[AnchorResponse] = None
    attestation_statement: str
    valid_from: datetime
    valid_to: datetime
    created_at: datetime
    updated_at: datetime
    verification_count: int = 0
    last_verified_at: Optional[datetime] = None


class AttestationSummary(BaseModel):
    """Abbreviated attestation info for lists"""
    claim_id: str
    system_id: str
    claim_type: str
    control_id: Optional[str] = None
    status: ClaimStatus
    valid_from: datetime
    valid_to: datetime
    created_at: datetime
    attestation_uri: str


class PaginationResponse(BaseModel):
    """Pagination metadata"""
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool


class AttestationListResponse(BaseModel):
    """List of attestations with pagination"""
    items: List[AttestationSummary]
    pagination: PaginationResponse


class VerificationResult(str, Enum):
    """Verification result values"""
    VALID = "valid"
    INVALID = "invalid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ERROR = "error"


class VerificationResponse(BaseModel):
    """Verification result"""
    receipt_id: str
    claim_id: str
    result: VerificationResult
    verified_at: datetime
    verifier_id: str
    verifier_type: str = "internal"
    verification_time_seconds: float
    checks_passed: List[str]
    details: Dict[str, Any]


class BatchVerificationResult(BaseModel):
    """Single result in batch verification"""
    claim_id: str
    result: VerificationResult
    receipt_id: str


class BatchVerificationSummary(BaseModel):
    """Summary of batch verification"""
    valid: int = 0
    invalid: int = 0
    expired: int = 0
    revoked: int = 0
    error: int = 0


class BatchVerificationResponse(BaseModel):
    """Batch verification results"""
    batch_id: str
    total: int
    results: List[BatchVerificationResult]
    summary: BatchVerificationSummary


class RevocationResponse(BaseModel):
    """Response after revoking attestation"""
    claim_id: str
    revocation_id: str
    status: ClaimStatus
    revoked_at: datetime
    revoked_by: str
    reason: str
    revocation_type: str
    affected_verifications: int = 0


class LifecycleEvent(BaseModel):
    """Single lifecycle event"""
    event_id: str
    event_type: str
    from_status: Optional[str] = None
    to_status: str
    triggered_by: Optional[str] = None
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


class LifecycleHistoryResponse(BaseModel):
    """Complete lifecycle history"""
    claim_id: str
    events: List[LifecycleEvent]


class VerificationHistoryItem(BaseModel):
    """Single verification in history"""
    receipt_id: str
    result: VerificationResult
    verifier_id: str
    verifier_type: str
    verified_at: datetime


class VerificationHistoryResponse(BaseModel):
    """Verification history for an attestation"""
    claim_id: str
    total_verifications: int
    valid_count: int
    invalid_count: int
    expired_count: int
    revoked_count: int
    verifications: List[VerificationHistoryItem]


class HealthComponent(BaseModel):
    """Health status of a component"""
    status: str
    message: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    environment: Optional[str] = None
    components: Dict[str, str]
    timestamp: str


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    message: str
    field: Optional[str] = None
    request_id: Optional[str] = None

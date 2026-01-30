"""
Request Schemas
Pydantic models for API requests
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ClaimType(str, Enum):
    """Supported claim types"""
    EVIDENCE_INTEGRITY = "evidence_integrity"
    CONTROL_EFFECTIVENESS = "control_effectiveness"
    THRESHOLD = "threshold"
    CONTINUOUS_VALIDITY = "continuous_validity"


class AnchoringPolicy(str, Enum):
    """Anchoring policies"""
    IMMEDIATE = "immediate"
    BATCHED = "batched"
    NONE = "none"


class EvidenceRef(BaseModel):
    """Reference to evidence artifact"""
    type: str = Field(..., description="Evidence type (log, scan_result, policy_document, code_artifact)")
    source: str = Field(..., description="Source agent (github_sentinel, cma, vca, pea, cea)")
    uri: str = Field(..., description="Evidence URI (evidence://bundle_id/artifact_id)")
    hash: str = Field(..., description="Evidence hash (sha256:...)")
    timestamp: datetime = Field(..., description="Evidence collection timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class AttestationRequest(BaseModel):
    """Request to generate an attestation"""
    system_id: str = Field(..., description="System identifier from RMF Engine")
    claim_type: ClaimType = Field(..., description="Type of claim to prove")
    framework: Optional[str] = Field(None, description="Compliance framework (NIST_800_53, FedRAMP, SOC2, ISO27001)")
    control_id: Optional[str] = Field(None, description="Control identifier (required for control_effectiveness)")
    evidence_refs: List[EvidenceRef] = Field(..., min_items=1, description="References to evidence sources")
    policy_logic_id: Optional[str] = Field(None, description="Policy evaluation logic identifier")
    valid_from: datetime = Field(..., description="Validity start timestamp")
    valid_to: datetime = Field(..., description="Validity end timestamp")
    anchoring_policy: AnchoringPolicy = Field(default=AnchoringPolicy.IMMEDIATE, description="Anchoring policy")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional context metadata")
    
    @validator('valid_to')
    def valid_to_after_valid_from(cls, v, values):
        if 'valid_from' in values and v <= values['valid_from']:
            raise ValueError('valid_to must be after valid_from')
        return v
    
    @validator('control_id', always=True)
    def control_id_required_for_control_effectiveness(cls, v, values):
        if values.get('claim_type') == ClaimType.CONTROL_EFFECTIVENESS and not v:
            raise ValueError('control_id is required for control_effectiveness claim type')
        return v


class ProofPackage(BaseModel):
    """Full proof package for independent verification"""
    proof: str = Field(..., description="Base64 encoded proof")
    public_inputs: Dict[str, Any] = Field(..., description="Public inputs to the circuit")
    verification_key: str = Field(..., description="Base64 encoded verification key")


class VerificationRequest(BaseModel):
    """Request to verify an attestation"""
    claim_id: Optional[str] = Field(None, description="Claim identifier")
    proof_package: Optional[ProofPackage] = Field(None, description="Full proof package for independent verification")
    check_anchor: bool = Field(default=True, description="Verify blockchain anchor")
    check_expiry: bool = Field(default=True, description="Check validity window")
    check_revocation: bool = Field(default=True, description="Check revocation status")
    
    @validator('proof_package', always=True)
    def claim_id_or_proof_package_required(cls, v, values):
        if not values.get('claim_id') and not v:
            raise ValueError('Either claim_id or proof_package must be provided')
        return v


class BatchVerificationRequest(BaseModel):
    """Request to verify multiple attestations"""
    claim_ids: List[str] = Field(..., min_items=1, max_items=100, description="List of claim IDs to verify")
    check_anchor: bool = Field(default=True, description="Verify blockchain anchors")
    check_expiry: bool = Field(default=True, description="Check validity windows")
    check_revocation: bool = Field(default=True, description="Check revocation status")


class RevocationType(str, Enum):
    """Revocation types"""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    POLICY_VIOLATION = "policy_violation"
    EVIDENCE_COMPROMISED = "evidence_compromised"
    EXPIRED = "expired"


class RevocationRequest(BaseModel):
    """Request to revoke an attestation"""
    reason: str = Field(..., min_length=10, description="Human-readable revocation reason")
    revoked_by: str = Field(..., description="Email/ID of person revoking")
    revocation_type: Optional[RevocationType] = Field(default=RevocationType.MANUAL, description="Type of revocation")
    effective_at: Optional[datetime] = Field(default=None, description="When revocation takes effect (default: now)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

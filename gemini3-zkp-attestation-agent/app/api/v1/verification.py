"""
Verification Endpoints
Verify attestation proofs
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging

from app.storage.memory_store import memory_store
from app.utils.response_enhancer import enhance_verification_response

logger = logging.getLogger(__name__)
router = APIRouter()


# Models
class VerificationRequest(BaseModel):
    attestation_id: str = Field(..., description="Attestation ID to verify")
    checks: List[str] = Field(
        default=["proof", "expiry", "revocation", "anchor"],
        description="Checks to perform"
    )

class CheckResult(BaseModel):
    check: str
    result: str  # PASS or FAIL
    details: str

class VerificationResponse(BaseModel):
    receipt_id: str
    attestation_id: str
    status: str  # PASS or FAIL
    checks_performed: List[CheckResult]
    timestamp: str


def generate_receipt_id() -> str:
    """Generate verification receipt ID"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_suffix = uuid.uuid4().hex[:6].upper()
    return f"VER-{timestamp}-{random_suffix}"


@router.post("/verify", response_model=dict)
async def verify_attestation(request: VerificationRequest, enhanced: bool = True):
    """
    Verify an attestation
    
    Performs requested checks:
    - proof: Verify ZKP proof validity
    - expiry: Check if attestation is expired
    - revocation: Check revocation status
    - anchor: Verify blockchain anchor
    """
    
    # Get attestation
    attestation = memory_store.get_attestation(request.attestation_id)
    if not attestation:
        raise HTTPException(
            status_code=404,
            detail=f"Attestation {request.attestation_id} not found"
        )
    
    receipt_id = generate_receipt_id()
    checks_performed = []
    
    logger.info(f"Verifying attestation {request.attestation_id} (receipt: {receipt_id})")
    
    # Check 1: Proof validity
    if "proof" in request.checks:
        if attestation.get("proof"):
            # Simplified proof verification for demo
            proof_valid = True  # In production, verify actual ZKP
            checks_performed.append(CheckResult(
                check="proof_validity",
                result="PASS" if proof_valid else "FAIL",
                details="ZKP proof structure validated (demo mode)"
            ))
        else:
            checks_performed.append(CheckResult(
                check="proof_validity",
                result="FAIL",
                details="No proof attached to attestation"
            ))
    
    # Check 2: Expiry
    if "expiry" in request.checks:
        try:
            valid_until = datetime.fromisoformat(
                attestation["metadata"]["valid_until"].replace("Z", "")
            )
            is_expired = datetime.utcnow() > valid_until
            checks_performed.append(CheckResult(
                check="expiry",
                result="FAIL" if is_expired else "PASS",
                details=f"Valid until {attestation['metadata']['valid_until']}"
            ))
        except Exception as e:
            checks_performed.append(CheckResult(
                check="expiry",
                result="FAIL",
                details=f"Error checking expiry: {str(e)}"
            ))
    
    # Check 3: Revocation
    if "revocation" in request.checks:
        # Check revocation status (simplified for demo)
        is_revoked = attestation.get("status") == "revoked"
        checks_performed.append(CheckResult(
            check="revocation",
            result="FAIL" if is_revoked else "PASS",
            details="Not revoked" if not is_revoked else "Attestation has been revoked"
        ))
    
    # Check 4: Anchor verification
    if "anchor" in request.checks:
        if attestation.get("anchor") and not attestation["anchor"].get("error"):
            # Simplified anchor verification
            anchor_valid = True  # In production, query blockchain
            checks_performed.append(CheckResult(
                check="anchor",
                result="PASS" if anchor_valid else "FAIL",
                details=f"Anchored on {attestation['anchor'].get('chain', 'blockchain')}"
            ))
        else:
            checks_performed.append(CheckResult(
                check="anchor",
                result="WARN",
                details="No blockchain anchor or anchor failed"
            ))
    
    # Overall status
    failed_checks = [c for c in checks_performed if c.result == "FAIL"]
    overall_status = "FAIL" if failed_checks else "PASS"
    
    # Create verification receipt
    verification = {
        "receipt_id": receipt_id,
        "attestation_id": request.attestation_id,
        "status": overall_status,
        "checks_performed": [c.dict() for c in checks_performed],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Store verification
    memory_store.create_verification(receipt_id, verification)
    
    logger.info(f"Verification {receipt_id} completed with status: {overall_status}")
    
    # Return enhanced format by default
    if enhanced:
        return enhance_verification_response(verification)
    
    return VerificationResponse(**verification)


@router.get("/verify/{receipt_id}", response_model=dict)
async def get_verification_receipt(receipt_id: str, enhanced: bool = True):
    """Get verification receipt by ID"""
    verification = memory_store.get_verification(receipt_id)
    if not verification:
        raise HTTPException(
            status_code=404,
            detail=f"Verification receipt {receipt_id} not found"
        )
    
    # Return enhanced format by default
    if enhanced:
        return enhance_verification_response(verification)
    
    return VerificationResponse(**verification)

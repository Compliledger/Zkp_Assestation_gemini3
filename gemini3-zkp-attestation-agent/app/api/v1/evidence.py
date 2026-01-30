"""
Evidence API Endpoints
Handles evidence submission, retrieval, and verification
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.dependencies import get_current_user, require_generate_permission
from app.services.evidence_service import EvidenceService
from app.core.auth import TokenPayload
from app.utils.errors import NotFoundError, ValidationError, AuthorizationError
from pydantic import BaseModel, Field


router = APIRouter(prefix="/evidence", tags=["Evidence"])


# Request/Response Models
class EvidenceItemRequest(BaseModel):
    """Single evidence item submission"""
    content: str = Field(..., description="Evidence content (JSON string or base64)")
    type: str = Field(..., description="Evidence type")
    source: str = Field(..., description="Source system")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class EvidenceSubmissionRequest(BaseModel):
    """Evidence bundle submission"""
    claim_id: str = Field(..., description="Claim ID to attach evidence to")
    evidence: List[EvidenceItemRequest] = Field(..., description="List of evidence items")
    encrypt: bool = Field(default=True, description="Whether to encrypt evidence")


class EvidenceSubmissionResponse(BaseModel):
    """Evidence submission response"""
    bundle_id: str
    claim_id: str
    evidence_count: int
    merkle_root: str
    encrypted: bool
    items: List[dict]
    created_at: str


class EvidenceProofRequest(BaseModel):
    """Merkle proof request"""
    bundle_id: str = Field(..., description="Evidence bundle ID")
    evidence_id: str = Field(..., description="Evidence item ID")


class EvidenceProofResponse(BaseModel):
    """Merkle proof response"""
    evidence_index: int
    evidence_hash: str
    merkle_root: str
    proof: List[dict]
    bundle_id: str
    hash_algorithm: str


class EvidenceVerificationRequest(BaseModel):
    """Evidence verification request"""
    evidence_hash: str = Field(..., description="Evidence hash to verify")
    proof: List[dict] = Field(..., description="Merkle proof")
    merkle_root: str = Field(..., description="Expected Merkle root")


class EvidenceVerificationResponse(BaseModel):
    """Evidence verification response"""
    valid: bool
    evidence_hash: str
    merkle_root: str
    verified_at: str


@router.post(
    "/submit",
    response_model=EvidenceSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Evidence",
    description="Submit evidence items for a claim with Merkle commitment"
)
async def submit_evidence(
    request: EvidenceSubmissionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_generate_permission)
):
    """
    Submit and process evidence for a claim
    
    - Normalizes evidence from various sources
    - Generates Merkle tree commitment
    - Encrypts and stores evidence
    - Returns bundle information with Merkle root
    """
    try:
        service = EvidenceService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        # Convert request to dict format
        raw_evidence = [
            {
                "content": item.content,
                "type": item.type,
                "source": item.source,
                "metadata": item.metadata
            }
            for item in request.evidence
        ]
        
        result = await service.submit_evidence(
            claim_id=request.claim_id,
            raw_evidence=raw_evidence,
            encrypt=request.encrypt
        )
        
        return result
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.get(
    "/{bundle_id}",
    summary="Get Evidence Bundle",
    description="Retrieve evidence bundle information"
)
async def get_evidence_bundle(
    bundle_id: str,
    include_content: bool = Query(False, description="Include evidence content"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Get evidence bundle by ID
    
    - Returns bundle metadata and Merkle root
    - Optionally includes evidence content
    - Verifies tenant access
    """
    try:
        service = EvidenceService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.get_evidence_bundle(
            bundle_id=bundle_id,
            include_content=include_content
        )
        
        return result
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.get(
    "/",
    summary="List Evidence Bundles",
    description="List evidence bundles for tenant"
)
async def list_evidence_bundles(
    claim_id: Optional[str] = Query(None, description="Filter by claim ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    List evidence bundles
    
    - Filter by claim ID (optional)
    - Paginated results
    - Tenant-scoped
    """
    try:
        service = EvidenceService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.list_evidence_bundles(
            claim_id=claim_id,
            limit=limit,
            offset=offset
        )
        
        return result
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.post(
    "/proof",
    response_model=EvidenceProofResponse,
    summary="Generate Evidence Proof",
    description="Generate Merkle proof for specific evidence"
)
async def generate_evidence_proof(
    request: EvidenceProofRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Generate Merkle proof for evidence
    
    - Proves evidence is part of bundle
    - Returns Merkle path
    - Can be verified independently
    """
    try:
        service = EvidenceService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.generate_evidence_proof(
            bundle_id=request.bundle_id,
            evidence_id=request.evidence_id
        )
        
        return result
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.post(
    "/verify",
    response_model=EvidenceVerificationResponse,
    summary="Verify Evidence Proof",
    description="Verify Merkle proof for evidence"
)
async def verify_evidence_proof(
    request: EvidenceVerificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Verify evidence Merkle proof
    
    - Validates proof against Merkle root
    - Independent verification
    - No database access needed
    """
    try:
        service = EvidenceService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.verify_evidence_proof(
            evidence_hash=request.evidence_hash,
            proof=request.proof,
            merkle_root=request.merkle_root
        )
        
        return result
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

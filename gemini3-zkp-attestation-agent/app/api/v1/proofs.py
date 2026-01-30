"""
Proof API Endpoints
Handles ZKP proof generation, verification, and management
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.api.dependencies import get_current_user, require_generate_permission, require_verify_permission
from app.services.proof_service import ProofService
from app.core.auth import TokenPayload
from app.utils.errors import NotFoundError, ValidationError, ProofGenerationError, VerificationError


router = APIRouter(prefix="/proofs", tags=["Proofs"])


# Request/Response Models
class ProofGenerationRequest(BaseModel):
    """Proof generation request"""
    claim_id: str = Field(..., description="Claim ID to generate proof for")
    circuit_type: str = Field(..., description="Type of circuit (merkle_proof, compliance_proof, range_proof)")
    witness_inputs: dict = Field(..., description="Witness inputs (public_inputs and private_inputs)")
    template_id: Optional[str] = Field(None, description="Specific template ID (optional)")


class ProofGenerationResponse(BaseModel):
    """Proof generation response"""
    proof_id: str
    claim_id: str
    circuit_type: str
    template_id: str
    proof_hash: str
    proving_time: float
    proof_size: int
    generated_at: str


class ProofVerificationRequest(BaseModel):
    """Proof verification request"""
    proof_id: str = Field(..., description="Proof ID to verify")
    verifier_id: Optional[str] = Field(None, description="Optional verifier identifier")


class ProofVerificationResponse(BaseModel):
    """Proof verification response"""
    verification_id: str
    proof_id: str
    is_valid: bool
    status: str
    checks_passed: dict
    verification_time: float
    error_message: Optional[str]
    verified_at: str


class MerkleProofRequest(BaseModel):
    """Merkle proof generation request"""
    claim_id: str = Field(..., description="Claim ID")
    evidence_id: str = Field(..., description="Evidence ID to prove")
    bundle_id: str = Field(..., description="Evidence bundle ID")


@router.post(
    "/generate",
    response_model=ProofGenerationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate ZKP Proof",
    description="Generate a zero-knowledge proof for a claim"
)
async def generate_proof(
    request: ProofGenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_generate_permission)
):
    """
    Generate ZKP proof
    
    - Builds witness from inputs
    - Generates proof using specified circuit
    - Stores proof artifact
    - Returns proof information
    """
    try:
        service = ProofService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.generate_proof(
            claim_id=request.claim_id,
            circuit_type=request.circuit_type,
            witness_inputs=request.witness_inputs,
            template_id=request.template_id
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
    except ProofGenerationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/verify",
    response_model=ProofVerificationResponse,
    summary="Verify ZKP Proof",
    description="Verify a zero-knowledge proof"
)
async def verify_proof(
    request: ProofVerificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_verify_permission)
):
    """
    Verify ZKP proof
    
    - Retrieves proof artifact
    - Performs cryptographic verification
    - Records verification receipt
    - Returns verification result
    """
    try:
        service = ProofService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.verify_proof(
            proof_id=request.proof_id,
            verifier_id=request.verifier_id
        )
        
        return result
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except VerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/merkle",
    summary="Generate Merkle Membership Proof",
    description="Generate ZKP proof of evidence membership in Merkle tree"
)
async def generate_merkle_proof(
    request: MerkleProofRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_generate_permission)
):
    """
    Generate Merkle membership proof
    
    - Proves evidence is part of bundle
    - Uses ZKP circuit for privacy
    - Returns ZKP proof artifact
    """
    try:
        service = ProofService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.generate_merkle_proof(
            claim_id=request.claim_id,
            evidence_id=request.evidence_id,
            bundle_id=request.bundle_id
        )
        
        return result
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ProofGenerationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/{proof_id}",
    summary="Get Proof Details",
    description="Retrieve detailed proof information"
)
async def get_proof_details(
    proof_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Get proof details
    
    - Returns proof artifact
    - Includes verification history
    - Tenant-scoped access
    """
    try:
        service = ProofService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.get_proof_details(proof_id=proof_id)
        
        return result
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/",
    summary="List Proofs",
    description="List proofs for tenant"
)
async def list_proofs(
    claim_id: Optional[str] = Query(None, description="Filter by claim ID"),
    circuit_type: Optional[str] = Query(None, description="Filter by circuit type"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    List proofs
    
    - Filter by claim or circuit type
    - Paginated results
    - Tenant-scoped
    """
    try:
        service = ProofService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.list_proofs(
            claim_id=claim_id,
            circuit_type=circuit_type,
            limit=limit,
            offset=offset
        )
        
        return result
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/circuits/templates",
    summary="List Circuit Templates",
    description="Get available ZKP circuit templates"
)
async def list_circuit_templates(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    List circuit templates
    
    - Returns available circuits
    - Includes readiness status
    - Showing proving time estimates
    """
    try:
        service = ProofService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        templates = await service.get_circuit_templates()
        
        return {
            "templates": templates,
            "total": len(templates)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve templates: {str(e)}"
        )

"""
Attestation Assembly API Endpoints
Handles attestation package creation, assembly, signing, and export
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from datetime import datetime

from app.db.session import get_db
from app.api.dependencies import get_current_user, require_attest_permission
from app.services.attestation_service import AttestationService
from app.core.auth import TokenPayload
from app.utils.errors import NotFoundError, ValidationError, SignatureError


router = APIRouter(prefix="/attestations/assembly", tags=["Attestation Assembly"])


# Request/Response Models
class CreateAttestationRequest(BaseModel):
    """Create attestation request"""
    claim_id: str = Field(..., description="Claim ID")
    title: str = Field(..., description="Attestation title")
    description: str = Field(..., description="Description")
    attestation_type: str = Field(..., description="Attestation type")
    issuer: dict = Field(..., description="Issuer information")
    subject: Optional[dict] = Field(None, description="Subject information")
    compliance_framework: Optional[str] = Field(None, description="Compliance framework")
    valid_until: Optional[datetime] = Field(None, description="Expiration date")


class AddEvidenceRequest(BaseModel):
    """Add evidence to attestation request"""
    package_id: str = Field(..., description="Package ID")
    bundle_id: str = Field(..., description="Evidence bundle ID")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class AddProofRequest(BaseModel):
    """Add proof to attestation request"""
    package_id: str = Field(..., description="Package ID")
    proof_id: str = Field(..., description="Proof ID")
    include_full_proof: bool = Field(False, description="Include full proof data")


class SignAttestationRequest(BaseModel):
    """Sign attestation request"""
    package_id: str = Field(..., description="Package ID")
    signer_name: str = Field(..., description="Signer name")
    algorithm: str = Field("RSA-SHA256", description="Signature algorithm")
    signer_email: Optional[str] = Field(None, description="Signer email")


class ExportAttestationRequest(BaseModel):
    """Export attestation request"""
    package_id: str = Field(..., description="Package ID")
    format: str = Field(..., description="Export format (json, oscal, pdf)")
    options: Optional[dict] = Field(None, description="Export options")


class RevokeAttestationRequest(BaseModel):
    """Revoke attestation request"""
    package_id: str = Field(..., description="Package ID")
    reason: str = Field(..., description="Revocation reason")


@router.post(
    "/create",
    status_code=status.HTTP_201_CREATED,
    summary="Create Attestation Package",
    description="Create new attestation package from claim"
)
async def create_attestation(
    request: CreateAttestationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_attest_permission)
):
    """
    Create attestation package
    
    - Creates package from claim
    - Sets issuer and metadata
    - Returns package summary
    """
    try:
        service = AttestationService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.create_attestation(
            claim_id=request.claim_id,
            title=request.title,
            description=request.description,
            attestation_type=request.attestation_type,
            issuer=request.issuer,
            subject=request.subject,
            compliance_framework=request.compliance_framework,
            valid_until=request.valid_until
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


@router.post(
    "/add-evidence",
    summary="Add Evidence to Attestation",
    description="Add evidence bundle to attestation package"
)
async def add_evidence(
    request: AddEvidenceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_attest_permission)
):
    """
    Add evidence to attestation
    
    - Adds evidence bundle to package
    - Updates package metadata
    """
    try:
        service = AttestationService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.add_evidence_to_attestation(
            package_id=request.package_id,
            bundle_id=request.bundle_id,
            metadata=request.metadata
        )
        
        return result
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/add-proof",
    summary="Add Proof to Attestation",
    description="Add ZKP proof to attestation package"
)
async def add_proof(
    request: AddProofRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_attest_permission)
):
    """
    Add proof to attestation
    
    - Adds ZKP proof to package
    - Updates package metadata
    """
    try:
        service = AttestationService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.add_proof_to_attestation(
            package_id=request.package_id,
            proof_id=request.proof_id,
            include_full_proof=request.include_full_proof
        )
        
        return result
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/assemble/{package_id}",
    summary="Assemble Attestation",
    description="Finalize attestation package assembly"
)
async def assemble_attestation(
    package_id: str,
    include_checksums: bool = Query(True, description="Include checksums"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_attest_permission)
):
    """
    Assemble attestation
    
    - Validates package completeness
    - Computes checksums
    - Finalizes assembly
    """
    try:
        service = AttestationService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.assemble_attestation(
            package_id=package_id,
            include_checksums=include_checksums
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


@router.post(
    "/sign",
    summary="Sign Attestation",
    description="Digitally sign attestation package"
)
async def sign_attestation(
    request: SignAttestationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_attest_permission)
):
    """
    Sign attestation
    
    - Generates digital signature
    - Updates package status to signed
    - Returns signature information
    """
    try:
        service = AttestationService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.sign_attestation(
            package_id=request.package_id,
            signer_name=request.signer_name,
            algorithm=request.algorithm,
            signer_email=request.signer_email
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
    except SignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/verify-signature/{package_id}",
    summary="Verify Attestation Signature",
    description="Verify digital signature of attestation package"
)
async def verify_signature(
    package_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Verify signature
    
    - Validates digital signature
    - Checks package integrity
    - Returns verification result
    """
    try:
        service = AttestationService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.verify_attestation_signature(package_id=package_id)
        
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


@router.post(
    "/export",
    summary="Export Attestation",
    description="Export attestation to specified format"
)
async def export_attestation(
    request: ExportAttestationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Export attestation
    
    - Exports to JSON, OSCAL, or PDF
    - Applies format-specific options
    - Returns file information
    """
    try:
        service = AttestationService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.export_attestation(
            package_id=request.package_id,
            format=request.format,
            options=request.options
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


@router.post(
    "/publish/{package_id}",
    summary="Publish Attestation",
    description="Publish signed attestation package"
)
async def publish_attestation(
    package_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_attest_permission)
):
    """
    Publish attestation
    
    - Verifies package is signed
    - Updates status to published
    - Makes attestation available
    """
    try:
        service = AttestationService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.publish_attestation(package_id=package_id)
        
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


@router.post(
    "/revoke",
    summary="Revoke Attestation",
    description="Revoke published attestation package"
)
async def revoke_attestation(
    request: RevokeAttestationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_attest_permission)
):
    """
    Revoke attestation
    
    - Revokes published attestation
    - Records revocation reason
    - Updates status
    """
    try:
        service = AttestationService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.revoke_attestation(
            package_id=request.package_id,
            reason=request.reason
        )
        
        return result
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/{package_id}",
    summary="Get Attestation Details",
    description="Retrieve detailed attestation package information"
)
async def get_attestation_details(
    package_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Get attestation details
    
    - Returns complete package information
    - Includes evidence and proofs
    - Shows status and signatures
    """
    try:
        service = AttestationService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.get_attestation_details(package_id=package_id)
        
        return result
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/",
    summary="List Attestations",
    description="List attestation packages for tenant"
)
async def list_attestations(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    List attestations
    
    - Filter by status
    - Paginated results
    - Tenant-scoped
    """
    try:
        service = AttestationService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.list_attestations(
            status=status,
            limit=limit,
            offset=offset
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list attestations: {str(e)}"
        )

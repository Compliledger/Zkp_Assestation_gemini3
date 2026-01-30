"""
Anchoring & Publication API Endpoints
Handles blockchain anchoring, IPFS storage, and public registry
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.api.dependencies import get_current_user, require_publish_permission
from app.services.anchoring_service import AnchoringService
from app.core.anchoring.blockchain_anchor import BlockchainAnchor, BlockchainType
from app.config import settings
from app.core.auth import TokenPayload
from app.utils.errors import NotFoundError, ValidationError, AnchoringError


router = APIRouter(prefix="/anchoring", tags=["Anchoring & Publication"])


# Request/Response Models
class PublishToIPFSRequest(BaseModel):
    """Publish to IPFS request"""
    package_id: str = Field(..., description="Package ID")
    pin: bool = Field(True, description="Pin content to prevent deletion")


class AnchorToBlockchainRequest(BaseModel):
    """Anchor to blockchain request"""
    package_id: str = Field(..., description="Package ID")
    blockchain: str = Field("algorand", description="Blockchain type (algorand, mock)")


class CompletePublicationRequest(BaseModel):
    """Complete publication request"""
    package_id: str = Field(..., description="Package ID")
    to_ipfs: bool = Field(True, description="Publish to IPFS")
    to_blockchain: bool = Field(True, description="Anchor to blockchain")
    to_registry: bool = Field(True, description="Register in public registry")
    blockchain: str = Field("algorand", description="Blockchain type (algorand, mock)")


class SearchRegistryRequest(BaseModel):
    """Search registry request"""
    attestation_type: Optional[str] = Field(None, description="Filter by attestation type")
    compliance_framework: Optional[str] = Field(None, description="Filter by framework")
    issuer_id: Optional[str] = Field(None, description="Filter by issuer")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    limit: int = Field(50, ge=1, le=100)


class AlgorandDeployResponse(BaseModel):
    transaction_id: str
    confirmed_round: Optional[int] = None
    app_id: int


class AlgorandServerAnchorRequest(BaseModel):
    package_id: str = Field(..., description="Package ID")
    package_hash: str = Field(..., description="Hex SHA-256 (64 chars)")
    merkle_root: str = Field("0" * 64, description="Hex SHA-256 (64 chars)")


class AlgorandPrepareTxnRequest(BaseModel):
    sender: str = Field(..., description="Sender address (wallet)")
    package_id: str = Field(..., description="Package ID")
    package_hash: str = Field(..., description="Hex SHA-256 (64 chars)")
    merkle_root: str = Field("0" * 64, description="Hex SHA-256 (64 chars)")


class AlgorandSubmitSignedTxnRequest(BaseModel):
    signed_txn_b64: str = Field(..., description="Base64-encoded signed transaction")


@router.post(
    "/ipfs/publish",
    summary="Publish to IPFS",
    description="Publish attestation package to IPFS for distributed storage"
)
async def publish_to_ipfs(
    request: PublishToIPFSRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_publish_permission)
):
    """
    Publish to IPFS
    
    - Uploads package to IPFS
    - Optionally pins content
    - Returns IPFS CID and gateway URLs
    """
    try:
        service = AnchoringService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.publish_to_ipfs(
            package_id=request.package_id,
            pin=request.pin
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
    "/blockchain/anchor",
    summary="Anchor to Blockchain",
    description="Anchor attestation package hash to blockchain for immutability"
)
async def anchor_to_blockchain(
    request: AnchorToBlockchainRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_publish_permission)
):
    """
    Anchor to blockchain
    
    - Creates blockchain transaction
    - Stores package hash on-chain
    - Returns transaction hash and explorer URL
    """
    try:
        service = AnchoringService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.anchor_to_blockchain(
            package_id=request.package_id,
            blockchain=request.blockchain
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
    except AnchoringError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/algorand/contract/deploy",
    summary="Deploy Algorand Anchoring Contract",
    description="Deploy the Algorand stateful anchoring app to TestNet using server mnemonic signer"
)
async def deploy_algorand_contract(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_publish_permission)
):
    try:
        anchor = BlockchainAnchor(
            blockchain_type=BlockchainType.ALGORAND,
            network=getattr(settings, "ALGORAND_NETWORK", "testnet"),
            rpc_url=getattr(settings, "ALGORAND_API_URL", None),
        )
        result = anchor.deploy_algorand_contract()
        return result
    except AnchoringError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/algorand/anchor/server",
    summary="Anchor on Algorand (Server Signer)",
    description="Anchor a package on Algorand via app-call, signed by server mnemonic"
)
async def algorand_anchor_server(
    request: AlgorandServerAnchorRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_publish_permission)
):
    try:
        anchor = BlockchainAnchor(
            blockchain_type=BlockchainType.ALGORAND,
            network=getattr(settings, "ALGORAND_NETWORK", "testnet"),
            rpc_url=getattr(settings, "ALGORAND_API_URL", None),
        )
        record = anchor.anchor_package(
            package_id=request.package_id,
            package_hash=request.package_hash,
            merkle_root=request.merkle_root,
            user_id=current_user.sub,
        )
        return {
            "anchor_id": record.anchor_id,
            "transaction_hash": record.transaction_hash,
            "block_number": record.block_number,
            "app_id": getattr(settings, "ALGORAND_ANCHOR_APP_ID", None) or getattr(settings, "REGISTRY_APP_ID", None),
            "explorer_url": anchor.get_explorer_url(record.transaction_hash),
            "status": record.status.value,
        }
    except (ValidationError, AnchoringError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/algorand/anchor/prepare",
    summary="Prepare Algorand Anchor Txn (Frontend Signer)",
    description="Build an unsigned app-call txn for the frontend wallet to sign"
)
async def algorand_anchor_prepare(
    request: AlgorandPrepareTxnRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_publish_permission)
):
    try:
        anchor = BlockchainAnchor(
            blockchain_type=BlockchainType.ALGORAND,
            network=getattr(settings, "ALGORAND_NETWORK", "testnet"),
            rpc_url=getattr(settings, "ALGORAND_API_URL", None),
        )
        result = anchor.prepare_algorand_anchor_txn(
            sender_address=request.sender,
            package_id=request.package_id,
            package_hash=request.package_hash,
            merkle_root=request.merkle_root,
        )
        return result
    except (ValidationError, AnchoringError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/algorand/anchor/submit",
    summary="Submit Signed Algorand Txn (Frontend Signer)",
    description="Submit a base64 signed transaction blob to Algorand"
)
async def algorand_anchor_submit(
    request: AlgorandSubmitSignedTxnRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_publish_permission)
):
    try:
        anchor = BlockchainAnchor(
            blockchain_type=BlockchainType.ALGORAND,
            network=getattr(settings, "ALGORAND_NETWORK", "testnet"),
            rpc_url=getattr(settings, "ALGORAND_API_URL", None),
        )
        result = anchor.submit_algorand_signed_txn(request.signed_txn_b64)
        return {
            "transaction_hash": result.get("transaction_hash"),
            "block_number": result.get("block_number"),
            "confirmed": result.get("confirmed", False),
            "explorer_url": anchor.get_explorer_url(result.get("transaction_hash")),
        }
    except AnchoringError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/algorand/anchor/{package_id}",
    summary="Get On-Chain Algorand Anchor",
    description="Read anchor record from Algorand app box by package_id"
)
async def algorand_get_anchor(
    package_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user)
):
    try:
        anchor = BlockchainAnchor(
            blockchain_type=BlockchainType.ALGORAND,
            network=getattr(settings, "ALGORAND_NETWORK", "testnet"),
            rpc_url=getattr(settings, "ALGORAND_API_URL", None),
        )
        data = anchor.get_algorand_anchor(package_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/publish/complete",
    summary="Complete Publication",
    description="Complete publication workflow (IPFS + Blockchain + Registry)"
)
async def publish_complete(
    request: CompletePublicationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_publish_permission)
):
    """
    Complete publication
    
    - Publishes to IPFS
    - Anchors to blockchain
    - Registers in public registry
    - Returns all publication information
    """
    try:
        service = AnchoringService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.publish_complete(
            package_id=request.package_id,
            to_ipfs=request.to_ipfs,
            to_blockchain=request.to_blockchain,
            to_registry=request.to_registry,
            blockchain=request.blockchain
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
    except AnchoringError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/registry/register",
    summary="Register in Public Registry",
    description="Register attestation in public searchable registry"
)
async def register_attestation(
    package_id: str = Query(..., description="Package ID"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_publish_permission)
):
    """
    Register attestation
    
    - Creates public registry entry
    - Makes attestation searchable
    - Returns registry entry ID
    """
    try:
        service = AnchoringService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.register_attestation(package_id=package_id)
        
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
    "/verify/{package_id}",
    summary="Verify Publication",
    description="Verify attestation across all publication channels"
)
async def verify_publication(
    package_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Verify publication
    
    - Verifies IPFS content
    - Verifies blockchain anchor
    - Verifies registry entry
    - Returns verification results
    """
    try:
        service = AnchoringService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.verify_publication(package_id=package_id)
        
        return result
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/ipfs/retrieve/{package_id}",
    summary="Retrieve from IPFS",
    description="Retrieve attestation content from IPFS"
)
async def retrieve_from_ipfs(
    package_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Retrieve from IPFS
    
    - Fetches content from IPFS
    - Returns attestation data
    - Provides gateway URLs
    """
    try:
        service = AnchoringService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.retrieve_from_ipfs(package_id=package_id)
        
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
    "/registry/search",
    summary="Search Registry",
    description="Search public attestation registry"
)
async def search_registry(
    request: SearchRegistryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Search registry
    
    - Searches public attestations
    - Filters by type, framework, issuer, tags
    - Returns matching entries
    """
    try:
        service = AnchoringService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.search_registry(
            attestation_type=request.attestation_type,
            compliance_framework=request.compliance_framework,
            issuer_id=request.issuer_id,
            tags=request.tags,
            limit=request.limit
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get(
    "/status/{package_id}",
    summary="Get Publication Status",
    description="Get complete publication status for attestation"
)
async def get_publication_status(
    package_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Get publication status
    
    - Shows IPFS publication
    - Shows blockchain anchoring
    - Shows registry status
    - Provides access URLs
    """
    try:
        service = AnchoringService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.get_publication_status(package_id=package_id)
        
        return result
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/statistics",
    summary="Get Anchoring Statistics",
    description="Get statistics about anchoring and publication"
)
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Get statistics
    
    - Total anchors by blockchain
    - Registry statistics
    - Publication metrics
    """
    try:
        service = AnchoringService(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub
        )
        
        result = await service.get_anchoring_statistics()
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )

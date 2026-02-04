"""
Attestation Endpoints
Generate and retrieve attestations
"""

from fastapi import APIRouter, HTTPException, Header, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import json
import logging

from app.storage.memory_store import memory_store
from app.utils.merkle import create_merkle_tree_from_hashes
from app.config import settings
from app.models.attestation_status import AttestationStatus
from app.services.webhook_service import webhook_service
from app.utils.response_enhancer import enhance_attestation_response
import hashlib

logger = logging.getLogger(__name__)
router = APIRouter()

# Request/Response Models
class EvidenceRef(BaseModel):
    uri: str = Field(..., description="Evidence URI or identifier")
    hash: str = Field(..., description="SHA-256 hash of evidence")
    type: str = Field(default="compliance_check", description="Evidence type")

class AttestationRequest(BaseModel):
    evidence: List[EvidenceRef] = Field(..., min_items=1, description="Evidence references")
    policy: str = Field(..., description="Compliance policy or framework")
    callback_url: Optional[HttpUrl] = Field(None, description="Webhook callback URL")

class AttestationResponse(BaseModel):
    claim_id: str
    status: str
    message: str
    created_at: str

class AttestationDetail(BaseModel):
    claim_id: str
    status: str
    evidence: dict
    proof: Optional[dict] = None
    package: Optional[dict] = None
    anchor: Optional[dict] = None
    metadata: dict
    created_at: str
    completed_at: Optional[str] = None

# Helper Functions
def generate_claim_id() -> str:
    """Generate unique claim ID"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_suffix = uuid.uuid4().hex[:6].upper()
    return f"ATT-{timestamp}-{random_suffix}"

def generate_evidence_id() -> str:
    """Generate unique evidence ID"""
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    random_suffix = uuid.uuid4().hex[:4].upper()
    return f"EV-{timestamp}-{random_suffix}"

async def process_attestation(claim_id: str):
    """Background task to process attestation with explicit status lifecycle"""
    try:
        attestation = memory_store.get_attestation(claim_id)
        
        # Step 1: Update to computing_commitment status
        attestation["status"] = AttestationStatus.COMPUTING_COMMITMENT.value
        memory_store.update_attestation(claim_id, attestation)
        await webhook_service.trigger_status_change(attestation)
        
        # Step 2: Generate proof (simplified for demo)
        attestation["status"] = AttestationStatus.GENERATING_PROOF.value
        memory_store.update_attestation(claim_id, attestation)
        await webhook_service.trigger_status_change(attestation)
        
        proof = {
            "proof_hash": hashlib.sha256(attestation["evidence"]["merkle_root"].encode()).hexdigest(),
            "algorithm": "demo_zkp",
            "size_bytes": 128,
            "generated_at": datetime.utcnow().isoformat()
        }
        attestation["proof"] = proof
        
        # Step 3: Assemble package
        attestation["status"] = AttestationStatus.ASSEMBLING_PACKAGE.value
        memory_store.update_attestation(claim_id, attestation)
        await webhook_service.trigger_status_change(attestation)
        await asyncio.sleep(delay)
        
        package = {
            "protocol": "zkpa",
            "version": "1.1",
            "attestation_id": claim_id,
            "evidence": attestation["evidence"],
            "proof": proof,
            "metadata": attestation["metadata"]
        }
        package_bytes = json.dumps(package, sort_keys=True).encode()
        package_hash = hashlib.sha256(package_bytes).hexdigest()
        
        attestation["package"] = {
            "package_hash": package_hash,
            "package_uri": f"memory://{claim_id}",
            "size_bytes": len(package_bytes)
        }
        
        # Step 4: Anchor (optional, if Algorand enabled)
        if settings.ALGORAND_MNEMONIC:
            attestation["status"] = AttestationStatus.ANCHORING.value
            memory_store.update_attestation(claim_id, attestation)
            await webhook_service.trigger_status_change(attestation)
            
            try:
                from app.core.anchoring.algorand_testnet import AlgorandTestnetAnchor
                algorand = AlgorandTestnetAnchor(sender_mnemonic=settings.ALGORAND_MNEMONIC)
                anchor_result = algorand.anchor_attestation(
                    attestation_id=claim_id,
                    merkle_root=attestation["evidence"]["merkle_root"],
                    package_hash=package_hash
                )
                attestation["anchor"] = anchor_result
            except Exception as e:
                logger.warning(f"Anchor failed (continuing without): {e}")
                attestation["anchor"] = {"error": str(e), "chain": "algorand"}
                attestation["status"] = AttestationStatus.FAILED_ANCHOR.value
                memory_store.update_attestation(claim_id, attestation)
                await webhook_service.trigger_failure(attestation, str(e))
                return
        
        # Final status
        attestation["status"] = AttestationStatus.VALID.value
        attestation["completed_at"] = datetime.utcnow().isoformat()
        memory_store.update_attestation(claim_id, attestation)
        
        # Trigger completion webhook
        await webhook_service.trigger_completion(attestation)
        
        logger.info(f"Attestation {claim_id} completed successfully with status: {attestation['status']}")
        
    except Exception as e:
        logger.error(f"Attestation processing failed: {e}", exc_info=True)
        attestation = memory_store.get_attestation(claim_id)
        attestation["status"] = AttestationStatus.FAILED.value
        attestation["error"] = str(e)
        attestation["failed_at"] = datetime.utcnow().isoformat()
        memory_store.update_attestation(claim_id, attestation)
        
        # Trigger failure webhook
        await webhook_service.trigger_failure(attestation, str(e))

# Endpoints
@router.post("", response_model=AttestationResponse)
async def create_attestation(
    request: AttestationRequest,
    background_tasks: BackgroundTasks,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """
    Create a new attestation
    
    Flow:
    1. Validate request + check idempotency
    2. Ingest evidence refs
    3. Compute commitment (Merkle root)
    4. Queue proof generation (background)
    5. Return claim_id immediately
    """
    
    try:
        # Check idempotency
        if idempotency_key:
            existing_id = memory_store.get_by_idempotency_key(idempotency_key)
            if existing_id:
                existing = memory_store.get_attestation(existing_id)
                return AttestationResponse(
                    claim_id=existing_id,
                    status=existing["status"],
                    message="Returned from idempotency cache",
                    created_at=existing["created_at"]
                )
        
        # Generate claim ID
        claim_id = generate_claim_id()
        logger.info(f"Creating attestation {claim_id}")
        
        # Step 1: Ingest evidence refs
        evidence_items = []
        hashes = []
        for ref in request.evidence:
            evidence_items.append({
                "id": generate_evidence_id(),
                "uri": ref.uri,
                "hash": ref.hash,
                "type": ref.type
            })
            hashes.append(ref.hash)
        
        # Step 2: Compute commitment (Merkle root)
        merkle_tree = create_merkle_tree_from_hashes(hashes)
        merkle_root = merkle_tree.get_root()
        
        commitment_hash = hashlib.sha256(
            json.dumps(evidence_items, sort_keys=True).encode()
        ).hexdigest()
        
        # Create attestation
        attestation = {
            "claim_id": claim_id,
            "status": AttestationStatus.PENDING.value,
            "evidence": {
                "items": evidence_items,
                "count": len(evidence_items),
                "merkle_root": merkle_root,
                "commitment_hash": commitment_hash,
                "leaf_count": len(hashes)
            },
            "metadata": {
                "policy": request.policy,
                "compliance_framework": "SOC2_TYPE_II",
                "issued_at": datetime.utcnow().isoformat(),
                "valid_until": (datetime.utcnow() + timedelta(days=90)).isoformat()
            },
            "callback_url": str(request.callback_url) if request.callback_url else None,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Store attestation (memory_store adds created_at timestamp)
        memory_store.create_attestation(claim_id, attestation, idempotency_key)
        
        # Retrieve stored attestation to get the created_at timestamp
        stored = memory_store.get_attestation(claim_id)
        
        # Queue background processing
        background_tasks.add_task(process_attestation, claim_id)
        
        return AttestationResponse(
            claim_id=claim_id,
            status="pending",
            message="Attestation creation initiated. Poll GET /api/v1/attestations/{claim_id} for status.",
            created_at=stored["created_at"]
        )
    
    except Exception as e:
        logger.error(f"Error creating attestation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Attestation creation failed: {str(e)}")

@router.get("/{claim_id}", response_model=dict)
async def get_attestation(claim_id: str, enhanced: bool = True):
    """
    Get attestation details by claim_id
    
    Returns full attestation including evidence, proof, package, and anchor.
    Enhanced format includes summary, verification_status, and privacy info.
    
    Query params:
    - enhanced: Return enhanced format for UI (default: true)
    """
    attestation = memory_store.get_attestation(claim_id)
    
    if not attestation:
        raise HTTPException(status_code=404, detail=f"Attestation {claim_id} not found")
    
    # Return enhanced format by default
    if enhanced:
        return enhance_attestation_response(attestation)
    
    return AttestationDetail(**attestation)

@router.get("/{claim_id}/download")
async def download_attestation(claim_id: str, format: str = "json"):
    """
    Download attestation as file
    
    Query params:
    - format: json (default) or oscal
    
    Returns attestation with Content-Disposition header for download.
    """
    attestation = memory_store.get_attestation(claim_id)
    
    if not attestation:
        raise HTTPException(status_code=404, detail=f"Attestation {claim_id} not found")
    
    # Enhance the response
    enhanced = enhance_attestation_response(attestation)
    
    # Format selection
    if format == "oscal":
        # Convert to OSCAL format (simplified)
        content = _convert_to_oscal(enhanced)
        filename = f"attestation-{claim_id}.oscal.json"
    else:
        # Default JSON format
        content = enhanced
        filename = f"attestation-{claim_id}.json"
    
    # Return as downloadable file
    return JSONResponse(
        content=content,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "application/json"
        }
    )


def _convert_to_oscal(attestation: dict) -> dict:
    """
    Convert attestation to OSCAL format (simplified)
    
    This is a basic OSCAL structure. Full OSCAL conversion would be more complex.
    """
    return {
        "oscal-version": "1.0.0",
        "assessment-results": {
            "uuid": attestation["claim_id"],
            "metadata": {
                "title": f"ZKP Attestation - {attestation['summary']['control_id']}",
                "published": attestation["created_at"],
                "last-modified": attestation.get("completed_at", attestation["created_at"]),
                "version": "1.0",
                "oscal-version": "1.0.0"
            },
            "results": [
                {
                    "uuid": attestation["claim_id"],
                    "title": attestation["summary"]["control_title"],
                    "description": f"Zero-knowledge attestation for {attestation['summary']['framework']} control {attestation['summary']['control_id']}",
                    "start": attestation["created_at"],
                    "end": attestation.get("completed_at"),
                    "findings": [
                        {
                            "uuid": f"{attestation['claim_id']}-finding-1",
                            "title": "Compliance Verification",
                            "description": "Zero-knowledge proof verification",
                            "target": {
                                "type": "control",
                                "id": attestation["summary"]["control_id"]
                            }
                        }
                    ]
                }
            ]
        },
        "zkp_metadata": {
            "proof_hash": attestation.get("cryptographic_proof", {}).get("proof_hash"),
            "merkle_root": attestation.get("cryptographic_proof", {}).get("merkle_root"),
            "verification_status": attestation.get("verification_status", {}).get("overall")
        }
    }

@router.get("", response_model=List[AttestationDetail])
async def list_attestations(limit: int = 100, offset: int = 0):
    """
    List all attestations
    """
    attestations = memory_store.list_attestations(limit, offset)
    return [AttestationDetail(**a) for a in attestations]

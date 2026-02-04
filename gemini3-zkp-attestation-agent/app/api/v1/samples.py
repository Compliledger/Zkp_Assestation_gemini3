"""
Sample Controls API
Endpoints for quick-start demo controls
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Body
from typing import List, Optional
from pydantic import BaseModel

from app.utils.sample_controls import (
    get_all_controls,
    get_control_by_id,
    get_controls_by_framework,
    get_all_frameworks,
    search_controls,
    SampleControl
)
from app.utils.demo_data import DemoDataGenerator
from app.storage.memory_store import memory_store
from app.models.attestation_status import AttestationStatus
from datetime import datetime
import hashlib

router = APIRouter()


class QuickAttestRequest(BaseModel):
    """Quick attestation from sample control"""
    callback_url: Optional[str] = None


class ControlSearchRequest(BaseModel):
    """Search request"""
    query: str


@router.get("/controls", response_model=dict)
async def get_sample_controls():
    """
    Get all sample controls
    
    Returns list of pre-defined compliance controls for quick demos.
    """
    controls = get_all_controls()
    
    return {
        "controls": [control.dict() for control in controls],
        "count": len(controls),
        "frameworks": list(get_all_frameworks().keys())
    }


@router.get("/controls/{control_id}", response_model=dict)
async def get_sample_control(control_id: str):
    """
    Get specific sample control by ID
    
    Example: GET /api/v1/samples/controls/AC-2
    """
    control = get_control_by_id(control_id)
    
    if not control:
        raise HTTPException(status_code=404, detail=f"Control {control_id} not found")
    
    return {
        "control": control.dict(),
        "usage": {
            "quick_attest_url": f"/api/v1/samples/quick-attest/{control_id}",
            "method": "POST"
        }
    }


@router.get("/frameworks", response_model=dict)
async def get_frameworks():
    """
    Get all supported frameworks with metadata
    
    Returns framework information and control counts.
    """
    frameworks = get_all_frameworks()
    
    # Count controls per framework
    for framework_name in frameworks:
        controls = get_controls_by_framework(framework_name)
        frameworks[framework_name]["control_count"] = len(controls)
    
    return {
        "frameworks": frameworks,
        "count": len(frameworks)
    }


@router.get("/frameworks/{framework_name}/controls", response_model=dict)
async def get_framework_controls(framework_name: str):
    """
    Get all controls for a specific framework
    
    Example: GET /api/v1/samples/frameworks/NIST 800-53/controls
    """
    controls = get_controls_by_framework(framework_name)
    
    if not controls:
        raise HTTPException(
            status_code=404,
            detail=f"Framework '{framework_name}' not found or has no controls"
        )
    
    return {
        "framework": framework_name,
        "controls": [control.dict() for control in controls],
        "count": len(controls)
    }


@router.post("/search", response_model=dict)
async def search_sample_controls(request: ControlSearchRequest):
    """
    Search controls by query
    
    Searches across control ID, title, statement, and framework.
    """
    results = search_controls(request.query)
    
    return {
        "query": request.query,
        "results": [control.dict() for control in results],
        "count": len(results)
    }


@router.post("/quick-attest/{control_id}", response_model=dict)
async def quick_attest_from_control(
    control_id: str,
    background_tasks: BackgroundTasks,
    request: Optional[QuickAttestRequest] = Body(None)
):
    """
    Create attestation from sample control with auto-generated evidence
    
    This is the 1-click attestation endpoint for demos.
    
    Example: POST /api/v1/samples/quick-attest/AC-2
    """
    # Get the sample control
    control = get_control_by_id(control_id)
    
    if not control:
        raise HTTPException(status_code=404, detail=f"Control {control_id} not found")
    
    # Generate claim ID
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    claim_hash = hashlib.sha256(f"{control_id}{timestamp}".encode()).hexdigest()[:8]
    claim_id = f"ATT-{timestamp[:8]}-{claim_hash.upper()}"
    
    # Auto-generate evidence based on control
    evidence_items = DemoDataGenerator.generate_evidence_list(control.evidence_count)
    
    # Create attestation
    attestation = {
        "claim_id": claim_id,
        "status": AttestationStatus.PENDING.value,
        "created_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        
        # Sample control info
        "control_info": {
            "control_id": control.control_id,
            "framework": control.framework,
            "title": control.title,
            "statement": control.statement,
            "claim_type": control.claim_type,
            "risk_level": control.risk_level
        },
        
        # Evidence
        "evidence": {
            "items": evidence_items,
            "count": len(evidence_items)
        },
        
        # Policy
        "policy": f"{control.framework} - {control.control_id}: {control.title}",
        
        # Callback
        "callback_url": request.callback_url if request else None,
        
        # Metadata
        "metadata": {
            "source": "sample_control",
            "quick_attest": True,
            "auto_generated_evidence": True
        }
    }
    
    # Store attestation
    memory_store.create_attestation(claim_id, attestation)
    
    # Queue background processing
    from app.api.v1.attestations import process_attestation
    background_tasks.add_task(process_attestation, claim_id)
    
    return {
        "claim_id": claim_id,
        "status": "pending",
        "message": f"Quick attestation created from {control.framework} control {control.control_id}",
        "control": {
            "control_id": control.control_id,
            "framework": control.framework,
            "title": control.title
        },
        "evidence_count": len(evidence_items),
        "created_at": attestation["created_at"],
        "poll_url": f"/api/v1/attestations/{claim_id}",
        "verify_url": "/api/v1/verify"
    }


@router.get("/stats", response_model=dict)
async def get_sample_stats():
    """
    Get statistics about sample controls
    """
    all_controls = get_all_controls()
    frameworks = get_all_frameworks()
    
    # Count by framework
    framework_counts = {}
    for framework_name in frameworks:
        framework_counts[framework_name] = len(get_controls_by_framework(framework_name))
    
    # Count by claim type
    claim_type_counts = {}
    for control in all_controls:
        claim_type = control.claim_type
        claim_type_counts[claim_type] = claim_type_counts.get(claim_type, 0) + 1
    
    # Count by risk level
    risk_level_counts = {}
    for control in all_controls:
        risk_level = control.risk_level
        risk_level_counts[risk_level] = risk_level_counts.get(risk_level, 0) + 1
    
    return {
        "total_controls": len(all_controls),
        "total_frameworks": len(frameworks),
        "by_framework": framework_counts,
        "by_claim_type": claim_type_counts,
        "by_risk_level": risk_level_counts
    }

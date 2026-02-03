"""
Demo Endpoints
Quick endpoints for hackathon demonstrations
"""

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging

from app.utils.demo_data import DemoDataGenerator, quick_demo_request
from app.storage.memory_store import memory_store
from app.api.v1.attestations import create_attestation, AttestationRequest, AttestationResponse

logger = logging.getLogger(__name__)
router = APIRouter()


class QuickDemoRequest(BaseModel):
    """Quick demo request"""
    policy: str = "SOC2_TYPE_II"
    evidence_count: int = 5
    callback_url: Optional[str] = None


class QuickDemoResponse(BaseModel):
    """Quick demo response"""
    claim_id: str
    status: str
    message: str
    policy_used: str
    evidence_count: int
    created_at: str


class DemoScenarioInfo(BaseModel):
    """Demo scenario information"""
    name: str
    description: str
    policy: str
    evidence_count: int


@router.get("/policies", summary="Get available demo policies")
async def get_demo_policies():
    """
    Get list of available demo compliance policies
    
    Returns available policy names and their full text for demo purposes.
    """
    policies = DemoDataGenerator.get_demo_policies()
    return {
        "count": len(policies),
        "policies": [
            {"name": name, "description": text.split("\n")[0]}
            for name, text in policies.items()
        ],
        "full_policies": policies
    }


@router.get("/scenarios", response_model=List[DemoScenarioInfo], summary="Get demo test scenarios")
async def get_demo_scenarios():
    """
    Get pre-configured demo test scenarios
    
    Returns various test scenarios with different policies and evidence counts.
    """
    return DemoDataGenerator.generate_test_scenarios()


@router.post("/quick", response_model=QuickDemoResponse, summary="Quick demo attestation")
async def quick_demo_attestation(
    request: QuickDemoRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a demo attestation with pre-generated data
    
    This is a convenience endpoint that generates evidence automatically
    based on the selected policy and evidence count.
    
    Perfect for hackathon demos and quick testing!
    """
    logger.info(f"Quick demo request: policy={request.policy}, evidence_count={request.evidence_count}")
    
    # Generate demo data
    demo_request_data = DemoDataGenerator.generate_demo_attestation_request(
        policy=request.policy,
        evidence_count=request.evidence_count,
        callback_url=request.callback_url
    )
    
    # Create attestation request
    attestation_request = AttestationRequest(**demo_request_data)
    
    # Use the existing attestation creation logic
    result = await create_attestation(
        request=attestation_request,
        background_tasks=background_tasks,
        idempotency_key=None
    )
    
    return QuickDemoResponse(
        claim_id=result.claim_id,
        status=result.status,
        message="Quick demo attestation created with auto-generated evidence",
        policy_used=request.policy,
        evidence_count=request.evidence_count,
        created_at=result.created_at
    )


@router.post("/scenario/{scenario_index}", summary="Run demo scenario by index")
async def run_demo_scenario(
    scenario_index: int,
    background_tasks: BackgroundTasks,
    callback_url: Optional[str] = None
):
    """
    Run a pre-configured demo scenario by index (0-based)
    
    Args:
        scenario_index: Index of the scenario (0-4)
        callback_url: Optional webhook callback URL
    
    Returns:
        Attestation creation response
    """
    scenarios = DemoDataGenerator.generate_test_scenarios()
    
    if scenario_index < 0 or scenario_index >= len(scenarios):
        return {
            "error": f"Invalid scenario index. Must be between 0 and {len(scenarios)-1}",
            "available_scenarios": scenarios
        }
    
    scenario = scenarios[scenario_index]
    logger.info(f"Running demo scenario {scenario_index}: {scenario['name']}")
    
    # Generate request
    demo_request = QuickDemoRequest(
        policy=scenario["policy"],
        evidence_count=scenario["evidence_count"],
        callback_url=callback_url
    )
    
    return await quick_demo_attestation(demo_request, background_tasks)


@router.get("/stats", summary="Get demo statistics")
async def get_demo_stats():
    """
    Get statistics about demo attestations
    
    Returns counts and status breakdown from in-memory storage.
    """
    stats = memory_store.get_stats()
    
    # Get status breakdown
    status_breakdown = {}
    for claim_id in memory_store.attestations.keys():
        attestation = memory_store.get_attestation(claim_id)
        status = attestation.get("status", "unknown")
        status_breakdown[status] = status_breakdown.get(status, 0) + 1
    
    return {
        "total_attestations": stats["attestations_count"],
        "total_verifications": stats["verifications_count"],
        "status_breakdown": status_breakdown,
        "demo_mode": True,
        "storage_type": "in-memory"
    }


@router.delete("/reset", summary="Reset demo data")
async def reset_demo_data():
    """
    Reset all demo data (clear in-memory storage)
    
    ⚠️ WARNING: This will delete all attestations and verifications!
    Only use this in demo mode for testing purposes.
    """
    initial_stats = memory_store.get_stats()
    
    # Clear all data
    memory_store.attestations.clear()
    memory_store.verifications.clear()
    memory_store.idempotency_keys.clear()
    
    logger.info("Demo data reset - all storage cleared")
    
    return {
        "message": "Demo data reset successfully",
        "cleared": {
            "attestations": initial_stats["attestations_count"],
            "verifications": initial_stats["verifications_count"],
            "idempotency_keys": initial_stats["idempotency_keys_count"]
        },
        "current_stats": memory_store.get_stats()
    }

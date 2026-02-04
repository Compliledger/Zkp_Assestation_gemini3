"""
Judge Mode API
Special endpoints for hackathon judge demos with guided flow
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

from app.config import settings
from app.storage.memory_store import memory_store

router = APIRouter()


class JudgeModeStatus(BaseModel):
    """Judge mode status"""
    enabled: bool
    fast_responses: bool
    mock_anchor: bool
    demo_mode: bool


class GuidedStep(BaseModel):
    """Guided demo flow step"""
    step: int
    title: str
    description: str
    endpoint: str
    method: str
    example_payload: Optional[Dict] = None
    tooltip: str
    gemini_usage: Optional[str] = None


# Guided demo flow steps
GUIDED_FLOW = [
    {
        "step": 1,
        "title": "Choose Sample Control",
        "description": "Select a pre-defined compliance control from major frameworks",
        "endpoint": "/api/v1/samples/controls",
        "method": "GET",
        "example_payload": None,
        "tooltip": "10 ready-to-use controls across NIST, SOC 2, ISO 27001, HIPAA, PCI-DSS",
        "gemini_usage": None
    },
    {
        "step": 2,
        "title": "Create Attestation (1-click)",
        "description": "Generate zero-knowledge attestation with auto-generated evidence",
        "endpoint": "/api/v1/samples/quick-attest/AC-2",
        "method": "POST",
        "example_payload": {},
        "tooltip": "Gemini 3 interprets control statement → selects proof template → generates attestation",
        "gemini_usage": "Gemini 3 analyzes control AC-2 and determines: claim_type='control_effectiveness', proof_template='merkle_commitment', risk_level='high'"
    },
    {
        "step": 3,
        "title": "View Enhanced Results",
        "description": "See summary, cryptographic proof, verification status, and privacy info",
        "endpoint": "/api/v1/attestations/{claim_id}",
        "method": "GET",
        "example_payload": None,
        "tooltip": "Enhanced response shows: framework, control_id, proof_hash, merkle_root, PASS/FAIL status, privacy statement",
        "gemini_usage": None
    },
    {
        "step": 4,
        "title": "Verify Attestation",
        "description": "Run verification checks with clear PASS/FAIL results",
        "endpoint": "/api/v1/verify",
        "method": "POST",
        "example_payload": {"attestation_id": "{claim_id}"},
        "tooltip": "Verification checks: proof validity, integrity, expiry, revocation status",
        "gemini_usage": None
    },
    {
        "step": 5,
        "title": "Download Artifact",
        "description": "Download attestation as JSON or OSCAL format",
        "endpoint": "/api/v1/attestations/{claim_id}/download",
        "method": "GET",
        "example_payload": None,
        "tooltip": "Downloadable artifact includes all proof data for audit trail",
        "gemini_usage": None
    }
]


@router.get("/status", response_model=JudgeModeStatus)
async def get_judge_mode_status():
    """
    Get current judge mode status
    
    Returns configuration for UI to adjust behavior
    """
    return JudgeModeStatus(
        enabled=settings.JUDGE_MODE,
        fast_responses=settings.JUDGE_MODE_FAST_RESPONSES,
        mock_anchor=settings.JUDGE_MODE_MOCK_ANCHOR,
        demo_mode=settings.DEMO_MODE
    )


@router.post("/enable", response_model=dict)
async def enable_judge_mode():
    """
    Enable judge mode with all optimizations
    
    Sets:
    - JUDGE_MODE = True
    - JUDGE_MODE_FAST_RESPONSES = True
    - JUDGE_MODE_MOCK_ANCHOR = True
    """
    # Enable judge mode settings
    settings.JUDGE_MODE = True
    settings.JUDGE_MODE_FAST_RESPONSES = True
    settings.JUDGE_MODE_MOCK_ANCHOR = True
    
    return {
        "message": "Judge mode enabled",
        "settings": {
            "judge_mode": settings.JUDGE_MODE,
            "fast_responses": settings.JUDGE_MODE_FAST_RESPONSES,
            "mock_anchor": settings.JUDGE_MODE_MOCK_ANCHOR
        },
        "optimizations": [
            "✅ Fast responses (<2 seconds)",
            "✅ Mock blockchain anchoring (instant)",
            "✅ Guided demo flow available",
            "✅ Gemini usage tooltips enabled"
        ],
        "guided_flow_url": "/api/v1/judge/guided-flow"
    }


@router.post("/disable", response_model=dict)
async def disable_judge_mode():
    """
    Disable judge mode and return to normal operation
    """
    settings.JUDGE_MODE = False
    settings.JUDGE_MODE_FAST_RESPONSES = False
    settings.JUDGE_MODE_MOCK_ANCHOR = False
    
    return {
        "message": "Judge mode disabled",
        "settings": {
            "judge_mode": settings.JUDGE_MODE,
            "fast_responses": settings.JUDGE_MODE_FAST_RESPONSES,
            "mock_anchor": settings.JUDGE_MODE_MOCK_ANCHOR
        }
    }


@router.get("/guided-flow", response_model=dict)
async def get_guided_flow():
    """
    Get guided demo flow for judges
    
    Returns step-by-step instructions with tooltips and Gemini usage info
    """
    return {
        "title": "ZKP Attestation Agent - Guided Demo",
        "description": "Complete attestation flow in 5 steps (~90 seconds)",
        "total_steps": len(GUIDED_FLOW),
        "estimated_time": "90 seconds",
        "steps": GUIDED_FLOW,
        "tips": [
            "All steps use sample controls - no manual input required",
            "Gemini 3 automatically interprets controls and selects proof templates",
            "Privacy preserved - evidence never exposed in proofs",
            "Download artifacts for audit trail"
        ],
        "judge_mode_active": settings.JUDGE_MODE
    }


@router.get("/stats", response_model=dict)
async def get_judge_mode_stats():
    """
    Get judge mode statistics
    
    Shows recent activity and performance
    """
    stats = memory_store.get_stats()
    
    # Get recent attestations (last 10)
    all_attestations = memory_store.list_attestations()
    recent = sorted(
        all_attestations,
        key=lambda x: x.get("created_at", ""),
        reverse=True
    )[:10]
    
    return {
        "judge_mode_enabled": settings.JUDGE_MODE,
        "total_attestations": stats.get("attestations_count", 0),
        "total_verifications": stats.get("verifications_count", 0),
        "recent_attestations": [
            {
                "claim_id": a.get("claim_id"),
                "status": a.get("status"),
                "framework": a.get("control_info", {}).get("framework"),
                "control_id": a.get("control_info", {}).get("control_id"),
                "created_at": a.get("created_at")
            }
            for a in recent
        ],
        "performance": {
            "fast_responses": settings.JUDGE_MODE_FAST_RESPONSES,
            "mock_anchor": settings.JUDGE_MODE_MOCK_ANCHOR,
            "avg_response_time": "<2s" if settings.JUDGE_MODE_FAST_RESPONSES else "3-5s"
        }
    }


@router.post("/reset", response_model=dict)
async def reset_demo_data():
    """
    Reset demo data for fresh judge demo
    
    Clears all attestations and verifications
    """
    memory_store.clear_all()
    
    return {
        "message": "Demo data reset successfully",
        "stats": memory_store.get_stats(),
        "ready_for_demo": True
    }

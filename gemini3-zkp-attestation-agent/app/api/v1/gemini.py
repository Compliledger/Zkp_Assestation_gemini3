"""
Gemini 3 AI Integration API
Control interpretation and proof template selection
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.services.gemini_service import get_gemini_service, ControlInterpretation, ProofTemplate

router = APIRouter()


class InterpretRequest(BaseModel):
    """Request to interpret a control"""
    control_statement: str
    framework: str
    control_id: Optional[str] = None


class InterpretResponse(BaseModel):
    """Response from control interpretation"""
    interpretation: ControlInterpretation
    gemini_available: bool
    message: str


@router.post("/interpret", response_model=InterpretResponse)
async def interpret_control(request: InterpretRequest):
    """
    Interpret compliance control using Gemini 3 AI
    
    Uses AI to determine:
    - Claim type (what kind of assertion)
    - Proof template (optimal ZKP method)
    - Evidence requirements (what's needed)
    - Risk level (criticality)
    
    Falls back to rule-based interpretation if Gemini API unavailable.
    
    Example:
    ```
    POST /api/v1/gemini/interpret
    {
      "control_statement": "The organization manages user accounts...",
      "framework": "NIST 800-53",
      "control_id": "AC-2"
    }
    ```
    """
    gemini_service = get_gemini_service()
    
    try:
        interpretation = await gemini_service.interpret_control(
            control_statement=request.control_statement,
            framework=request.framework,
            control_id=request.control_id
        )
        
        message = "✨ Control interpreted successfully"
        if interpretation.interpreted_by == "rule-based-fallback":
            message += " (using rule-based fallback - add GEMINI_API_KEY for AI interpretation)"
        else:
            message += f" (using {interpretation.interpreted_by})"
        
        return InterpretResponse(
            interpretation=interpretation,
            gemini_available=gemini_service.use_real_api,
            message=message
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Control interpretation failed: {str(e)}"
        )


@router.get("/templates", response_model=dict)
async def get_proof_templates():
    """
    Get all available proof templates with descriptions
    
    Returns information about:
    - Merkle commitment (data integrity)
    - ZK predicate (conditional proofs)
    - Signature chain (audit trails)
    
    Each template includes:
    - Description
    - Use cases
    - Complexity level
    - Privacy level
    """
    gemini_service = get_gemini_service()
    templates = gemini_service.get_all_templates()
    
    return {
        "templates": [template.dict() for template in templates],
        "count": len(templates),
        "message": "Available zero-knowledge proof templates"
    }


@router.post("/select-template", response_model=dict)
async def select_proof_template(
    claim_type: str,
    risk_level: str,
    data_sensitivity: str = "medium"
):
    """
    Select optimal proof template based on requirements
    
    Parameters:
    - claim_type: evidence_integrity, control_effectiveness, or audit_trail
    - risk_level: high, medium, or low
    - data_sensitivity: high, medium, or low
    
    Returns recommended proof template with reasoning.
    """
    gemini_service = get_gemini_service()
    
    try:
        template = await gemini_service.select_proof_template(
            claim_type=claim_type,
            risk_level=risk_level,
            data_sensitivity=data_sensitivity
        )
        
        return {
            "recommended_template": template.dict(),
            "reasoning": f"Selected {template.name} for {claim_type} claims with {risk_level} risk level",
            "privacy_level": template.privacy_level,
            "complexity": template.complexity
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Template selection failed: {str(e)}"
        )


@router.get("/status", response_model=dict)
async def get_gemini_status():
    """
    Get Gemini integration status
    
    Shows whether real Gemini API is available or using fallback.
    """
    gemini_service = get_gemini_service()
    
    return {
        "gemini_available": gemini_service.use_real_api,
        "mode": "gemini-api" if gemini_service.use_real_api else "rule-based-fallback",
        "message": "Gemini API active" if gemini_service.use_real_api else "Using rule-based interpretation (add GEMINI_API_KEY for AI)",
        "api_key_configured": bool(gemini_service.api_key),
        "capabilities": [
            "Control interpretation",
            "Proof template selection",
            "Risk assessment",
            "Evidence requirement analysis"
        ]
    }


@router.post("/batch-interpret", response_model=dict)
async def batch_interpret_controls(controls: List[InterpretRequest]):
    """
    Interpret multiple controls in batch
    
    Useful for processing entire frameworks or control sets.
    """
    gemini_service = get_gemini_service()
    results = []
    
    for control in controls:
        try:
            interpretation = await gemini_service.interpret_control(
                control_statement=control.control_statement,
                framework=control.framework,
                control_id=control.control_id
            )
            results.append({
                "control_id": control.control_id,
                "framework": control.framework,
                "interpretation": interpretation.dict(),
                "status": "success"
            })
        except Exception as e:
            results.append({
                "control_id": control.control_id,
                "framework": control.framework,
                "error": str(e),
                "status": "failed"
            })
    
    return {
        "total": len(controls),
        "successful": sum(1 for r in results if r["status"] == "success"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
        "results": results
    }

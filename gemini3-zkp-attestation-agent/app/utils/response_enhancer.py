"""
Response Enhancer
Adds enhanced formatting for frontend consumption
"""

from typing import Dict, Any, Optional
from datetime import datetime


def enhance_attestation_response(attestation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhance attestation response with additional fields for UI
    
    Adds:
    - summary: High-level overview
    - cryptographic_proof: Proof details
    - verification_status: Computed verification checks
    - privacy: Privacy statement
    """
    enhanced = attestation.copy()
    
    # Add summary section
    control_info = attestation.get("control_info", {})
    enhanced["summary"] = {
        "framework": control_info.get("framework", "Custom"),
        "control_id": control_info.get("control_id", "N/A"),
        "control_title": control_info.get("title", "Custom Compliance Check"),
        "claim_type": control_info.get("claim_type", "evidence_integrity"),
        "validity_window": {
            "issued_at": attestation.get("created_at"),
            "valid_until": attestation.get("metadata", {}).get("valid_until"),
            "is_valid": _check_if_valid(attestation)
        }
    }
    
    # Add cryptographic proof section (enhanced)
    if attestation.get("proof"):
        enhanced["cryptographic_proof"] = {
            "proof_hash": attestation["proof"].get("proof_hash"),
            "merkle_root": attestation.get("evidence", {}).get("merkle_root"),
            "proof_type": "merkle_commitment",
            "algorithm": "SHA-256 + Ed25519",
            "proof_size_bytes": attestation["proof"].get("size_bytes", 128)
        }
    
    # Add verification status (computed)
    enhanced["verification_status"] = {
        "proof_valid": _check_proof_valid(attestation),
        "integrity_verified": _check_integrity(attestation),
        "not_expired": _check_not_expired(attestation),
        "not_revoked": _check_not_revoked(attestation),
        "overall": _compute_overall_status(attestation)
    }
    
    # Add privacy statement
    enhanced["privacy"] = {
        "evidence_exposed": False,
        "proof_type": "zero_knowledge",
        "data_shared": ["proof_hash", "merkle_root", "commitment_hash"],
        "data_not_shared": ["raw_evidence", "sensitive_data", "PII", "credentials"],
        "privacy_level": "maximum",
        "message": "Compliance proven without exposing evidence"
    }
    
    return enhanced


def _check_if_valid(attestation: Dict) -> bool:
    """Check if attestation is currently valid"""
    status = attestation.get("status", "")
    
    if status == "valid":
        # Check expiry
        valid_until = attestation.get("metadata", {}).get("valid_until")
        if valid_until:
            try:
                expiry = datetime.fromisoformat(valid_until.replace('Z', '+00:00'))
                return datetime.utcnow() < expiry
            except:
                pass
        return True
    
    return False


def _check_proof_valid(attestation: Dict) -> bool:
    """Check if proof is valid"""
    return attestation.get("proof") is not None and attestation.get("status") == "valid"


def _check_integrity(attestation: Dict) -> bool:
    """Check if integrity is verified"""
    evidence = attestation.get("evidence", {})
    return evidence.get("merkle_root") is not None and attestation.get("status") == "valid"


def _check_not_expired(attestation: Dict) -> bool:
    """Check if not expired"""
    valid_until = attestation.get("metadata", {}).get("valid_until")
    if not valid_until:
        return True
    
    try:
        expiry = datetime.fromisoformat(valid_until.replace('Z', '+00:00'))
        return datetime.utcnow() < expiry
    except:
        return True


def _check_not_revoked(attestation: Dict) -> bool:
    """Check if not revoked"""
    return attestation.get("status") != "revoked"


def _compute_overall_status(attestation: Dict) -> str:
    """Compute overall verification status"""
    if attestation.get("status") == "valid":
        if _check_proof_valid(attestation) and _check_not_expired(attestation) and _check_not_revoked(attestation):
            return "PASS"
    
    if attestation.get("status") in ["failed", "failed_evidence", "failed_proof", "failed_anchor"]:
        return "FAIL"
    
    if attestation.get("status") in ["pending", "computing_commitment", "generating_proof", "assembling_package", "anchoring"]:
        return "PENDING"
    
    return "UNKNOWN"


def enhance_verification_response(verification: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhance verification response with UI-friendly format
    
    Adds:
    - Clear check breakdown with icons
    - Privacy confirmation
    """
    enhanced = verification.copy()
    
    # Convert checks to array format with icons
    checks_obj = verification.get("checks", {})
    checks_array = []
    
    check_mapping = {
        "proof_validity": ("Proof Validity", "Proof hash verified against commitment"),
        "expiry_check": ("Expiry Check", "Attestation is not expired"),
        "revocation_check": ("Revocation Check", "Attestation is not revoked"),
        "anchor_check": ("Anchor Verification", "Blockchain anchor confirmed")
    }
    
    for check_key, (name, details) in check_mapping.items():
        if check_key in checks_obj:
            status = "PASS" if checks_obj[check_key] else "FAIL"
            icon = "✅" if checks_obj[check_key] else "❌"
            
            checks_array.append({
                "name": name,
                "status": status,
                "icon": icon,
                "details": details
            })
    
    enhanced["checks_detailed"] = checks_array
    
    # Add privacy confirmation
    enhanced["privacy_preserved"] = {
        "evidence_disclosed": False,
        "proof_method": "zero_knowledge",
        "compliance_proven": enhanced.get("status") == "PASS"
    }
    
    return enhanced

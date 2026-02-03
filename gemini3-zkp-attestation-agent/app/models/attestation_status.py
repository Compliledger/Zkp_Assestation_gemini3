"""
Attestation Status Lifecycle
Defines valid states and transitions for attestation processing
"""

from enum import Enum
from typing import Dict, List


class AttestationStatus(str, Enum):
    """
    Attestation lifecycle states
    
    Processing Flow:
    pending → ingesting_evidence → computing_commitment → generating_proof 
    → assembling_package → anchoring → valid
    
    Terminal States: valid, failed_*, revoked, expired
    """
    
    # Active processing states
    PENDING = "pending"
    INGESTING_EVIDENCE = "ingesting_evidence"
    COMPUTING_COMMITMENT = "computing_commitment"
    GENERATING_PROOF = "generating_proof"
    ASSEMBLING_PACKAGE = "assembling_package"
    ANCHORING = "anchoring"
    
    # Success state
    VALID = "valid"
    
    # Terminal failure states
    FAILED_EVIDENCE = "failed_evidence"
    FAILED_PROOF = "failed_proof"
    FAILED_ANCHOR = "failed_anchor"
    FAILED = "failed"
    
    # Other terminal states
    REVOKED = "revoked"
    EXPIRED = "expired"


# Valid state transitions
VALID_TRANSITIONS: Dict[AttestationStatus, List[AttestationStatus]] = {
    AttestationStatus.PENDING: [
        AttestationStatus.INGESTING_EVIDENCE,
        AttestationStatus.FAILED
    ],
    AttestationStatus.INGESTING_EVIDENCE: [
        AttestationStatus.COMPUTING_COMMITMENT,
        AttestationStatus.FAILED_EVIDENCE
    ],
    AttestationStatus.COMPUTING_COMMITMENT: [
        AttestationStatus.GENERATING_PROOF,
        AttestationStatus.FAILED_EVIDENCE
    ],
    AttestationStatus.GENERATING_PROOF: [
        AttestationStatus.ASSEMBLING_PACKAGE,
        AttestationStatus.FAILED_PROOF
    ],
    AttestationStatus.ASSEMBLING_PACKAGE: [
        AttestationStatus.ANCHORING,
        AttestationStatus.VALID,  # Can skip anchoring
        AttestationStatus.FAILED_PROOF
    ],
    AttestationStatus.ANCHORING: [
        AttestationStatus.VALID,
        AttestationStatus.FAILED_ANCHOR
    ],
    AttestationStatus.VALID: [
        AttestationStatus.REVOKED,
        AttestationStatus.EXPIRED
    ],
}


def is_valid_transition(current: AttestationStatus, new: AttestationStatus) -> bool:
    """
    Check if state transition is valid
    
    Args:
        current: Current attestation status
        new: New status to transition to
        
    Returns:
        True if transition is allowed
    """
    valid_next_states = VALID_TRANSITIONS.get(current, [])
    return new in valid_next_states


def is_terminal_state(status: AttestationStatus) -> bool:
    """
    Check if status is a terminal state (no further transitions)
    
    Args:
        status: Attestation status to check
        
    Returns:
        True if status is terminal
    """
    terminal_states = {
        AttestationStatus.VALID,
        AttestationStatus.FAILED_EVIDENCE,
        AttestationStatus.FAILED_PROOF,
        AttestationStatus.FAILED_ANCHOR,
        AttestationStatus.FAILED,
        AttestationStatus.REVOKED,
        AttestationStatus.EXPIRED
    }
    return status in terminal_states


def is_failure_state(status: AttestationStatus) -> bool:
    """
    Check if status represents a failure
    
    Args:
        status: Attestation status to check
        
    Returns:
        True if status is a failure state
    """
    failure_states = {
        AttestationStatus.FAILED_EVIDENCE,
        AttestationStatus.FAILED_PROOF,
        AttestationStatus.FAILED_ANCHOR,
        AttestationStatus.FAILED
    }
    return status in failure_states

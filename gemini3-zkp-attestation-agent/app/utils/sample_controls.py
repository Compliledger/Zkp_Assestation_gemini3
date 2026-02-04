"""
Sample Controls for Quick Demo
Pre-defined compliance controls for 1-click attestation demos
"""

from typing import List, Dict, Optional
from pydantic import BaseModel


class SampleControl(BaseModel):
    """Sample compliance control"""
    control_id: str
    framework: str
    title: str
    statement: str
    claim_type: str
    proof_template: str
    evidence_count: int
    risk_level: str
    description: str


# Pre-defined sample controls for major compliance frameworks
SAMPLE_CONTROLS: List[Dict] = [
    {
        "control_id": "AC-2",
        "framework": "NIST 800-53",
        "title": "Account Management",
        "statement": "The organization manages information system accounts, including establishing, activating, modifying, reviewing, disabling, and removing accounts. The organization reviews information system accounts at least annually.",
        "claim_type": "control_effectiveness",
        "proof_template": "merkle_commitment",
        "evidence_count": 5,
        "risk_level": "high",
        "description": "Account management controls ensure proper user access lifecycle management"
    },
    {
        "control_id": "CC6.1",
        "framework": "SOC 2",
        "title": "Logical and Physical Access Controls",
        "statement": "The entity implements logical access security software, infrastructure, and architectures over protected information assets to protect them from security events to meet the entity's objectives.",
        "claim_type": "evidence_integrity",
        "proof_template": "merkle_commitment",
        "evidence_count": 4,
        "risk_level": "high",
        "description": "Logical access controls protect systems from unauthorized access"
    },
    {
        "control_id": "A.5.15",
        "framework": "ISO 27001",
        "title": "Access Control",
        "statement": "Rules for the effective control of access to information and associated assets, including authorization process, access rights, and access control to networks and networked services shall be established, documented and reviewed.",
        "claim_type": "control_effectiveness",
        "proof_template": "merkle_commitment",
        "evidence_count": 3,
        "risk_level": "high",
        "description": "Access control policy ensures proper authorization and authentication"
    },
    {
        "control_id": "AC-3",
        "framework": "NIST 800-53",
        "title": "Access Enforcement",
        "statement": "The information system enforces approved authorizations for logical access to information and system resources in accordance with applicable access control policies.",
        "claim_type": "control_effectiveness",
        "proof_template": "merkle_commitment",
        "evidence_count": 4,
        "risk_level": "high",
        "description": "Access enforcement ensures only authorized users can access resources"
    },
    {
        "control_id": "CC6.6",
        "framework": "SOC 2",
        "title": "Logical Access - Removal",
        "statement": "The entity discontinues logical and physical protections over physical assets only after the ability to read or recover data and software from those assets has been diminished and is no longer required to meet the entity's objectives.",
        "claim_type": "evidence_integrity",
        "proof_template": "merkle_commitment",
        "evidence_count": 3,
        "risk_level": "medium",
        "description": "Ensures proper removal of access when no longer needed"
    },
    {
        "control_id": "A.9.2.1",
        "framework": "ISO 27001",
        "title": "User Registration and De-registration",
        "statement": "A formal user registration and de-registration process shall be implemented to enable assignment of access rights.",
        "claim_type": "control_effectiveness",
        "proof_template": "merkle_commitment",
        "evidence_count": 4,
        "risk_level": "medium",
        "description": "User lifecycle management from registration to deregistration"
    },
    {
        "control_id": "AU-2",
        "framework": "NIST 800-53",
        "title": "Audit Events",
        "statement": "The organization determines that the information system is capable of auditing specific events; coordinates the security audit function with other organizational entities; provides a rationale for why the auditable events are deemed to be adequate; and determines that the events are to be audited within the information system.",
        "claim_type": "audit_trail",
        "proof_template": "merkle_commitment",
        "evidence_count": 5,
        "risk_level": "high",
        "description": "Audit logging captures security-relevant events"
    },
    {
        "control_id": "CC7.2",
        "framework": "SOC 2",
        "title": "System Monitoring",
        "statement": "The entity monitors system components and the operation of those components for anomalies that are indicative of malicious acts, natural disasters, and errors affecting the entity's ability to meet its objectives.",
        "claim_type": "audit_trail",
        "proof_template": "merkle_commitment",
        "evidence_count": 4,
        "risk_level": "high",
        "description": "Continuous monitoring detects security events and anomalies"
    },
    {
        "control_id": "164.308(a)(1)(ii)(D)",
        "framework": "HIPAA",
        "title": "Information System Activity Review",
        "statement": "Implement procedures to regularly review records of information system activity, such as audit logs, access reports, and security incident tracking reports.",
        "claim_type": "audit_trail",
        "proof_template": "merkle_commitment",
        "evidence_count": 4,
        "risk_level": "high",
        "description": "Regular review of system activity for HIPAA compliance"
    },
    {
        "control_id": "PCI-10.2",
        "framework": "PCI-DSS",
        "title": "Audit Trail Implementation",
        "statement": "Implement automated audit trails for all system components to reconstruct events including all access to cardholder data, actions by individuals with root or administrative privileges, access to audit trails, and invalid logical access attempts.",
        "claim_type": "audit_trail",
        "proof_template": "merkle_commitment",
        "evidence_count": 5,
        "risk_level": "high",
        "description": "Comprehensive audit trails for payment card security"
    }
]


# Framework information
FRAMEWORKS = {
    "NIST 800-53": {
        "name": "NIST 800-53",
        "full_name": "NIST Special Publication 800-53",
        "description": "Security and Privacy Controls for Information Systems and Organizations",
        "control_count": 3,
        "url": "https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final"
    },
    "SOC 2": {
        "name": "SOC 2",
        "full_name": "Service Organization Control 2",
        "description": "Trust Services Criteria for Security, Availability, and Confidentiality",
        "control_count": 3,
        "url": "https://www.aicpa.org/soc"
    },
    "ISO 27001": {
        "name": "ISO 27001",
        "full_name": "ISO/IEC 27001:2013",
        "description": "Information Security Management Systems Requirements",
        "control_count": 2,
        "url": "https://www.iso.org/standard/54534.html"
    },
    "HIPAA": {
        "name": "HIPAA",
        "full_name": "Health Insurance Portability and Accountability Act",
        "description": "Security Rule for Protected Health Information",
        "control_count": 1,
        "url": "https://www.hhs.gov/hipaa"
    },
    "PCI-DSS": {
        "name": "PCI-DSS",
        "full_name": "Payment Card Industry Data Security Standard",
        "description": "Security Standards for Payment Card Processing",
        "control_count": 1,
        "url": "https://www.pcisecuritystandards.org"
    }
}


def get_all_controls() -> List[SampleControl]:
    """Get all sample controls"""
    return [SampleControl(**control) for control in SAMPLE_CONTROLS]


def get_control_by_id(control_id: str) -> Optional[SampleControl]:
    """Get specific control by ID"""
    for control in SAMPLE_CONTROLS:
        if control["control_id"] == control_id:
            return SampleControl(**control)
    return None


def get_controls_by_framework(framework: str) -> List[SampleControl]:
    """Get all controls for a specific framework"""
    return [
        SampleControl(**control)
        for control in SAMPLE_CONTROLS
        if control["framework"] == framework
    ]


def get_all_frameworks() -> Dict:
    """Get all supported frameworks with metadata"""
    return FRAMEWORKS


def search_controls(query: str) -> List[SampleControl]:
    """Search controls by query string"""
    query_lower = query.lower()
    results = []
    
    for control in SAMPLE_CONTROLS:
        if (query_lower in control["control_id"].lower() or
            query_lower in control["title"].lower() or
            query_lower in control["statement"].lower() or
            query_lower in control["framework"].lower()):
            results.append(SampleControl(**control))
    
    return results

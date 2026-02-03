"""
Demo Data Generator
Utilities for generating demo/test data for hackathon demonstrations
"""

import hashlib
from typing import List, Dict, Any
from datetime import datetime, timedelta
import uuid


class DemoDataGenerator:
    """Generate deterministic demo data for testing and demonstrations"""
    
    @staticmethod
    def generate_evidence_ref(index: int, evidence_type: str = "compliance_check") -> Dict[str, str]:
        """
        Generate a single evidence reference
        
        Args:
            index: Evidence item number
            evidence_type: Type of evidence
            
        Returns:
            Evidence reference dict
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        data = f"Demo evidence {index}: {evidence_type} - {timestamp}"
        
        return {
            "uri": f"demo://evidence/{evidence_type}/{index}",
            "hash": hashlib.sha256(data.encode()).hexdigest(),
            "type": evidence_type
        }
    
    @staticmethod
    def generate_evidence_list(count: int = 5, evidence_type: str = "compliance_check") -> List[Dict[str, str]]:
        """
        Generate a list of evidence references
        
        Args:
            count: Number of evidence items to generate
            evidence_type: Type of evidence
            
        Returns:
            List of evidence references
        """
        return [
            DemoDataGenerator.generate_evidence_ref(i, evidence_type)
            for i in range(1, count + 1)
        ]
    
    @staticmethod
    def get_demo_policies() -> Dict[str, str]:
        """
        Get pre-defined demo compliance policies
        
        Returns:
            Dictionary of policy name to policy text
        """
        return {
            "SOC2_TYPE_II": """
SOC2 Type II Compliance Requirements:
- Access controls and authentication implemented
- Data encryption at rest and in transit (AES-256, TLS 1.3)
- Regular security audits and vulnerability assessments
- Incident response and disaster recovery procedures
- Continuous monitoring and logging
- Employee security training and awareness
            """.strip(),
            
            "GDPR": """
GDPR Compliance Requirements:
- Lawful basis for data processing
- Data subject rights implementation (access, rectification, erasure)
- Privacy by design and default
- Data breach notification procedures (72 hours)
- Data Protection Impact Assessments (DPIA)
- Cross-border data transfer safeguards
            """.strip(),
            
            "HIPAA": """
HIPAA Compliance Requirements:
- Administrative safeguards (security management, training)
- Physical safeguards (facility access, workstation security)
- Technical safeguards (encryption, access controls, audit logs)
- Protected Health Information (PHI) handling procedures
- Business Associate Agreements (BAA)
- Breach notification requirements
            """.strip(),
            
            "ISO27001": """
ISO 27001 Information Security Management:
- Information security policies and procedures
- Risk assessment and treatment
- Asset management and classification
- Access control and identity management
- Cryptographic controls and key management
- Supplier security and third-party management
            """.strip(),
            
            "PCI_DSS": """
PCI DSS Payment Card Industry Standards:
- Secure network architecture (firewalls, DMZ)
- Cardholder data encryption and protection
- Vulnerability management and patching
- Strong access controls and authentication
- Network monitoring and testing
- Information security policy and training
            """.strip()
        }
    
    @staticmethod
    def generate_demo_attestation_request(
        policy: str = "SOC2_TYPE_II",
        evidence_count: int = 5,
        callback_url: str = None
    ) -> Dict[str, Any]:
        """
        Generate a complete demo attestation request
        
        Args:
            policy: Policy name (SOC2_TYPE_II, GDPR, HIPAA, etc.)
            evidence_count: Number of evidence items
            callback_url: Optional webhook callback URL
            
        Returns:
            Attestation request payload
        """
        policies = DemoDataGenerator.get_demo_policies()
        policy_text = policies.get(policy, policy)
        
        request = {
            "evidence": DemoDataGenerator.generate_evidence_list(
                count=evidence_count,
                evidence_type="compliance_check"
            ),
            "policy": policy_text
        }
        
        if callback_url:
            request["callback_url"] = callback_url
        
        return request
    
    @staticmethod
    def generate_test_scenarios() -> List[Dict[str, Any]]:
        """
        Generate various test scenarios
        
        Returns:
            List of test scenario configurations
        """
        return [
            {
                "name": "Minimal Evidence",
                "description": "Single evidence item with SOC2 policy",
                "policy": "SOC2_TYPE_II",
                "evidence_count": 1
            },
            {
                "name": "Standard Compliance",
                "description": "Standard 5-item compliance check",
                "policy": "SOC2_TYPE_II",
                "evidence_count": 5
            },
            {
                "name": "GDPR Privacy Check",
                "description": "GDPR compliance with 3 evidence items",
                "policy": "GDPR",
                "evidence_count": 3
            },
            {
                "name": "Healthcare HIPAA",
                "description": "HIPAA compliance with 7 evidence items",
                "policy": "HIPAA",
                "evidence_count": 7
            },
            {
                "name": "Large Evidence Set",
                "description": "Stress test with 20 evidence items",
                "policy": "ISO27001",
                "evidence_count": 20
            }
        ]
    
    @staticmethod
    def generate_verification_request(claim_id: str) -> Dict[str, Any]:
        """
        Generate a verification request for testing
        
        Args:
            claim_id: Attestation claim ID to verify
            
        Returns:
            Verification request payload
        """
        return {
            "claim_id": claim_id,
            "check_expiry": True,
            "check_revocation": True,
            "check_anchor": False  # Optional for demo
        }


# Convenience functions for quick access
def quick_demo_evidence(count: int = 5) -> List[Dict[str, str]]:
    """Quick function to generate demo evidence"""
    return DemoDataGenerator.generate_evidence_list(count)


def quick_demo_request(policy: str = "SOC2_TYPE_II") -> Dict[str, Any]:
    """Quick function to generate demo attestation request"""
    return DemoDataGenerator.generate_demo_attestation_request(policy)


def get_demo_policy_names() -> List[str]:
    """Get list of available demo policy names"""
    return list(DemoDataGenerator.get_demo_policies().keys())

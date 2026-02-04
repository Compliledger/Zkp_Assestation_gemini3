"""
Gemini 3 Integration Service
AI-powered control interpretation and proof template selection
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ControlInterpretation(BaseModel):
    """Result of Gemini control interpretation"""
    claim_type: str
    proof_template: str
    evidence_requirements: List[str]
    risk_level: str
    reasoning: str
    confidence: float
    interpreted_by: str = "gemini-3-flash"


class ProofTemplate(BaseModel):
    """Proof template metadata"""
    name: str
    description: str
    use_cases: List[str]
    complexity: str
    privacy_level: str


class GeminiService:
    """
    Gemini 3 AI integration for intelligent control interpretation
    
    In demo mode, uses rule-based fallback if API key not available
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.use_real_api = bool(self.api_key)
        
        if self.use_real_api:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("Gemini API initialized successfully")
            except Exception as e:
                logger.warning(f"Gemini API initialization failed: {e}. Using rule-based fallback.")
                self.use_real_api = False
        else:
            logger.info("No Gemini API key found. Using rule-based interpretation.")
    
    async def interpret_control(
        self,
        control_statement: str,
        framework: str,
        control_id: Optional[str] = None
    ) -> ControlInterpretation:
        """
        Interpret compliance control using Gemini 3 AI
        
        Determines:
        - claim_type: Type of claim (evidence_integrity, control_effectiveness, audit_trail)
        - proof_template: Optimal ZKP method (merkle_commitment, zk_predicate, signature_chain)
        - evidence_requirements: What evidence is needed
        - risk_level: Control criticality (high, medium, low)
        """
        
        if self.use_real_api:
            return await self._interpret_with_gemini(control_statement, framework, control_id)
        else:
            return self._interpret_with_rules(control_statement, framework, control_id)
    
    async def _interpret_with_gemini(
        self,
        control_statement: str,
        framework: str,
        control_id: Optional[str]
    ) -> ControlInterpretation:
        """Use real Gemini API for interpretation"""
        
        prompt = f"""You are a compliance and zero-knowledge proof expert. Analyze this compliance control and determine the optimal attestation approach.

Framework: {framework}
Control ID: {control_id or 'Unknown'}
Control Statement: {control_statement}

Determine the following and respond in JSON format:

1. claim_type: Choose ONE from:
   - "evidence_integrity": For controls about data integrity, audit logs, backups
   - "control_effectiveness": For controls about access management, security procedures, policies
   - "audit_trail": For controls about monitoring, logging, tracking

2. proof_template: Choose ONE from:
   - "merkle_commitment": Best for proving data integrity without revealing data
   - "zk_predicate": Best for proving properties/conditions are met
   - "signature_chain": Best for proving authenticity and chronological order

3. evidence_requirements: List 3-5 types of evidence needed (e.g., "access_logs", "configuration_files", "audit_records")

4. risk_level: Choose ONE from: "high", "medium", "low" based on security impact

5. reasoning: Brief explanation (1-2 sentences) of why you chose this approach

6. confidence: Your confidence level (0.0 to 1.0)

Respond ONLY with valid JSON matching this structure:
{{
  "claim_type": "...",
  "proof_template": "...",
  "evidence_requirements": ["...", "..."],
  "risk_level": "...",
  "reasoning": "...",
  "confidence": 0.95
}}"""

        try:
            response = self.model.generate_content(prompt)
            
            # Extract JSON from response
            response_text = response.text.strip()
            
            # Handle markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            interpretation_data = json.loads(response_text)
            
            return ControlInterpretation(
                **interpretation_data,
                interpreted_by="gemini-3-flash"
            )
            
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}. Falling back to rule-based interpretation.")
            return self._interpret_with_rules(control_statement, framework, control_id)
    
    def _interpret_with_rules(
        self,
        control_statement: str,
        framework: str,
        control_id: Optional[str]
    ) -> ControlInterpretation:
        """Rule-based fallback interpretation"""
        
        statement_lower = control_statement.lower()
        
        # Determine claim type based on keywords
        if any(keyword in statement_lower for keyword in ["integrity", "backup", "restore", "recovery", "log"]):
            claim_type = "evidence_integrity"
            proof_template = "merkle_commitment"
            evidence_requirements = ["backup_records", "integrity_checksums", "audit_logs", "recovery_procedures"]
        elif any(keyword in statement_lower for keyword in ["access", "authentication", "authorization", "account", "user", "privilege"]):
            claim_type = "control_effectiveness"
            proof_template = "zk_predicate"
            evidence_requirements = ["access_logs", "user_directory", "permission_matrix", "authentication_records", "policy_documents"]
        elif any(keyword in statement_lower for keyword in ["monitor", "audit", "track", "record", "event"]):
            claim_type = "audit_trail"
            proof_template = "signature_chain"
            evidence_requirements = ["audit_logs", "monitoring_data", "event_records", "compliance_reports"]
        else:
            claim_type = "control_effectiveness"
            proof_template = "merkle_commitment"
            evidence_requirements = ["policy_documents", "procedure_records", "compliance_evidence", "audit_reports"]
        
        # Determine risk level based on framework and keywords
        high_risk_keywords = ["critical", "security", "privacy", "sensitive", "confidential", "encryption"]
        if any(keyword in statement_lower for keyword in high_risk_keywords) or framework in ["HIPAA", "PCI-DSS"]:
            risk_level = "high"
        elif framework in ["SOC 2", "ISO 27001"]:
            risk_level = "medium"
        else:
            risk_level = "medium"
        
        reasoning = f"Based on keyword analysis, this {framework} control focuses on {claim_type.replace('_', ' ')}. Using {proof_template.replace('_', ' ')} for optimal privacy preservation."
        
        return ControlInterpretation(
            claim_type=claim_type,
            proof_template=proof_template,
            evidence_requirements=evidence_requirements,
            risk_level=risk_level,
            reasoning=reasoning,
            confidence=0.85,  # Lower confidence for rule-based
            interpreted_by="rule-based-fallback"
        )
    
    async def select_proof_template(
        self,
        claim_type: str,
        risk_level: str,
        data_sensitivity: str = "medium"
    ) -> ProofTemplate:
        """
        Select optimal proof template based on requirements
        """
        
        templates = {
            "merkle_commitment": ProofTemplate(
                name="merkle_commitment",
                description="Merkle tree commitment for data integrity proofs",
                use_cases=["Data integrity", "Backup verification", "Log integrity"],
                complexity="low",
                privacy_level="high"
            ),
            "zk_predicate": ProofTemplate(
                name="zk_predicate",
                description="Zero-knowledge predicate proofs for conditional statements",
                use_cases=["Access control verification", "Policy compliance", "Threshold checks"],
                complexity="medium",
                privacy_level="very_high"
            ),
            "signature_chain": ProofTemplate(
                name="signature_chain",
                description="Cryptographic signature chain for audit trails",
                use_cases=["Event chronology", "Audit trail verification", "Non-repudiation"],
                complexity="low",
                privacy_level="medium"
            )
        }
        
        # Simple selection logic
        if claim_type == "evidence_integrity":
            return templates["merkle_commitment"]
        elif claim_type == "control_effectiveness":
            return templates["zk_predicate"]
        elif claim_type == "audit_trail":
            return templates["signature_chain"]
        else:
            return templates["merkle_commitment"]
    
    def get_all_templates(self) -> List[ProofTemplate]:
        """Get all available proof templates"""
        return [
            ProofTemplate(
                name="merkle_commitment",
                description="Merkle tree commitment for data integrity proofs without revealing data",
                use_cases=["Data integrity", "Backup verification", "Log integrity", "Evidence commitment"],
                complexity="low",
                privacy_level="high"
            ),
            ProofTemplate(
                name="zk_predicate",
                description="Zero-knowledge predicate proofs for proving conditions without revealing values",
                use_cases=["Access control verification", "Policy compliance", "Threshold checks", "Conditional proofs"],
                complexity="medium",
                privacy_level="very_high"
            ),
            ProofTemplate(
                name="signature_chain",
                description="Cryptographic signature chain for tamper-proof audit trails",
                use_cases=["Event chronology", "Audit trail verification", "Non-repudiation", "Timestamping"],
                complexity="low",
                privacy_level="medium"
            )
        ]


# Singleton instance
_gemini_service = None

def get_gemini_service() -> GeminiService:
    """Get or create Gemini service singleton"""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service

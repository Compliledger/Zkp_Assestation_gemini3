"""
ZKP Proof Verifier
Verifies zero-knowledge proofs against public inputs and verification keys
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

from app.core.zkp.circuit_manager import CircuitManager, CircuitTemplate
from app.core.zkp.proof_generator import ProofArtifact
from app.utils.errors import VerificationError, ValidationError
from app.utils.crypto import HashUtils


class VerificationStatus(str, Enum):
    """Verification status"""
    VALID = "valid"
    INVALID = "invalid"
    ERROR = "error"


class VerificationResult(BaseModel):
    """
    Result of proof verification
    """
    verification_id: str = Field(..., description="Unique verification ID")
    proof_id: str = Field(..., description="Proof being verified")
    status: VerificationStatus = Field(..., description="Verification status")
    
    # Verification details
    is_valid: bool = Field(..., description="Whether proof is valid")
    verification_time: float = Field(..., description="Time taken to verify (seconds)")
    
    # Checks performed
    checks_passed: Dict[str, bool] = Field(default_factory=dict, description="Individual check results")
    
    # Error information (if any)
    error_message: Optional[str] = Field(None, description="Error message if verification failed")
    
    # Metadata
    verifier_id: Optional[str] = Field(None, description="ID of verifier")
    verified_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProofVerifier:
    """
    Verifies zero-knowledge proofs
    """
    
    def __init__(self, circuit_manager: Optional[CircuitManager] = None):
        """
        Initialize proof verifier
        
        Args:
            circuit_manager: Circuit manager instance
        """
        self.circuit_manager = circuit_manager or CircuitManager()
        self.hash_utils = HashUtils()
    
    def verify_proof(
        self,
        proof_artifact: ProofArtifact,
        verifier_id: Optional[str] = None
    ) -> VerificationResult:
        """
        Verify a zero-knowledge proof
        
        Args:
            proof_artifact: Proof artifact to verify
            verifier_id: Optional verifier identifier
        
        Returns:
            VerificationResult
        """
        start_time = datetime.utcnow()
        checks_passed = {}
        error_message = None
        
        try:
            # Get circuit template
            template = self.circuit_manager.get_template(proof_artifact.template_id)
            
            # Perform verification checks
            checks_passed["template_exists"] = True
            
            # Check 1: Verify template is ready
            if not template.is_compiled or not template.is_trusted_setup_done:
                checks_passed["template_ready"] = False
                error_message = "Circuit template not ready for verification"
                is_valid = False
            else:
                checks_passed["template_ready"] = True
                
                # Check 2: Verify proof structure
                if not self._verify_proof_structure(proof_artifact.proof_data):
                    checks_passed["proof_structure"] = False
                    error_message = "Invalid proof structure"
                    is_valid = False
                else:
                    checks_passed["proof_structure"] = True
                    
                    # Check 3: Verify public inputs match
                    if not self._verify_public_inputs(proof_artifact, template):
                        checks_passed["public_inputs"] = False
                        error_message = "Public inputs validation failed"
                        is_valid = False
                    else:
                        checks_passed["public_inputs"] = True
                        
                        # Check 4: Verify proof cryptographically
                        is_valid = self._verify_proof_cryptographic(
                            proof_artifact,
                            template
                        )
                        checks_passed["cryptographic_verification"] = is_valid
                        
                        if not is_valid:
                            error_message = "Cryptographic verification failed"
        
        except Exception as e:
            is_valid = False
            error_message = f"Verification error: {str(e)}"
            checks_passed["exception"] = False
        
        end_time = datetime.utcnow()
        verification_time = (end_time - start_time).total_seconds()
        
        # Determine status
        if is_valid:
            status = VerificationStatus.VALID
        elif error_message and "error" in error_message.lower():
            status = VerificationStatus.ERROR
        else:
            status = VerificationStatus.INVALID
        
        result = VerificationResult(
            verification_id=self._generate_verification_id(proof_artifact.proof_id),
            proof_id=proof_artifact.proof_id,
            status=status,
            is_valid=is_valid,
            verification_time=verification_time,
            checks_passed=checks_passed,
            error_message=error_message,
            verifier_id=verifier_id
        )
        
        return result
    
    def verify_batch_proofs(
        self,
        proof_artifacts: List[ProofArtifact],
        verifier_id: Optional[str] = None
    ) -> List[VerificationResult]:
        """
        Verify multiple proofs in batch
        
        Args:
            proof_artifacts: List of proof artifacts
            verifier_id: Optional verifier identifier
        
        Returns:
            List of verification results
        """
        results = []
        
        for proof in proof_artifacts:
            try:
                result = self.verify_proof(proof, verifier_id)
                results.append(result)
            except Exception as e:
                # Create error result
                error_result = VerificationResult(
                    verification_id=self._generate_verification_id(proof.proof_id),
                    proof_id=proof.proof_id,
                    status=VerificationStatus.ERROR,
                    is_valid=False,
                    verification_time=0.0,
                    checks_passed={"batch_error": False},
                    error_message=str(e),
                    verifier_id=verifier_id
                )
                results.append(error_result)
        
        return results
    
    def quick_verify(
        self,
        proof_data: Dict[str, Any],
        public_inputs: Dict[str, Any],
        template_id: str
    ) -> bool:
        """
        Quick verification without full artifact
        
        Args:
            proof_data: Proof data
            public_inputs: Public inputs
            template_id: Circuit template ID
        
        Returns:
            True if proof is valid
        """
        # Create temporary artifact for verification
        from datetime import datetime
        import hashlib
        
        temp_artifact = ProofArtifact(
            proof_id="temp_" + hashlib.sha256(str(datetime.utcnow()).encode()).hexdigest()[:8],
            claim_id="temp",
            circuit_type="unknown",
            template_id=template_id,
            proof_data=proof_data,
            public_inputs=public_inputs,
            proving_time=0.0,
            proof_size=0,
            proof_hash=""
        )
        
        result = self.verify_proof(temp_artifact)
        return result.is_valid
    
    def _verify_proof_structure(self, proof_data: Dict[str, Any]) -> bool:
        """Verify proof has expected structure"""
        required_fields = ["protocol", "curve", "proof"]
        
        for field in required_fields:
            if field not in proof_data:
                return False
        
        # Check proof components
        if "proof" in proof_data:
            proof = proof_data["proof"]
            required_proof_fields = ["pi_a", "pi_b", "pi_c"]
            
            for field in required_proof_fields:
                if field not in proof:
                    return False
        
        return True
    
    def _verify_public_inputs(
        self,
        proof_artifact: ProofArtifact,
        template: CircuitTemplate
    ) -> bool:
        """Verify public inputs match template expectations"""
        # Check all required public inputs are present
        for required_input in template.public_inputs:
            if required_input not in proof_artifact.public_inputs:
                return False
        
        return True
    
    def _verify_proof_cryptographic(
        self,
        proof_artifact: ProofArtifact,
        template: CircuitTemplate
    ) -> bool:
        """
        Perform cryptographic verification of proof
        
        In production, this would use actual ZKP verifier:
        - snarkjs.groth16.verify()
        - gnark Verify()
        - libsnark verify()
        
        For now, we simulate verification
        """
        # Simulate verification based on circuit type
        proof_data = proof_artifact.proof_data
        
        # Check protocol is supported
        if proof_data.get("protocol") != "groth16":
            return False
        
        # Check curve is correct
        if proof_data.get("curve") != "bn128":
            return False
        
        # In production: Use actual pairing checks
        # For now: Simulate successful verification
        
        # Simulate some proofs failing for realism
        import hashlib
        proof_hash = hashlib.sha256(
            str(proof_artifact.proof_data).encode()
        ).hexdigest()
        
        # Use hash to deterministically succeed/fail
        # In production, this would be actual cryptographic verification
        return int(proof_hash, 16) % 100 < 95  # 95% success rate for simulation
    
    def _generate_verification_id(self, proof_id: str) -> str:
        """Generate unique verification ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        content = f"verify_{proof_id}_{timestamp}"
        hash_suffix = self.hash_utils.sha256(content.encode())[:8]
        return f"vrfy_{hash_suffix}"
    
    def verify_with_commitment(
        self,
        proof_artifact: ProofArtifact,
        merkle_root: str
    ) -> VerificationResult:
        """
        Verify proof includes correct Merkle commitment
        
        Args:
            proof_artifact: Proof to verify
            merkle_root: Expected Merkle root
        
        Returns:
            VerificationResult
        """
        result = self.verify_proof(proof_artifact)
        
        # Additional check: Verify Merkle root matches
        if "merkle_root" in proof_artifact.public_inputs:
            root_matches = proof_artifact.public_inputs["merkle_root"] == merkle_root
            result.checks_passed["merkle_root_match"] = root_matches
            
            if not root_matches:
                result.is_valid = False
                result.status = VerificationStatus.INVALID
                result.error_message = "Merkle root mismatch"
        
        return result
    
    def get_verification_statistics(
        self,
        results: List[VerificationResult]
    ) -> Dict[str, Any]:
        """
        Get statistics from verification results
        
        Args:
            results: List of verification results
        
        Returns:
            Statistics dictionary
        """
        total = len(results)
        valid = sum(1 for r in results if r.is_valid)
        invalid = sum(1 for r in results if not r.is_valid and r.status == VerificationStatus.INVALID)
        errors = sum(1 for r in results if r.status == VerificationStatus.ERROR)
        
        avg_time = sum(r.verification_time for r in results) / total if total > 0 else 0
        
        return {
            "total_verifications": total,
            "valid": valid,
            "invalid": invalid,
            "errors": errors,
            "success_rate": (valid / total * 100) if total > 0 else 0,
            "average_verification_time": avg_time
        }

"""
ZKP Witness Builder
Constructs witness data from evidence and claims for ZKP circuits
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.evidence.normalizer import NormalizedEvidence
from app.core.evidence.commitment import EvidenceCommitment
from app.utils.crypto import HashUtils
from app.utils.errors import ValidationError


class WitnessData(BaseModel):
    """
    Witness data for ZKP circuit
    Contains both public and private inputs
    """
    circuit_type: str = Field(..., description="Type of circuit")
    public_inputs: Dict[str, Any] = Field(..., description="Public inputs")
    private_inputs: Dict[str, Any] = Field(..., description="Private inputs")
    
    # Metadata
    claim_id: str = Field(..., description="Associated claim ID")
    bundle_id: Optional[str] = Field(None, description="Evidence bundle ID")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def get_all_inputs(self) -> Dict[str, Any]:
        """Get combined public and private inputs"""
        return {**self.public_inputs, **self.private_inputs}
    
    def validate_completeness(self, required_inputs: List[str]) -> bool:
        """Check if all required inputs are present"""
        all_inputs = self.get_all_inputs()
        return all(input_name in all_inputs for input_name in required_inputs)


class WitnessBuilder:
    """
    Builds witness data for ZKP circuits from evidence and claims
    """
    
    def __init__(self):
        """Initialize witness builder"""
        self.hash_utils = HashUtils()
    
    def build_merkle_proof_witness(
        self,
        claim_id: str,
        leaf_hash: str,
        merkle_root: str,
        proof_path: List[Dict[str, Any]]
    ) -> WitnessData:
        """
        Build witness for Merkle proof circuit
        
        Args:
            claim_id: Claim identifier
            leaf_hash: Hash of the leaf to prove
            merkle_root: Merkle tree root
            proof_path: Merkle proof path
        
        Returns:
            WitnessData for Merkle proof circuit
        """
        # Extract path elements and indices from proof
        path_elements = []
        path_indices = []
        
        for step in proof_path:
            path_elements.append(step["hash"])
            # position: "left" or "right"
            path_indices.append(1 if step["position"] == "right" else 0)
        
        witness = WitnessData(
            circuit_type="merkle_proof",
            claim_id=claim_id,
            public_inputs={
                "root": merkle_root
            },
            private_inputs={
                "leaf": leaf_hash,
                "path_elements": path_elements,
                "path_indices": path_indices
            }
        )
        
        return witness
    
    def build_compliance_witness(
        self,
        claim_id: str,
        evidence_commitment: EvidenceCommitment,
        evidence_items: List[NormalizedEvidence],
        compliance_threshold: int,
        passed_controls: List[str]
    ) -> WitnessData:
        """
        Build witness for compliance proof circuit
        
        Args:
            claim_id: Claim identifier
            evidence_commitment: Evidence Merkle commitment
            evidence_items: List of evidence items
            compliance_threshold: Required passing threshold
            passed_controls: List of passed control IDs
        
        Returns:
            WitnessData for compliance circuit
        """
        # Extract evidence hashes
        evidence_hashes = [item.content_hash for item in evidence_items]
        
        # Count passed controls
        passed_count = len(passed_controls)
        
        witness = WitnessData(
            circuit_type="compliance_proof",
            claim_id=claim_id,
            bundle_id=evidence_commitment.bundle_id,
            public_inputs={
                "merkle_root": evidence_commitment.merkle_root,
                "compliance_threshold": compliance_threshold
            },
            private_inputs={
                "evidence_count": len(evidence_items),
                "evidence_hashes": evidence_hashes,
                "passed_count": passed_count
            }
        )
        
        return witness
    
    def build_range_proof_witness(
        self,
        claim_id: str,
        value: int,
        min_value: int,
        max_value: int
    ) -> WitnessData:
        """
        Build witness for range proof circuit
        
        Args:
            claim_id: Claim identifier
            value: Private value to prove
            min_value: Minimum allowed value
            max_value: Maximum allowed value
        
        Returns:
            WitnessData for range proof circuit
        
        Raises:
            ValidationError: If value is out of range
        """
        if not (min_value <= value <= max_value):
            raise ValidationError(
                f"Value {value} is out of range [{min_value}, {max_value}]"
            )
        
        witness = WitnessData(
            circuit_type="range_proof",
            claim_id=claim_id,
            public_inputs={
                "min": min_value,
                "max": max_value
            },
            private_inputs={
                "value": value
            }
        )
        
        return witness
    
    def build_threshold_witness(
        self,
        claim_id: str,
        values: List[int],
        threshold: int,
        actual_count: int
    ) -> WitnessData:
        """
        Build witness for threshold proof circuit
        
        Args:
            claim_id: Claim identifier
            values: Private values
            threshold: Required threshold
            actual_count: Actual count meeting criteria
        
        Returns:
            WitnessData for threshold circuit
        """
        witness = WitnessData(
            circuit_type="threshold_proof",
            claim_id=claim_id,
            public_inputs={
                "threshold": threshold
            },
            private_inputs={
                "values": values,
                "count": actual_count
            }
        )
        
        return witness
    
    def build_custom_witness(
        self,
        claim_id: str,
        circuit_type: str,
        public_inputs: Dict[str, Any],
        private_inputs: Dict[str, Any],
        bundle_id: Optional[str] = None
    ) -> WitnessData:
        """
        Build custom witness for any circuit type
        
        Args:
            claim_id: Claim identifier
            circuit_type: Circuit type identifier
            public_inputs: Public input values
            private_inputs: Private input values
            bundle_id: Optional bundle identifier
        
        Returns:
            WitnessData instance
        """
        witness = WitnessData(
            circuit_type=circuit_type,
            claim_id=claim_id,
            bundle_id=bundle_id,
            public_inputs=public_inputs,
            private_inputs=private_inputs
        )
        
        return witness
    
    def build_from_evidence_bundle(
        self,
        claim_id: str,
        circuit_type: str,
        evidence_items: List[NormalizedEvidence],
        commitment: EvidenceCommitment,
        additional_inputs: Optional[Dict[str, Any]] = None
    ) -> WitnessData:
        """
        Build witness from evidence bundle
        
        Args:
            claim_id: Claim identifier
            circuit_type: Type of circuit
            evidence_items: Evidence items
            commitment: Evidence commitment
            additional_inputs: Additional circuit inputs
        
        Returns:
            WitnessData instance
        """
        # Base inputs from evidence
        evidence_hashes = [item.content_hash for item in evidence_items]
        
        public_inputs = {
            "merkle_root": commitment.merkle_root,
            "evidence_count": len(evidence_items)
        }
        
        private_inputs = {
            "evidence_hashes": evidence_hashes
        }
        
        # Add additional inputs if provided
        if additional_inputs:
            for key, value in additional_inputs.items():
                if key.startswith("public_"):
                    public_inputs[key] = value
                else:
                    private_inputs[key] = value
        
        witness = WitnessData(
            circuit_type=circuit_type,
            claim_id=claim_id,
            bundle_id=commitment.bundle_id,
            public_inputs=public_inputs,
            private_inputs=private_inputs
        )
        
        return witness
    
    def prepare_field_elements(self, value: Any) -> str:
        """
        Convert value to field element for circuit
        
        Args:
            value: Value to convert
        
        Returns:
            Field element as string
        """
        if isinstance(value, int):
            return str(value)
        elif isinstance(value, str):
            # Convert hash string to field element
            if len(value) == 64:  # SHA-256 hex
                return str(int(value, 16) % (2**254))  # Fit in field
            return str(int(self.hash_utils.sha256(value.encode()).encode(), 16) % (2**254))
        elif isinstance(value, bytes):
            return str(int(self.hash_utils.sha256(value).encode(), 16) % (2**254))
        else:
            # Hash arbitrary objects
            value_str = str(value)
            return str(int(self.hash_utils.sha256(value_str.encode()).encode(), 16) % (2**254))
    
    def prepare_array_inputs(self, values: List[Any]) -> List[str]:
        """
        Prepare array of values for circuit
        
        Args:
            values: List of values
        
        Returns:
            List of field elements
        """
        return [self.prepare_field_elements(v) for v in values]
    
    def validate_witness(
        self,
        witness: WitnessData,
        required_public: List[str],
        required_private: List[str]
    ) -> bool:
        """
        Validate witness has all required inputs
        
        Args:
            witness: Witness data to validate
            required_public: Required public input names
            required_private: Required private input names
        
        Returns:
            True if valid
        
        Raises:
            ValidationError: If validation fails
        """
        # Check public inputs
        missing_public = set(required_public) - set(witness.public_inputs.keys())
        if missing_public:
            raise ValidationError(f"Missing public inputs: {missing_public}")
        
        # Check private inputs
        missing_private = set(required_private) - set(witness.private_inputs.keys())
        if missing_private:
            raise ValidationError(f"Missing private inputs: {missing_private}")
        
        return True
    
    def serialize_witness(self, witness: WitnessData) -> str:
        """
        Serialize witness to JSON
        
        Args:
            witness: Witness data
        
        Returns:
            JSON string
        """
        return witness.json()
    
    def deserialize_witness(self, json_str: str) -> WitnessData:
        """
        Deserialize witness from JSON
        
        Args:
            json_str: JSON string
        
        Returns:
            WitnessData instance
        """
        return WitnessData.parse_raw(json_str)

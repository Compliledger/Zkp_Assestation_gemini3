"""
ZKP Proof Generator
Generates zero-knowledge proofs from witness data using circuit templates
"""

from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import json
import hashlib
from pathlib import Path

from app.core.zkp.circuit_manager import CircuitManager, CircuitTemplate
from app.core.zkp.witness_builder import WitnessData
from app.utils.errors import ProofGenerationError, ValidationError
from app.utils.crypto import HashUtils


class ProofArtifact(BaseModel):
    """
    Generated ZKP proof artifact
    """
    proof_id: str = Field(..., description="Unique proof identifier")
    claim_id: str = Field(..., description="Associated claim ID")
    circuit_type: str = Field(..., description="Circuit type used")
    template_id: str = Field(..., description="Circuit template ID")
    
    # Proof data
    proof_data: Dict[str, Any] = Field(..., description="Proof bytes/data")
    public_inputs: Dict[str, Any] = Field(..., description="Public inputs")
    
    # Metadata
    proving_time: float = Field(..., description="Time taken to generate proof (seconds)")
    proof_size: int = Field(..., description="Proof size in bytes")
    proof_hash: str = Field(..., description="Hash of proof data")
    
    # Verification info
    verification_key_hash: Optional[str] = Field(None, description="Hash of verification key")
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def compute_proof_hash(self) -> str:
        """Compute hash of proof data"""
        proof_str = json.dumps(self.proof_data, sort_keys=True)
        return hashlib.sha256(proof_str.encode()).hexdigest()


class ProofGenerator:
    """
    Generates zero-knowledge proofs from witness data
    """
    
    def __init__(
        self,
        circuit_manager: Optional[CircuitManager] = None,
        proofs_path: Optional[Path] = None
    ):
        """
        Initialize proof generator
        
        Args:
            circuit_manager: Circuit manager instance
            proofs_path: Path to store generated proofs
        """
        self.circuit_manager = circuit_manager or CircuitManager()
        self.proofs_path = proofs_path or Path("./proofs")
        self.proofs_path.mkdir(parents=True, exist_ok=True)
        
        self.hash_utils = HashUtils()
    
    def generate_proof(
        self,
        witness: WitnessData,
        template_id: str,
        claim_id: Optional[str] = None
    ) -> ProofArtifact:
        """
        Generate zero-knowledge proof from witness
        
        Args:
            witness: Witness data
            template_id: Circuit template to use
            claim_id: Optional claim identifier
        
        Returns:
            Generated proof artifact
        
        Raises:
            ProofGenerationError: If proof generation fails
            ValidationError: If inputs are invalid
        """
        # Get circuit template
        try:
            template = self.circuit_manager.get_template(template_id)
        except Exception as e:
            raise ProofGenerationError(f"Failed to get circuit template: {e}")
        
        # Validate template is ready
        if not template.is_compiled:
            raise ProofGenerationError(f"Circuit not compiled: {template_id}")
        
        if not template.is_trusted_setup_done:
            raise ProofGenerationError(f"Trusted setup not done: {template_id}")
        
        # Validate witness inputs
        all_inputs = witness.get_all_inputs()
        try:
            self.circuit_manager.validate_inputs(template_id, all_inputs)
        except Exception as e:
            raise ValidationError(f"Invalid witness inputs: {e}")
        
        # Generate proof
        start_time = datetime.utcnow()
        
        try:
            proof_data = self._generate_proof_internal(template, witness)
        except Exception as e:
            raise ProofGenerationError(f"Proof generation failed: {e}")
        
        end_time = datetime.utcnow()
        proving_time = (end_time - start_time).total_seconds()
        
        # Create proof artifact
        proof_id = self._generate_proof_id(claim_id or witness.claim_id, template_id)
        
        artifact = ProofArtifact(
            proof_id=proof_id,
            claim_id=claim_id or witness.claim_id,
            circuit_type=witness.circuit_type,
            template_id=template_id,
            proof_data=proof_data,
            public_inputs=witness.public_inputs,
            proving_time=proving_time,
            proof_size=len(json.dumps(proof_data)),
            proof_hash=hashlib.sha256(json.dumps(proof_data, sort_keys=True).encode()).hexdigest(),
            verification_key_hash=self._hash_verification_key(template)
        )
        
        # Store proof
        self._store_proof(artifact)
        
        return artifact
    
    def generate_batch_proofs(
        self,
        witnesses: list[WitnessData],
        template_id: str
    ) -> list[ProofArtifact]:
        """
        Generate multiple proofs in batch
        
        Args:
            witnesses: List of witness data
            template_id: Circuit template to use
        
        Returns:
            List of generated proof artifacts
        """
        proofs = []
        
        for witness in witnesses:
            try:
                proof = self.generate_proof(witness, template_id)
                proofs.append(proof)
            except Exception as e:
                # Log error but continue with other proofs
                print(f"Failed to generate proof for claim {witness.claim_id}: {e}")
                continue
        
        return proofs
    
    def _generate_proof_internal(
        self,
        template: CircuitTemplate,
        witness: WitnessData
    ) -> Dict[str, Any]:
        """
        Internal proof generation logic
        
        In production, this would interface with actual ZKP libraries:
        - Circom + snarkjs
        - gnark
        - libsnark
        - etc.
        
        For now, we simulate proof generation
        """
        # Simulate proof generation based on circuit type
        
        if template.circuit_type.value == "merkle_proof":
            return self._generate_merkle_proof(witness)
        elif template.circuit_type.value == "compliance_proof":
            return self._generate_compliance_proof(witness)
        elif template.circuit_type.value == "range_proof":
            return self._generate_range_proof(witness)
        else:
            return self._generate_generic_proof(witness)
    
    def _generate_merkle_proof(self, witness: WitnessData) -> Dict[str, Any]:
        """Generate simulated Merkle proof"""
        # In production: Use actual ZKP prover
        # For now: Simulate proof structure
        
        return {
            "protocol": "groth16",
            "curve": "bn128",
            "proof": {
                "pi_a": ["0x123...", "0x456..."],
                "pi_b": [["0x789...", "0xabc..."], ["0xdef...", "0x012..."]],
                "pi_c": ["0x345...", "0x678..."]
            },
            "public_signals": list(witness.public_inputs.values())
        }
    
    def _generate_compliance_proof(self, witness: WitnessData) -> Dict[str, Any]:
        """Generate simulated compliance proof"""
        return {
            "protocol": "groth16",
            "curve": "bn128",
            "proof": {
                "pi_a": ["0xaaa...", "0xbbb..."],
                "pi_b": [["0xccc...", "0xddd..."], ["0xeee...", "0xfff..."]],
                "pi_c": ["0x111...", "0x222..."]
            },
            "public_signals": list(witness.public_inputs.values()),
            "compliance_metadata": {
                "threshold": witness.public_inputs.get("compliance_threshold"),
                "merkle_root": witness.public_inputs.get("merkle_root")
            }
        }
    
    def _generate_range_proof(self, witness: WitnessData) -> Dict[str, Any]:
        """Generate simulated range proof"""
        return {
            "protocol": "groth16",
            "curve": "bn128",
            "proof": {
                "pi_a": ["0x999...", "0x888..."],
                "pi_b": [["0x777...", "0x666..."], ["0x555...", "0x444..."]],
                "pi_c": ["0x333...", "0x222..."]
            },
            "public_signals": [
                witness.public_inputs.get("min"),
                witness.public_inputs.get("max")
            ]
        }
    
    def _generate_generic_proof(self, witness: WitnessData) -> Dict[str, Any]:
        """Generate generic simulated proof"""
        return {
            "protocol": "groth16",
            "curve": "bn128",
            "proof": {
                "pi_a": ["0xgeneric_a1", "0xgeneric_a2"],
                "pi_b": [["0xgeneric_b1", "0xgeneric_b2"], ["0xgeneric_b3", "0xgeneric_b4"]],
                "pi_c": ["0xgeneric_c1", "0xgeneric_c2"]
            },
            "public_signals": list(witness.public_inputs.values())
        }
    
    def _generate_proof_id(self, claim_id: str, template_id: str) -> str:
        """Generate unique proof ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        content = f"{claim_id}:{template_id}:{timestamp}"
        hash_suffix = hashlib.sha256(content.encode()).hexdigest()[:8]
        return f"proof_{claim_id}_{template_id}_{hash_suffix}"
    
    def _hash_verification_key(self, template: CircuitTemplate) -> Optional[str]:
        """Hash verification key for integrity checking"""
        if not template.verification_key_file:
            return None
        
        vkey_path = Path(template.verification_key_file)
        if vkey_path.exists():
            vkey_data = vkey_path.read_bytes()
            return self.hash_utils.sha256(vkey_data)
        
        return None
    
    def _store_proof(self, artifact: ProofArtifact):
        """Store proof artifact to disk"""
        proof_file = self.proofs_path / f"{artifact.proof_id}.json"
        proof_file.write_text(artifact.json(indent=2))
    
    def load_proof(self, proof_id: str) -> Optional[ProofArtifact]:
        """
        Load proof artifact from storage
        
        Args:
            proof_id: Proof identifier
        
        Returns:
            ProofArtifact if found, None otherwise
        """
        proof_file = self.proofs_path / f"{proof_id}.json"
        
        if proof_file.exists():
            return ProofArtifact.parse_raw(proof_file.read_text())
        
        return None
    
    def estimate_proving_time(self, template_id: str) -> float:
        """
        Estimate proving time for a circuit
        
        Args:
            template_id: Circuit template ID
        
        Returns:
            Estimated time in seconds
        """
        try:
            template = self.circuit_manager.get_template(template_id)
            return template.proving_time_estimate or 1.0
        except:
            return 1.0
    
    def get_proof_statistics(self) -> Dict[str, Any]:
        """Get statistics about generated proofs"""
        proof_files = list(self.proofs_path.glob("*.json"))
        
        total_proofs = len(proof_files)
        total_size = sum(f.stat().st_size for f in proof_files)
        
        # Load proofs to get more stats
        proofs = []
        for proof_file in proof_files[:100]:  # Limit to avoid loading too many
            try:
                proof = ProofArtifact.parse_raw(proof_file.read_text())
                proofs.append(proof)
            except:
                continue
        
        avg_proving_time = sum(p.proving_time for p in proofs) / len(proofs) if proofs else 0
        avg_proof_size = sum(p.proof_size for p in proofs) / len(proofs) if proofs else 0
        
        by_circuit_type = {}
        for proof in proofs:
            circuit_type = proof.circuit_type
            by_circuit_type[circuit_type] = by_circuit_type.get(circuit_type, 0) + 1
        
        return {
            "total_proofs": total_proofs,
            "total_size_bytes": total_size,
            "average_proving_time": avg_proving_time,
            "average_proof_size": avg_proof_size,
            "by_circuit_type": by_circuit_type
        }

"""
Proof Service
Orchestrates ZKP proof generation, verification, and management
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.zkp.circuit_manager import CircuitManager, CircuitType
from app.core.zkp.witness_builder import WitnessBuilder, WitnessData
from app.core.zkp.proof_generator import ProofGenerator, ProofArtifact
from app.core.zkp.proof_verifier import ProofVerifier, VerificationResult
from app.core.evidence.commitment import EvidenceCommitment
from app.models.proof import ProofArtifact as ProofArtifactModel
from app.models.verification import VerificationReceipt
from app.models.claim import Claim
from app.models.evidence import EvidenceBundle
from app.utils.errors import (
    ValidationError,
    NotFoundError,
    ProofGenerationError,
    VerificationError,
    AuthorizationError
)


class ProofService:
    """
    Service for ZKP proof generation and verification
    """
    
    def __init__(
        self,
        db: AsyncSession,
        tenant_id: str,
        user_id: str
    ):
        """
        Initialize proof service
        
        Args:
            db: Database session
            tenant_id: Tenant identifier
            user_id: User identifier
        """
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        
        # Initialize ZKP components
        self.circuit_manager = CircuitManager()
        self.witness_builder = WitnessBuilder()
        self.proof_generator = ProofGenerator(self.circuit_manager)
        self.proof_verifier = ProofVerifier(self.circuit_manager)
    
    async def generate_proof(
        self,
        claim_id: str,
        circuit_type: str,
        witness_inputs: Dict[str, Any],
        template_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate ZKP proof for a claim
        
        Args:
            claim_id: Claim identifier
            circuit_type: Type of circuit to use
            witness_inputs: Inputs for witness generation
            template_id: Optional specific template ID
        
        Returns:
            Proof information
        
        Raises:
            NotFoundError: If claim not found
            ProofGenerationError: If proof generation fails
        """
        # Verify claim exists and belongs to tenant
        claim = await self._get_claim(claim_id)
        
        # Select circuit template
        if not template_id:
            template_id = self._select_template_for_circuit_type(circuit_type)
        
        # Build witness
        witness = await self._build_witness(
            claim_id=claim_id,
            circuit_type=circuit_type,
            witness_inputs=witness_inputs
        )
        
        # Generate proof
        try:
            proof_artifact = self.proof_generator.generate_proof(
                witness=witness,
                template_id=template_id,
                claim_id=claim_id
            )
        except Exception as e:
            raise ProofGenerationError(f"Failed to generate proof: {e}")
        
        # Store proof in database
        proof_model = ProofArtifactModel(
            proof_id=proof_artifact.proof_id,
            claim_id=claim_id,
            circuit_type=circuit_type,
            template_id=template_id,
            proof_data=proof_artifact.proof_data,
            public_inputs=proof_artifact.public_inputs,
            proving_time=proof_artifact.proving_time,
            proof_size=proof_artifact.proof_size,
            proof_hash=proof_artifact.proof_hash
        )
        
        self.db.add(proof_model)
        await self.db.commit()
        await self.db.refresh(proof_model)
        
        return {
            "proof_id": proof_artifact.proof_id,
            "claim_id": claim_id,
            "circuit_type": circuit_type,
            "template_id": template_id,
            "proof_hash": proof_artifact.proof_hash,
            "proving_time": proof_artifact.proving_time,
            "proof_size": proof_artifact.proof_size,
            "generated_at": proof_artifact.generated_at.isoformat()
        }
    
    async def verify_proof(
        self,
        proof_id: str,
        verifier_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify a ZKP proof
        
        Args:
            proof_id: Proof identifier
            verifier_id: Optional verifier identifier
        
        Returns:
            Verification result
        
        Raises:
            NotFoundError: If proof not found
        """
        # Get proof from database
        proof_model = await self._get_proof(proof_id)
        
        # Verify claim access
        claim = await self._get_claim(proof_model.claim_id)
        
        # Convert to proof artifact
        proof_artifact = ProofArtifact(
            proof_id=proof_model.proof_id,
            claim_id=proof_model.claim_id,
            circuit_type=proof_model.circuit_type,
            template_id=proof_model.template_id,
            proof_data=proof_model.proof_data,
            public_inputs=proof_model.public_inputs,
            proving_time=proof_model.proving_time,
            proof_size=proof_model.proof_size,
            proof_hash=proof_model.proof_hash
        )
        
        # Verify proof
        verification_result = self.proof_verifier.verify_proof(
            proof_artifact=proof_artifact,
            verifier_id=verifier_id or self.user_id
        )
        
        # Store verification receipt
        receipt = VerificationReceipt(
            receipt_id=verification_result.verification_id,
            claim_id=proof_model.claim_id,
            verifier_id=verifier_id or self.user_id,
            verification_result=verification_result.status.value,
            checks_passed=verification_result.checks_passed,
            verification_time=verification_result.verification_time,
            verified_at=verification_result.verified_at
        )
        
        self.db.add(receipt)
        await self.db.commit()
        
        return {
            "verification_id": verification_result.verification_id,
            "proof_id": proof_id,
            "is_valid": verification_result.is_valid,
            "status": verification_result.status.value,
            "checks_passed": verification_result.checks_passed,
            "verification_time": verification_result.verification_time,
            "error_message": verification_result.error_message,
            "verified_at": verification_result.verified_at.isoformat()
        }
    
    async def generate_merkle_proof(
        self,
        claim_id: str,
        evidence_id: str,
        bundle_id: str
    ) -> Dict[str, Any]:
        """
        Generate Merkle membership proof for evidence
        
        Args:
            claim_id: Claim identifier
            evidence_id: Evidence identifier
            bundle_id: Evidence bundle identifier
        
        Returns:
            Proof information
        """
        # Get evidence bundle
        result = await self.db.execute(
            select(EvidenceBundle).where(EvidenceBundle.bundle_id == bundle_id)
        )
        bundle = result.scalar_one_or_none()
        
        if not bundle:
            raise NotFoundError(f"Evidence bundle not found: {bundle_id}")
        
        # Get Merkle proof path (from evidence service)
        from app.services.evidence_service import EvidenceService
        evidence_service = EvidenceService(self.db, self.tenant_id, self.user_id)
        
        merkle_proof = await evidence_service.generate_evidence_proof(
            bundle_id=bundle_id,
            evidence_id=evidence_id
        )
        
        # Build witness for Merkle proof circuit
        witness = self.witness_builder.build_merkle_proof_witness(
            claim_id=claim_id,
            leaf_hash=merkle_proof["evidence_hash"],
            merkle_root=merkle_proof["merkle_root"],
            proof_path=merkle_proof["proof"]
        )
        
        # Generate ZKP proof
        proof_artifact = self.proof_generator.generate_proof(
            witness=witness,
            template_id="merkle_proof_v1",
            claim_id=claim_id
        )
        
        # Store proof
        proof_model = ProofArtifactModel(
            proof_id=proof_artifact.proof_id,
            claim_id=claim_id,
            circuit_type="merkle_proof",
            template_id="merkle_proof_v1",
            proof_data=proof_artifact.proof_data,
            public_inputs=proof_artifact.public_inputs,
            proving_time=proof_artifact.proving_time,
            proof_size=proof_artifact.proof_size,
            proof_hash=proof_artifact.proof_hash
        )
        
        self.db.add(proof_model)
        await self.db.commit()
        
        return {
            "proof_id": proof_artifact.proof_id,
            "claim_id": claim_id,
            "evidence_id": evidence_id,
            "merkle_root": merkle_proof["merkle_root"],
            "proof_hash": proof_artifact.proof_hash
        }
    
    async def list_proofs(
        self,
        claim_id: Optional[str] = None,
        circuit_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List proofs for tenant
        
        Args:
            claim_id: Optional claim filter
            circuit_type: Optional circuit type filter
            limit: Max results
            offset: Pagination offset
        
        Returns:
            List of proofs
        """
        # Build query
        query = select(ProofArtifactModel).limit(limit).offset(offset)
        
        if claim_id:
            # Verify claim belongs to tenant
            claim = await self._get_claim(claim_id)
            query = query.where(ProofArtifactModel.claim_id == claim_id)
        else:
            # Get all claims for tenant
            claims_result = await self.db.execute(
                select(Claim.claim_id).where(Claim.tenant_id == self.tenant_id)
            )
            claim_ids = [row[0] for row in claims_result]
            query = query.where(ProofArtifactModel.claim_id.in_(claim_ids))
        
        if circuit_type:
            query = query.where(ProofArtifactModel.circuit_type == circuit_type)
        
        result = await self.db.execute(query)
        proofs = result.scalars().all()
        
        return {
            "proofs": [
                {
                    "proof_id": proof.proof_id,
                    "claim_id": proof.claim_id,
                    "circuit_type": proof.circuit_type,
                    "template_id": proof.template_id,
                    "proof_hash": proof.proof_hash,
                    "proving_time": proof.proving_time,
                    "generated_at": proof.created_at.isoformat()
                }
                for proof in proofs
            ],
            "total": len(proofs),
            "limit": limit,
            "offset": offset
        }
    
    async def get_proof_details(self, proof_id: str) -> Dict[str, Any]:
        """
        Get detailed proof information
        
        Args:
            proof_id: Proof identifier
        
        Returns:
            Detailed proof information
        """
        proof = await self._get_proof(proof_id)
        claim = await self._get_claim(proof.claim_id)
        
        # Get verification history
        verifications_result = await self.db.execute(
            select(VerificationReceipt)
            .where(VerificationReceipt.claim_id == proof.claim_id)
            .order_by(VerificationReceipt.verified_at.desc())
        )
        verifications = verifications_result.scalars().all()
        
        return {
            "proof_id": proof.proof_id,
            "claim_id": proof.claim_id,
            "circuit_type": proof.circuit_type,
            "template_id": proof.template_id,
            "proof_data": proof.proof_data,
            "public_inputs": proof.public_inputs,
            "proof_hash": proof.proof_hash,
            "proving_time": proof.proving_time,
            "proof_size": proof.proof_size,
            "generated_at": proof.created_at.isoformat(),
            "verifications": [
                {
                    "verification_id": v.receipt_id,
                    "verifier_id": v.verifier_id,
                    "result": v.verification_result,
                    "verified_at": v.verified_at.isoformat()
                }
                for v in verifications
            ]
        }
    
    async def _build_witness(
        self,
        claim_id: str,
        circuit_type: str,
        witness_inputs: Dict[str, Any]
    ) -> WitnessData:
        """Build witness from inputs"""
        # Extract public and private inputs
        public_inputs = witness_inputs.get("public_inputs", {})
        private_inputs = witness_inputs.get("private_inputs", {})
        
        witness = self.witness_builder.build_custom_witness(
            claim_id=claim_id,
            circuit_type=circuit_type,
            public_inputs=public_inputs,
            private_inputs=private_inputs
        )
        
        return witness
    
    def _select_template_for_circuit_type(self, circuit_type: str) -> str:
        """Select appropriate template for circuit type"""
        template_map = {
            "merkle_proof": "merkle_proof_v1",
            "compliance_proof": "compliance_proof_v1",
            "range_proof": "range_proof_v1",
        }
        
        return template_map.get(circuit_type, "merkle_proof_v1")
    
    async def _get_claim(self, claim_id: str) -> Claim:
        """Get claim and verify access"""
        result = await self.db.execute(
            select(Claim).where(Claim.claim_id == claim_id)
        )
        claim = result.scalar_one_or_none()
        
        if not claim:
            raise NotFoundError(f"Claim not found: {claim_id}")
        
        if claim.tenant_id != self.tenant_id:
            raise AuthorizationError("Access denied to claim")
        
        return claim
    
    async def _get_proof(self, proof_id: str) -> ProofArtifactModel:
        """Get proof from database"""
        result = await self.db.execute(
            select(ProofArtifactModel).where(ProofArtifactModel.proof_id == proof_id)
        )
        proof = result.scalar_one_or_none()
        
        if not proof:
            raise NotFoundError(f"Proof not found: {proof_id}")
        
        return proof
    
    async def get_circuit_templates(self) -> List[Dict[str, Any]]:
        """Get available circuit templates"""
        templates = self.circuit_manager.list_templates()
        
        return [
            {
                "template_id": t.template_id,
                "circuit_type": t.circuit_type.value,
                "name": t.name,
                "description": t.description,
                "version": t.version,
                "is_compiled": t.is_compiled,
                "is_ready": t.is_trusted_setup_done,
                "proving_time_estimate": t.proving_time_estimate
            }
            for t in templates
        ]

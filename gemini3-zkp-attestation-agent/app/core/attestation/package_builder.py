"""
Attestation Package Builder
Assembles complete attestation packages with evidence, proofs, and metadata
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from pathlib import Path
import json
from pydantic import BaseModel, Field

from app.models.claim import Claim
from app.models.evidence import EvidenceBundle
from app.models.proof import ProofArtifact
from app.core.zkp.proof_generator import ProofArtifact as ProofArtifactCore
from app.utils.crypto import HashUtils
from app.utils.errors import ValidationError


class AttestationStatus(str, Enum):
    """Attestation package status"""
    DRAFT = "draft"
    ASSEMBLED = "assembled"
    SIGNED = "signed"
    PUBLISHED = "published"
    REVOKED = "revoked"


class AttestationFormat(str, Enum):
    """Supported attestation formats"""
    JSON = "json"
    OSCAL = "oscal"
    PDF = "pdf"
    XML = "xml"


class AttestationPackage(BaseModel):
    """
    Complete attestation package
    """
    package_id: str = Field(..., description="Unique package identifier")
    claim_id: str = Field(..., description="Associated claim ID")
    tenant_id: str = Field(..., description="Tenant identifier")
    
    # Package metadata
    title: str = Field(..., description="Attestation title")
    description: str = Field(..., description="Attestation description")
    version: str = Field(default="1.0.0", description="Package version")
    status: AttestationStatus = Field(default=AttestationStatus.DRAFT)
    
    # Content
    claim_data: Dict[str, Any] = Field(..., description="Claim information")
    evidence_bundles: List[Dict[str, Any]] = Field(default_factory=list, description="Evidence bundles")
    proofs: List[Dict[str, Any]] = Field(default_factory=list, description="ZKP proofs")
    
    # Metadata
    issuer: Dict[str, str] = Field(..., description="Issuer information")
    subject: Optional[Dict[str, str]] = Field(None, description="Subject information")
    
    # Attestation details
    attestation_type: str = Field(..., description="Type of attestation")
    compliance_framework: Optional[str] = Field(None, description="Compliance framework (e.g., SOC2, ISO27001)")
    assessment_date: datetime = Field(default_factory=datetime.utcnow)
    valid_from: datetime = Field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = Field(None, description="Expiration date")
    
    # Integrity
    package_hash: Optional[str] = Field(None, description="Package content hash")
    signature: Optional[str] = Field(None, description="Digital signature")
    signature_algorithm: Optional[str] = Field(None, description="Signature algorithm")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    assembled_at: Optional[datetime] = Field(None)
    signed_at: Optional[datetime] = Field(None)
    published_at: Optional[datetime] = Field(None)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def compute_hash(self) -> str:
        """Compute hash of package content"""
        content = {
            "package_id": self.package_id,
            "claim_id": self.claim_id,
            "claim_data": self.claim_data,
            "evidence_bundles": self.evidence_bundles,
            "proofs": self.proofs,
            "version": self.version
        }
        content_str = json.dumps(content, sort_keys=True)
        hash_utils = HashUtils()
        return hash_utils.sha256(content_str.encode())


class AttestationPackageBuilder:
    """
    Builds complete attestation packages from claims, evidence, and proofs
    """
    
    def __init__(self, packages_path: Optional[Path] = None):
        """
        Initialize package builder
        
        Args:
            packages_path: Path to store packages
        """
        self.packages_path = packages_path or Path("./packages")
        self.packages_path.mkdir(parents=True, exist_ok=True)
        self.hash_utils = HashUtils()
    
    def create_package(
        self,
        claim: Claim,
        title: str,
        description: str,
        attestation_type: str,
        issuer: Dict[str, str],
        subject: Optional[Dict[str, str]] = None,
        compliance_framework: Optional[str] = None,
        valid_until: Optional[datetime] = None
    ) -> AttestationPackage:
        """
        Create new attestation package
        
        Args:
            claim: Claim object
            title: Attestation title
            description: Attestation description
            attestation_type: Type of attestation
            issuer: Issuer information
            subject: Subject information
            compliance_framework: Compliance framework
            valid_until: Expiration date
        
        Returns:
            AttestationPackage instance
        """
        package_id = self._generate_package_id(claim.claim_id)
        
        # Extract claim data
        claim_data = {
            "claim_id": claim.claim_id,
            "claim_type": claim.claim_type,
            "claim_statement": claim.claim_statement,
            "tenant_id": claim.tenant_id,
            "status": claim.status,
            "created_at": claim.created_at.isoformat() if claim.created_at else None
        }
        
        package = AttestationPackage(
            package_id=package_id,
            claim_id=claim.claim_id,
            tenant_id=claim.tenant_id,
            title=title,
            description=description,
            attestation_type=attestation_type,
            issuer=issuer,
            subject=subject,
            compliance_framework=compliance_framework,
            valid_until=valid_until,
            claim_data=claim_data,
            status=AttestationStatus.DRAFT
        )
        
        return package
    
    def add_evidence_bundle(
        self,
        package: AttestationPackage,
        bundle: EvidenceBundle,
        evidence_metadata: Optional[Dict[str, Any]] = None
    ) -> AttestationPackage:
        """
        Add evidence bundle to package
        
        Args:
            package: Attestation package
            bundle: Evidence bundle
            evidence_metadata: Additional metadata
        
        Returns:
            Updated package
        """
        bundle_data = {
            "bundle_id": bundle.bundle_id,
            "evidence_count": bundle.evidence_count,
            "merkle_root": bundle.merkle_root,
            "created_at": bundle.created_at.isoformat() if bundle.created_at else None,
            "metadata": evidence_metadata or {}
        }
        
        package.evidence_bundles.append(bundle_data)
        
        return package
    
    def add_proof(
        self,
        package: AttestationPackage,
        proof: ProofArtifact,
        include_full_proof: bool = False
    ) -> AttestationPackage:
        """
        Add ZKP proof to package
        
        Args:
            package: Attestation package
            proof: Proof artifact
            include_full_proof: Whether to include full proof data
        
        Returns:
            Updated package
        """
        proof_data = {
            "proof_id": proof.proof_id,
            "circuit_type": proof.circuit_type,
            "template_id": proof.template_id,
            "proof_hash": proof.proof_hash,
            "public_inputs": proof.public_inputs,
            "proving_time": proof.proving_time,
            "generated_at": proof.created_at.isoformat() if hasattr(proof, 'created_at') and proof.created_at else None
        }
        
        if include_full_proof:
            proof_data["proof_data"] = proof.proof_data
        
        package.proofs.append(proof_data)
        
        return package
    
    def assemble_package(
        self,
        package: AttestationPackage,
        include_checksums: bool = True
    ) -> AttestationPackage:
        """
        Finalize package assembly
        
        Args:
            package: Attestation package
            include_checksums: Whether to compute checksums
        
        Returns:
            Assembled package
        """
        if package.status != AttestationStatus.DRAFT:
            raise ValidationError("Only draft packages can be assembled")
        
        # Compute package hash
        if include_checksums:
            package.package_hash = package.compute_hash()
        
        # Update status and timestamp
        package.status = AttestationStatus.ASSEMBLED
        package.assembled_at = datetime.utcnow()
        
        # Store package
        self._store_package(package)
        
        return package
    
    def validate_package(self, package: AttestationPackage) -> bool:
        """
        Validate package completeness
        
        Args:
            package: Attestation package
        
        Returns:
            True if valid
        
        Raises:
            ValidationError: If package is invalid
        """
        # Check required fields
        if not package.claim_id:
            raise ValidationError("Claim ID is required")
        
        if not package.title or not package.description:
            raise ValidationError("Title and description are required")
        
        if not package.issuer:
            raise ValidationError("Issuer information is required")
        
        # Check has evidence or proofs
        if not package.evidence_bundles and not package.proofs:
            raise ValidationError("Package must contain evidence or proofs")
        
        # Verify hash if present
        if package.package_hash:
            computed_hash = package.compute_hash()
            if computed_hash != package.package_hash:
                raise ValidationError("Package hash mismatch - content has been modified")
        
        return True
    
    def update_package_status(
        self,
        package: AttestationPackage,
        new_status: AttestationStatus
    ) -> AttestationPackage:
        """
        Update package status
        
        Args:
            package: Attestation package
            new_status: New status
        
        Returns:
            Updated package
        """
        old_status = package.status
        package.status = new_status
        
        # Update timestamps based on status
        if new_status == AttestationStatus.SIGNED and not package.signed_at:
            package.signed_at = datetime.utcnow()
        elif new_status == AttestationStatus.PUBLISHED and not package.published_at:
            package.published_at = datetime.utcnow()
        
        # Store updated package
        self._store_package(package)
        
        return package
    
    def add_metadata(
        self,
        package: AttestationPackage,
        metadata: Dict[str, Any]
    ) -> AttestationPackage:
        """
        Add custom metadata to package
        
        Args:
            package: Attestation package
            metadata: Metadata to add
        
        Returns:
            Updated package
        """
        if "metadata" not in package.claim_data:
            package.claim_data["metadata"] = {}
        
        package.claim_data["metadata"].update(metadata)
        
        return package
    
    def get_package_summary(self, package: AttestationPackage) -> Dict[str, Any]:
        """
        Get package summary
        
        Args:
            package: Attestation package
        
        Returns:
            Summary dictionary
        """
        return {
            "package_id": package.package_id,
            "claim_id": package.claim_id,
            "title": package.title,
            "status": package.status.value,
            "attestation_type": package.attestation_type,
            "compliance_framework": package.compliance_framework,
            "evidence_count": len(package.evidence_bundles),
            "proof_count": len(package.proofs),
            "issuer": package.issuer,
            "valid_from": package.valid_from.isoformat(),
            "valid_until": package.valid_until.isoformat() if package.valid_until else None,
            "created_at": package.created_at.isoformat(),
            "assembled_at": package.assembled_at.isoformat() if package.assembled_at else None,
            "signed_at": package.signed_at.isoformat() if package.signed_at else None,
            "is_signed": package.signature is not None,
            "package_hash": package.package_hash
        }
    
    def _generate_package_id(self, claim_id: str) -> str:
        """Generate unique package ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        content = f"pkg_{claim_id}_{timestamp}"
        hash_suffix = self.hash_utils.sha256(content.encode())[:8]
        return f"pkg_{claim_id}_{hash_suffix}"
    
    def _store_package(self, package: AttestationPackage):
        """Store package to disk"""
        package_file = self.packages_path / f"{package.package_id}.json"
        package_file.write_text(package.json(indent=2))
    
    def load_package(self, package_id: str) -> Optional[AttestationPackage]:
        """
        Load package from storage
        
        Args:
            package_id: Package identifier
        
        Returns:
            AttestationPackage if found
        """
        package_file = self.packages_path / f"{package_id}.json"
        
        if package_file.exists():
            return AttestationPackage.parse_raw(package_file.read_text())
        
        return None
    
    def list_packages(
        self,
        tenant_id: Optional[str] = None,
        status: Optional[AttestationStatus] = None
    ) -> List[AttestationPackage]:
        """
        List packages
        
        Args:
            tenant_id: Filter by tenant
            status: Filter by status
        
        Returns:
            List of packages
        """
        packages = []
        
        for package_file in self.packages_path.glob("*.json"):
            try:
                package = AttestationPackage.parse_raw(package_file.read_text())
                
                # Apply filters
                if tenant_id and package.tenant_id != tenant_id:
                    continue
                
                if status and package.status != status:
                    continue
                
                packages.append(package)
            except:
                continue
        
        return packages
    
    def export_package(
        self,
        package: AttestationPackage,
        format: AttestationFormat,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Export package to file
        
        Args:
            package: Attestation package
            format: Export format
            output_path: Output file path
        
        Returns:
            Path to exported file
        """
        if not output_path:
            output_path = self.packages_path / f"{package.package_id}.{format.value}"
        
        if format == AttestationFormat.JSON:
            output_path.write_text(package.json(indent=2))
        else:
            # Other formats handled by specialized exporters
            raise NotImplementedError(f"Export to {format.value} not implemented in base builder")
        
        return output_path

"""
Attestation Service
Orchestrates attestation package assembly, export, signing, and lifecycle management
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path

from app.core.attestation.package_builder import (
    AttestationPackageBuilder,
    AttestationPackage,
    AttestationStatus,
    AttestationFormat
)
from app.core.attestation.oscal_exporter import OSCALExporter
from app.core.attestation.pdf_generator import PDFGenerator
from app.core.attestation.signature_manager import SignatureManager, SignatureAlgorithm
from app.models.claim import Claim
from app.models.evidence import EvidenceBundle
from app.models.proof import ProofArtifact
from app.models.attestation import AttestationPackage as AttestationPackageModel
from app.utils.errors import (
    NotFoundError,
    ValidationError,
    AuthorizationError,
    SignatureError
)


class AttestationService:
    """
    Service for attestation package assembly and lifecycle management
    """
    
    def __init__(
        self,
        db: AsyncSession,
        tenant_id: str,
        user_id: str
    ):
        """
        Initialize attestation service
        
        Args:
            db: Database session
            tenant_id: Tenant identifier
            user_id: User identifier
        """
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        
        # Initialize components
        self.package_builder = AttestationPackageBuilder()
        self.oscal_exporter = OSCALExporter()
        self.pdf_generator = PDFGenerator()
        self.signature_manager = SignatureManager()
    
    async def create_attestation(
        self,
        claim_id: str,
        title: str,
        description: str,
        attestation_type: str,
        issuer: Dict[str, str],
        subject: Optional[Dict[str, str]] = None,
        compliance_framework: Optional[str] = None,
        valid_until: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Create new attestation package
        
        Args:
            claim_id: Claim identifier
            title: Attestation title
            description: Description
            attestation_type: Type of attestation
            issuer: Issuer information
            subject: Subject information
            compliance_framework: Compliance framework
            valid_until: Expiration date
        
        Returns:
            Attestation package info
        """
        # Get claim and verify access
        claim = await self._get_claim(claim_id)
        
        # Create package
        package = self.package_builder.create_package(
            claim=claim,
            title=title,
            description=description,
            attestation_type=attestation_type,
            issuer=issuer,
            subject=subject,
            compliance_framework=compliance_framework,
            valid_until=valid_until
        )
        
        # Store in database
        package_model = AttestationPackageModel(
            package_id=package.package_id,
            claim_id=claim_id,
            tenant_id=self.tenant_id,
            title=title,
            description=description,
            status=package.status.value,
            package_data=package.dict()
        )
        
        self.db.add(package_model)
        await self.db.commit()
        await self.db.refresh(package_model)
        
        return self.package_builder.get_package_summary(package)
    
    async def add_evidence_to_attestation(
        self,
        package_id: str,
        bundle_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add evidence bundle to attestation
        
        Args:
            package_id: Package identifier
            bundle_id: Evidence bundle ID
            metadata: Additional metadata
        
        Returns:
            Updated package info
        """
        # Load package
        package = await self._get_package(package_id)
        
        # Get evidence bundle
        result = await self.db.execute(
            select(EvidenceBundle).where(EvidenceBundle.bundle_id == bundle_id)
        )
        bundle = result.scalar_one_or_none()
        
        if not bundle:
            raise NotFoundError(f"Evidence bundle not found: {bundle_id}")
        
        # Add to package
        self.package_builder.add_evidence_bundle(package, bundle, metadata)
        
        # Update database
        await self._update_package_in_db(package)
        
        return self.package_builder.get_package_summary(package)
    
    async def add_proof_to_attestation(
        self,
        package_id: str,
        proof_id: str,
        include_full_proof: bool = False
    ) -> Dict[str, Any]:
        """
        Add ZKP proof to attestation
        
        Args:
            package_id: Package identifier
            proof_id: Proof identifier
            include_full_proof: Include full proof data
        
        Returns:
            Updated package info
        """
        # Load package
        package = await self._get_package(package_id)
        
        # Get proof
        result = await self.db.execute(
            select(ProofArtifact).where(ProofArtifact.proof_id == proof_id)
        )
        proof = result.scalar_one_or_none()
        
        if not proof:
            raise NotFoundError(f"Proof not found: {proof_id}")
        
        # Add to package
        self.package_builder.add_proof(package, proof, include_full_proof)
        
        # Update database
        await self._update_package_in_db(package)
        
        return self.package_builder.get_package_summary(package)
    
    async def assemble_attestation(
        self,
        package_id: str,
        include_checksums: bool = True
    ) -> Dict[str, Any]:
        """
        Finalize attestation assembly
        
        Args:
            package_id: Package identifier
            include_checksums: Compute checksums
        
        Returns:
            Assembled package info
        """
        # Load package
        package = await self._get_package(package_id)
        
        # Validate before assembly
        self.package_builder.validate_package(package)
        
        # Assemble
        package = self.package_builder.assemble_package(package, include_checksums)
        
        # Update database
        await self._update_package_in_db(package)
        
        return self.package_builder.get_package_summary(package)
    
    async def sign_attestation(
        self,
        package_id: str,
        signer_name: str,
        algorithm: str = "RSA-SHA256",
        signer_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sign attestation package
        
        Args:
            package_id: Package identifier
            signer_name: Signer name
            algorithm: Signature algorithm
            signer_email: Signer email
        
        Returns:
            Signature information
        """
        # Load package
        package = await self._get_package(package_id)
        
        # Verify package is assembled
        if package.status != AttestationStatus.ASSEMBLED:
            raise ValidationError("Package must be assembled before signing")
        
        # Sign package
        try:
            signature = self.signature_manager.sign_package(
                package=package,
                signer_id=self.user_id,
                signer_name=signer_name,
                algorithm=SignatureAlgorithm(algorithm),
                signer_email=signer_email
            )
        except Exception as e:
            raise SignatureError(f"Failed to sign package: {e}")
        
        # Update package status
        package = self.package_builder.update_package_status(
            package,
            AttestationStatus.SIGNED
        )
        
        # Update database
        await self._update_package_in_db(package)
        
        return self.signature_manager.get_signature_info(signature)
    
    async def verify_attestation_signature(
        self,
        package_id: str
    ) -> Dict[str, Any]:
        """
        Verify attestation signature
        
        Args:
            package_id: Package identifier
        
        Returns:
            Verification result
        """
        # Load package
        package = await self._get_package(package_id)
        
        if not package.signature:
            raise ValidationError("Package is not signed")
        
        # Load signature
        # Find signature by package hash
        signature = None
        signatures_path = Path("./keys")
        for sig_file in signatures_path.glob("*.json"):
            try:
                from app.core.attestation.signature_manager import DigitalSignature
                sig = DigitalSignature.parse_raw(sig_file.read_text())
                if sig.package_id == package_id:
                    signature = sig
                    break
            except:
                continue
        
        if not signature:
            raise NotFoundError("Signature not found")
        
        # Verify
        is_valid = self.signature_manager.verify_signature(package, signature)
        
        return {
            "package_id": package_id,
            "is_valid": is_valid,
            "signature_id": signature.signature_id,
            "signer": signature.signer_name,
            "algorithm": signature.algorithm.value,
            "verified_at": datetime.utcnow().isoformat()
        }
    
    async def export_attestation(
        self,
        package_id: str,
        format: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Export attestation to specified format
        
        Args:
            package_id: Package identifier
            format: Export format (json, oscal, pdf)
            options: Export options
        
        Returns:
            Export information
        """
        # Load package
        package = await self._get_package(package_id)
        options = options or {}
        
        if format == "json":
            file_path = self.package_builder.export_package(
                package,
                AttestationFormat.JSON
            )
            return {
                "format": "json",
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size
            }
        
        elif format == "oscal":
            doc_type = options.get("document_type", "assessment-results")
            
            if doc_type == "assessment-results":
                oscal_doc = self.oscal_exporter.export_assessment_results(package)
            elif doc_type == "system-security-plan":
                oscal_doc = self.oscal_exporter.export_system_security_plan(package)
            elif doc_type == "plan-of-action-and-milestones":
                oscal_doc = self.oscal_exporter.export_plan_of_action(package)
            else:
                raise ValidationError(f"Unsupported OSCAL document type: {doc_type}")
            
            file_path = self.oscal_exporter.save_to_file(oscal_doc)
            
            return {
                "format": "oscal",
                "document_type": doc_type,
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size
            }
        
        elif format == "pdf":
            report_type = options.get("report_type", "full")
            
            if report_type == "full":
                report = self.pdf_generator.generate_attestation_report(
                    package,
                    include_evidence=options.get("include_evidence", True),
                    include_proofs=options.get("include_proofs", True)
                )
            elif report_type == "summary":
                report = self.pdf_generator.generate_executive_summary(package)
            elif report_type == "compliance":
                framework = options.get("framework", package.compliance_framework)
                if not framework:
                    raise ValidationError("Framework required for compliance report")
                report = self.pdf_generator.generate_compliance_report(package, framework)
            else:
                raise ValidationError(f"Unsupported PDF report type: {report_type}")
            
            return {
                "format": "pdf",
                "report_type": report_type,
                "file_path": report.file_path,
                "file_size": report.file_size,
                "page_count": report.page_count
            }
        
        else:
            raise ValidationError(f"Unsupported export format: {format}")
    
    async def publish_attestation(
        self,
        package_id: str
    ) -> Dict[str, Any]:
        """
        Publish attestation package
        
        Args:
            package_id: Package identifier
        
        Returns:
            Published package info
        """
        # Load package
        package = await self._get_package(package_id)
        
        # Verify package is signed
        if package.status != AttestationStatus.SIGNED:
            raise ValidationError("Package must be signed before publishing")
        
        # Update status
        package = self.package_builder.update_package_status(
            package,
            AttestationStatus.PUBLISHED
        )
        
        # Update database
        await self._update_package_in_db(package)
        
        return self.package_builder.get_package_summary(package)
    
    async def revoke_attestation(
        self,
        package_id: str,
        reason: str
    ) -> Dict[str, Any]:
        """
        Revoke attestation package
        
        Args:
            package_id: Package identifier
            reason: Revocation reason
        
        Returns:
            Revoked package info
        """
        # Load package
        package = await self._get_package(package_id)
        
        # Update status
        package = self.package_builder.update_package_status(
            package,
            AttestationStatus.REVOKED
        )
        
        # Add revocation metadata
        self.package_builder.add_metadata(package, {
            "revocation": {
                "revoked_at": datetime.utcnow().isoformat(),
                "reason": reason,
                "revoked_by": self.user_id
            }
        })
        
        # Update database
        await self._update_package_in_db(package)
        
        return self.package_builder.get_package_summary(package)
    
    async def list_attestations(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List attestation packages
        
        Args:
            status: Filter by status
            limit: Max results
            offset: Pagination offset
        
        Returns:
            List of attestations
        """
        query = select(AttestationPackageModel).where(
            AttestationPackageModel.tenant_id == self.tenant_id
        ).limit(limit).offset(offset)
        
        if status:
            query = query.where(AttestationPackageModel.status == status)
        
        result = await self.db.execute(query)
        packages = result.scalars().all()
        
        return {
            "attestations": [
                {
                    "package_id": pkg.package_id,
                    "claim_id": pkg.claim_id,
                    "title": pkg.title,
                    "status": pkg.status,
                    "created_at": pkg.created_at.isoformat() if pkg.created_at else None
                }
                for pkg in packages
            ],
            "total": len(packages),
            "limit": limit,
            "offset": offset
        }
    
    async def get_attestation_details(
        self,
        package_id: str
    ) -> Dict[str, Any]:
        """
        Get detailed attestation information
        
        Args:
            package_id: Package identifier
        
        Returns:
            Detailed package info
        """
        package = await self._get_package(package_id)
        
        summary = self.package_builder.get_package_summary(package)
        
        # Add full package data
        summary["claim_data"] = package.claim_data
        summary["evidence_bundles"] = package.evidence_bundles
        summary["proofs"] = package.proofs
        
        return summary
    
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
    
    async def _get_package(self, package_id: str) -> AttestationPackage:
        """Get package from storage"""
        package = self.package_builder.load_package(package_id)
        
        if not package:
            raise NotFoundError(f"Package not found: {package_id}")
        
        if package.tenant_id != self.tenant_id:
            raise AuthorizationError("Access denied to package")
        
        return package
    
    async def _update_package_in_db(self, package: AttestationPackage):
        """Update package in database"""
        result = await self.db.execute(
            select(AttestationPackageModel).where(
                AttestationPackageModel.package_id == package.package_id
            )
        )
        package_model = result.scalar_one_or_none()
        
        if package_model:
            package_model.status = package.status.value
            package_model.package_data = package.dict()
            await self.db.commit()

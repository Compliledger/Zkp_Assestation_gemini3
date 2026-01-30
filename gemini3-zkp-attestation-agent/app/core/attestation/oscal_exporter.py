"""
OSCAL Format Exporter
Exports attestation packages to OSCAL (Open Security Controls Assessment Language) format
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import json
import uuid
from pydantic import BaseModel, Field

from app.core.attestation.package_builder import AttestationPackage
from app.utils.errors import ValidationError


class OSCALDocument(BaseModel):
    """
    OSCAL document structure
    """
    oscal_version: str = Field(default="1.0.6", description="OSCAL version")
    document_type: str = Field(..., description="Document type (assessment-results, ssp, etc.)")
    uuid: str = Field(..., description="Document UUID")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")
    content: Dict[str, Any] = Field(..., description="Document content")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OSCALExporter:
    """
    Exports attestation packages to OSCAL format
    """
    
    def __init__(self, output_path: Optional[Path] = None):
        """
        Initialize OSCAL exporter
        
        Args:
            output_path: Path for OSCAL exports
        """
        self.output_path = output_path or Path("./exports/oscal")
        self.output_path.mkdir(parents=True, exist_ok=True)
    
    def export_assessment_results(
        self,
        package: AttestationPackage
    ) -> OSCALDocument:
        """
        Export package as OSCAL Assessment Results
        
        Args:
            package: Attestation package
        
        Returns:
            OSCAL document
        """
        # Generate UUID
        doc_uuid = str(uuid.uuid4())
        
        # Build metadata
        metadata = self._build_metadata(package)
        
        # Build assessment results content
        content = {
            "assessment-results": {
                "uuid": doc_uuid,
                "metadata": metadata,
                "import-ap": self._build_import_ap(package),
                "local-definitions": self._build_local_definitions(package),
                "results": [self._build_result(package)]
            }
        }
        
        oscal_doc = OSCALDocument(
            document_type="assessment-results",
            uuid=doc_uuid,
            metadata=metadata,
            content=content
        )
        
        return oscal_doc
    
    def export_system_security_plan(
        self,
        package: AttestationPackage
    ) -> OSCALDocument:
        """
        Export package as OSCAL System Security Plan
        
        Args:
            package: Attestation package
        
        Returns:
            OSCAL document
        """
        doc_uuid = str(uuid.uuid4())
        metadata = self._build_metadata(package)
        
        content = {
            "system-security-plan": {
                "uuid": doc_uuid,
                "metadata": metadata,
                "import-profile": self._build_import_profile(package),
                "system-characteristics": self._build_system_characteristics(package),
                "system-implementation": self._build_system_implementation(package),
                "control-implementation": self._build_control_implementation(package)
            }
        }
        
        oscal_doc = OSCALDocument(
            document_type="system-security-plan",
            uuid=doc_uuid,
            metadata=metadata,
            content=content
        )
        
        return oscal_doc
    
    def export_plan_of_action(
        self,
        package: AttestationPackage
    ) -> OSCALDocument:
        """
        Export package as OSCAL Plan of Action and Milestones
        
        Args:
            package: Attestation package
        
        Returns:
            OSCAL document
        """
        doc_uuid = str(uuid.uuid4())
        metadata = self._build_metadata(package)
        
        content = {
            "plan-of-action-and-milestones": {
                "uuid": doc_uuid,
                "metadata": metadata,
                "import-ssp": self._build_import_ssp(package),
                "local-definitions": self._build_local_definitions(package),
                "observations": self._build_observations(package),
                "risks": self._build_risks(package),
                "poam-items": []
            }
        }
        
        oscal_doc = OSCALDocument(
            document_type="plan-of-action-and-milestones",
            uuid=doc_uuid,
            metadata=metadata,
            content=content
        )
        
        return oscal_doc
    
    def save_to_file(
        self,
        oscal_doc: OSCALDocument,
        filename: Optional[str] = None
    ) -> Path:
        """
        Save OSCAL document to file
        
        Args:
            oscal_doc: OSCAL document
            filename: Output filename
        
        Returns:
            Path to saved file
        """
        if not filename:
            filename = f"{oscal_doc.document_type}_{oscal_doc.uuid}.json"
        
        output_file = self.output_path / filename
        
        # Write OSCAL JSON
        output_file.write_text(
            json.dumps(oscal_doc.content, indent=2, default=str)
        )
        
        return output_file
    
    def _build_metadata(self, package: AttestationPackage) -> Dict[str, Any]:
        """Build OSCAL metadata section"""
        return {
            "title": package.title,
            "last-modified": datetime.utcnow().isoformat(),
            "version": package.version,
            "oscal-version": "1.0.6",
            "published": package.published_at.isoformat() if package.published_at else None,
            "roles": [
                {
                    "id": "assessor",
                    "title": "Assessor"
                },
                {
                    "id": "issuer",
                    "title": "Attestation Issuer"
                }
            ],
            "parties": [
                {
                    "uuid": str(uuid.uuid4()),
                    "type": "organization",
                    "name": package.issuer.get("name", "Unknown"),
                    "email-addresses": [package.issuer.get("email", "")],
                    "addresses": []
                }
            ],
            "responsible-parties": [
                {
                    "role-id": "issuer",
                    "party-uuids": [str(uuid.uuid4())]
                }
            ],
            "remarks": package.description
        }
    
    def _build_import_ap(self, package: AttestationPackage) -> Dict[str, Any]:
        """Build import assessment plan section"""
        return {
            "href": f"#assessment-plan-{package.claim_id}",
            "remarks": f"Assessment plan for {package.attestation_type}"
        }
    
    def _build_import_profile(self, package: AttestationPackage) -> Dict[str, Any]:
        """Build import profile section"""
        framework = package.compliance_framework or "custom"
        return {
            "href": f"#{framework.lower().replace(' ', '-')}-profile",
            "remarks": f"Profile for {framework}"
        }
    
    def _build_import_ssp(self, package: AttestationPackage) -> Dict[str, Any]:
        """Build import SSP section"""
        return {
            "href": f"#ssp-{package.claim_id}",
            "remarks": "System Security Plan reference"
        }
    
    def _build_local_definitions(self, package: AttestationPackage) -> Dict[str, Any]:
        """Build local definitions section"""
        return {
            "components": [],
            "inventory-items": [],
            "remarks": "Local definitions for assessment"
        }
    
    def _build_result(self, package: AttestationPackage) -> Dict[str, Any]:
        """Build assessment result"""
        return {
            "uuid": str(uuid.uuid4()),
            "title": f"Assessment Results - {package.title}",
            "description": package.description,
            "start": package.valid_from.isoformat(),
            "end": package.valid_until.isoformat() if package.valid_until else None,
            "reviewed-controls": self._build_reviewed_controls(package),
            "attestations": self._build_attestations(package),
            "assessment-log": self._build_assessment_log(package)
        }
    
    def _build_reviewed_controls(self, package: AttestationPackage) -> Dict[str, Any]:
        """Build reviewed controls section"""
        controls = []
        
        # Extract controls from claim data
        if "controls" in package.claim_data:
            for control_id in package.claim_data["controls"]:
                controls.append({
                    "control-id": control_id,
                    "control-selections": [
                        {
                            "description": f"Selected control {control_id}"
                        }
                    ]
                })
        
        return {
            "control-selections": controls
        }
    
    def _build_attestations(self, package: AttestationPackage) -> List[Dict[str, Any]]:
        """Build attestations section"""
        attestations = []
        
        for proof in package.proofs:
            attestation = {
                "responsible-parties": [],
                "parts": [
                    {
                        "name": "attestation-statement",
                        "prose": f"ZKP proof {proof['proof_id']} validates compliance"
                    },
                    {
                        "name": "proof-type",
                        "prose": proof["circuit_type"]
                    },
                    {
                        "name": "proof-hash",
                        "prose": proof["proof_hash"]
                    }
                ]
            }
            attestations.append(attestation)
        
        return attestations
    
    def _build_assessment_log(self, package: AttestationPackage) -> Dict[str, Any]:
        """Build assessment log"""
        entries = []
        
        # Add assembly entry
        if package.assembled_at:
            entries.append({
                "uuid": str(uuid.uuid4()),
                "title": "Package Assembly",
                "description": "Attestation package assembled",
                "start": package.assembled_at.isoformat(),
                "logged-by": [{"party-uuid": str(uuid.uuid4())}]
            })
        
        # Add signing entry
        if package.signed_at:
            entries.append({
                "uuid": str(uuid.uuid4()),
                "title": "Digital Signature",
                "description": "Package digitally signed",
                "start": package.signed_at.isoformat(),
                "logged-by": [{"party-uuid": str(uuid.uuid4())}]
            })
        
        return {
            "entries": entries
        }
    
    def _build_system_characteristics(self, package: AttestationPackage) -> Dict[str, Any]:
        """Build system characteristics section"""
        return {
            "system-ids": [
                {
                    "identifier-type": "claim",
                    "id": package.claim_id
                }
            ],
            "system-name": package.title,
            "description": package.description,
            "security-sensitivity-level": "moderate",
            "system-information": {
                "information-types": []
            },
            "security-impact-level": {
                "security-objective-confidentiality": "moderate",
                "security-objective-integrity": "high",
                "security-objective-availability": "moderate"
            },
            "status": {
                "state": "operational"
            },
            "authorization-boundary": {
                "description": "System authorization boundary"
            }
        }
    
    def _build_system_implementation(self, package: AttestationPackage) -> Dict[str, Any]:
        """Build system implementation section"""
        return {
            "users": [],
            "components": [],
            "remarks": "System implementation details"
        }
    
    def _build_control_implementation(self, package: AttestationPackage) -> Dict[str, Any]:
        """Build control implementation section"""
        return {
            "description": "Control implementation description",
            "implemented-requirements": []
        }
    
    def _build_observations(self, package: AttestationPackage) -> List[Dict[str, Any]]:
        """Build observations section"""
        observations = []
        
        for evidence_bundle in package.evidence_bundles:
            observation = {
                "uuid": str(uuid.uuid4()),
                "description": f"Evidence bundle {evidence_bundle['bundle_id']}",
                "methods": ["EXAMINE"],
                "types": ["evidence"],
                "collected": evidence_bundle.get("created_at", datetime.utcnow().isoformat())
            }
            observations.append(observation)
        
        return observations
    
    def _build_risks(self, package: AttestationPackage) -> List[Dict[str, Any]]:
        """Build risks section"""
        return []
    
    def validate_oscal(self, oscal_doc: OSCALDocument) -> bool:
        """
        Validate OSCAL document structure
        
        Args:
            oscal_doc: OSCAL document
        
        Returns:
            True if valid
        
        Raises:
            ValidationError: If invalid
        """
        # Check required fields
        if not oscal_doc.uuid:
            raise ValidationError("OSCAL document must have UUID")
        
        if not oscal_doc.metadata:
            raise ValidationError("OSCAL document must have metadata")
        
        if not oscal_doc.content:
            raise ValidationError("OSCAL document must have content")
        
        # Validate metadata
        metadata = oscal_doc.metadata
        if "title" not in metadata:
            raise ValidationError("OSCAL metadata must have title")
        
        if "last-modified" not in metadata:
            raise ValidationError("OSCAL metadata must have last-modified")
        
        return True
    
    def get_supported_types(self) -> List[str]:
        """Get list of supported OSCAL document types"""
        return [
            "assessment-results",
            "system-security-plan",
            "plan-of-action-and-milestones",
            "assessment-plan"
        ]

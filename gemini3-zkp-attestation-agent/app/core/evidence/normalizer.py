"""
Evidence Normalizer
Converts various evidence formats into canonical normalized format
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
import json
import base64
from pathlib import Path

from app.utils.crypto import HashUtils
from app.utils.errors import ValidationError


class NormalizedEvidence(BaseModel):
    """
    Canonical evidence format after normalization
    """
    evidence_id: str = Field(..., description="Unique evidence identifier")
    evidence_type: str = Field(..., description="Type of evidence (log, scan, artifact, etc.)")
    source_system: str = Field(..., description="System that generated the evidence")
    source_id: Optional[str] = Field(None, description="Original ID in source system")
    
    # Content
    content_hash: str = Field(..., description="SHA-256 hash of evidence content")
    content_type: str = Field(..., description="MIME type or format")
    content_size: int = Field(..., description="Size in bytes")
    
    # Metadata
    collected_at: datetime = Field(..., description="When evidence was collected")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Provenance
    collector_id: Optional[str] = Field(None, description="ID of collector agent/system")
    collection_method: Optional[str] = Field(None, description="How evidence was collected")
    chain_of_custody: List[Dict[str, Any]] = Field(default_factory=list, description="Custody chain")
    
    # Classification
    sensitivity_level: str = Field(default="normal", description="Sensitivity: public, internal, confidential, secret")
    compliance_tags: List[str] = Field(default_factory=list, description="Compliance framework tags")
    
    @validator('sensitivity_level')
    def validate_sensitivity(cls, v):
        valid_levels = ['public', 'internal', 'confidential', 'secret']
        if v not in valid_levels:
            raise ValueError(f"sensitivity_level must be one of {valid_levels}")
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EvidenceNormalizer:
    """
    Normalizes evidence from various sources into canonical format
    """
    
    # Supported evidence types
    SUPPORTED_TYPES = {
        'log',
        'scan_result',
        'test_result',
        'code_artifact',
        'configuration',
        'certificate',
        'audit_record',
        'compliance_report',
        'vulnerability_scan',
        'penetration_test',
        'access_log',
        'change_log',
    }
    
    # Supported source systems
    SUPPORTED_SOURCES = {
        'github',
        'gitlab',
        'jenkins',
        'sonarqube',
        'veracode',
        'snyk',
        'cma',  # CompliLedger CMA
        'sca',  # Software Composition Analysis
        'sast', # Static Analysis
        'dast', # Dynamic Analysis
        'manual', # Manual upload
    }
    
    def __init__(self):
        self.hash_utils = HashUtils()
    
    def normalize(
        self,
        raw_evidence: Union[Dict[str, Any], str, bytes],
        evidence_type: str,
        source_system: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> NormalizedEvidence:
        """
        Normalize raw evidence into canonical format
        
        Args:
            raw_evidence: Raw evidence data (dict, string, or bytes)
            evidence_type: Type of evidence
            source_system: Source system identifier
            metadata: Additional metadata
        
        Returns:
            NormalizedEvidence instance
        
        Raises:
            ValidationError: If evidence cannot be normalized
        """
        # Validate inputs
        if evidence_type not in self.SUPPORTED_TYPES:
            raise ValidationError(f"Unsupported evidence type: {evidence_type}")
        
        if source_system not in self.SUPPORTED_SOURCES:
            raise ValidationError(f"Unsupported source system: {source_system}")
        
        # Convert to bytes for hashing
        content_bytes = self._to_bytes(raw_evidence)
        
        # Generate hash
        content_hash = self.hash_utils.sha256(content_bytes)
        
        # Determine content type
        content_type = self._determine_content_type(raw_evidence)
        
        # Generate evidence ID (hash-based for deduplication)
        evidence_id = f"{source_system}:{evidence_type}:{content_hash[:16]}"
        
        # Extract metadata from source if available
        extracted_metadata = self._extract_metadata(raw_evidence, source_system)
        if metadata:
            extracted_metadata.update(metadata)
        
        # Create normalized evidence
        normalized = NormalizedEvidence(
            evidence_id=evidence_id,
            evidence_type=evidence_type,
            source_system=source_system,
            content_hash=content_hash,
            content_type=content_type,
            content_size=len(content_bytes),
            collected_at=datetime.utcnow(),
            metadata=extracted_metadata,
            source_id=extracted_metadata.get('source_id'),
            collector_id=extracted_metadata.get('collector_id'),
            collection_method=extracted_metadata.get('collection_method', 'api'),
            sensitivity_level=extracted_metadata.get('sensitivity_level', 'internal'),
            compliance_tags=extracted_metadata.get('compliance_tags', [])
        )
        
        return normalized
    
    def normalize_batch(
        self,
        evidence_list: List[Dict[str, Any]]
    ) -> List[NormalizedEvidence]:
        """
        Normalize multiple evidence items
        
        Args:
            evidence_list: List of evidence items with required fields
        
        Returns:
            List of normalized evidence
        """
        normalized_list = []
        
        for item in evidence_list:
            try:
                normalized = self.normalize(
                    raw_evidence=item.get('content'),
                    evidence_type=item.get('type'),
                    source_system=item.get('source'),
                    metadata=item.get('metadata')
                )
                normalized_list.append(normalized)
            except Exception as e:
                # Log error but continue processing other items
                print(f"Error normalizing evidence: {e}")
                continue
        
        return normalized_list
    
    def _to_bytes(self, data: Union[Dict, str, bytes]) -> bytes:
        """Convert data to bytes for hashing"""
        if isinstance(data, bytes):
            return data
        elif isinstance(data, str):
            return data.encode('utf-8')
        elif isinstance(data, dict):
            # Sort keys for consistent hashing
            return json.dumps(data, sort_keys=True).encode('utf-8')
        else:
            return str(data).encode('utf-8')
    
    def _determine_content_type(self, data: Union[Dict, str, bytes]) -> str:
        """Determine MIME type or content format"""
        if isinstance(data, bytes):
            # Try to detect file type
            if data.startswith(b'%PDF'):
                return 'application/pdf'
            elif data.startswith(b'\x89PNG'):
                return 'image/png'
            elif data.startswith(b'\xff\xd8\xff'):
                return 'image/jpeg'
            else:
                return 'application/octet-stream'
        elif isinstance(data, dict):
            return 'application/json'
        else:
            return 'text/plain'
    
    def _extract_metadata(
        self,
        raw_evidence: Union[Dict, str, bytes],
        source_system: str
    ) -> Dict[str, Any]:
        """Extract metadata from evidence based on source system"""
        metadata = {}
        
        if not isinstance(raw_evidence, dict):
            return metadata
        
        # Source-specific metadata extraction
        if source_system == 'github':
            metadata.update(self._extract_github_metadata(raw_evidence))
        elif source_system == 'gitlab':
            metadata.update(self._extract_gitlab_metadata(raw_evidence))
        elif source_system == 'sonarqube':
            metadata.update(self._extract_sonarqube_metadata(raw_evidence))
        elif source_system == 'cma':
            metadata.update(self._extract_cma_metadata(raw_evidence))
        
        return metadata
    
    def _extract_github_metadata(self, data: Dict) -> Dict[str, Any]:
        """Extract GitHub-specific metadata"""
        return {
            'repository': data.get('repository'),
            'commit_sha': data.get('commit_sha'),
            'branch': data.get('branch'),
            'author': data.get('author'),
            'timestamp': data.get('timestamp'),
            'source_id': data.get('id'),
        }
    
    def _extract_gitlab_metadata(self, data: Dict) -> Dict[str, Any]:
        """Extract GitLab-specific metadata"""
        return {
            'project_id': data.get('project_id'),
            'commit_sha': data.get('commit_sha'),
            'branch': data.get('ref'),
            'author': data.get('user_username'),
            'timestamp': data.get('created_at'),
            'source_id': data.get('id'),
        }
    
    def _extract_sonarqube_metadata(self, data: Dict) -> Dict[str, Any]:
        """Extract SonarQube-specific metadata"""
        return {
            'project_key': data.get('projectKey'),
            'analysis_id': data.get('analysisId'),
            'quality_gate': data.get('qualityGate', {}).get('status'),
            'timestamp': data.get('analysedAt'),
            'source_id': data.get('taskId'),
        }
    
    def _extract_cma_metadata(self, data: Dict) -> Dict[str, Any]:
        """Extract CMA (Continuous Monitoring Agent) metadata"""
        return {
            'assessment_id': data.get('assessmentId'),
            'control_id': data.get('controlId'),
            'framework': data.get('framework'),
            'status': data.get('status'),
            'timestamp': data.get('timestamp'),
            'collector_id': data.get('agentId'),
            'source_id': data.get('evidenceId'),
        }
    
    @staticmethod
    def validate_format(evidence_type: str, content: Any) -> bool:
        """
        Validate that evidence content matches expected format for type
        
        Args:
            evidence_type: Type of evidence
            content: Evidence content
        
        Returns:
            True if format is valid
        """
        # Format validation rules per evidence type
        format_rules = {
            'log': lambda c: isinstance(c, (str, dict)),
            'scan_result': lambda c: isinstance(c, dict) and 'findings' in c,
            'test_result': lambda c: isinstance(c, dict) and 'status' in c,
            'code_artifact': lambda c: isinstance(c, (str, bytes)),
            'configuration': lambda c: isinstance(c, dict),
        }
        
        validator = format_rules.get(evidence_type, lambda c: True)
        return validator(content)

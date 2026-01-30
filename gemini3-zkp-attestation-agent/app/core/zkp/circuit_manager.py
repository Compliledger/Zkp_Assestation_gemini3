"""
ZKP Circuit Manager
Manages circuit templates, compilation, and circuit lifecycle
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from enum import Enum
import json
import hashlib
from pydantic import BaseModel, Field

from app.utils.errors import ValidationError, NotFoundError
from app.config import settings


class CircuitType(str, Enum):
    """Supported circuit types"""
    MERKLE_PROOF = "merkle_proof"
    RANGE_PROOF = "range_proof"
    MEMBERSHIP_PROOF = "membership_proof"
    EQUALITY_PROOF = "equality_proof"
    THRESHOLD_PROOF = "threshold_proof"
    COMPLIANCE_PROOF = "compliance_proof"


class CircuitTemplate(BaseModel):
    """
    ZKP Circuit Template Definition
    """
    template_id: str = Field(..., description="Unique template identifier")
    circuit_type: CircuitType = Field(..., description="Type of circuit")
    version: str = Field(..., description="Template version")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Circuit description")
    
    # Circuit specification
    input_schema: Dict[str, Any] = Field(..., description="Expected input structure")
    public_inputs: List[str] = Field(default_factory=list, description="Public input names")
    private_inputs: List[str] = Field(default_factory=list, description="Private input names")
    
    # Circuit metadata
    constraint_count: Optional[int] = Field(None, description="Number of constraints")
    variable_count: Optional[int] = Field(None, description="Number of variables")
    proving_time_estimate: Optional[float] = Field(None, description="Estimated proving time (seconds)")
    
    # Circuit files
    circuit_file: Optional[str] = Field(None, description="Circuit definition file path")
    proving_key_file: Optional[str] = Field(None, description="Proving key file path")
    verification_key_file: Optional[str] = Field(None, description="Verification key file path")
    
    # Status
    is_compiled: bool = Field(default=False, description="Whether circuit is compiled")
    is_trusted_setup_done: bool = Field(default=False, description="Whether trusted setup is complete")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def compute_hash(self) -> str:
        """Compute hash of circuit template for integrity checking"""
        content = f"{self.template_id}{self.version}{json.dumps(self.input_schema, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()


class CircuitManager:
    """
    Manages ZKP circuit templates and lifecycle
    """
    
    def __init__(self, circuits_path: Optional[Path] = None):
        """
        Initialize circuit manager
        
        Args:
            circuits_path: Path to circuits directory
        """
        self.circuits_path = circuits_path or Path("./circuits")
        self.circuits_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache of templates
        self._templates: Dict[str, CircuitTemplate] = {}
        
        # Load built-in templates
        self._load_builtin_templates()
    
    def register_template(self, template: CircuitTemplate) -> CircuitTemplate:
        """
        Register a new circuit template
        
        Args:
            template: Circuit template to register
        
        Returns:
            Registered template
        
        Raises:
            ValidationError: If template is invalid
        """
        # Validate template
        if not template.template_id:
            raise ValidationError("Template ID is required")
        
        if template.template_id in self._templates:
            raise ValidationError(f"Template already exists: {template.template_id}")
        
        # Store template
        self._templates[template.template_id] = template
        
        # Persist to disk
        self._save_template(template)
        
        return template
    
    def get_template(self, template_id: str) -> CircuitTemplate:
        """
        Get circuit template by ID
        
        Args:
            template_id: Template identifier
        
        Returns:
            Circuit template
        
        Raises:
            NotFoundError: If template not found
        """
        if template_id not in self._templates:
            # Try loading from disk
            template = self._load_template(template_id)
            if template:
                self._templates[template_id] = template
            else:
                raise NotFoundError(f"Circuit template not found: {template_id}")
        
        return self._templates[template_id]
    
    def list_templates(
        self,
        circuit_type: Optional[CircuitType] = None,
        compiled_only: bool = False
    ) -> List[CircuitTemplate]:
        """
        List available circuit templates
        
        Args:
            circuit_type: Filter by circuit type
            compiled_only: Only return compiled circuits
        
        Returns:
            List of templates
        """
        templates = list(self._templates.values())
        
        # Apply filters
        if circuit_type:
            templates = [t for t in templates if t.circuit_type == circuit_type]
        
        if compiled_only:
            templates = [t for t in templates if t.is_compiled]
        
        return templates
    
    def update_template(
        self,
        template_id: str,
        updates: Dict[str, Any]
    ) -> CircuitTemplate:
        """
        Update circuit template
        
        Args:
            template_id: Template identifier
            updates: Fields to update
        
        Returns:
            Updated template
        """
        template = self.get_template(template_id)
        
        # Update fields
        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        template.updated_at = datetime.utcnow()
        
        # Persist changes
        self._save_template(template)
        
        return template
    
    def compile_circuit(
        self,
        template_id: str,
        circuit_code: Optional[str] = None
    ) -> CircuitTemplate:
        """
        Compile circuit from template
        
        Args:
            template_id: Template identifier
            circuit_code: Optional circuit code (Circom, etc.)
        
        Returns:
            Updated template with compilation status
        """
        template = self.get_template(template_id)
        
        # In production, this would invoke actual circuit compiler (circom, gnark, etc.)
        # For now, we simulate compilation
        
        if circuit_code:
            # Save circuit code
            circuit_file = self.circuits_path / f"{template_id}.circom"
            circuit_file.write_text(circuit_code)
            template.circuit_file = str(circuit_file)
        
        # Mark as compiled
        template.is_compiled = True
        template.updated_at = datetime.utcnow()
        
        # Persist changes
        self._save_template(template)
        
        return template
    
    def perform_trusted_setup(
        self,
        template_id: str,
        entropy: Optional[bytes] = None
    ) -> CircuitTemplate:
        """
        Perform trusted setup for circuit
        
        Args:
            template_id: Template identifier
            entropy: Optional entropy for setup
        
        Returns:
            Updated template with setup keys
        """
        template = self.get_template(template_id)
        
        if not template.is_compiled:
            raise ValidationError("Circuit must be compiled before trusted setup")
        
        # In production, this would run actual trusted setup ceremony
        # For now, we simulate key generation
        
        # Generate proving and verification keys
        proving_key_file = self.circuits_path / f"{template_id}_proving.key"
        verification_key_file = self.circuits_path / f"{template_id}_verification.key"
        
        # Simulate key generation
        proving_key_file.write_bytes(b"simulated_proving_key")
        verification_key_file.write_bytes(b"simulated_verification_key")
        
        template.proving_key_file = str(proving_key_file)
        template.verification_key_file = str(verification_key_file)
        template.is_trusted_setup_done = True
        template.updated_at = datetime.utcnow()
        
        # Persist changes
        self._save_template(template)
        
        return template
    
    def validate_inputs(
        self,
        template_id: str,
        inputs: Dict[str, Any]
    ) -> bool:
        """
        Validate inputs against circuit template schema
        
        Args:
            template_id: Template identifier
            inputs: Input values to validate
        
        Returns:
            True if inputs are valid
        
        Raises:
            ValidationError: If inputs are invalid
        """
        template = self.get_template(template_id)
        
        # Check all required inputs are provided
        all_inputs = set(template.public_inputs + template.private_inputs)
        provided_inputs = set(inputs.keys())
        
        missing = all_inputs - provided_inputs
        if missing:
            raise ValidationError(f"Missing required inputs: {missing}")
        
        # Check input types match schema
        for input_name, expected_type in template.input_schema.items():
            if input_name in inputs:
                actual_value = inputs[input_name]
                # Basic type validation
                if not self._validate_input_type(actual_value, expected_type):
                    raise ValidationError(
                        f"Invalid type for input '{input_name}': "
                        f"expected {expected_type}, got {type(actual_value)}"
                    )
        
        return True
    
    def _validate_input_type(self, value: Any, expected_type: Any) -> bool:
        """Validate input type matches expected type"""
        if expected_type == "field":
            return isinstance(value, (int, str))
        elif expected_type == "bool":
            return isinstance(value, bool)
        elif expected_type == "array":
            return isinstance(value, list)
        elif expected_type == "hash":
            return isinstance(value, str) and len(value) == 64  # SHA-256
        else:
            return True  # Accept any type for unknown types
    
    def _load_builtin_templates(self):
        """Load built-in circuit templates"""
        # Merkle proof circuit
        merkle_template = CircuitTemplate(
            template_id="merkle_proof_v1",
            circuit_type=CircuitType.MERKLE_PROOF,
            version="1.0.0",
            name="Merkle Tree Membership Proof",
            description="Proves that a leaf is part of a Merkle tree without revealing the leaf",
            input_schema={
                "leaf": "hash",
                "root": "hash",
                "path_elements": "array",
                "path_indices": "array"
            },
            public_inputs=["root"],
            private_inputs=["leaf", "path_elements", "path_indices"],
            constraint_count=1000,
            variable_count=500,
            proving_time_estimate=0.5,
            is_compiled=True,  # Simulated as pre-compiled
            is_trusted_setup_done=True
        )
        
        # Compliance proof circuit
        compliance_template = CircuitTemplate(
            template_id="compliance_proof_v1",
            circuit_type=CircuitType.COMPLIANCE_PROOF,
            version="1.0.0",
            name="Compliance Attestation Proof",
            description="Proves compliance without revealing specific evidence",
            input_schema={
                "evidence_count": "field",
                "evidence_hashes": "array",
                "merkle_root": "hash",
                "compliance_threshold": "field",
                "passed_count": "field"
            },
            public_inputs=["merkle_root", "compliance_threshold"],
            private_inputs=["evidence_count", "evidence_hashes", "passed_count"],
            constraint_count=5000,
            variable_count=2000,
            proving_time_estimate=2.0,
            is_compiled=True,
            is_trusted_setup_done=True
        )
        
        # Range proof circuit
        range_template = CircuitTemplate(
            template_id="range_proof_v1",
            circuit_type=CircuitType.RANGE_PROOF,
            version="1.0.0",
            name="Range Proof",
            description="Proves a value is within a range without revealing the value",
            input_schema={
                "value": "field",
                "min": "field",
                "max": "field"
            },
            public_inputs=["min", "max"],
            private_inputs=["value"],
            constraint_count=500,
            variable_count=250,
            proving_time_estimate=0.2,
            is_compiled=True,
            is_trusted_setup_done=True
        )
        
        self._templates = {
            merkle_template.template_id: merkle_template,
            compliance_template.template_id: compliance_template,
            range_template.template_id: range_template,
        }
    
    def _save_template(self, template: CircuitTemplate):
        """Save template to disk"""
        template_file = self.circuits_path / f"{template.template_id}.json"
        template_file.write_text(template.json(indent=2))
    
    def _load_template(self, template_id: str) -> Optional[CircuitTemplate]:
        """Load template from disk"""
        template_file = self.circuits_path / f"{template_id}.json"
        
        if template_file.exists():
            return CircuitTemplate.parse_raw(template_file.read_text())
        
        return None
    
    def get_circuit_statistics(self) -> Dict[str, Any]:
        """Get statistics about registered circuits"""
        total = len(self._templates)
        compiled = sum(1 for t in self._templates.values() if t.is_compiled)
        setup_done = sum(1 for t in self._templates.values() if t.is_trusted_setup_done)
        
        by_type = {}
        for template in self._templates.values():
            circuit_type = template.circuit_type.value
            by_type[circuit_type] = by_type.get(circuit_type, 0) + 1
        
        return {
            "total_templates": total,
            "compiled": compiled,
            "trusted_setup_complete": setup_done,
            "by_type": by_type,
            "ready_for_use": setup_done
        }

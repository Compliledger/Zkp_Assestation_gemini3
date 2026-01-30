"""
Digital Signature Manager
Manages digital signatures for attestation packages
"""

from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field
import json
import hashlib

from app.core.attestation.package_builder import AttestationPackage
from app.utils.crypto import HashUtils
from app.utils.errors import ValidationError, SignatureError


class SignatureAlgorithm(str, Enum):
    """Supported signature algorithms"""
    RSA_SHA256 = "RSA-SHA256"
    ECDSA_SHA256 = "ECDSA-SHA256"
    ED25519 = "Ed25519"


class KeyType(str, Enum):
    """Key types"""
    RSA_2048 = "RSA-2048"
    RSA_4096 = "RSA-4096"
    ECDSA_P256 = "ECDSA-P256"
    ED25519 = "Ed25519"


class DigitalSignature(BaseModel):
    """
    Digital signature for attestation package
    """
    signature_id: str = Field(..., description="Signature identifier")
    package_id: str = Field(..., description="Signed package ID")
    algorithm: SignatureAlgorithm = Field(..., description="Signature algorithm")
    signature_value: str = Field(..., description="Signature value (hex)")
    public_key: str = Field(..., description="Public key (PEM or hex)")
    certificate: Optional[str] = Field(None, description="X.509 certificate (PEM)")
    
    # Signature metadata
    signer_id: str = Field(..., description="Signer identifier")
    signer_name: str = Field(..., description="Signer name")
    signer_email: Optional[str] = Field(None, description="Signer email")
    
    # Signed content
    package_hash: str = Field(..., description="Hash of signed package")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Verification
    is_valid: Optional[bool] = Field(None, description="Signature verification status")
    verified_at: Optional[datetime] = Field(None, description="Verification timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SignatureManager:
    """
    Manages digital signatures for attestation packages
    
    Note: This is a simplified implementation. In production, use:
    - cryptography library for real signatures
    - Hardware Security Modules (HSM)
    - Key Management Services (KMS)
    - X.509 certificate chains
    """
    
    def __init__(self, keys_path: Optional[Path] = None):
        """
        Initialize signature manager
        
        Args:
            keys_path: Path to store keys
        """
        self.keys_path = keys_path or Path("./keys")
        self.keys_path.mkdir(parents=True, exist_ok=True)
        self.hash_utils = HashUtils()
    
    def sign_package(
        self,
        package: AttestationPackage,
        signer_id: str,
        signer_name: str,
        algorithm: SignatureAlgorithm = SignatureAlgorithm.RSA_SHA256,
        private_key: Optional[str] = None,
        signer_email: Optional[str] = None
    ) -> DigitalSignature:
        """
        Sign attestation package
        
        Args:
            package: Attestation package to sign
            signer_id: Signer identifier
            signer_name: Signer name
            algorithm: Signature algorithm
            private_key: Private key (PEM or hex)
            signer_email: Signer email
        
        Returns:
            DigitalSignature instance
        
        Raises:
            SignatureError: If signing fails
        """
        # Compute package hash
        package_hash = package.compute_hash()
        
        # Generate or load key pair
        if not private_key:
            private_key, public_key = self._generate_key_pair(algorithm)
        else:
            public_key = self._extract_public_key(private_key, algorithm)
        
        # Sign package hash
        try:
            signature_value = self._sign_data(package_hash, private_key, algorithm)
        except Exception as e:
            raise SignatureError(f"Failed to sign package: {e}")
        
        # Create signature object
        signature_id = self._generate_signature_id(package.package_id)
        
        signature = DigitalSignature(
            signature_id=signature_id,
            package_id=package.package_id,
            algorithm=algorithm,
            signature_value=signature_value,
            public_key=public_key,
            signer_id=signer_id,
            signer_name=signer_name,
            signer_email=signer_email,
            package_hash=package_hash
        )
        
        # Update package with signature
        package.signature = signature_value
        package.signature_algorithm = algorithm.value
        package.signed_at = datetime.utcnow()
        
        # Store signature
        self._store_signature(signature)
        
        return signature
    
    def verify_signature(
        self,
        package: AttestationPackage,
        signature: DigitalSignature
    ) -> bool:
        """
        Verify package signature
        
        Args:
            package: Attestation package
            signature: Digital signature
        
        Returns:
            True if signature is valid
        
        Raises:
            SignatureError: If verification fails
        """
        # Verify package hash matches
        current_hash = package.compute_hash()
        if current_hash != signature.package_hash:
            raise SignatureError("Package hash mismatch - content has been modified")
        
        # Verify signature
        try:
            is_valid = self._verify_signature_data(
                signature.package_hash,
                signature.signature_value,
                signature.public_key,
                signature.algorithm
            )
        except Exception as e:
            raise SignatureError(f"Signature verification failed: {e}")
        
        # Update signature verification status
        signature.is_valid = is_valid
        signature.verified_at = datetime.utcnow()
        
        return is_valid
    
    def add_countersignature(
        self,
        package: AttestationPackage,
        original_signature: DigitalSignature,
        countersigner_id: str,
        countersigner_name: str,
        algorithm: SignatureAlgorithm = SignatureAlgorithm.RSA_SHA256
    ) -> DigitalSignature:
        """
        Add countersignature to package
        
        Args:
            package: Attestation package
            original_signature: Original signature
            countersigner_id: Countersigner ID
            countersigner_name: Countersigner name
            algorithm: Signature algorithm
        
        Returns:
            Countersignature
        """
        # Sign both package and original signature
        combined_data = f"{package.package_hash}:{original_signature.signature_value}"
        combined_hash = self.hash_utils.sha256(combined_data.encode())
        
        private_key, public_key = self._generate_key_pair(algorithm)
        signature_value = self._sign_data(combined_hash, private_key, algorithm)
        
        countersignature = DigitalSignature(
            signature_id=self._generate_signature_id(package.package_id, suffix="counter"),
            package_id=package.package_id,
            algorithm=algorithm,
            signature_value=signature_value,
            public_key=public_key,
            signer_id=countersigner_id,
            signer_name=countersigner_name,
            package_hash=combined_hash
        )
        
        return countersignature
    
    def generate_certificate(
        self,
        subject_name: str,
        subject_email: str,
        key_type: KeyType = KeyType.RSA_2048,
        validity_days: int = 365
    ) -> Dict[str, str]:
        """
        Generate self-signed certificate
        
        Args:
            subject_name: Certificate subject name
            subject_email: Subject email
            key_type: Key type
            validity_days: Certificate validity in days
        
        Returns:
            Dictionary with certificate and private key
        """
        # In production, use cryptography library to generate real certificates
        # For now, simulate certificate generation
        
        private_key, public_key = self._generate_key_pair_for_type(key_type)
        
        # Simulate certificate (would use cryptography.x509 in production)
        certificate = f"""-----BEGIN CERTIFICATE-----
SIMULATED CERTIFICATE
Subject: CN={subject_name}, E={subject_email}
Validity: {validity_days} days
Public Key: {public_key[:32]}...
-----END CERTIFICATE-----"""
        
        return {
            "certificate": certificate,
            "private_key": private_key,
            "public_key": public_key
        }
    
    def _generate_key_pair(self, algorithm: SignatureAlgorithm) -> tuple[str, str]:
        """Generate key pair for algorithm"""
        # In production, use cryptography library
        # For now, simulate key generation
        
        import secrets
        
        if algorithm == SignatureAlgorithm.RSA_SHA256:
            private_key = secrets.token_hex(256)  # Simulated RSA private key
            public_key = secrets.token_hex(64)    # Simulated RSA public key
        elif algorithm == SignatureAlgorithm.ECDSA_SHA256:
            private_key = secrets.token_hex(32)   # Simulated ECDSA private key
            public_key = secrets.token_hex(64)    # Simulated ECDSA public key
        elif algorithm == SignatureAlgorithm.ED25519:
            private_key = secrets.token_hex(32)   # Simulated Ed25519 private key
            public_key = secrets.token_hex(32)    # Simulated Ed25519 public key
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        return private_key, public_key
    
    def _generate_key_pair_for_type(self, key_type: KeyType) -> tuple[str, str]:
        """Generate key pair for key type"""
        import secrets
        
        if key_type in [KeyType.RSA_2048, KeyType.RSA_4096]:
            key_size = 256 if key_type == KeyType.RSA_2048 else 512
            private_key = secrets.token_hex(key_size)
            public_key = secrets.token_hex(64)
        elif key_type == KeyType.ECDSA_P256:
            private_key = secrets.token_hex(32)
            public_key = secrets.token_hex(64)
        elif key_type == KeyType.ED25519:
            private_key = secrets.token_hex(32)
            public_key = secrets.token_hex(32)
        else:
            raise ValueError(f"Unsupported key type: {key_type}")
        
        return private_key, public_key
    
    def _extract_public_key(self, private_key: str, algorithm: SignatureAlgorithm) -> str:
        """Extract public key from private key"""
        # In production, use cryptography library
        # For now, simulate extraction
        return hashlib.sha256(private_key.encode()).hexdigest()
    
    def _sign_data(self, data: str, private_key: str, algorithm: SignatureAlgorithm) -> str:
        """Sign data with private key"""
        # In production, use cryptography library for real signatures
        # For now, simulate signature
        
        combined = f"{data}:{private_key}:{algorithm.value}"
        signature = hashlib.sha256(combined.encode()).hexdigest()
        
        return signature
    
    def _verify_signature_data(
        self,
        data: str,
        signature: str,
        public_key: str,
        algorithm: SignatureAlgorithm
    ) -> bool:
        """Verify signature"""
        # In production, use cryptography library for real verification
        # For now, simulate verification by checking signature format
        
        # Check signature is valid hex
        try:
            int(signature, 16)
            return len(signature) == 64  # SHA-256 hex
        except ValueError:
            return False
    
    def _generate_signature_id(self, package_id: str, suffix: str = "") -> str:
        """Generate signature ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        content = f"sig_{package_id}_{suffix}_{timestamp}"
        hash_suffix = self.hash_utils.sha256(content.encode())[:8]
        return f"sig_{hash_suffix}"
    
    def _store_signature(self, signature: DigitalSignature):
        """Store signature to disk"""
        signature_file = self.keys_path / f"{signature.signature_id}.json"
        signature_file.write_text(signature.json(indent=2))
    
    def load_signature(self, signature_id: str) -> Optional[DigitalSignature]:
        """Load signature from storage"""
        signature_file = self.keys_path / f"{signature_id}.json"
        
        if signature_file.exists():
            return DigitalSignature.parse_raw(signature_file.read_text())
        
        return None
    
    def revoke_signature(self, signature_id: str, reason: str) -> bool:
        """
        Revoke signature
        
        Args:
            signature_id: Signature to revoke
            reason: Revocation reason
        
        Returns:
            True if revoked
        """
        signature = self.load_signature(signature_id)
        if not signature:
            return False
        
        # Mark as invalid
        signature.is_valid = False
        
        # Add revocation metadata
        revocation_info = {
            "revoked_at": datetime.utcnow().isoformat(),
            "reason": reason
        }
        
        # Store updated signature
        self._store_signature(signature)
        
        return True
    
    def get_signature_info(self, signature: DigitalSignature) -> Dict[str, Any]:
        """Get signature information"""
        return {
            "signature_id": signature.signature_id,
            "package_id": signature.package_id,
            "algorithm": signature.algorithm.value,
            "signer": {
                "id": signature.signer_id,
                "name": signature.signer_name,
                "email": signature.signer_email
            },
            "timestamp": signature.timestamp.isoformat(),
            "is_valid": signature.is_valid,
            "verified_at": signature.verified_at.isoformat() if signature.verified_at else None,
            "package_hash": signature.package_hash
        }
    
    def export_public_key(self, signature: DigitalSignature, format: str = "pem") -> str:
        """Export public key in specified format"""
        if format == "pem":
            return f"""-----BEGIN PUBLIC KEY-----
{signature.public_key}
-----END PUBLIC KEY-----"""
        elif format == "hex":
            return signature.public_key
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def get_supported_algorithms(self) -> list[str]:
        """Get list of supported signature algorithms"""
        return [algo.value for algo in SignatureAlgorithm]

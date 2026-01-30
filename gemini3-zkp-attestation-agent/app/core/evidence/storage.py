"""
Evidence Storage Layer
Provides encrypted storage with multiple backend support
"""

from typing import Optional, Dict, Any, BinaryIO
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod
import os
import shutil
from enum import Enum

from app.utils.crypto import CryptoUtils, KeyManager
from app.utils.errors import StorageError, ValidationError
from app.config import settings


class StorageBackendType(str, Enum):
    """Storage backend types"""
    LOCAL = "local"
    S3 = "s3"
    AZURE_BLOB = "azure_blob"


class StorageBackend(ABC):
    """
    Abstract base class for storage backends
    """
    
    @abstractmethod
    async def store(
        self,
        key: str,
        data: bytes,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store data and return URI
        
        Args:
            key: Storage key/path
            data: Data to store
            metadata: Optional metadata
        
        Returns:
            Storage URI
        """
        pass
    
    @abstractmethod
    async def retrieve(self, key: str) -> bytes:
        """
        Retrieve data by key
        
        Args:
            key: Storage key
        
        Returns:
            Stored data
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete stored data
        
        Args:
            key: Storage key
        
        Returns:
            True if deleted
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if key exists
        
        Args:
            key: Storage key
        
        Returns:
            True if exists
        """
        pass
    
    @abstractmethod
    async def get_metadata(self, key: str) -> Dict[str, Any]:
        """
        Get metadata for stored object
        
        Args:
            key: Storage key
        
        Returns:
            Metadata dictionary
        """
        pass


class LocalStorageBackend(StorageBackend):
    """
    Local filesystem storage backend
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize local storage
        
        Args:
            base_path: Base directory for storage
        """
        self.base_path = base_path or Path(settings.STORAGE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def store(
        self,
        key: str,
        data: bytes,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store data to local filesystem"""
        try:
            file_path = self.base_path / key
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write data
            file_path.write_bytes(data)
            
            # Write metadata if provided
            if metadata:
                metadata_path = file_path.with_suffix('.meta.json')
                import json
                metadata_path.write_text(json.dumps(metadata, indent=2))
            
            return f"file://{file_path.absolute()}"
        
        except Exception as e:
            raise StorageError(f"Failed to store data: {e}")
    
    async def retrieve(self, key: str) -> bytes:
        """Retrieve data from local filesystem"""
        try:
            file_path = self.base_path / key
            
            if not file_path.exists():
                raise StorageError(f"File not found: {key}")
            
            return file_path.read_bytes()
        
        except Exception as e:
            raise StorageError(f"Failed to retrieve data: {e}")
    
    async def delete(self, key: str) -> bool:
        """Delete file from local filesystem"""
        try:
            file_path = self.base_path / key
            
            if file_path.exists():
                file_path.unlink()
                
                # Delete metadata if exists
                metadata_path = file_path.with_suffix('.meta.json')
                if metadata_path.exists():
                    metadata_path.unlink()
                
                return True
            
            return False
        
        except Exception as e:
            raise StorageError(f"Failed to delete data: {e}")
    
    async def exists(self, key: str) -> bool:
        """Check if file exists"""
        file_path = self.base_path / key
        return file_path.exists()
    
    async def get_metadata(self, key: str) -> Dict[str, Any]:
        """Get file metadata"""
        try:
            file_path = self.base_path / key
            
            if not file_path.exists():
                raise StorageError(f"File not found: {key}")
            
            # Try to load custom metadata
            metadata_path = file_path.with_suffix('.meta.json')
            if metadata_path.exists():
                import json
                return json.loads(metadata_path.read_text())
            
            # Return basic file info
            stat = file_path.stat()
            return {
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }
        
        except Exception as e:
            raise StorageError(f"Failed to get metadata: {e}")


class EvidenceStorage:
    """
    Evidence storage with encryption support
    """
    
    def __init__(
        self,
        backend: Optional[StorageBackend] = None,
        master_key: Optional[bytes] = None
    ):
        """
        Initialize evidence storage
        
        Args:
            backend: Storage backend to use
            master_key: Master encryption key
        """
        self.backend = backend or LocalStorageBackend()
        self.crypto = CryptoUtils()
        self.key_manager = KeyManager(master_key) if master_key else None
        self.encrypt_by_default = settings.EVIDENCE_ENCRYPTION_ENABLED
    
    async def store_evidence(
        self,
        evidence_id: str,
        content: bytes,
        metadata: Optional[Dict[str, Any]] = None,
        encrypt: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Store evidence with optional encryption
        
        Args:
            evidence_id: Unique evidence identifier
            content: Evidence content
            metadata: Optional metadata
            encrypt: Whether to encrypt (uses default if None)
        
        Returns:
            Storage info dict with URI and encryption details
        """
        should_encrypt = encrypt if encrypt is not None else self.encrypt_by_default
        
        storage_key = self._generate_storage_key(evidence_id)
        stored_content = content
        encryption_info = None
        
        if should_encrypt:
            # Generate data key
            data_key = self.crypto.generate_key(32)
            
            # Encrypt content
            ciphertext, nonce = self.crypto.encrypt(content, data_key)
            stored_content = ciphertext + nonce
            
            # Wrap data key with master key if available
            wrapped_key = None
            if self.key_manager:
                wrapped_key = self.key_manager.wrap_key(data_key)
            
            encryption_info = {
                "encrypted": True,
                "algorithm": "AES-256-GCM",
                "wrapped_key": wrapped_key,
                "key_id": f"key_{evidence_id}"
            }
        
        # Store to backend
        storage_uri = await self.backend.store(
            storage_key,
            stored_content,
            metadata
        )
        
        return {
            "evidence_id": evidence_id,
            "storage_uri": storage_uri,
            "storage_key": storage_key,
            "size": len(stored_content),
            "encrypted": should_encrypt,
            "encryption_info": encryption_info,
            "stored_at": datetime.utcnow().isoformat()
        }
    
    async def retrieve_evidence(
        self,
        evidence_id: str,
        decrypt: bool = True
    ) -> bytes:
        """
        Retrieve evidence with optional decryption
        
        Args:
            evidence_id: Evidence identifier
            decrypt: Whether to decrypt if encrypted
        
        Returns:
            Evidence content
        """
        storage_key = self._generate_storage_key(evidence_id)
        
        # Retrieve from backend
        stored_content = await self.backend.retrieve(storage_key)
        
        # Get metadata to check if encrypted
        metadata = await self.backend.get_metadata(storage_key)
        
        if decrypt and metadata.get('encrypted'):
            # Would need to unwrap key and decrypt
            # For now, return as-is
            pass
        
        return stored_content
    
    async def delete_evidence(self, evidence_id: str) -> bool:
        """
        Delete stored evidence
        
        Args:
            evidence_id: Evidence identifier
        
        Returns:
            True if deleted
        """
        storage_key = self._generate_storage_key(evidence_id)
        return await self.backend.delete(storage_key)
    
    async def exists(self, evidence_id: str) -> bool:
        """
        Check if evidence exists
        
        Args:
            evidence_id: Evidence identifier
        
        Returns:
            True if exists
        """
        storage_key = self._generate_storage_key(evidence_id)
        return await self.backend.exists(storage_key)
    
    async def store_bundle(
        self,
        bundle_id: str,
        evidence_items: Dict[str, bytes],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store multiple evidence items as a bundle
        
        Args:
            bundle_id: Bundle identifier
            evidence_items: Dict of evidence_id -> content
            metadata: Bundle metadata
        
        Returns:
            Bundle storage info
        """
        stored_items = []
        
        for evidence_id, content in evidence_items.items():
            storage_info = await self.store_evidence(
                evidence_id,
                content,
                metadata
            )
            stored_items.append(storage_info)
        
        # Store bundle manifest
        bundle_manifest = {
            "bundle_id": bundle_id,
            "evidence_count": len(evidence_items),
            "items": stored_items,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat()
        }
        
        import json
        manifest_key = f"bundles/{bundle_id}/manifest.json"
        await self.backend.store(
            manifest_key,
            json.dumps(bundle_manifest).encode('utf-8')
        )
        
        return bundle_manifest
    
    async def retrieve_bundle(self, bundle_id: str) -> Dict[str, bytes]:
        """
        Retrieve all evidence in a bundle
        
        Args:
            bundle_id: Bundle identifier
        
        Returns:
            Dict of evidence_id -> content
        """
        # Load manifest
        manifest_key = f"bundles/{bundle_id}/manifest.json"
        manifest_data = await self.backend.retrieve(manifest_key)
        
        import json
        manifest = json.loads(manifest_data.decode('utf-8'))
        
        # Retrieve all items
        evidence_items = {}
        for item in manifest['items']:
            evidence_id = item['evidence_id']
            content = await self.retrieve_evidence(evidence_id)
            evidence_items[evidence_id] = content
        
        return evidence_items
    
    def _generate_storage_key(self, evidence_id: str) -> str:
        """
        Generate storage key from evidence ID
        
        Args:
            evidence_id: Evidence identifier
        
        Returns:
            Storage key path
        """
        # Create hierarchical path based on ID
        # e.g., github:log:abc123 -> evidence/github/log/abc123.bin
        parts = evidence_id.split(':')
        
        if len(parts) >= 2:
            source = parts[0]
            type_or_hash = '/'.join(parts[1:])
            return f"evidence/{source}/{type_or_hash}.bin"
        else:
            return f"evidence/{evidence_id}.bin"
    
    @staticmethod
    def get_backend(backend_type: StorageBackendType) -> StorageBackend:
        """
        Get storage backend instance
        
        Args:
            backend_type: Type of backend
        
        Returns:
            Storage backend instance
        """
        if backend_type == StorageBackendType.LOCAL:
            return LocalStorageBackend()
        elif backend_type == StorageBackendType.S3:
            # S3 backend would be implemented here
            raise NotImplementedError("S3 backend not yet implemented")
        elif backend_type == StorageBackendType.AZURE_BLOB:
            # Azure backend would be implemented here
            raise NotImplementedError("Azure Blob backend not yet implemented")
        else:
            raise ValidationError(f"Unknown backend type: {backend_type}")

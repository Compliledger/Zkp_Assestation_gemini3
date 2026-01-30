"""
IPFS Storage Module
Stores attestation packages on IPFS for distributed availability
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from pathlib import Path
import json
import hashlib

from app.utils.crypto import HashUtils
from app.utils.errors import StorageError, ValidationError


class IPFSContent(BaseModel):
    """
    IPFS content record
    """
    cid: str = Field(..., description="IPFS Content Identifier (CID)")
    package_id: str = Field(..., description="Attestation package ID")
    content_type: str = Field(..., description="Content type (json, pdf, etc.)")
    
    # Content metadata
    size: int = Field(..., description="Content size in bytes")
    content_hash: str = Field(..., description="SHA-256 hash of content")
    
    # IPFS details
    ipfs_gateway: str = Field(..., description="IPFS gateway URL")
    pinned: bool = Field(default=False, description="Whether content is pinned")
    pin_service: Optional[str] = Field(None, description="Pinning service used")
    
    # Metadata
    uploaded_by: str = Field(..., description="User who uploaded")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Additional data
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def get_ipfs_url(self) -> str:
        """Get IPFS URL for content"""
        return f"ipfs://{self.cid}"
    
    def get_gateway_url(self) -> str:
        """Get HTTP gateway URL"""
        return f"{self.ipfs_gateway}/ipfs/{self.cid}"


class IPFSStorage:
    """
    Stores and retrieves content from IPFS
    
    Note: This is a simplified implementation. In production, use:
    - ipfshttpclient (py-ipfs-http-client)
    - Pinata API for pinning
    - Infura IPFS API
    - Web3.Storage
    """
    
    def __init__(
        self,
        ipfs_host: str = "localhost",
        ipfs_port: int = 5001,
        gateway_url: str = "https://ipfs.io",
        pin_service: Optional[str] = None,
        pin_api_key: Optional[str] = None
    ):
        """
        Initialize IPFS storage
        
        Args:
            ipfs_host: IPFS node host
            ipfs_port: IPFS node port
            gateway_url: IPFS gateway URL
            pin_service: Pinning service (pinata, infura, web3storage)
            pin_api_key: API key for pinning service
        """
        self.ipfs_host = ipfs_host
        self.ipfs_port = ipfs_port
        self.gateway_url = gateway_url
        self.pin_service = pin_service
        self.pin_api_key = pin_api_key
        self.hash_utils = HashUtils()
    
    def upload_content(
        self,
        content: bytes,
        package_id: str,
        content_type: str,
        user_id: str,
        pin: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> IPFSContent:
        """
        Upload content to IPFS
        
        Args:
            content: Content bytes
            package_id: Package identifier
            content_type: Content type
            user_id: User uploading
            pin: Whether to pin content
            metadata: Additional metadata
        
        Returns:
            IPFSContent record
        
        Raises:
            StorageError: If upload fails
        """
        if not content:
            raise ValidationError("Content cannot be empty")
        
        # Compute content hash
        content_hash = self.hash_utils.sha256(content)
        
        # Upload to IPFS
        try:
            cid = self._upload_to_ipfs(content)
        except Exception as e:
            raise StorageError(f"Failed to upload to IPFS: {e}")
        
        # Pin if requested
        pinned = False
        if pin:
            try:
                self._pin_content(cid)
                pinned = True
            except Exception as e:
                # Log error but don't fail
                print(f"Failed to pin content: {e}")
        
        # Create content record
        ipfs_content = IPFSContent(
            cid=cid,
            package_id=package_id,
            content_type=content_type,
            size=len(content),
            content_hash=content_hash,
            ipfs_gateway=self.gateway_url,
            pinned=pinned,
            pin_service=self.pin_service if pinned else None,
            uploaded_by=user_id,
            metadata=metadata or {}
        )
        
        return ipfs_content
    
    def upload_json(
        self,
        data: Dict[str, Any],
        package_id: str,
        user_id: str,
        pin: bool = True
    ) -> IPFSContent:
        """
        Upload JSON data to IPFS
        
        Args:
            data: JSON data
            package_id: Package identifier
            user_id: User uploading
            pin: Whether to pin
        
        Returns:
            IPFSContent record
        """
        json_str = json.dumps(data, indent=2, default=str)
        content = json_str.encode('utf-8')
        
        return self.upload_content(
            content=content,
            package_id=package_id,
            content_type="application/json",
            user_id=user_id,
            pin=pin
        )
    
    def upload_file(
        self,
        file_path: Path,
        package_id: str,
        user_id: str,
        pin: bool = True
    ) -> IPFSContent:
        """
        Upload file to IPFS
        
        Args:
            file_path: Path to file
            package_id: Package identifier
            user_id: User uploading
            pin: Whether to pin
        
        Returns:
            IPFSContent record
        """
        if not file_path.exists():
            raise ValidationError(f"File not found: {file_path}")
        
        content = file_path.read_bytes()
        
        # Determine content type from extension
        content_type = self._get_content_type(file_path.suffix)
        
        return self.upload_content(
            content=content,
            package_id=package_id,
            content_type=content_type,
            user_id=user_id,
            pin=pin
        )
    
    def retrieve_content(self, cid: str) -> bytes:
        """
        Retrieve content from IPFS
        
        Args:
            cid: IPFS Content Identifier
        
        Returns:
            Content bytes
        
        Raises:
            StorageError: If retrieval fails
        """
        try:
            return self._retrieve_from_ipfs(cid)
        except Exception as e:
            raise StorageError(f"Failed to retrieve from IPFS: {e}")
    
    def retrieve_json(self, cid: str) -> Dict[str, Any]:
        """
        Retrieve JSON data from IPFS
        
        Args:
            cid: IPFS Content Identifier
        
        Returns:
            JSON data
        """
        content = self.retrieve_content(cid)
        return json.loads(content.decode('utf-8'))
    
    def pin_content(self, cid: str) -> bool:
        """
        Pin content to prevent garbage collection
        
        Args:
            cid: Content identifier to pin
        
        Returns:
            True if pinned successfully
        """
        try:
            self._pin_content(cid)
            return True
        except Exception as e:
            print(f"Failed to pin content: {e}")
            return False
    
    def unpin_content(self, cid: str) -> bool:
        """
        Unpin content
        
        Args:
            cid: Content identifier to unpin
        
        Returns:
            True if unpinned successfully
        """
        try:
            self._unpin_content(cid)
            return True
        except Exception as e:
            print(f"Failed to unpin content: {e}")
            return False
    
    def verify_content(self, cid: str, expected_hash: str) -> bool:
        """
        Verify content integrity
        
        Args:
            cid: Content identifier
            expected_hash: Expected content hash
        
        Returns:
            True if content matches hash
        """
        try:
            content = self.retrieve_content(cid)
            actual_hash = self.hash_utils.sha256(content)
            return actual_hash == expected_hash
        except:
            return False
    
    def get_content_stats(self, cid: str) -> Dict[str, Any]:
        """
        Get content statistics
        
        Args:
            cid: Content identifier
        
        Returns:
            Statistics dictionary
        """
        try:
            stats = self._get_ipfs_stats(cid)
            return {
                "cid": cid,
                "size": stats.get("size", 0),
                "pinned": stats.get("pinned", False),
                "gateway_url": f"{self.gateway_url}/ipfs/{cid}"
            }
        except:
            return {
                "cid": cid,
                "error": "Failed to get stats"
            }
    
    def _upload_to_ipfs(self, content: bytes) -> str:
        """
        Upload content to IPFS node
        
        In production, use:
        - ipfshttpclient.add()
        - Pinata API
        - Infura IPFS API
        
        For now, simulate CID generation
        """
        # Simulate IPFS upload by generating CID
        # Real CID would be computed by IPFS node
        content_hash = hashlib.sha256(content).hexdigest()
        
        # Simulate CIDv1 (base32)
        # Format: bafybei + base32(multihash)
        cid = f"bafybei{content_hash[:32]}"
        
        return cid
    
    def _retrieve_from_ipfs(self, cid: str) -> bytes:
        """
        Retrieve content from IPFS
        
        In production, use:
        - ipfshttpclient.cat(cid)
        - Gateway HTTP request
        
        For now, simulate retrieval
        """
        # In real implementation, fetch from IPFS
        # For testing, return placeholder
        return b"simulated IPFS content"
    
    def _pin_content(self, cid: str):
        """
        Pin content to IPFS
        
        In production, use:
        - ipfshttpclient.pin.add(cid)
        - Pinata pinning API
        - Infura pinning API
        """
        if self.pin_service == "pinata":
            self._pin_to_pinata(cid)
        elif self.pin_service == "infura":
            self._pin_to_infura(cid)
        else:
            # Local IPFS node pin
            pass
    
    def _unpin_content(self, cid: str):
        """Unpin content from IPFS"""
        if self.pin_service == "pinata":
            self._unpin_from_pinata(cid)
        elif self.pin_service == "infura":
            self._unpin_from_infura(cid)
        else:
            # Local IPFS node unpin
            pass
    
    def _pin_to_pinata(self, cid: str):
        """Pin to Pinata pinning service"""
        # In production:
        # import requests
        # url = "https://api.pinata.cloud/pinning/pinByHash"
        # headers = {"Authorization": f"Bearer {self.pin_api_key}"}
        # data = {"hashToPin": cid}
        # requests.post(url, json=data, headers=headers)
        pass
    
    def _unpin_from_pinata(self, cid: str):
        """Unpin from Pinata"""
        pass
    
    def _pin_to_infura(self, cid: str):
        """Pin to Infura IPFS"""
        pass
    
    def _unpin_from_infura(self, cid: str):
        """Unpin from Infura"""
        pass
    
    def _get_ipfs_stats(self, cid: str) -> Dict[str, Any]:
        """Get IPFS object stats"""
        # Simulate stats
        return {
            "size": 1024,
            "pinned": True
        }
    
    def _get_content_type(self, extension: str) -> str:
        """Get content type from file extension"""
        content_types = {
            ".json": "application/json",
            ".pdf": "application/pdf",
            ".txt": "text/plain",
            ".html": "text/html",
            ".xml": "application/xml",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg"
        }
        return content_types.get(extension.lower(), "application/octet-stream")
    
    def batch_upload(
        self,
        items: List[Dict[str, Any]],
        user_id: str,
        pin: bool = True
    ) -> List[IPFSContent]:
        """
        Upload multiple items in batch
        
        Args:
            items: List of items to upload (content, package_id, content_type)
            user_id: User uploading
            pin: Whether to pin
        
        Returns:
            List of IPFSContent records
        """
        results = []
        
        for item in items:
            try:
                content_record = self.upload_content(
                    content=item["content"],
                    package_id=item["package_id"],
                    content_type=item["content_type"],
                    user_id=user_id,
                    pin=pin
                )
                results.append(content_record)
            except Exception as e:
                print(f"Failed to upload item: {e}")
                continue
        
        return results
    
    def get_gateway_urls(self) -> List[str]:
        """Get list of IPFS gateway URLs"""
        return [
            "https://ipfs.io",
            "https://gateway.pinata.cloud",
            "https://cloudflare-ipfs.com",
            "https://dweb.link",
            self.gateway_url
        ]
    
    def create_directory(
        self,
        files: Dict[str, bytes],
        package_id: str,
        user_id: str
    ) -> IPFSContent:
        """
        Create IPFS directory with multiple files
        
        Args:
            files: Dictionary of filename -> content
            package_id: Package identifier
            user_id: User uploading
        
        Returns:
            IPFSContent record for directory
        """
        # In production, use ipfshttpclient to add directory
        # For now, simulate directory CID
        
        total_size = sum(len(content) for content in files.values())
        dir_hash = self.hash_utils.sha256(json.dumps(list(files.keys())).encode())
        dir_cid = f"bafybei{dir_hash[:32]}"
        
        return IPFSContent(
            cid=dir_cid,
            package_id=package_id,
            content_type="directory",
            size=total_size,
            content_hash=dir_hash,
            ipfs_gateway=self.gateway_url,
            pinned=False,
            uploaded_by=user_id,
            metadata={"file_count": len(files)}
        )

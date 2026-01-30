"""
Public Attestation Registry
Maintains searchable registry of published attestations
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from app.utils.crypto import HashUtils
from app.utils.errors import ValidationError, NotFoundError


class RegistryStatus(str, Enum):
    """Registry entry status"""
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class RegistryEntry(BaseModel):
    """
    Public registry entry for attestation
    """
    entry_id: str = Field(..., description="Registry entry ID")
    package_id: str = Field(..., description="Attestation package ID")
    
    # Attestation info
    title: str = Field(..., description="Attestation title")
    attestation_type: str = Field(..., description="Type of attestation")
    compliance_framework: Optional[str] = Field(None, description="Compliance framework")
    
    # Issuer (public info only)
    issuer_name: str = Field(..., description="Issuer name")
    issuer_id: str = Field(..., description="Issuer identifier")
    
    # Content references
    ipfs_cid: Optional[str] = Field(None, description="IPFS CID")
    blockchain_tx: Optional[str] = Field(None, description="Blockchain transaction hash")
    package_hash: str = Field(..., description="Package content hash")
    
    # Validity
    status: RegistryStatus = Field(default=RegistryStatus.ACTIVE)
    valid_from: datetime = Field(..., description="Valid from date")
    valid_until: Optional[datetime] = Field(None, description="Valid until date")
    
    # Registry metadata
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    revoked_at: Optional[datetime] = Field(None)
    revocation_reason: Optional[str] = Field(None)
    
    # Searchable tags
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def is_valid(self) -> bool:
        """Check if entry is currently valid"""
        if self.status != RegistryStatus.ACTIVE:
            return False
        
        now = datetime.utcnow()
        
        if now < self.valid_from:
            return False
        
        if self.valid_until and now > self.valid_until:
            return False
        
        return True


class AttestationRegistry:
    """
    Public registry for published attestations
    Provides searchable index of attestations
    """
    
    def __init__(self):
        """Initialize attestation registry"""
        self._entries: Dict[str, RegistryEntry] = {}
        self._package_index: Dict[str, str] = {}  # package_id -> entry_id
        self._issuer_index: Dict[str, List[str]] = {}  # issuer_id -> [entry_ids]
        self._hash_index: Dict[str, str] = {}  # package_hash -> entry_id
        self.hash_utils = HashUtils()
    
    def register(
        self,
        package_id: str,
        title: str,
        attestation_type: str,
        issuer_name: str,
        issuer_id: str,
        package_hash: str,
        valid_from: datetime,
        valid_until: Optional[datetime] = None,
        ipfs_cid: Optional[str] = None,
        blockchain_tx: Optional[str] = None,
        compliance_framework: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> RegistryEntry:
        """
        Register attestation in public registry
        
        Args:
            package_id: Package identifier
            title: Attestation title
            attestation_type: Type of attestation
            issuer_name: Issuer name
            issuer_id: Issuer identifier
            package_hash: Package content hash
            valid_from: Valid from date
            valid_until: Valid until date
            ipfs_cid: IPFS content ID
            blockchain_tx: Blockchain transaction
            compliance_framework: Framework name
            tags: Searchable tags
        
        Returns:
            RegistryEntry
        
        Raises:
            ValidationError: If registration fails
        """
        # Check if already registered
        if package_id in self._package_index:
            raise ValidationError(f"Package already registered: {package_id}")
        
        # Generate entry ID
        entry_id = self._generate_entry_id(package_id, issuer_id)
        
        # Create entry
        entry = RegistryEntry(
            entry_id=entry_id,
            package_id=package_id,
            title=title,
            attestation_type=attestation_type,
            compliance_framework=compliance_framework,
            issuer_name=issuer_name,
            issuer_id=issuer_id,
            ipfs_cid=ipfs_cid,
            blockchain_tx=blockchain_tx,
            package_hash=package_hash,
            valid_from=valid_from,
            valid_until=valid_until,
            tags=tags or []
        )
        
        # Store entry
        self._entries[entry_id] = entry
        self._package_index[package_id] = entry_id
        self._hash_index[package_hash] = entry_id
        
        # Update issuer index
        if issuer_id not in self._issuer_index:
            self._issuer_index[issuer_id] = []
        self._issuer_index[issuer_id].append(entry_id)
        
        return entry
    
    def get_entry(self, entry_id: str) -> RegistryEntry:
        """
        Get registry entry by ID
        
        Args:
            entry_id: Entry identifier
        
        Returns:
            RegistryEntry
        
        Raises:
            NotFoundError: If entry not found
        """
        if entry_id not in self._entries:
            raise NotFoundError(f"Registry entry not found: {entry_id}")
        
        return self._entries[entry_id]
    
    def get_by_package(self, package_id: str) -> RegistryEntry:
        """Get entry by package ID"""
        if package_id not in self._package_index:
            raise NotFoundError(f"Package not registered: {package_id}")
        
        entry_id = self._package_index[package_id]
        return self._entries[entry_id]
    
    def get_by_hash(self, package_hash: str) -> RegistryEntry:
        """Get entry by package hash"""
        if package_hash not in self._hash_index:
            raise NotFoundError(f"Package hash not found: {package_hash}")
        
        entry_id = self._hash_index[package_hash]
        return self._entries[entry_id]
    
    def search(
        self,
        attestation_type: Optional[str] = None,
        issuer_id: Optional[str] = None,
        compliance_framework: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[RegistryStatus] = None,
        limit: int = 50
    ) -> List[RegistryEntry]:
        """
        Search registry entries
        
        Args:
            attestation_type: Filter by type
            issuer_id: Filter by issuer
            compliance_framework: Filter by framework
            tags: Filter by tags (any match)
            status: Filter by status
            limit: Maximum results
        
        Returns:
            List of matching entries
        """
        results = []
        
        # Start with issuer filter if provided (most selective)
        if issuer_id:
            entry_ids = self._issuer_index.get(issuer_id, [])
            candidates = [self._entries[eid] for eid in entry_ids]
        else:
            candidates = list(self._entries.values())
        
        # Apply filters
        for entry in candidates:
            if attestation_type and entry.attestation_type != attestation_type:
                continue
            
            if compliance_framework and entry.compliance_framework != compliance_framework:
                continue
            
            if status and entry.status != status:
                continue
            
            if tags and not any(tag in entry.tags for tag in tags):
                continue
            
            results.append(entry)
            
            if len(results) >= limit:
                break
        
        return results
    
    def list_active(self, limit: int = 50) -> List[RegistryEntry]:
        """List active attestations"""
        return self.search(status=RegistryStatus.ACTIVE, limit=limit)
    
    def list_by_issuer(self, issuer_id: str) -> List[RegistryEntry]:
        """List all attestations by issuer"""
        return self.search(issuer_id=issuer_id, limit=1000)
    
    def revoke(
        self,
        entry_id: str,
        reason: str
    ) -> RegistryEntry:
        """
        Revoke registry entry
        
        Args:
            entry_id: Entry to revoke
            reason: Revocation reason
        
        Returns:
            Updated entry
        """
        entry = self.get_entry(entry_id)
        
        entry.status = RegistryStatus.REVOKED
        entry.revoked_at = datetime.utcnow()
        entry.revocation_reason = reason
        
        return entry
    
    def update_status(self, entry_id: str, status: RegistryStatus) -> RegistryEntry:
        """Update entry status"""
        entry = self.get_entry(entry_id)
        entry.status = status
        return entry
    
    def check_expiration(self):
        """Check and update expired entries"""
        now = datetime.utcnow()
        
        for entry in self._entries.values():
            if entry.status == RegistryStatus.ACTIVE:
                if entry.valid_until and now > entry.valid_until:
                    entry.status = RegistryStatus.EXPIRED
    
    def verify_entry(
        self,
        entry_id: str,
        package_hash: str
    ) -> bool:
        """
        Verify entry matches package hash
        
        Args:
            entry_id: Entry identifier
            package_hash: Package hash to verify
        
        Returns:
            True if hash matches
        """
        try:
            entry = self.get_entry(entry_id)
            return entry.package_hash == package_hash
        except:
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics"""
        total = len(self._entries)
        active = sum(1 for e in self._entries.values() if e.status == RegistryStatus.ACTIVE)
        revoked = sum(1 for e in self._entries.values() if e.status == RegistryStatus.REVOKED)
        expired = sum(1 for e in self._entries.values() if e.status == RegistryStatus.EXPIRED)
        
        # Count by type
        by_type = {}
        for entry in self._entries.values():
            atype = entry.attestation_type
            by_type[atype] = by_type.get(atype, 0) + 1
        
        # Count by framework
        by_framework = {}
        for entry in self._entries.values():
            if entry.compliance_framework:
                fw = entry.compliance_framework
                by_framework[fw] = by_framework.get(fw, 0) + 1
        
        return {
            "total_entries": total,
            "active": active,
            "revoked": revoked,
            "expired": expired,
            "by_type": by_type,
            "by_framework": by_framework,
            "total_issuers": len(self._issuer_index)
        }
    
    def _generate_entry_id(self, package_id: str, issuer_id: str) -> str:
        """Generate unique entry ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        content = f"entry_{package_id}_{issuer_id}_{timestamp}"
        hash_suffix = self.hash_utils.sha256(content.encode())[:8]
        return f"entry_{hash_suffix}"
    
    def export_registry(self) -> List[Dict[str, Any]]:
        """Export entire registry"""
        return [entry.dict() for entry in self._entries.values()]
    
    def import_registry(self, entries: List[Dict[str, Any]]):
        """Import registry entries"""
        for entry_data in entries:
            entry = RegistryEntry(**entry_data)
            self._entries[entry.entry_id] = entry
            self._package_index[entry.package_id] = entry.entry_id
            self._hash_index[entry.package_hash] = entry.entry_id
            
            if entry.issuer_id not in self._issuer_index:
                self._issuer_index[entry.issuer_id] = []
            if entry.entry_id not in self._issuer_index[entry.issuer_id]:
                self._issuer_index[entry.issuer_id].append(entry.entry_id)

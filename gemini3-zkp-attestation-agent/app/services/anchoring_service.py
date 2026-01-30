"""
Anchoring Service
Orchestrates blockchain anchoring, IPFS storage, and public registry
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path

from app.core.anchoring.blockchain_anchor import BlockchainAnchor, AnchorRecord, BlockchainType
from app.core.anchoring.ipfs_storage import IPFSStorage, IPFSContent
from app.core.anchoring.registry import AttestationRegistry, RegistryEntry, RegistryStatus
from app.core.attestation.package_builder import AttestationPackage, AttestationPackageBuilder
from app.models.attestation import AttestationPackage as AttestationPackageModel
from app.models.anchoring import AnchorRecord as AnchorRecordModel
from app.config import settings
from app.utils.errors import (
    NotFoundError,
    ValidationError,
    AuthorizationError,
    AnchoringError
)


class AnchoringService:
    """
    Service for anchoring attestations to blockchain and distributed storage
    """
    
    def __init__(
        self,
        db: AsyncSession,
        tenant_id: str,
        user_id: str
    ):
        """
        Initialize anchoring service
        
        Args:
            db: Database session
            tenant_id: Tenant identifier
            user_id: User identifier
        """
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        
        # Initialize components
        self.blockchain_anchor = BlockchainAnchor(
            blockchain_type=BlockchainType.ALGORAND,
            network=getattr(settings, "ALGORAND_NETWORK", "testnet"),
            rpc_url=getattr(settings, "ALGORAND_API_URL", None),
        )
        self.ipfs_storage = IPFSStorage()
        self.registry = AttestationRegistry()
        self.package_builder = AttestationPackageBuilder()
    
    async def publish_to_ipfs(
        self,
        package_id: str,
        pin: bool = True
    ) -> Dict[str, Any]:
        """
        Publish attestation package to IPFS
        
        Args:
            package_id: Package identifier
            pin: Whether to pin content
        
        Returns:
            IPFS publication information
        """
        # Load package
        package = await self._get_package(package_id)
        
        # Verify package is signed
        if not package.package_data.get("signature"):
            raise ValidationError("Package must be signed before publishing to IPFS")
        
        # Upload to IPFS
        ipfs_content = self.ipfs_storage.upload_json(
            data=package.package_data,
            package_id=package_id,
            user_id=self.user_id,
            pin=pin
        )
        
        # Store IPFS reference in database
        package.package_data["ipfs_cid"] = ipfs_content.cid
        package.package_data["ipfs_gateway"] = ipfs_content.get_gateway_url()
        await self._update_package_in_db(package)
        
        return {
            "package_id": package_id,
            "ipfs_cid": ipfs_content.cid,
            "ipfs_url": ipfs_content.get_ipfs_url(),
            "gateway_url": ipfs_content.get_gateway_url(),
            "size": ipfs_content.size,
            "pinned": ipfs_content.pinned,
            "uploaded_at": ipfs_content.uploaded_at.isoformat()
        }
    
    async def anchor_to_blockchain(
        self,
        package_id: str,
        blockchain: str = "mock"
    ) -> Dict[str, Any]:
        """
        Anchor attestation package to blockchain
        
        Args:
            package_id: Package identifier
            blockchain: Blockchain type
        
        Returns:
            Anchor information
        """
        # Load package
        package = await self._get_package(package_id)
        
        # Verify package is signed
        if not package.package_data.get("signature"):
            raise ValidationError("Package must be signed before anchoring")
        
        # Get package hash
        package_hash = package.package_data.get("package_hash")
        if not package_hash:
            raise ValidationError("Package hash not found")
        
        # Select blockchain implementation
        chain = (blockchain or "algorand").lower()
        anchor = self.blockchain_anchor
        if chain == "mock":
            anchor = BlockchainAnchor(blockchain_type=BlockchainType.MOCK)

        # Anchor to blockchain
        anchor_record = anchor.anchor_package(
            package_id=package_id,
            package_hash=package_hash,
            user_id=self.user_id,
            merkle_root=package.package_data.get("merkle_root")
        )
        
        # Store anchor record in database
        anchor_model = AnchorRecordModel(
            anchor_id=anchor_record.anchor_id,
            package_id=package_id,
            blockchain=anchor_record.blockchain.value,
            transaction_hash=anchor_record.transaction_hash,
            block_number=anchor_record.block_number,
            package_hash=package_hash,
            status=anchor_record.status.value
        )
        
        self.db.add(anchor_model)
        await self.db.commit()
        
        # Update package with anchor info
        package.package_data["blockchain_tx"] = anchor_record.transaction_hash
        package.package_data["blockchain"] = anchor_record.blockchain.value
        await self._update_package_in_db(package)
        
        return {
            "anchor_id": anchor_record.anchor_id,
            "package_id": package_id,
            "blockchain": anchor_record.blockchain.value,
            "transaction_hash": anchor_record.transaction_hash,
            "block_number": anchor_record.block_number,
            "explorer_url": anchor.get_explorer_url(anchor_record.transaction_hash),
            "status": anchor_record.status.value,
            "anchored_at": anchor_record.anchored_at.isoformat()
        }
    
    async def publish_complete(
        self,
        package_id: str,
        to_ipfs: bool = True,
        to_blockchain: bool = True,
        to_registry: bool = True,
        blockchain: str = "mock"
    ) -> Dict[str, Any]:
        """
        Complete publication workflow (IPFS + Blockchain + Registry)
        
        Args:
            package_id: Package identifier
            to_ipfs: Publish to IPFS
            to_blockchain: Anchor to blockchain
            to_registry: Register in public registry
            blockchain: Blockchain type
        
        Returns:
            Complete publication information
        """
        # Load package
        package = await self._get_package(package_id)
        
        result = {
            "package_id": package_id,
            "published_at": datetime.utcnow().isoformat()
        }
        
        # Publish to IPFS
        if to_ipfs:
            ipfs_result = await self.publish_to_ipfs(package_id)
            result["ipfs"] = ipfs_result
        
        # Anchor to blockchain
        if to_blockchain:
            anchor_result = await self.anchor_to_blockchain(package_id, blockchain)
            result["blockchain"] = anchor_result
        
        # Register in public registry
        if to_registry:
            registry_result = await self.register_attestation(package_id)
            result["registry"] = registry_result
        
        # Update package status to published
        package.status = "published"
        package.published_at = datetime.utcnow()
        await self.db.commit()
        
        return result
    
    async def register_attestation(
        self,
        package_id: str
    ) -> Dict[str, Any]:
        """
        Register attestation in public registry
        
        Args:
            package_id: Package identifier
        
        Returns:
            Registry entry information
        """
        # Load package
        package = await self._get_package(package_id)
        
        # Extract package data
        pkg_data = package.package_data
        
        # Register in public registry
        entry = self.registry.register(
            package_id=package_id,
            title=package.title,
            attestation_type=package.attestation_type or "general",
            issuer_name=pkg_data.get("issuer", {}).get("name", "Unknown"),
            issuer_id=self.user_id,
            package_hash=pkg_data.get("package_hash", ""),
            valid_from=pkg_data.get("valid_from") or datetime.utcnow(),
            valid_until=pkg_data.get("valid_until"),
            ipfs_cid=pkg_data.get("ipfs_cid"),
            blockchain_tx=pkg_data.get("blockchain_tx"),
            compliance_framework=package.compliance_framework,
            tags=pkg_data.get("tags", [])
        )
        
        return {
            "entry_id": entry.entry_id,
            "package_id": package_id,
            "status": entry.status.value,
            "registered_at": entry.registered_at.isoformat(),
            "valid_from": entry.valid_from.isoformat(),
            "valid_until": entry.valid_until.isoformat() if entry.valid_until else None
        }
    
    async def verify_publication(
        self,
        package_id: str
    ) -> Dict[str, Any]:
        """
        Verify publication across all channels
        
        Args:
            package_id: Package identifier
        
        Returns:
            Verification results
        """
        # Load package
        package = await self._get_package(package_id)
        pkg_data = package.package_data
        
        results = {
            "package_id": package_id,
            "verifications": {}
        }
        
        # Verify IPFS
        if pkg_data.get("ipfs_cid"):
            ipfs_cid = pkg_data["ipfs_cid"]
            ipfs_valid = self.ipfs_storage.verify_content(
                ipfs_cid,
                pkg_data.get("package_hash", "")
            )
            results["verifications"]["ipfs"] = {
                "cid": ipfs_cid,
                "valid": ipfs_valid
            }
        
        # Verify blockchain
        if pkg_data.get("blockchain_tx"):
            anchor_status = self.blockchain_anchor.get_anchor_status(
                pkg_data["blockchain_tx"]
            )
            results["verifications"]["blockchain"] = anchor_status
        
        # Verify registry
        try:
            entry = self.registry.get_by_package(package_id)
            registry_valid = self.registry.verify_entry(
                entry.entry_id,
                pkg_data.get("package_hash", "")
            )
            results["verifications"]["registry"] = {
                "entry_id": entry.entry_id,
                "valid": registry_valid,
                "status": entry.status.value
            }
        except NotFoundError:
            results["verifications"]["registry"] = {
                "valid": False,
                "error": "Not registered"
            }
        
        # Overall validity
        results["is_valid"] = all(
            v.get("valid", False) 
            for v in results["verifications"].values()
            if "valid" in v
        )
        
        return results
    
    async def retrieve_from_ipfs(
        self,
        package_id: Optional[str] = None,
        ipfs_cid: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve attestation from IPFS
        
        Args:
            package_id: Package identifier (will lookup CID)
            ipfs_cid: Direct IPFS CID
        
        Returns:
            Retrieved content
        """
        if not ipfs_cid:
            if not package_id:
                raise ValidationError("Either package_id or ipfs_cid required")
            
            package = await self._get_package(package_id)
            ipfs_cid = package.package_data.get("ipfs_cid")
            
            if not ipfs_cid:
                raise ValidationError("Package not published to IPFS")
        
        # Retrieve from IPFS
        content = self.ipfs_storage.retrieve_json(ipfs_cid)
        
        return {
            "ipfs_cid": ipfs_cid,
            "content": content,
            "gateway_url": f"{self.ipfs_storage.gateway_url}/ipfs/{ipfs_cid}"
        }
    
    async def search_registry(
        self,
        attestation_type: Optional[str] = None,
        compliance_framework: Optional[str] = None,
        issuer_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Search public attestation registry
        
        Args:
            attestation_type: Filter by type
            compliance_framework: Filter by framework
            issuer_id: Filter by issuer
            tags: Filter by tags
            limit: Maximum results
        
        Returns:
            Search results
        """
        entries = self.registry.search(
            attestation_type=attestation_type,
            compliance_framework=compliance_framework,
            issuer_id=issuer_id,
            tags=tags,
            status=RegistryStatus.ACTIVE,
            limit=limit
        )
        
        return {
            "results": [
                {
                    "entry_id": entry.entry_id,
                    "package_id": entry.package_id,
                    "title": entry.title,
                    "attestation_type": entry.attestation_type,
                    "compliance_framework": entry.compliance_framework,
                    "issuer_name": entry.issuer_name,
                    "ipfs_cid": entry.ipfs_cid,
                    "blockchain_tx": entry.blockchain_tx,
                    "valid_from": entry.valid_from.isoformat(),
                    "valid_until": entry.valid_until.isoformat() if entry.valid_until else None,
                    "is_valid": entry.is_valid()
                }
                for entry in entries
            ],
            "total": len(entries),
            "limit": limit
        }
    
    async def get_publication_status(
        self,
        package_id: str
    ) -> Dict[str, Any]:
        """
        Get complete publication status
        
        Args:
            package_id: Package identifier
        
        Returns:
            Publication status
        """
        package = await self._get_package(package_id)
        pkg_data = package.package_data
        
        status = {
            "package_id": package_id,
            "status": package.status,
            "published": {
                "ipfs": pkg_data.get("ipfs_cid") is not None,
                "blockchain": pkg_data.get("blockchain_tx") is not None,
                "registry": False
            }
        }
        
        # Check registry
        try:
            entry = self.registry.get_by_package(package_id)
            status["published"]["registry"] = True
            status["registry_entry_id"] = entry.entry_id
        except NotFoundError:
            pass
        
        # Add URLs if available
        if pkg_data.get("ipfs_cid"):
            status["ipfs_url"] = f"ipfs://{pkg_data['ipfs_cid']}"
            status["gateway_url"] = f"{self.ipfs_storage.gateway_url}/ipfs/{pkg_data['ipfs_cid']}"
        
        if pkg_data.get("blockchain_tx"):
            status["explorer_url"] = self.blockchain_anchor.get_explorer_url(
                pkg_data["blockchain_tx"]
            )
        
        return status
    
    async def _get_package(self, package_id: str) -> AttestationPackageModel:
        """Get package from database"""
        result = await self.db.execute(
            select(AttestationPackageModel).where(
                AttestationPackageModel.package_id == package_id
            )
        )
        package = result.scalar_one_or_none()
        
        if not package:
            raise NotFoundError(f"Package not found: {package_id}")
        
        if package.tenant_id != self.tenant_id:
            raise AuthorizationError("Access denied to package")
        
        return package
    
    async def _update_package_in_db(self, package: AttestationPackageModel):
        """Update package in database"""
        await self.db.commit()
        await self.db.refresh(package)
    
    async def get_anchoring_statistics(self) -> Dict[str, Any]:
        """Get anchoring statistics"""
        # Query database for anchor records
        result = await self.db.execute(
            select(AnchorRecordModel)
        )
        anchors = result.scalars().all()
        
        total_anchors = len(anchors)
        by_blockchain = {}
        by_status = {}
        
        for anchor in anchors:
            blockchain = anchor.blockchain
            by_blockchain[blockchain] = by_blockchain.get(blockchain, 0) + 1
            
            status = anchor.status
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            "total_anchors": total_anchors,
            "by_blockchain": by_blockchain,
            "by_status": by_status,
            "registry_stats": self.registry.get_statistics()
        }

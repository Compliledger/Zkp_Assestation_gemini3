"""
Evidence Service
Business logic for evidence processing and management
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.evidence.normalizer import EvidenceNormalizer, NormalizedEvidence
from app.core.evidence.commitment import CommitmentGenerator, EvidenceCommitment
from app.core.evidence.storage import EvidenceStorage, LocalStorageBackend
from app.models.evidence import EvidenceBundle, EvidenceItem
from app.models.claim import Claim
from app.utils.errors import ValidationError, NotFoundError, AuthorizationError
from app.utils.crypto import CryptoUtils


class EvidenceService:
    """
    Service for evidence processing and management
    """
    
    def __init__(
        self,
        db: AsyncSession,
        tenant_id: str,
        user_id: str
    ):
        """
        Initialize evidence service
        
        Args:
            db: Database session
            tenant_id: Tenant identifier
            user_id: User identifier
        """
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        
        # Initialize components
        self.normalizer = EvidenceNormalizer()
        self.commitment_generator = CommitmentGenerator()
        self.storage = EvidenceStorage(backend=LocalStorageBackend())
        self.crypto = CryptoUtils()
    
    async def submit_evidence(
        self,
        claim_id: str,
        raw_evidence: List[Dict[str, Any]],
        encrypt: bool = True
    ) -> Dict[str, Any]:
        """
        Submit and process evidence for a claim
        
        Args:
            claim_id: Claim identifier
            raw_evidence: List of raw evidence items
            encrypt: Whether to encrypt evidence
        
        Returns:
            Evidence bundle information
        
        Raises:
            NotFoundError: If claim not found
            ValidationError: If evidence is invalid
        """
        # Verify claim exists and belongs to tenant
        claim = await self._get_claim(claim_id)
        
        # Normalize evidence
        normalized_items = []
        for item in raw_evidence:
            normalized = self.normalizer.normalize(
                raw_evidence=item.get('content'),
                evidence_type=item.get('type'),
                source_system=item.get('source'),
                metadata=item.get('metadata')
            )
            normalized_items.append(normalized)
        
        # Generate bundle ID
        bundle_id = CommitmentGenerator.generate_bundle_id(
            self.tenant_id,
            claim_id
        )
        
        # Store evidence items
        stored_items = []
        for normalized in normalized_items:
            # Store content
            storage_info = await self.storage.store_evidence(
                evidence_id=normalized.evidence_id,
                content=normalized.model_dump_json().encode('utf-8'),
                encrypt=encrypt,
                metadata={
                    "tenant_id": self.tenant_id,
                    "claim_id": claim_id,
                    "evidence_type": normalized.evidence_type
                }
            )
            stored_items.append(storage_info)
        
        # Generate Merkle commitment
        commitment = self.commitment_generator.generate_commitment(
            evidence_items=normalized_items,
            bundle_id=bundle_id,
            encrypt=encrypt,
            encryption_key=self.crypto.generate_key(32) if encrypt else None
        )
        
        # Create evidence bundle in database
        evidence_bundle = EvidenceBundle(
            bundle_id=bundle_id,
            claim_id=claim_id,
            merkle_root=commitment.merkle_root,
            evidence_count=commitment.evidence_count,
            storage_uri=stored_items[0]['storage_uri'] if stored_items else None,
            encryption_enabled=encrypt,
            encryption_key_id=commitment.encryption_key_id,
            collected_at=datetime.utcnow()
        )
        
        self.db.add(evidence_bundle)
        
        # Create evidence items in database
        for idx, (normalized, storage_info) in enumerate(zip(normalized_items, stored_items)):
            evidence_item = EvidenceItem(
                bundle_id=bundle_id,
                evidence_id=normalized.evidence_id,
                evidence_type=normalized.evidence_type,
                source_system=normalized.source_system,
                content_hash=normalized.content_hash,
                content_size=normalized.content_size,
                storage_uri=storage_info['storage_uri'],
                metadata=normalized.metadata,
                item_index=idx
            )
            self.db.add(evidence_item)
        
        await self.db.commit()
        await self.db.refresh(evidence_bundle)
        
        return {
            "bundle_id": bundle_id,
            "claim_id": claim_id,
            "evidence_count": commitment.evidence_count,
            "merkle_root": commitment.merkle_root,
            "encrypted": encrypt,
            "items": [
                {
                    "evidence_id": item.evidence_id,
                    "type": item.evidence_type,
                    "hash": item.content_hash,
                    "size": item.content_size
                }
                for item in normalized_items
            ],
            "created_at": evidence_bundle.created_at.isoformat()
        }
    
    async def get_evidence_bundle(
        self,
        bundle_id: str,
        include_content: bool = False
    ) -> Dict[str, Any]:
        """
        Get evidence bundle information
        
        Args:
            bundle_id: Bundle identifier
            include_content: Whether to include evidence content
        
        Returns:
            Bundle information
        
        Raises:
            NotFoundError: If bundle not found
            AuthorizationError: If user doesn't have access
        """
        # Get bundle from database
        bundle = await self._get_bundle(bundle_id)
        
        # Verify tenant access
        claim = await self._get_claim(bundle.claim_id)
        if claim.tenant_id != self.tenant_id:
            raise AuthorizationError("Access denied to evidence bundle")
        
        # Get evidence items
        result = await self.db.execute(
            select(EvidenceItem)
            .where(EvidenceItem.bundle_id == bundle_id)
            .order_by(EvidenceItem.item_index)
        )
        items = result.scalars().all()
        
        bundle_info = {
            "bundle_id": bundle.bundle_id,
            "claim_id": bundle.claim_id,
            "merkle_root": bundle.merkle_root,
            "evidence_count": bundle.evidence_count,
            "encrypted": bundle.encryption_enabled,
            "created_at": bundle.created_at.isoformat(),
            "items": [
                {
                    "evidence_id": item.evidence_id,
                    "type": item.evidence_type,
                    "source": item.source_system,
                    "hash": item.content_hash,
                    "size": item.content_size,
                    "metadata": item.metadata
                }
                for item in items
            ]
        }
        
        if include_content:
            # Retrieve evidence content
            contents = []
            for item in items:
                try:
                    content = await self.storage.retrieve_evidence(item.evidence_id)
                    contents.append({
                        "evidence_id": item.evidence_id,
                        "content": content.decode('utf-8') if content else None
                    })
                except Exception as e:
                    contents.append({
                        "evidence_id": item.evidence_id,
                        "error": str(e)
                    })
            
            bundle_info["contents"] = contents
        
        return bundle_info
    
    async def generate_evidence_proof(
        self,
        bundle_id: str,
        evidence_id: str
    ) -> Dict[str, Any]:
        """
        Generate Merkle proof for specific evidence
        
        Args:
            bundle_id: Bundle identifier
            evidence_id: Evidence identifier
        
        Returns:
            Merkle proof information
        """
        # Get bundle
        bundle = await self._get_bundle(bundle_id)
        
        # Verify access
        claim = await self._get_claim(bundle.claim_id)
        if claim.tenant_id != self.tenant_id:
            raise AuthorizationError("Access denied to evidence bundle")
        
        # Get evidence item
        result = await self.db.execute(
            select(EvidenceItem)
            .where(
                EvidenceItem.bundle_id == bundle_id,
                EvidenceItem.evidence_id == evidence_id
            )
        )
        evidence_item = result.scalar_one_or_none()
        
        if not evidence_item:
            raise NotFoundError(f"Evidence not found: {evidence_id}")
        
        # Get all items for commitment recreation
        result = await self.db.execute(
            select(EvidenceItem)
            .where(EvidenceItem.bundle_id == bundle_id)
            .order_by(EvidenceItem.item_index)
        )
        all_items = result.scalars().all()
        
        # Create commitment
        evidence_hashes = [item.content_hash for item in all_items]
        commitment = EvidenceCommitment(
            bundle_id=bundle_id,
            merkle_root=bundle.merkle_root,
            evidence_count=bundle.evidence_count,
            evidence_hashes=evidence_hashes,
            hash_algorithm="SHA256"
        )
        
        # Generate proof
        proof = self.commitment_generator.generate_proof(
            commitment=commitment,
            evidence_index=evidence_item.item_index
        )
        
        return proof
    
    async def verify_evidence_proof(
        self,
        evidence_hash: str,
        proof: List[Dict[str, Any]],
        merkle_root: str
    ) -> Dict[str, Any]:
        """
        Verify Merkle proof for evidence
        
        Args:
            evidence_hash: Evidence hash
            proof: Merkle proof
            merkle_root: Expected root
        
        Returns:
            Verification result
        """
        is_valid = self.commitment_generator.verify_proof(
            evidence_hash=evidence_hash,
            proof=proof,
            merkle_root=merkle_root
        )
        
        return {
            "valid": is_valid,
            "evidence_hash": evidence_hash,
            "merkle_root": merkle_root,
            "verified_at": datetime.utcnow().isoformat()
        }
    
    async def list_evidence_bundles(
        self,
        claim_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List evidence bundles for tenant
        
        Args:
            claim_id: Optional claim filter
            limit: Max results
            offset: Pagination offset
        
        Returns:
            List of bundles
        """
        query = select(EvidenceBundle).limit(limit).offset(offset)
        
        if claim_id:
            # Verify claim belongs to tenant
            claim = await self._get_claim(claim_id)
            query = query.where(EvidenceBundle.claim_id == claim_id)
        else:
            # Get all claims for tenant first
            claims_result = await self.db.execute(
                select(Claim.claim_id).where(Claim.tenant_id == self.tenant_id)
            )
            claim_ids = [row[0] for row in claims_result]
            query = query.where(EvidenceBundle.claim_id.in_(claim_ids))
        
        result = await self.db.execute(query)
        bundles = result.scalars().all()
        
        return {
            "bundles": [
                {
                    "bundle_id": bundle.bundle_id,
                    "claim_id": bundle.claim_id,
                    "evidence_count": bundle.evidence_count,
                    "merkle_root": bundle.merkle_root,
                    "created_at": bundle.created_at.isoformat()
                }
                for bundle in bundles
            ],
            "total": len(bundles),
            "limit": limit,
            "offset": offset
        }
    
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
    
    async def _get_bundle(self, bundle_id: str) -> EvidenceBundle:
        """Get evidence bundle"""
        result = await self.db.execute(
            select(EvidenceBundle).where(EvidenceBundle.bundle_id == bundle_id)
        )
        bundle = result.scalar_one_or_none()
        
        if not bundle:
            raise NotFoundError(f"Evidence bundle not found: {bundle_id}")
        
        return bundle

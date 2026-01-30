"""
Blockchain Anchoring Module
Anchors attestation packages to blockchain for immutability and timestamping
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import hashlib
import json

from algosdk import encoding
import base64

from app.utils.crypto import HashUtils
from app.utils.errors import AnchoringError, ValidationError
from app.config import settings
from app.core.anchoring.algorand_client import (
    build_funded_anchor_group,
    build_anchor_app_call_txn,
    deploy_anchor_app,
    encode_unsigned_txn,
    make_clients,
    mnemonic_to_keys,
    read_anchor_box,
    send_signed_txn_bytes,
    sign_and_send,
 )


class BlockchainType(str, Enum):
    """Supported blockchain types"""
    ALGORAND = "algorand"
    MOCK = "mock"  # For testing


class AnchorStatus(str, Enum):
    """Anchor status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class AnchorRecord(BaseModel):
    """
    Blockchain anchor record
    """
    anchor_id: str = Field(..., description="Unique anchor identifier")
    package_id: str = Field(..., description="Attestation package ID")
    blockchain: BlockchainType = Field(..., description="Blockchain type")
    
    # Anchor data
    package_hash: str = Field(..., description="Hash of package content")
    merkle_root: Optional[str] = Field(None, description="Merkle root if applicable")
    
    # Blockchain details
    transaction_hash: str = Field(..., description="Blockchain transaction hash")
    block_number: Optional[int] = Field(None, description="Block number")
    block_hash: Optional[str] = Field(None, description="Block hash")
    contract_address: Optional[str] = Field(None, description="Smart contract address")
    
    # Status
    status: AnchorStatus = Field(default=AnchorStatus.PENDING)
    confirmations: int = Field(default=0, description="Number of confirmations")
    
    # Metadata
    anchored_by: str = Field(..., description="User who anchored")
    anchored_at: datetime = Field(default_factory=datetime.utcnow)
    confirmed_at: Optional[datetime] = Field(None, description="Confirmation timestamp")
    
    # Additional data
    gas_used: Optional[int] = Field(None, description="Gas used for transaction")
    transaction_fee: Optional[str] = Field(None, description="Transaction fee")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BlockchainAnchor:
    """
    Anchors attestation packages to Algorand blockchain
    
    Note: This is a simplified implementation. In production, use:
    - py-algorand-sdk for Algorand
    - Algorand node or API service (e.g., PureStake, AlgoNode)
    - Hardware Security Modules (HSM) for key management
    """
    
    def __init__(
        self,
        blockchain_type: BlockchainType = BlockchainType.ALGORAND,
        network: str = "mainnet",
        rpc_url: Optional[str] = None,
        contract_address: Optional[str] = None
    ):
        """
        Initialize blockchain anchor
        
        Args:
            blockchain_type: Type of blockchain
            network: Network name (mainnet, testnet, etc.)
            rpc_url: RPC endpoint URL
            contract_address: Smart contract address for anchoring
        """
        self.blockchain_type = blockchain_type
        self.network = network
        self.rpc_url = rpc_url or self._get_default_rpc(blockchain_type, network)
        self.contract_address = contract_address
        self.hash_utils = HashUtils()

        if self.blockchain_type == BlockchainType.ALGORAND:
            self._algo_clients = make_clients(
                algod_url=self.rpc_url,
                algod_token=getattr(settings, "ALGORAND_API_TOKEN", "") or "",
                indexer_url=getattr(settings, "ALGORAND_INDEXER_URL", None),
            )
        else:
            self._algo_clients = None

        self._algo_app_id = getattr(settings, "ALGORAND_ANCHOR_APP_ID", None)
    
    def anchor_package(
        self,
        package_id: str,
        package_hash: str,
        user_id: str,
        merkle_root: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AnchorRecord:
        """
        Anchor attestation package to blockchain
        
        Args:
            package_id: Package identifier
            package_hash: Hash of package content
            user_id: User anchoring the package
            merkle_root: Optional Merkle root
            metadata: Additional metadata
        
        Returns:
            AnchorRecord with transaction details
        
        Raises:
            AnchoringError: If anchoring fails
        """
        # Validate inputs
        if not package_hash or len(package_hash) != 64:
            raise ValidationError("Invalid package hash")
        
        if self.blockchain_type == BlockchainType.ALGORAND:
            if merkle_root is None:
                merkle_root = "0" * 64

            tx_result = self._anchor_to_algorand_app(
                package_id=package_id,
                package_hash=package_hash,
                merkle_root=merkle_root,
            )
        else:
            # Prepare anchor data
            anchor_data = self._prepare_anchor_data(
                package_id,
                package_hash,
                merkle_root,
                metadata
            )

            # Submit to blockchain
            try:
                tx_result = self._submit_to_blockchain(anchor_data)
            except Exception as e:
                raise AnchoringError(f"Failed to anchor to blockchain: {e}")
        
        # Create anchor record
        anchor_id = self._generate_anchor_id(package_id, self.blockchain_type)
        
        record = AnchorRecord(
            anchor_id=anchor_id,
            package_id=package_id,
            blockchain=self.blockchain_type,
            package_hash=package_hash,
            merkle_root=merkle_root,
            transaction_hash=tx_result["transaction_hash"],
            block_number=tx_result.get("block_number"),
            block_hash=tx_result.get("block_hash"),
            contract_address=self.contract_address or (str(self._algo_app_id) if self._algo_app_id else None),
            status=AnchorStatus.CONFIRMED if tx_result.get("confirmed") else AnchorStatus.PENDING,
            anchored_by=user_id,
            gas_used=tx_result.get("gas_used"),
            transaction_fee=tx_result.get("transaction_fee")
        )
        
        return record
    
    def verify_anchor(
        self,
        anchor_record: AnchorRecord,
        package_hash: str
    ) -> bool:
        """
        Verify anchor on blockchain
        
        Args:
            anchor_record: Anchor record to verify
            package_hash: Expected package hash
        
        Returns:
            True if anchor is valid
        
        Raises:
            AnchoringError: If verification fails
        """
        # Check hash matches
        if anchor_record.package_hash != package_hash:
            return False
        
        # Verify on blockchain
        try:
            if self.blockchain_type == BlockchainType.ALGORAND:
                blockchain_data = self._query_algorand_tx(anchor_record.transaction_hash)
            else:
                blockchain_data = self._query_blockchain(anchor_record.transaction_hash)
        except Exception as e:
            raise AnchoringError(f"Failed to query blockchain: {e}")
        
        # Verify transaction exists and contains correct data
        if not blockchain_data:
            return False
        
        # Check confirmations
        if blockchain_data.get("confirmations", 0) < 6:  # Require 6 confirmations
            return False
        
        return True
    
    def get_anchor_status(
        self,
        transaction_hash: str
    ) -> Dict[str, Any]:
        """
        Get anchor status from blockchain
        
        Args:
            transaction_hash: Transaction hash
        
        Returns:
            Status information
        """
        try:
            if self.blockchain_type == BlockchainType.ALGORAND:
                data = self._query_algorand_tx(transaction_hash)
            else:
                data = self._query_blockchain(transaction_hash)
            
            return {
                "transaction_hash": transaction_hash,
                "status": "confirmed" if data.get("confirmations", 0) >= 6 else "pending",
                "confirmations": data.get("confirmations", 0),
                "block_number": data.get("block_number"),
                "block_hash": data.get("block_hash"),
                "timestamp": data.get("timestamp")
            }
        except Exception as e:
            return {
                "transaction_hash": transaction_hash,
                "status": "failed",
                "error": str(e)
            }
    
    def batch_anchor(
        self,
        packages: List[Dict[str, str]],
        user_id: str
    ) -> List[AnchorRecord]:
        """
        Anchor multiple packages in batch
        
        Args:
            packages: List of package data (id, hash)
            user_id: User anchoring packages
        
        Returns:
            List of anchor records
        """
        # Create Merkle tree of package hashes
        hashes = [pkg["hash"] for pkg in packages]
        merkle_root = self._compute_merkle_root(hashes)
        
        # Anchor Merkle root
        anchor_data = {
            "merkle_root": merkle_root,
            "package_count": len(packages),
            "package_ids": [pkg["id"] for pkg in packages]
        }
        
        tx_result = self._submit_to_blockchain(anchor_data)
        
        # Create anchor records for each package
        records = []
        for pkg in packages:
            anchor_id = self._generate_anchor_id(pkg["id"], self.blockchain_type)
            
            record = AnchorRecord(
                anchor_id=anchor_id,
                package_id=pkg["id"],
                blockchain=self.blockchain_type,
                package_hash=pkg["hash"],
                merkle_root=merkle_root,
                transaction_hash=tx_result["transaction_hash"],
                status=AnchorStatus.PENDING,
                anchored_by=user_id
            )
            records.append(record)
        
        return records
    
    def _prepare_anchor_data(
        self,
        package_id: str,
        package_hash: str,
        merkle_root: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Prepare data for blockchain anchoring"""
        data = {
            "package_id": package_id,
            "package_hash": package_hash,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0"
        }
        
        if merkle_root:
            data["merkle_root"] = merkle_root
        
        if metadata:
            data["metadata"] = metadata
        
        return data
    
    def _submit_to_blockchain(
        self,
        anchor_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit anchor to Algorand blockchain
        
        In production, use py-algorand-sdk:
        - from algosdk.v2client import algod
        - from algosdk import transaction, account
        - algod_client = algod.AlgodClient(token, address)
        - Create note transaction with anchor_data
        - Sign and submit transaction
        
        For now, simulate transaction
        """
        if self.blockchain_type == BlockchainType.ALGORAND:
            raise AnchoringError("Direct note-based anchoring is not supported in real mode; use the anchoring app")
        elif self.blockchain_type == BlockchainType.MOCK:
            return self._submit_to_mock(anchor_data)
        else:
            raise AnchoringError(f"Unsupported blockchain: {self.blockchain_type}")
    
    def _submit_to_mock(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock blockchain for testing"""
        data_str = json.dumps(data, sort_keys=True)
        tx_hash = "mock_" + self.hash_utils.sha256(data_str.encode())[:32]
        
        return {
            "transaction_hash": tx_hash,
            "block_number": 999999,
            "block_hash": "mock_block_hash",
            "gas_used": 0,
            "transaction_fee": "0"
        }
    
    def _query_blockchain(self, transaction_hash: str) -> Dict[str, Any]:
        """
        Query blockchain for transaction details
        
        In production, use blockchain APIs
        For now, simulate query
        """
        # Simulate blockchain query
        return {
            "transaction_hash": transaction_hash,
            "confirmations": 12,
            "block_number": 12345678,
            "block_hash": "0xabcdef...",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }

    def deploy_algorand_contract(self) -> Dict[str, Any]:
        """Deploy the anchoring smart contract to Algorand (server signer from .env)."""
        if self.blockchain_type != BlockchainType.ALGORAND:
            raise AnchoringError("deploy_algorand_contract only supported for algorand")

        if not settings.ALGORAND_MNEMONIC:
            raise AnchoringError("ALGORAND_MNEMONIC missing")

        creator_addr, creator_pk = mnemonic_to_keys(settings.ALGORAND_MNEMONIC)
        result = deploy_anchor_app(self._algo_clients.algod, creator_addr, creator_pk)
        self._algo_app_id = int(result["app_id"])
        return result

    def prepare_algorand_anchor_txn(
        self,
        sender_address: str,
        package_id: str,
        package_hash: str,
        merkle_root: str,
    ) -> Dict[str, Any]:
        """Prepare an unsigned app-call txn for frontend wallet signing."""
        if self.blockchain_type != BlockchainType.ALGORAND:
            raise AnchoringError("prepare_algorand_anchor_txn only supported for algorand")

        app_id = self._require_algorand_app_id()
        txn = build_anchor_app_call_txn(
            algod_client=self._algo_clients.algod,
            sender_addr=sender_address,
            app_id=app_id,
            package_id=package_id,
            package_hash_hex=package_hash,
            merkle_root_hex=merkle_root,
        )

        encoded = encode_unsigned_txn(txn)
        return {
            "app_id": app_id,
            "sender": sender_address,
            "txn": encoded,
        }

    def submit_algorand_signed_txn(self, signed_txn_b64: str) -> Dict[str, Any]:
        """Submit a signed transaction blob (frontend-signed)."""
        if self.blockchain_type != BlockchainType.ALGORAND:
            raise AnchoringError("submit_algorand_signed_txn only supported for algorand")

        # Wallets typically return base64-encoded msgpack bytes
        signed_bytes = base64.b64decode(signed_txn_b64)

        result = send_signed_txn_bytes(self._algo_clients.algod, signed_bytes)
        confirmed_round = result.get("confirmed_round")
        return {
            "transaction_hash": result["transaction_id"],
            "block_number": confirmed_round,
            "confirmed": True,
        }

    def get_algorand_anchor(self, package_id: str) -> Dict[str, Any]:
        """Read on-chain anchor data for a package_id."""
        if self.blockchain_type != BlockchainType.ALGORAND:
            raise AnchoringError("get_algorand_anchor only supported for algorand")

        app_id = self._require_algorand_app_id()
        data = read_anchor_box(self._algo_clients.algod, app_id, package_id)
        data["app_id"] = app_id
        return data

    def _require_algorand_app_id(self) -> int:
        if not self._algo_app_id:
            raise AnchoringError("Algorand anchoring app id not configured. Set ALGORAND_ANCHOR_APP_ID or deploy via API.")
        return int(self._algo_app_id)

    def _anchor_to_algorand_app(self, package_id: str, package_hash: str, merkle_root: str) -> Dict[str, Any]:
        if not settings.ALGORAND_MNEMONIC:
            raise AnchoringError("ALGORAND_MNEMONIC missing")

        app_id = self._require_algorand_app_id()
        sender_addr, sender_pk = mnemonic_to_keys(settings.ALGORAND_MNEMONIC)

        # Writing app boxes requires the application account to maintain sufficient minimum balance.
        # Fund the application address and perform the anchor call atomically.
        from app.core.anchoring.algorand_client import sign_and_send_group

        txns = build_funded_anchor_group(
            algod_client=self._algo_clients.algod,
            sender_addr=sender_addr,
            app_id=app_id,
            package_id=package_id,
            package_hash_hex=package_hash,
            merkle_root_hex=merkle_root,
            funding_amount_microalgos=300_000,
        )
        result = sign_and_send_group(self._algo_clients.algod, txns, sender_pk)
        confirmed_round = result.get("confirmed_round")
        return {
            "transaction_hash": result["transaction_id"],
            "block_number": confirmed_round,
            "confirmed": True,
            "transaction_fee": "0.001 ALGO",
        }

    def _query_algorand_tx(self, txid: str) -> Dict[str, Any]:
        pending = self._algo_clients.algod.pending_transaction_info(txid)
        confirmed_round = int(pending.get("confirmed-round", 0) or 0)

        confirmations = 0
        if confirmed_round:
            status = self._algo_clients.algod.status()
            last_round = int(status.get("last-round", 0) or 0)
            if last_round >= confirmed_round:
                confirmations = (last_round - confirmed_round) + 1

        return {
            "transaction_hash": txid,
            "confirmations": confirmations,
            "block_number": confirmed_round or None,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def _compute_merkle_root(self, hashes: List[str]) -> str:
        """Compute Merkle root of hashes"""
        if not hashes:
            return ""
        
        if len(hashes) == 1:
            return hashes[0]
        
        # Build Merkle tree
        level = hashes[:]
        while len(level) > 1:
            next_level = []
            for i in range(0, len(level), 2):
                left = level[i]
                right = level[i + 1] if i + 1 < len(level) else level[i]
                combined = left + right
                parent = self.hash_utils.sha256(combined.encode())
                next_level.append(parent)
            level = next_level
        
        return level[0]
    
    def _generate_anchor_id(self, package_id: str, blockchain: BlockchainType) -> str:
        """Generate unique anchor ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        content = f"anchor_{package_id}_{blockchain.value}_{timestamp}"
        hash_suffix = self.hash_utils.sha256(content.encode())[:8]
        return f"anchor_{blockchain.value}_{hash_suffix}"
    
    def _get_default_rpc(self, blockchain: BlockchainType, network: str) -> str:
        """Get default RPC URL for Algorand network"""
        rpcs = {
            BlockchainType.ALGORAND: {
                "mainnet": "https://mainnet-api.algonode.cloud",
                "testnet": "https://testnet-api.algonode.cloud",
                "betanet": "https://betanet-api.algonode.cloud"
            },
            BlockchainType.MOCK: {
                "mainnet": "http://localhost:4001"
            }
        }
        
        return rpcs.get(blockchain, {}).get(network, "http://localhost:4001")
    
    def get_explorer_url(self, transaction_hash: str) -> str:
        """Get Algorand blockchain explorer URL for transaction"""
        if self.blockchain_type == BlockchainType.MOCK:
            return f"http://localhost:4001/tx/{transaction_hash}"

        # AlgoExplorer uses different subdomains for networks
        if (self.network or "mainnet").lower() == "testnet":
            return f"https://testnet.algoexplorer.io/tx/{transaction_hash}"
        if (self.network or "mainnet").lower() == "betanet":
            return f"https://betanet.algoexplorer.io/tx/{transaction_hash}"
        return f"https://algoexplorer.io/tx/{transaction_hash}"
    
    def estimate_cost(self, data_size: int) -> Dict[str, Any]:
        """Estimate Algorand anchoring cost"""
        # Algorand uses fixed fees
        costs = {
            BlockchainType.ALGORAND: {
                "base_fee": 0.001,  # 0.001 ALGO per transaction
                "note_size": data_size,
                "max_note_size": 1024,  # 1KB max note size
                "currency": "ALGO",
                "estimated_cost": 0.001  # Fixed fee regardless of note size
            },
            BlockchainType.MOCK: {
                "cost": 0,
                "currency": "FREE"
            }
        }
        
        return costs.get(self.blockchain_type, {})

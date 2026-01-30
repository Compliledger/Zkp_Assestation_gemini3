"""
Real Algorand TESTNET Integration
Implements actual blockchain anchoring to Algorand TESTNET
"""

from typing import Dict, Any, Optional
from datetime import datetime
import json
import time

from algosdk import account, transaction, mnemonic
from algosdk.v2client import algod
from algosdk.encoding import encode_address

from app.utils.crypto import HashUtils
from app.utils.errors import AnchoringError


class AlgorandTestnetAnchor:
    """
    Real Algorand TESTNET anchoring implementation
    Uses AlgoNode free API for TESTNET access
    """
    
    def __init__(
        self,
        algod_address: str = "https://testnet-api.algonode.cloud",
        algod_token: str = "",  # AlgoNode doesn't require token
        sender_mnemonic: Optional[str] = None
    ):
        """
        Initialize Algorand TESTNET client
        
        Args:
            algod_address: Algorand node API address (default: AlgoNode TESTNET)
            algod_token: API token (empty for AlgoNode)
            sender_mnemonic: 25-word mnemonic for sender account
        """
        self.algod_client = algod.AlgodClient(algod_token, algod_address)
        self.hash_utils = HashUtils()
        
        # Setup account from mnemonic or generate new one
        if sender_mnemonic:
            self.private_key = mnemonic.to_private_key(sender_mnemonic)
            self.sender_address = account.address_from_private_key(self.private_key)
        else:
            # Generate new account for testing (user must fund it)
            self.private_key, self.sender_address = account.generate_account()
            self.mnemonic = mnemonic.from_private_key(self.private_key)
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information and balance"""
        try:
            account_info = self.algod_client.account_info(self.sender_address)
            return {
                "address": self.sender_address,
                "balance_microalgos": account_info.get("amount", 0),
                "balance_algos": account_info.get("amount", 0) / 1_000_000,
                "status": account_info.get("status"),
                "mnemonic": getattr(self, 'mnemonic', None)
            }
        except Exception as e:
            raise AnchoringError(f"Failed to get account info: {e}")
    
    def anchor_attestation(
        self,
        attestation_id: str,
        merkle_root: str,
        package_hash: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Anchor attestation to Algorand TESTNET
        
        Args:
            attestation_id: Unique attestation identifier
            merkle_root: Merkle tree root hash
            package_hash: Hash of attestation package
            metadata: Additional metadata
        
        Returns:
            Transaction details including txn_id, confirmed_round, and explorer URL
        
        Raises:
            AnchoringError: If anchoring fails
        """
        # Prepare note data according to ZKPA v1.1 spec
        note_data = {
            "protocol": "zkpa",
            "version": "1.1",
            "attestation_id": attestation_id,
            "merkle_root": merkle_root,
            "package_hash": package_hash,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if metadata:
            note_data["metadata"] = metadata
        
        # Convert to JSON and encode
        note_json = json.dumps(note_data, sort_keys=True)
        note_bytes = note_json.encode('utf-8')
        
        # Check note size (Algorand max is 1024 bytes)
        if len(note_bytes) > 1024:
            raise AnchoringError(f"Note too large: {len(note_bytes)} bytes (max 1024)")
        
        try:
            # Get suggested params from network
            params = self.algod_client.suggested_params()
            
            # Create payment transaction (self-transfer with note)
            # Amount = 0 for pure data anchoring
            txn = transaction.PaymentTxn(
                sender=self.sender_address,
                sp=params,
                receiver=self.sender_address,
                amt=0,
                note=note_bytes
            )
            
            # Sign transaction
            signed_txn = txn.sign(self.private_key)
            
            # Submit transaction
            tx_id = self.algod_client.send_transaction(signed_txn)
            
            print(f"Transaction submitted: {tx_id}")
            print("Waiting for confirmation...")
            
            # Wait for confirmation (up to 4 rounds, ~16 seconds)
            confirmed_txn = transaction.wait_for_confirmation(
                self.algod_client, 
                tx_id, 
                4
            )
            
            confirmed_round = confirmed_txn.get("confirmed-round")
            
            print(f"Transaction confirmed in round: {confirmed_round}")
            
            # Get transaction details
            txn_info = self.algod_client.pending_transaction_info(tx_id)
            
            # Verify note was included
            txn_note = txn_info.get("txn", {}).get("txn", {}).get("note")
            if txn_note:
                # Decode and verify
                import base64
                decoded_note = base64.b64decode(txn_note).decode('utf-8')
                verified_data = json.loads(decoded_note)
            else:
                verified_data = None
            
            # Build explorer URL
            explorer_url = f"https://testnet.algoexplorer.io/tx/{tx_id}"
            
            return {
                "transaction_id": tx_id,
                "confirmed_round": confirmed_round,
                "explorer_url": explorer_url,
                "block_time": confirmed_txn.get("pool-error", ""),
                "sender": self.sender_address,
                "note_data": note_data,
                "verified_on_chain": verified_data == note_data if verified_data else False,
                "transaction_fee": txn_info.get("txn", {}).get("txn", {}).get("fee", 0) / 1_000_000
            }
            
        except Exception as e:
            raise AnchoringError(f"Failed to anchor to Algorand TESTNET: {e}")
    
    def verify_transaction(self, tx_id: str) -> Dict[str, Any]:
        """
        Verify transaction exists on-chain and extract note data
        
        Args:
            tx_id: Transaction ID to verify
        
        Returns:
            Transaction details with decoded note
        """
        try:
            # Get transaction info
            txn_info = self.algod_client.pending_transaction_info(tx_id)
            
            # Extract note
            txn_note = txn_info.get("txn", {}).get("txn", {}).get("note")
            
            if txn_note:
                import base64
                decoded_note = base64.b64decode(txn_note).decode('utf-8')
                note_data = json.loads(decoded_note)
            else:
                note_data = None
            
            return {
                "transaction_id": tx_id,
                "confirmed": txn_info.get("confirmed-round") is not None,
                "confirmed_round": txn_info.get("confirmed-round"),
                "note_data": note_data,
                "sender": txn_info.get("txn", {}).get("txn", {}).get("snd"),
                "fee": txn_info.get("txn", {}).get("txn", {}).get("fee", 0) / 1_000_000
            }
            
        except Exception as e:
            raise AnchoringError(f"Failed to verify transaction: {e}")
    
    def get_network_status(self) -> Dict[str, Any]:
        """Get Algorand TESTNET status"""
        try:
            status = self.algod_client.status()
            return {
                "network": "testnet",
                "last_round": status.get("last-round"),
                "time_since_last_round": status.get("time-since-last-round"),
                "catchup_time": status.get("catchup-time"),
                "last_version": status.get("last-version")
            }
        except Exception as e:
            raise AnchoringError(f"Failed to get network status: {e}")
    
    def fund_account_instructions(self) -> str:
        """
        Get instructions for funding the account via TESTNET dispenser
        """
        return f"""
To fund this account for TESTNET transactions:

1. Visit the Algorand TESTNET Dispenser:
   https://bank.testnet.algorand.network/

2. Enter this address: {self.sender_address}

3. Request TESTNET ALGO (you'll receive ~10 ALGO for testing)

Account Details:
- Address: {self.sender_address}
- Mnemonic: {getattr(self, 'mnemonic', 'Not available (loaded from existing key)')}

IMPORTANT: Save your mnemonic in a secure location!
"""

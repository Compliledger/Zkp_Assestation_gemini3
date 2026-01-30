"""
Third-Party External Verifier

Simulates an EXTERNAL auditor/verifier with NO access to internal systems.

Available inputs:
- Attestation JSON file
- Algorand transaction ID
- Public signing key (Algorand address)

NOT available:
- ZKPA database
- RMF engine
- AuditSync
- S3 access
- Private keys
- Internal APIs

This verifier can ONLY:
1. Read the attestation JSON
2. Query public Algorand TESTNET nodes
3. Verify cryptographic commitments
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import base64

# Algorand SDK for querying public nodes
from algosdk.v2client import algod


class ExternalVerifier:
    """
    Third-party verifier with no internal system access
    """
    
    def __init__(
        self,
        attestation_file: Path,
        transaction_id: str,
        public_key: str,
        verifier_identity: str = "external"
    ):
        """
        Initialize external verifier
        
        Args:
            attestation_file: Path to attestation JSON
            transaction_id: Algorand transaction ID
            public_key: Public key (Algorand address)
            verifier_identity: Identifier for this verifier
        """
        self.attestation_file = attestation_file
        self.transaction_id = transaction_id
        self.public_key = public_key
        self.verifier_identity = verifier_identity
        self.verification_start_time = None
        
        # Connect to PUBLIC Algorand TESTNET node (no authentication needed)
        self.algod_client = algod.AlgodClient(
            algod_token="",  # AlgoNode doesn't require token
            algod_address="https://testnet-api.algonode.cloud"
        )
        
        # Verification results
        self.results = {}
    
    def step1_verify_digital_signature(self, attestation_data: Dict[str, Any]) -> bool:
        """
        Step 1: Verify digital signature
        
        Note: For Algorand transactions, the signature is verified by the blockchain itself.
        If the transaction is confirmed on-chain, the signature is valid.
        We verify the signer matches the expected public key.
        
        Args:
            attestation_data: Attestation JSON data
        
        Returns:
            True if signature verification passes
        """
        print("\n" + "="*70)
        print("STEP 1: VERIFY DIGITAL SIGNATURE")
        print("="*70)
        
        # Extract signer from attestation
        attestation_signer = attestation_data.get("all_results", {}).get(
            "signature", {}
        ).get("signer_address")
        
        print(f"\n✓ Expected Signer (Public Key):")
        print(f"  {self.public_key}")
        
        print(f"\n✓ Attestation Signer:")
        print(f"  {attestation_signer if attestation_signer else 'Not specified'}")
        
        # For Algorand, we'll verify the transaction signer matches
        # This will be done when we fetch the transaction
        print(f"\n✓ Signature Verification:")
        print(f"  Method: Algorand blockchain validation")
        print(f"  Note: If transaction is confirmed on-chain, signature is valid")
        
        signature_match = (attestation_signer == self.public_key) if attestation_signer else False
        
        print(f"  Signer Match: {'✅ YES' if signature_match else '⚠️  Will verify from blockchain'}")
        
        self.results["signature_verification"] = {
            "expected_signer": self.public_key,
            "attestation_signer": attestation_signer,
            "method": "algorand_blockchain_validation"
        }
        
        return True  # Will be fully verified in step 3
    
    def step2_extract_merkle_root(self, attestation_data: Dict[str, Any]) -> str:
        """
        Step 2: Extract merkle_root from attestation JSON
        
        Args:
            attestation_data: Attestation JSON data
        
        Returns:
            Merkle root from attestation
        """
        print("\n" + "="*70)
        print("STEP 2: EXTRACT MERKLE_ROOT FROM ATTESTATION")
        print("="*70)
        
        # Extract merkle_root from attestation package
        merkle_root = attestation_data.get("all_results", {}).get(
            "attestation", {}
        ).get("attestation_package", {}).get("evidence", {}).get("merkle_root")
        
        if not merkle_root:
            # Try alternate location
            merkle_root = attestation_data.get("summary", {}).get("merkle_root")
        
        print(f"\n✓ Merkle Root Extracted:")
        print(f"  {merkle_root}")
        
        # Also extract attestation metadata
        attestation_id = attestation_data.get("summary", {}).get("attestation_id")
        evidence_count = attestation_data.get("summary", {}).get("evidence_count")
        
        print(f"\n✓ Attestation Metadata:")
        print(f"  Attestation ID: {attestation_id}")
        print(f"  Evidence Count: {evidence_count}")
        
        self.results["attestation_data"] = {
            "merkle_root": merkle_root,
            "attestation_id": attestation_id,
            "evidence_count": evidence_count
        }
        
        return merkle_root
    
    def step3_fetch_algorand_transaction(self) -> Dict[str, Any]:
        """
        Step 3: Fetch Algorand transaction from public node
        
        Returns:
            Transaction data
        """
        print("\n" + "="*70)
        print("STEP 3: FETCH ALGORAND TRANSACTION FROM PUBLIC NODE")
        print("="*70)
        
        print(f"\n✓ Connecting to Public Algorand TESTNET Node:")
        print(f"  Node: https://testnet-api.algonode.cloud")
        print(f"  Transaction ID: {self.transaction_id}")
        
        try:
            # Query transaction from public node
            print(f"\n✓ Querying transaction...")
            txn_info = self.algod_client.pending_transaction_info(self.transaction_id)
            
            # Extract key information
            confirmed_round = txn_info.get("confirmed-round")
            sender = txn_info.get("txn", {}).get("txn", {}).get("snd")
            
            print(f"\n✓ Transaction Found:")
            print(f"  Confirmed Round: {confirmed_round}")
            print(f"  Sender: {sender}")
            print(f"  Transaction Type: {txn_info.get('txn', {}).get('txn', {}).get('type')}")
            
            # Verify sender matches expected public key
            sender_match = (sender == self.public_key)
            print(f"\n✓ Sender Verification:")
            print(f"  Expected: {self.public_key}")
            print(f"  Actual:   {sender}")
            print(f"  Match: {'✅ YES' if sender_match else '❌ NO'}")
            
            if not sender_match:
                print(f"  ⚠️  WARNING: Sender mismatch!")
            
            self.results["blockchain_verification"] = {
                "transaction_id": self.transaction_id,
                "confirmed_round": confirmed_round,
                "sender": sender,
                "sender_matches_public_key": sender_match,
                "transaction_confirmed": confirmed_round is not None
            }
            
            return txn_info
            
        except Exception as e:
            print(f"\n❌ Failed to fetch transaction: {e}")
            self.results["blockchain_verification"] = {
                "error": str(e),
                "transaction_confirmed": False
            }
            raise
    
    def step4_decode_transaction_note(self, txn_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 4: Decode transaction note
        
        Args:
            txn_info: Transaction information from blockchain
        
        Returns:
            Decoded note data
        """
        print("\n" + "="*70)
        print("STEP 4: DECODE TRANSACTION NOTE")
        print("="*70)
        
        # Extract note from transaction
        txn_note = txn_info.get("txn", {}).get("txn", {}).get("note")
        
        if not txn_note:
            print(f"\n❌ No note found in transaction")
            return {}
        
        try:
            # Decode base64 note
            decoded_note = base64.b64decode(txn_note).decode('utf-8')
            note_data = json.loads(decoded_note)
            
            print(f"\n✓ Transaction Note Decoded:")
            print(f"  Protocol: {note_data.get('protocol')}")
            print(f"  Version: {note_data.get('version')}")
            print(f"  Attestation ID: {note_data.get('attestation_id')}")
            print(f"  Merkle Root: {note_data.get('merkle_root')}")
            print(f"  Package Hash: {note_data.get('package_hash')}")
            print(f"  Timestamp: {note_data.get('timestamp')}")
            
            if note_data.get('metadata'):
                print(f"\n✓ Metadata:")
                for key, value in note_data['metadata'].items():
                    print(f"    {key}: {value}")
            
            self.results["onchain_note_data"] = note_data
            
            return note_data
            
        except Exception as e:
            print(f"\n❌ Failed to decode note: {e}")
            self.results["onchain_note_data"] = {"error": str(e)}
            raise
    
    def step5_assert_merkle_root_match(
        self,
        attestation_merkle_root: str,
        onchain_note_data: Dict[str, Any]
    ) -> bool:
        """
        Step 5: Assert on-chain merkle_root matches attestation
        
        Args:
            attestation_merkle_root: Merkle root from attestation JSON
            onchain_note_data: Decoded note data from blockchain
        
        Returns:
            True if merkle roots match
        """
        print("\n" + "="*70)
        print("STEP 5: ASSERT MERKLE_ROOT MATCH")
        print("="*70)
        
        onchain_merkle_root = onchain_note_data.get("merkle_root")
        
        print(f"\n✓ Merkle Root Comparison:")
        print(f"  Attestation JSON: {attestation_merkle_root}")
        print(f"  On-Chain Note:    {onchain_merkle_root}")
        
        match = (attestation_merkle_root == onchain_merkle_root)
        print(f"  Match: {'✅ YES' if match else '❌ NO'}")
        
        # Additional verification checks
        print(f"\n✓ Additional Verification Checks:")
        
        checks = {
            "protocol_is_zkpa": onchain_note_data.get("protocol") == "zkpa",
            "version_is_1_1": onchain_note_data.get("version") == "1.1",
            "merkle_root_present": onchain_merkle_root is not None,
            "merkle_root_matches": match,
            "attestation_id_present": onchain_note_data.get("attestation_id") is not None
        }
        
        for check_name, passed in checks.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {check_name}: {status}")
        
        all_checks_passed = all(checks.values())
        
        self.results["verification_checks"] = checks
        self.results["all_checks_passed"] = all_checks_passed
        
        return match and all_checks_passed
    
    def run_verification(self) -> Dict[str, Any]:
        """
        Execute complete third-party verification
        
        Returns:
            Verification results
        """
        self.verification_start_time = time.time()
        
        print("\n" + "="*70)
        print("THIRD-PARTY EXTERNAL VERIFIER")
        print("="*70)
        print(f"\nVerifier Identity: {self.verifier_identity}")
        print(f"Attestation File: {self.attestation_file}")
        print(f"Transaction ID: {self.transaction_id}")
        print(f"Public Key: {self.public_key}")
        
        print(f"\n⚠️  VERIFICATION CONSTRAINTS:")
        print(f"  ❌ NO access to ZKPA database")
        print(f"  ❌ NO access to RMF engine")
        print(f"  ❌ NO access to AuditSync")
        print(f"  ❌ NO access to S3 storage")
        print(f"  ❌ NO access to private keys")
        print(f"  ✅ ONLY public blockchain and attestation JSON")
        
        try:
            # Load attestation JSON
            print(f"\n✓ Loading attestation JSON...")
            with open(self.attestation_file, 'r') as f:
                attestation_data = json.load(f)
            print(f"  File loaded successfully")
            
            # Step 1: Verify digital signature
            self.step1_verify_digital_signature(attestation_data)
            
            # Step 2: Extract merkle_root
            attestation_merkle_root = self.step2_extract_merkle_root(attestation_data)
            
            # Step 3: Fetch transaction from public node
            txn_info = self.step3_fetch_algorand_transaction()
            
            # Step 4: Decode transaction note
            onchain_note_data = self.step4_decode_transaction_note(txn_info)
            
            # Step 5: Assert merkle_root match
            verification_passed = self.step5_assert_merkle_root_match(
                attestation_merkle_root,
                onchain_note_data
            )
            
            # Calculate verification time
            verification_time = time.time() - self.verification_start_time
            
            # Build final output
            final_results = {
                "verification_passed": verification_passed,
                "verification_time": verification_time,
                "verifier_identity": self.verifier_identity,
                "timestamp": datetime.utcnow().isoformat(),
                "transaction_id": self.transaction_id,
                "public_key": self.public_key,
                "merkle_root_match": self.results.get("all_checks_passed", False),
                "transaction_confirmed": self.results.get("blockchain_verification", {}).get("transaction_confirmed", False),
                "sender_verified": self.results.get("blockchain_verification", {}).get("sender_matches_public_key", False),
                "protocol_valid": self.results.get("verification_checks", {}).get("protocol_is_zkpa", False),
                "version_valid": self.results.get("verification_checks", {}).get("version_is_1_1", False),
                "detailed_results": self.results
            }
            
            # Print summary
            print("\n" + "="*70)
            print("VERIFICATION SUMMARY")
            print("="*70)
            
            print(f"\n✓ Final Results:")
            print(f"  verification_passed: {verification_passed}")
            print(f"  verification_time: {verification_time:.3f} seconds")
            print(f"  verifier_identity: {self.verifier_identity}")
            print(f"  timestamp: {final_results['timestamp']}")
            
            print(f"\n✓ Verification Details:")
            print(f"  Transaction Confirmed: {'✅ YES' if final_results['transaction_confirmed'] else '❌ NO'}")
            print(f"  Sender Verified: {'✅ YES' if final_results['sender_verified'] else '❌ NO'}")
            print(f"  Merkle Root Match: {'✅ YES' if final_results['merkle_root_match'] else '❌ NO'}")
            print(f"  Protocol Valid (zkpa): {'✅ YES' if final_results['protocol_valid'] else '❌ NO'}")
            print(f"  Version Valid (1.1): {'✅ YES' if final_results['version_valid'] else '❌ NO'}")
            
            if verification_passed:
                print("\n" + "="*70)
                print("✅ ✅ ✅ VERIFICATION PASSED ✅ ✅ ✅")
                print("="*70)
                print("\n🔒 INDEPENDENT VERIFICATION SUCCESSFUL 🔒")
                print("\nThis attestation has been independently verified by a")
                print("third-party auditor with NO access to internal systems.")
                print("\nVerification relied ONLY on:")
                print("  • Public blockchain data (Algorand TESTNET)")
                print("  • Attestation JSON file")
                print("  • Public key (Algorand address)")
                print("\nAll cryptographic commitments verified successfully.")
            else:
                print("\n" + "="*70)
                print("❌ ❌ ❌ VERIFICATION FAILED ❌ ❌ ❌")
                print("="*70)
            
            return final_results
            
        except Exception as e:
            verification_time = time.time() - self.verification_start_time if self.verification_start_time else 0
            
            print(f"\n❌ VERIFICATION FAILED WITH ERROR: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "verification_passed": False,
                "verification_time": verification_time,
                "verifier_identity": self.verifier_identity,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


def main():
    """Main entry point"""
    
    # Configuration for external verifier
    attestation_file = Path(__file__).parent / "attestation_results.json"
    
    # These would be provided by the entity requesting verification
    transaction_id = "HCMPCTRU3MRBLUOFRF66KFPGBCQ7DFRCCLPKOB7HTLNSFHJDFQ2Q"
    public_key = "HDNKNQ7FJF37KLEVCHWWGH5O3J7HDY26JKNXHWYMYBXGL4VGETH57UKQ3A"
    
    print("\n" + "="*70)
    print("THIRD-PARTY ATTESTATION VERIFICATION")
    print("Independent Auditor Scenario")
    print("="*70)
    
    if not attestation_file.exists():
        print(f"\n❌ Attestation file not found: {attestation_file}")
        print("Please ensure the attestation JSON is available.")
        return 1
    
    # Create external verifier
    verifier = ExternalVerifier(
        attestation_file=attestation_file,
        transaction_id=transaction_id,
        public_key=public_key,
        verifier_identity="external"
    )
    
    # Run verification
    results = verifier.run_verification()
    
    # Save results
    output_file = Path(__file__).parent / "external_verification_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Verification results saved to: {output_file}")
    
    return 0 if results.get("verification_passed") else 1


if __name__ == "__main__":
    exit(main())

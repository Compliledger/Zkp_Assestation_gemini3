"""
End-to-End Attestation with Real Algorand TESTNET Anchoring

This script performs a complete attestation workflow:
1. Collect mock evidence (5+ items) and generate SHA-256 hashes
2. Build Merkle tree and output merkle_root, leaf_count
3. Assemble attestation package using ZKPA v1.1 schema
4. Sign attestation using Ed25519
5. Anchor to Algorand TESTNET using real note transaction
6. Wait for confirmation and return transaction details
7. Verify transaction exists on-chain with correct data

NO MOCKING - This uses real Algorand TESTNET blockchain.
"""

import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import secrets

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.merkle import create_merkle_tree_from_hashes
from app.core.anchoring.algorand_testnet import AlgorandTestnetAnchor
from app.utils.crypto import HashUtils


class EndToEndAttestation:
    """Complete end-to-end attestation workflow"""
    
    def __init__(self, sender_mnemonic: str = None):
        """
        Initialize attestation workflow
        
        Args:
            sender_mnemonic: 25-word Algorand mnemonic (if None, generates new account)
        """
        self.hash_utils = HashUtils()
        self.algorand = AlgorandTestnetAnchor(sender_mnemonic=sender_mnemonic)
        self.results = {}
        
    def step1_collect_evidence(self, min_items: int = 5) -> dict:
        """
        Step 1: Collect mock evidence and generate SHA-256 hashes
        
        Args:
            min_items: Minimum number of evidence items (default: 5)
        
        Returns:
            Evidence collection results
        """
        print("\n" + "="*70)
        print("STEP 1: COLLECT EVIDENCE AND GENERATE SHA-256 HASHES")
        print("="*70)
        
        evidence_items = []
        
        # Generate mock evidence
        evidence_types = [
            "compliance_report",
            "security_audit",
            "access_log",
            "configuration_snapshot",
            "vulnerability_scan",
            "penetration_test",
            "code_review"
        ]
        
        for i in range(min_items):
            evidence_type = evidence_types[i % len(evidence_types)]
            
            # Create mock evidence content
            evidence_content = {
                "evidence_id": f"EV-{datetime.utcnow().strftime('%Y%m%d')}-{i+1:04d}",
                "type": evidence_type,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "compliance_verification_agent",
                "data": {
                    "description": f"Mock {evidence_type.replace('_', ' ')} evidence #{i+1}",
                    "status": "compliant",
                    "score": 95 + (i % 5),
                    "findings": [
                        f"Finding {j+1}: All controls verified"
                        for j in range(3)
                    ]
                }
            }
            
            # Serialize to JSON
            evidence_json = json.dumps(evidence_content, sort_keys=True)
            
            # Generate SHA-256 hash
            evidence_hash = self.hash_utils.sha256(evidence_json.encode())
            
            evidence_items.append({
                "evidence_id": evidence_content["evidence_id"],
                "type": evidence_type,
                "content": evidence_content,
                "content_hash": evidence_hash,
                "size_bytes": len(evidence_json)
            })
            
            print(f"\n✓ Evidence #{i+1}:")
            print(f"  ID: {evidence_content['evidence_id']}")
            print(f"  Type: {evidence_type}")
            print(f"  Hash: {evidence_hash}")
            print(f"  Size: {len(evidence_json)} bytes")
        
        results = {
            "evidence_count": len(evidence_items),
            "evidence_items": evidence_items,
            "evidence_hashes": [item["content_hash"] for item in evidence_items],
            "total_size_bytes": sum(item["size_bytes"] for item in evidence_items)
        }
        
        print(f"\n{'='*70}")
        print(f"COLLECTED {results['evidence_count']} EVIDENCE ITEMS")
        print(f"Total Size: {results['total_size_bytes']} bytes")
        print(f"{'='*70}")
        
        self.results["evidence"] = results
        return results
    
    def step2_build_merkle_tree(self, evidence_hashes: list) -> dict:
        """
        Step 2: Build Merkle tree and output merkle_root, leaf_count
        
        Args:
            evidence_hashes: List of evidence hashes
        
        Returns:
            Merkle tree results
        """
        print("\n" + "="*70)
        print("STEP 2: BUILD MERKLE TREE")
        print("="*70)
        
        # Create Merkle tree
        merkle_tree = create_merkle_tree_from_hashes(
            evidence_hashes,
            hash_algorithm="SHA256"
        )
        
        merkle_root = merkle_tree.get_root()
        leaf_count = len(evidence_hashes)
        
        print(f"\n✓ Merkle Tree Built:")
        print(f"  Merkle Root: {merkle_root}")
        print(f"  Leaf Count: {leaf_count}")
        print(f"  Hash Algorithm: SHA256")
        
        # Generate proof for first leaf (demonstration)
        proof = merkle_tree.get_proof(0)
        print(f"\n✓ Sample Merkle Proof (Leaf 0):")
        print(f"  Proof Path Length: {len(proof)}")
        print(f"  Proof Valid: {merkle_tree.verify_proof(evidence_hashes[0], proof, merkle_root)}")
        
        results = {
            "merkle_root": merkle_root,
            "leaf_count": leaf_count,
            "hash_algorithm": "SHA256",
            "sample_proof": proof
        }
        
        print(f"\n{'='*70}")
        print(f"MERKLE ROOT: {merkle_root}")
        print(f"LEAF COUNT: {leaf_count}")
        print(f"{'='*70}")
        
        self.results["merkle_tree"] = results
        return results
    
    def step3_assemble_attestation(self, evidence_data: dict, merkle_data: dict) -> dict:
        """
        Step 3: Assemble attestation package using ZKPA v1.1 schema
        
        Args:
            evidence_data: Evidence collection results
            merkle_data: Merkle tree results
        
        Returns:
            Attestation package
        """
        print("\n" + "="*70)
        print("STEP 3: ASSEMBLE ATTESTATION PACKAGE (ZKPA v1.1)")
        print("="*70)
        
        # Generate unique attestation ID
        attestation_id = f"ATT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4).upper()}"
        
        # Build attestation package according to ZKPA v1.1
        attestation_package = {
            "protocol": "zkpa",
            "version": "1.1",
            "attestation_id": attestation_id,
            "created_at": datetime.utcnow().isoformat(),
            
            # Claim information
            "claim": {
                "claim_id": f"CLM-{datetime.utcnow().strftime('%Y%m%d')}-001",
                "claim_type": "compliance_verification",
                "claim_statement": "Organization maintains SOC2 Type II compliance controls",
                "status": "verified"
            },
            
            # Evidence commitment
            "evidence": {
                "bundle_id": f"BDL-{datetime.utcnow().strftime('%Y%m%d')}-001",
                "evidence_count": evidence_data["evidence_count"],
                "merkle_root": merkle_data["merkle_root"],
                "hash_algorithm": merkle_data["hash_algorithm"],
                "evidence_types": list(set(item["type"] for item in evidence_data["evidence_items"]))
            },
            
            # Issuer information
            "issuer": {
                "id": "compliance-agent-001",
                "name": "ZKP Compliance Verification Agent",
                "type": "automated_agent"
            },
            
            # Subject (organization being attested)
            "subject": {
                "organization": "Example Corp",
                "domain": "example.com",
                "assessment_period": {
                    "start": (datetime.utcnow() - timedelta(days=90)).isoformat(),
                    "end": datetime.utcnow().isoformat()
                }
            },
            
            # Attestation metadata
            "metadata": {
                "compliance_framework": "SOC2_TYPE_II",
                "assessment_type": "continuous_monitoring",
                "confidence_level": "high",
                "validity_period_days": 90
            }
        }
        
        # Compute package hash
        package_json = json.dumps(attestation_package, sort_keys=True)
        package_hash = self.hash_utils.sha256(package_json.encode())
        attestation_package["package_hash"] = package_hash
        
        print(f"\n✓ Attestation Package Assembled:")
        print(f"  Attestation ID: {attestation_id}")
        print(f"  Protocol: {attestation_package['protocol']}")
        print(f"  Version: {attestation_package['version']}")
        print(f"  Package Hash: {package_hash}")
        print(f"  Evidence Count: {evidence_data['evidence_count']}")
        print(f"  Merkle Root: {merkle_data['merkle_root']}")
        
        results = {
            "attestation_package": attestation_package,
            "attestation_id": attestation_id,
            "package_hash": package_hash,
            "package_size_bytes": len(package_json)
        }
        
        print(f"\n{'='*70}")
        print(f"ATTESTATION ID: {attestation_id}")
        print(f"PACKAGE HASH: {package_hash}")
        print(f"{'='*70}")
        
        self.results["attestation"] = results
        return results
    
    def step4_sign_attestation(self, package_hash: str) -> dict:
        """
        Step 4: Sign attestation using Ed25519
        
        Args:
            package_hash: Hash of attestation package
        
        Returns:
            Signature results
        """
        print("\n" + "="*70)
        print("STEP 4: SIGN ATTESTATION (Ed25519)")
        print("="*70)
        
        # For Algorand, the transaction signing is done with Ed25519
        # The account's private key will be used to sign the transaction
        
        # Get account info
        account_info = self.algorand.get_account_info()
        signer_address = account_info["address"]
        
        # Simulate signature metadata (actual signing happens in step 5)
        signature_metadata = {
            "algorithm": "Ed25519",
            "signer_address": signer_address,
            "signed_at": datetime.utcnow().isoformat(),
            "content_hash": package_hash,
            "signature_type": "algorand_account"
        }
        
        print(f"\n✓ Signature Prepared:")
        print(f"  Algorithm: Ed25519")
        print(f"  Signer Address: {signer_address}")
        print(f"  Content Hash: {package_hash}")
        print(f"  Note: Actual signature will be created during blockchain transaction")
        
        results = {
            "signature_metadata": signature_metadata,
            "signer_address": signer_address,
            "algorithm": "Ed25519"
        }
        
        print(f"\n{'='*70}")
        print(f"SIGNER: {signer_address}")
        print(f"ALGORITHM: Ed25519")
        print(f"{'='*70}")
        
        self.results["signature"] = results
        return results
    
    def step5_anchor_to_algorand(self, attestation_data: dict, merkle_data: dict) -> dict:
        """
        Step 5: Anchor attestation to Algorand TESTNET
        
        Args:
            attestation_data: Attestation package data
            merkle_data: Merkle tree data
        
        Returns:
            Blockchain anchoring results
        """
        print("\n" + "="*70)
        print("STEP 5: ANCHOR TO ALGORAND TESTNET (REAL BLOCKCHAIN)")
        print("="*70)
        
        # Check account balance
        account_info = self.algorand.get_account_info()
        print(f"\n✓ Account Status:")
        print(f"  Address: {account_info['address']}")
        print(f"  Balance: {account_info['balance_algos']:.6f} ALGO")
        
        if account_info['balance_algos'] < 0.1:
            print(f"\n⚠️  WARNING: Low balance!")
            print(f"\nTo fund your account, visit:")
            print(f"https://bank.testnet.algorand.network/")
            print(f"and send TESTNET ALGO to: {account_info['address']}")
            
            if account_info.get('mnemonic'):
                print(f"\n⚠️  SAVE YOUR MNEMONIC:")
                print(f"{account_info['mnemonic']}")
            
            # For demo purposes, continue anyway (will fail if insufficient funds)
        
        # Prepare metadata for blockchain note
        metadata = {
            "claim_type": attestation_data["attestation_package"]["claim"]["claim_type"],
            "evidence_count": attestation_data["attestation_package"]["evidence"]["evidence_count"],
            "framework": attestation_data["attestation_package"]["metadata"]["compliance_framework"]
        }
        
        print(f"\n✓ Submitting transaction to Algorand TESTNET...")
        print(f"  Attestation ID: {attestation_data['attestation_id']}")
        print(f"  Merkle Root: {merkle_data['merkle_root']}")
        print(f"  Package Hash: {attestation_data['package_hash']}")
        
        try:
            # Anchor to Algorand TESTNET (REAL BLOCKCHAIN TRANSACTION)
            anchor_result = self.algorand.anchor_attestation(
                attestation_id=attestation_data["attestation_id"],
                merkle_root=merkle_data["merkle_root"],
                package_hash=attestation_data["package_hash"],
                metadata=metadata
            )
            
            print(f"\n✅ TRANSACTION CONFIRMED ON ALGORAND TESTNET!")
            print(f"\n✓ Transaction Details:")
            print(f"  Transaction ID: {anchor_result['transaction_id']}")
            print(f"  Confirmed Round: {anchor_result['confirmed_round']}")
            print(f"  Sender: {anchor_result['sender']}")
            print(f"  Fee: {anchor_result['transaction_fee']} ALGO")
            print(f"  Explorer URL: {anchor_result['explorer_url']}")
            
            results = {
                "success": True,
                "transaction_id": anchor_result["transaction_id"],
                "confirmed_round": anchor_result["confirmed_round"],
                "explorer_url": anchor_result["explorer_url"],
                "sender": anchor_result["sender"],
                "fee": anchor_result["transaction_fee"],
                "note_data": anchor_result["note_data"],
                "verified_on_chain": anchor_result.get("verified_on_chain", False)
            }
            
            print(f"\n{'='*70}")
            print(f"✅ ANCHORED TO BLOCKCHAIN")
            print(f"Transaction ID: {anchor_result['transaction_id']}")
            print(f"Confirmed Round: {anchor_result['confirmed_round']}")
            print(f"{'='*70}")
            
        except Exception as e:
            print(f"\n❌ FAILED TO ANCHOR: {e}")
            results = {
                "success": False,
                "error": str(e)
            }
        
        self.results["anchoring"] = results
        return results
    
    def step6_verify_transaction(self, transaction_id: str, expected_data: dict) -> dict:
        """
        Step 6: Verify transaction on-chain
        
        Args:
            transaction_id: Transaction ID to verify
            expected_data: Expected data in transaction note
        
        Returns:
            Verification results
        """
        print("\n" + "="*70)
        print("STEP 6: VERIFY TRANSACTION ON-CHAIN")
        print("="*70)
        
        print(f"\n✓ Querying Algorand TESTNET for transaction: {transaction_id}")
        
        try:
            # Verify transaction exists on-chain
            verification = self.algorand.verify_transaction(transaction_id)
            
            print(f"\n✓ Transaction Found:")
            print(f"  Confirmed: {verification['confirmed']}")
            print(f"  Confirmed Round: {verification['confirmed_round']}")
            print(f"  Sender: {verification['sender']}")
            print(f"  Fee: {verification['fee']} ALGO")
            
            # Verify note data
            note_data = verification.get("note_data")
            
            if note_data:
                print(f"\n✓ Note Data Extracted:")
                print(f"  Protocol: {note_data.get('protocol')}")
                print(f"  Version: {note_data.get('version')}")
                print(f"  Attestation ID: {note_data.get('attestation_id')}")
                print(f"  Merkle Root: {note_data.get('merkle_root')}")
                print(f"  Package Hash: {note_data.get('package_hash')}")
                
                # Verify required fields
                checks = {
                    "protocol_correct": note_data.get("protocol") == "zkpa",
                    "version_correct": note_data.get("version") == "1.1",
                    "merkle_root_present": note_data.get("merkle_root") == expected_data.get("merkle_root"),
                    "attestation_id_present": note_data.get("attestation_id") == expected_data.get("attestation_id")
                }
                
                all_checks_passed = all(checks.values())
                
                print(f"\n✓ Verification Checks:")
                for check_name, passed in checks.items():
                    status = "✅ PASS" if passed else "❌ FAIL"
                    print(f"  {check_name}: {status}")
                
                results = {
                    "verified": all_checks_passed,
                    "transaction_confirmed": verification['confirmed'],
                    "note_data": note_data,
                    "verification_checks": checks
                }
                
                if all_checks_passed:
                    print(f"\n{'='*70}")
                    print(f"✅ ALL VERIFICATION CHECKS PASSED")
                    print(f"{'='*70}")
                else:
                    print(f"\n{'='*70}")
                    print(f"⚠️  SOME VERIFICATION CHECKS FAILED")
                    print(f"{'='*70}")
                
            else:
                print(f"\n❌ No note data found in transaction")
                results = {
                    "verified": False,
                    "error": "No note data found"
                }
            
        except Exception as e:
            print(f"\n❌ VERIFICATION FAILED: {e}")
            results = {
                "verified": False,
                "error": str(e)
            }
        
        self.results["verification"] = results
        return results
    
    def run_complete_workflow(self) -> dict:
        """
        Execute complete end-to-end attestation workflow
        
        Returns:
            Complete workflow results
        """
        print("\n" + "="*70)
        print("END-TO-END ATTESTATION WORKFLOW")
        print("Real Algorand TESTNET Integration")
        print("="*70)
        print(f"Started: {datetime.utcnow().isoformat()}")
        
        try:
            # Step 1: Collect evidence
            evidence_data = self.step1_collect_evidence(min_items=5)
            
            # Step 2: Build Merkle tree
            merkle_data = self.step2_build_merkle_tree(evidence_data["evidence_hashes"])
            
            # Step 3: Assemble attestation
            attestation_data = self.step3_assemble_attestation(evidence_data, merkle_data)
            
            # Step 4: Sign attestation
            signature_data = self.step4_sign_attestation(attestation_data["package_hash"])
            
            # Step 5: Anchor to Algorand TESTNET
            anchoring_data = self.step5_anchor_to_algorand(attestation_data, merkle_data)
            
            if not anchoring_data.get("success"):
                print(f"\n❌ WORKFLOW FAILED AT ANCHORING STEP")
                return {
                    "success": False,
                    "error": anchoring_data.get("error"),
                    "completed_steps": ["evidence", "merkle_tree", "attestation", "signature"]
                }
            
            # Step 6: Verify transaction
            verification_data = self.step6_verify_transaction(
                transaction_id=anchoring_data["transaction_id"],
                expected_data={
                    "merkle_root": merkle_data["merkle_root"],
                    "attestation_id": attestation_data["attestation_id"]
                }
            )
            
            # Final summary
            print("\n" + "="*70)
            print("WORKFLOW COMPLETE - FINAL SUMMARY")
            print("="*70)
            print(f"\n✓ Evidence Items: {evidence_data['evidence_count']}")
            print(f"✓ Merkle Root: {merkle_data['merkle_root']}")
            print(f"✓ Attestation ID: {attestation_data['attestation_id']}")
            print(f"✓ Package Hash: {attestation_data['package_hash']}")
            print(f"✓ Transaction ID: {anchoring_data['transaction_id']}")
            print(f"✓ Confirmed Round: {anchoring_data['confirmed_round']}")
            print(f"✓ Explorer URL: {anchoring_data['explorer_url']}")
            print(f"✓ Verification: {'PASSED ✅' if verification_data.get('verified') else 'FAILED ❌'}")
            
            print(f"\nView transaction on Algorand Explorer:")
            print(f"{anchoring_data['explorer_url']}")
            
            return {
                "success": True,
                "completed_at": datetime.utcnow().isoformat(),
                "summary": {
                    "evidence_count": evidence_data["evidence_count"],
                    "merkle_root": merkle_data["merkle_root"],
                    "leaf_count": merkle_data["leaf_count"],
                    "attestation_id": attestation_data["attestation_id"],
                    "package_hash": attestation_data["package_hash"],
                    "transaction_id": anchoring_data["transaction_id"],
                    "confirmed_round": anchoring_data["confirmed_round"],
                    "explorer_url": anchoring_data["explorer_url"],
                    "verified": verification_data.get("verified", False)
                },
                "all_results": self.results
            }
            
        except Exception as e:
            print(f"\n❌ WORKFLOW FAILED: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "partial_results": self.results
            }


def main():
    """Main entry point"""
    print("\n" + "="*70)
    print("COMPLIANCE VERIFICATION AGENT")
    print("End-to-End Attestation with Real Algorand TESTNET")
    print("="*70)
    
    # Check for mnemonic in environment or create new account
    mnemonic = os.environ.get("ALGORAND_MNEMONIC")
    
    if not mnemonic:
        print("\n⚠️  No ALGORAND_MNEMONIC found in environment.")
        print("Generating new account for this run...")
        print("To reuse an account, set ALGORAND_MNEMONIC environment variable.")
    
    # Create workflow instance
    workflow = EndToEndAttestation(sender_mnemonic=mnemonic)
    
    # Check account status
    account_info = workflow.algorand.get_account_info()
    print(f"\n✓ Algorand Account:")
    print(f"  Address: {account_info['address']}")
    print(f"  Balance: {account_info['balance_algos']:.6f} ALGO")
    
    if account_info['balance_algos'] < 0.001:
        print(f"\n⚠️  ACCOUNT NEEDS FUNDING")
        print(workflow.algorand.fund_account_instructions())
        print("\nAfter funding, run this script again.")
        return
    
    # Run complete workflow
    results = workflow.run_complete_workflow()
    
    # Save results to file
    results_file = Path(__file__).parent / "attestation_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to: {results_file}")
    
    if results.get("success"):
        print("\n✅ END-TO-END ATTESTATION COMPLETED SUCCESSFULLY")
        return 0
    else:
        print("\n❌ END-TO-END ATTESTATION FAILED")
        return 1


if __name__ == "__main__":
    exit(main())

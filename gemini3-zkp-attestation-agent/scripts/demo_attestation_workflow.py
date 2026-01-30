"""
DEMONSTRATION: Complete End-to-End Attestation Workflow
Shows all steps of the attestation process with detailed output

Note: Steps 1-4 execute fully. Step 5 (blockchain anchoring) requires a funded account.
To complete with real blockchain: Fund the account and use run_with_funded_account.py
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from run_e2e_attestation import EndToEndAttestation
import json

def demonstrate_workflow():
    """Demonstrate the complete workflow with detailed output"""
    
    print("\n" + "="*70)
    print("COMPLIANCE VERIFICATION AGENT - WORKFLOW DEMONSTRATION")
    print("Real Algorand TESTNET Integration")
    print("="*70)
    
    # Initialize with the generated account
    mnemonic = os.environ.get("ALGORAND_MNEMONIC")
    
    workflow = EndToEndAttestation(sender_mnemonic=mnemonic)
    
    # Show account details
    account_info = workflow.algorand.get_account_info()
    print(f"\n✓ Algorand Account Created:")
    print(f"  Address: {account_info['address']}")
    print(f"  Current Balance: {account_info['balance_algos']:.6f} ALGO")
    print(f"  Network: TESTNET")
    
    # Execute steps 1-4 (non-blockchain steps)
    print("\n" + "="*70)
    print("EXECUTING NON-BLOCKCHAIN STEPS (1-4)")
    print("="*70)
    
    try:
        # Step 1: Evidence Collection
        evidence_data = workflow.step1_collect_evidence(min_items=5)
        
        # Step 2: Merkle Tree
        merkle_data = workflow.step2_build_merkle_tree(evidence_data["evidence_hashes"])
        
        # Step 3: Attestation Assembly
        attestation_data = workflow.step3_assemble_attestation(evidence_data, merkle_data)
        
        # Step 4: Signature
        signature_data = workflow.step4_sign_attestation(attestation_data["package_hash"])
        
        print("\n" + "="*70)
        print("✅ STEPS 1-4 COMPLETED SUCCESSFULLY")
        print("="*70)
        
        # Show what we have so far
        print("\n📋 ATTESTATION READY FOR BLOCKCHAIN ANCHORING:")
        print(f"\n  Evidence Items: {evidence_data['evidence_count']}")
        print(f"  Merkle Root: {merkle_data['merkle_root'][:64]}...")
        print(f"  Attestation ID: {attestation_data['attestation_id']}")
        print(f"  Package Hash: {attestation_data['package_hash'][:64]}...")
        print(f"  Signer: {signature_data['signer_address']}")
        
        # Show attestation package structure
        print("\n📦 ATTESTATION PACKAGE (ZKPA v1.1):")
        package = attestation_data["attestation_package"]
        print(f"  Protocol: {package['protocol']}")
        print(f"  Version: {package['version']}")
        print(f"  Attestation ID: {package['attestation_id']}")
        print(f"  Merkle Root: {package['evidence']['merkle_root']}")
        print(f"  Evidence Count: {package['evidence']['evidence_count']}")
        print(f"  Compliance Framework: {package['metadata']['compliance_framework']}")
        
        # Explain Step 5 requirement
        print("\n" + "="*70)
        print("⏸️  STEP 5: BLOCKCHAIN ANCHORING (REQUIRES FUNDING)")
        print("="*70)
        print("\nTo complete the blockchain anchoring:")
        print(f"\n1. Fund this address with TESTNET ALGO:")
        print(f"   {account_info['address']}")
        print(f"\n2. Visit: https://bank.testnet.algorand.network/")
        print(f"\n3. Run: python scripts/run_with_funded_account.py")
        
        print("\n📝 WHAT HAPPENS IN STEP 5 (Blockchain Anchoring):")
        print("\n  • Creates Algorand payment transaction (0 ALGO, self-transfer)")
        print(f"  • Attaches note with ZKPA v1.1 data:")
        print(f"    - protocol: zkpa")
        print(f"    - version: 1.1")
        print(f"    - attestation_id: {attestation_data['attestation_id']}")
        print(f"    - merkle_root: {merkle_data['merkle_root']}")
        print(f"    - package_hash: {attestation_data['package_hash']}")
        print(f"  • Signs transaction with Ed25519 (account private key)")
        print(f"  • Submits to Algorand TESTNET")
        print(f"  • Waits for confirmation (~4 seconds, 1 block)")
        print(f"  • Returns transaction_id and confirmed_round")
        print(f"  • Generates explorer URL for verification")
        
        print("\n📝 WHAT HAPPENS IN STEP 6 (Verification):")
        print("\n  • Queries Algorand TESTNET for transaction")
        print(f"  • Extracts and decodes note data")
        print(f"  • Verifies protocol = 'zkpa'")
        print(f"  • Verifies version = '1.1'")
        print(f"  • Verifies merkle_root matches")
        print(f"  • Verifies attestation_id matches")
        print(f"  • Returns verification status")
        
        # Save partial results
        results = {
            "demonstration": True,
            "steps_completed": ["evidence", "merkle_tree", "attestation", "signature"],
            "steps_pending": ["blockchain_anchoring", "verification"],
            "account": {
                "address": account_info['address'],
                "balance": account_info['balance_algos'],
                "funded": account_info['balance_algos'] > 0.001
            },
            "evidence": {
                "count": evidence_data['evidence_count'],
                "total_size": evidence_data['total_size_bytes']
            },
            "merkle_tree": {
                "root": merkle_data['merkle_root'],
                "leaf_count": merkle_data['leaf_count']
            },
            "attestation": {
                "id": attestation_data['attestation_id'],
                "package_hash": attestation_data['package_hash'],
                "package_size": attestation_data['package_size_bytes']
            },
            "signature": {
                "algorithm": signature_data['algorithm'],
                "signer": signature_data['signer_address']
            }
        }
        
        # Save to file
        results_file = Path(__file__).parent / "demo_results.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✓ Demo results saved to: {results_file}")
        
        print("\n" + "="*70)
        print("✅ DEMONSTRATION COMPLETE")
        print("="*70)
        print("\n📌 KEY OUTPUTS:")
        print(f"  • Evidence Count: {evidence_data['evidence_count']}")
        print(f"  • Merkle Root: {merkle_data['merkle_root']}")
        print(f"  • Leaf Count: {merkle_data['leaf_count']}")
        print(f"  • Attestation ID: {attestation_data['attestation_id']}")
        print(f"  • Package Hash: {attestation_data['package_hash']}")
        print(f"  • Signer Address: {signature_data['signer_address']}")
        
        print("\n🔗 TO COMPLETE WITH REAL BLOCKCHAIN:")
        print(f"  1. Fund: {account_info['address']}")
        print(f"  2. Run: python scripts/run_with_funded_account.py")
        print(f"  3. View transaction on: https://testnet.algoexplorer.io/")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    results = demonstrate_workflow()
    exit(0 if results else 1)

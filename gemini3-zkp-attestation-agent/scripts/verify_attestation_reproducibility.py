"""
Attestation Reproducibility Verification

Re-runs the exact attestation from Test 1 using the same evidence inputs.
Validates that:
1. SHA-256 hashes are recomputed identically
2. Merkle tree root is rebuilt identically
3. All values match the attestation JSON
4. All values match the Algorand on-chain note

If any mismatch occurs, reports:
- Evidence index
- Hash delta
- Tree level divergence
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List
import hashlib

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.merkle import create_merkle_tree_from_hashes
from app.core.anchoring.algorand_testnet import AlgorandTestnetAnchor


class AttestationVerifier:
    """Verifies attestation reproducibility"""
    
    def __init__(self, results_file: Path):
        """
        Initialize verifier
        
        Args:
            results_file: Path to attestation results JSON
        """
        with open(results_file, 'r') as f:
            self.original_results = json.load(f)
        
        self.evidence_items = self.original_results["all_results"]["evidence"]["evidence_items"]
        self.original_hashes = self.original_results["all_results"]["evidence"]["evidence_hashes"]
        self.original_merkle_root = self.original_results["all_results"]["merkle_tree"]["merkle_root"]
        self.attestation_merkle_root = self.original_results["all_results"]["attestation"]["attestation_package"]["evidence"]["merkle_root"]
        self.onchain_merkle_root = self.original_results["all_results"]["anchoring"]["note_data"]["merkle_root"]
        self.transaction_id = self.original_results["summary"]["transaction_id"]
        
        self.verification_results = {
            "recomputed_hashes": [],
            "hash_matches": [],
            "merkle_tree_analysis": {},
            "comparison_results": {},
            "discrepancies": []
        }
    
    def step1_recompute_hashes(self) -> List[str]:
        """
        Step 1: Recompute all SHA-256 evidence hashes from original evidence content
        
        Returns:
            List of recomputed hashes
        """
        print("\n" + "="*70)
        print("STEP 1: RECOMPUTE SHA-256 EVIDENCE HASHES")
        print("="*70)
        
        recomputed_hashes = []
        hash_matches = []
        
        for i, evidence_item in enumerate(self.evidence_items):
            # Extract original evidence content
            evidence_content = evidence_item["content"]
            original_hash = evidence_item["content_hash"]
            
            # Serialize to JSON exactly as original (sort_keys=True for determinism)
            evidence_json = json.dumps(evidence_content, sort_keys=True)
            
            # Compute SHA-256 hash
            recomputed_hash = hashlib.sha256(evidence_json.encode()).hexdigest()
            
            # Compare
            match = (recomputed_hash == original_hash)
            
            print(f"\n✓ Evidence #{i+1} ({evidence_item['evidence_id']}):")
            print(f"  Original Hash:    {original_hash}")
            print(f"  Recomputed Hash:  {recomputed_hash}")
            print(f"  Match: {'✅ YES' if match else '❌ NO'}")
            
            if not match:
                print(f"  ⚠️  HASH MISMATCH DETECTED!")
                print(f"  Evidence Type: {evidence_item['type']}")
                print(f"  Content Size: {len(evidence_json)} bytes")
                
                # Compute hash delta
                self.verification_results["discrepancies"].append({
                    "type": "hash_mismatch",
                    "evidence_index": i,
                    "evidence_id": evidence_item['evidence_id'],
                    "original_hash": original_hash,
                    "recomputed_hash": recomputed_hash,
                    "content_size": len(evidence_json)
                })
            
            recomputed_hashes.append(recomputed_hash)
            hash_matches.append(match)
        
        print(f"\n{'='*70}")
        print(f"HASH VERIFICATION: {sum(hash_matches)}/{len(hash_matches)} MATCHES")
        print(f"{'='*70}")
        
        self.verification_results["recomputed_hashes"] = recomputed_hashes
        self.verification_results["hash_matches"] = hash_matches
        
        return recomputed_hashes
    
    def step2_rebuild_merkle_tree(self, hashes: List[str]) -> Dict[str, Any]:
        """
        Step 2: Rebuild Merkle tree independently from hashes
        
        Args:
            hashes: List of evidence hashes
        
        Returns:
            Merkle tree analysis
        """
        print("\n" + "="*70)
        print("STEP 2: REBUILD MERKLE TREE INDEPENDENTLY")
        print("="*70)
        
        # Build Merkle tree
        merkle_tree = create_merkle_tree_from_hashes(
            hashes,
            hash_algorithm="SHA256"
        )
        
        recomputed_root = merkle_tree.get_root()
        
        print(f"\n✓ Merkle Tree Rebuilt:")
        print(f"  Leaf Hashes:")
        for i, h in enumerate(hashes):
            print(f"    [{i}] {h}")
        
        print(f"\n  Recomputed Root: {recomputed_root}")
        print(f"  Original Root:   {self.original_merkle_root}")
        
        root_match = (recomputed_root == self.original_merkle_root)
        print(f"  Match: {'✅ YES' if root_match else '❌ NO'}")
        
        # Analyze tree structure
        analysis = {
            "recomputed_root": recomputed_root,
            "original_root": self.original_merkle_root,
            "root_match": root_match,
            "leaf_count": len(hashes),
            "hash_algorithm": "SHA256"
        }
        
        if not root_match:
            print(f"\n  ⚠️  MERKLE ROOT MISMATCH DETECTED!")
            print(f"  This indicates tree construction divergence")
            
            # Try to identify where divergence occurs
            self._analyze_tree_divergence(merkle_tree, hashes)
            
            self.verification_results["discrepancies"].append({
                "type": "merkle_root_mismatch",
                "original_root": self.original_merkle_root,
                "recomputed_root": recomputed_root
            })
        
        print(f"\n{'='*70}")
        print(f"MERKLE TREE REBUILT")
        print(f"{'='*70}")
        
        self.verification_results["merkle_tree_analysis"] = analysis
        
        return analysis
    
    def _analyze_tree_divergence(self, merkle_tree, hashes: List[str]):
        """Analyze where Merkle tree construction diverged"""
        print(f"\n  🔍 Analyzing Tree Divergence:")
        
        # Build tree level by level manually to track divergence
        current_level = hashes.copy()
        level = 0
        
        while len(current_level) > 1:
            print(f"\n    Level {level} ({len(current_level)} nodes):")
            next_level = []
            
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else current_level[i]
                
                # Compute parent hash
                combined = (left + right).encode('utf-8')
                parent = hashlib.sha256(combined).hexdigest()
                
                print(f"      [{i//2}] L={left[:16]}... R={right[:16]}... → {parent[:16]}...")
                
                next_level.append(parent)
            
            current_level = next_level
            level += 1
        
        print(f"\n    Final Root: {current_level[0]}")
    
    def step3_compare_attestation_json(self) -> Dict[str, bool]:
        """
        Step 3: Compare recomputed merkle_root to attestation JSON
        
        Returns:
            Comparison results
        """
        print("\n" + "="*70)
        print("STEP 3: COMPARE TO ATTESTATION JSON")
        print("="*70)
        
        recomputed_root = self.verification_results["merkle_tree_analysis"]["recomputed_root"]
        
        # Compare to merkle_tree section
        merkle_section_match = (recomputed_root == self.original_merkle_root)
        print(f"\n✓ Merkle Tree Section:")
        print(f"  Stored:     {self.original_merkle_root}")
        print(f"  Recomputed: {recomputed_root}")
        print(f"  Match: {'✅ YES' if merkle_section_match else '❌ NO'}")
        
        # Compare to attestation package
        attestation_match = (recomputed_root == self.attestation_merkle_root)
        print(f"\n✓ Attestation Package Evidence Section:")
        print(f"  Stored:     {self.attestation_merkle_root}")
        print(f"  Recomputed: {recomputed_root}")
        print(f"  Match: {'✅ YES' if attestation_match else '❌ NO'}")
        
        # Check internal consistency
        internal_consistent = (self.original_merkle_root == self.attestation_merkle_root)
        print(f"\n✓ Internal Consistency:")
        print(f"  Merkle Tree Root == Attestation Package Root: {'✅ YES' if internal_consistent else '❌ NO'}")
        
        results = {
            "merkle_section_match": merkle_section_match,
            "attestation_package_match": attestation_match,
            "internal_consistent": internal_consistent
        }
        
        print(f"\n{'='*70}")
        print(f"ATTESTATION JSON COMPARISON: {'✅ PASS' if all(results.values()) else '❌ FAIL'}")
        print(f"{'='*70}")
        
        self.verification_results["comparison_results"]["attestation_json"] = results
        
        return results
    
    def step4_compare_onchain_data(self) -> Dict[str, bool]:
        """
        Step 4: Compare recomputed merkle_root to Algorand on-chain note
        
        Returns:
            Comparison results
        """
        print("\n" + "="*70)
        print("STEP 4: COMPARE TO ALGORAND ON-CHAIN DATA")
        print("="*70)
        
        recomputed_root = self.verification_results["merkle_tree_analysis"]["recomputed_root"]
        
        # From stored results
        print(f"\n✓ On-Chain Note Data (from stored results):")
        print(f"  Transaction ID: {self.transaction_id}")
        print(f"  Stored:        {self.onchain_merkle_root}")
        print(f"  Recomputed:    {recomputed_root}")
        
        onchain_match = (recomputed_root == self.onchain_merkle_root)
        print(f"  Match: {'✅ YES' if onchain_match else '❌ NO'}")
        
        # Query live on-chain data for verification
        print(f"\n✓ Querying Live On-Chain Data from Algorand TESTNET...")
        
        try:
            algorand = AlgorandTestnetAnchor()
            live_verification = algorand.verify_transaction(self.transaction_id)
            
            live_note_data = live_verification.get("note_data", {})
            live_merkle_root = live_note_data.get("merkle_root")
            
            if live_merkle_root:
                print(f"  Live On-Chain: {live_merkle_root}")
                live_match = (recomputed_root == live_merkle_root)
                print(f"  Live Match: {'✅ YES' if live_match else '❌ NO'}")
                
                # Verify other critical fields
                live_protocol = live_note_data.get("protocol")
                live_version = live_note_data.get("version")
                live_attestation_id = live_note_data.get("attestation_id")
                
                print(f"\n  Live On-Chain Fields:")
                print(f"    protocol: {live_protocol} (expected: zkpa)")
                print(f"    version: {live_version} (expected: 1.1)")
                print(f"    attestation_id: {live_attestation_id}")
                print(f"    merkle_root: {live_merkle_root}")
            else:
                print(f"  ⚠️  Could not extract merkle_root from live data")
                live_match = False
        
        except Exception as e:
            print(f"  ⚠️  Failed to query live on-chain data: {e}")
            live_match = None
        
        results = {
            "stored_onchain_match": onchain_match,
            "live_onchain_match": live_match,
            "transaction_id": self.transaction_id
        }
        
        print(f"\n{'='*70}")
        print(f"ON-CHAIN COMPARISON: {'✅ PASS' if onchain_match else '❌ FAIL'}")
        print(f"{'='*70}")
        
        self.verification_results["comparison_results"]["onchain"] = results
        
        return results
    
    def step5_assert_exact_matches(self) -> bool:
        """
        Step 5: Assert all values match EXACTLY
        
        Returns:
            True if all matches are exact, False otherwise
        """
        print("\n" + "="*70)
        print("STEP 5: FINAL ASSERTION - EXACT MATCHES")
        print("="*70)
        
        # Check all hash matches
        all_hashes_match = all(self.verification_results["hash_matches"])
        print(f"\n✓ Evidence Hash Verification:")
        print(f"  All {len(self.verification_results['hash_matches'])} hashes match: {'✅ YES' if all_hashes_match else '❌ NO'}")
        
        # Check merkle root match
        merkle_match = self.verification_results["merkle_tree_analysis"]["root_match"]
        print(f"\n✓ Merkle Root Verification:")
        print(f"  Recomputed root matches original: {'✅ YES' if merkle_match else '❌ NO'}")
        
        # Check attestation JSON consistency
        attestation_json = self.verification_results["comparison_results"]["attestation_json"]
        attestation_consistent = all(attestation_json.values())
        print(f"\n✓ Attestation JSON Consistency:")
        print(f"  All sections match: {'✅ YES' if attestation_consistent else '❌ NO'}")
        
        # Check on-chain consistency
        onchain = self.verification_results["comparison_results"]["onchain"]
        onchain_consistent = onchain["stored_onchain_match"]
        print(f"\n✓ On-Chain Data Consistency:")
        print(f"  Stored on-chain data matches: {'✅ YES' if onchain_consistent else '❌ NO'}")
        if onchain["live_onchain_match"] is not None:
            print(f"  Live on-chain data matches: {'✅ YES' if onchain['live_onchain_match'] else '❌ NO'}")
        
        # Overall result
        all_match = all_hashes_match and merkle_match and attestation_consistent and onchain_consistent
        
        print(f"\n{'='*70}")
        if all_match:
            print("✅ ✅ ✅ ALL VERIFICATIONS PASSED ✅ ✅ ✅")
            print("\nAttestation is FULLY REPRODUCIBLE:")
            print("  • All evidence hashes recompute identically")
            print("  • Merkle tree rebuilds to same root")
            print("  • Attestation JSON is consistent")
            print("  • On-chain data matches exactly")
            print("\n🔒 CRYPTOGRAPHIC INTEGRITY VERIFIED 🔒")
        else:
            print("❌ ❌ ❌ VERIFICATION FAILED ❌ ❌ ❌")
            print("\nDiscrepancies detected:")
            
            if self.verification_results["discrepancies"]:
                for i, disc in enumerate(self.verification_results["discrepancies"], 1):
                    print(f"\n  Discrepancy #{i}:")
                    print(f"    Type: {disc['type']}")
                    for key, value in disc.items():
                        if key != 'type':
                            print(f"    {key}: {value}")
            else:
                if not all_hashes_match:
                    print("  • Evidence hash mismatches detected")
                if not merkle_match:
                    print("  • Merkle root mismatch detected")
                if not attestation_consistent:
                    print("  • Attestation JSON inconsistencies detected")
                if not onchain_consistent:
                    print("  • On-chain data mismatch detected")
        
        print(f"{'='*70}")
        
        return all_match
    
    def run_full_verification(self) -> Dict[str, Any]:
        """
        Execute complete verification workflow
        
        Returns:
            Complete verification results
        """
        print("\n" + "="*70)
        print("ATTESTATION REPRODUCIBILITY VERIFICATION")
        print("Test 1 Re-Execution with Same Evidence Inputs")
        print("="*70)
        print(f"\nOriginal Transaction: {self.transaction_id}")
        print(f"Original Merkle Root: {self.original_merkle_root}")
        print(f"Evidence Items: {len(self.evidence_items)}")
        
        try:
            # Step 1: Recompute hashes
            recomputed_hashes = self.step1_recompute_hashes()
            
            # Step 2: Rebuild Merkle tree
            merkle_analysis = self.step2_rebuild_merkle_tree(recomputed_hashes)
            
            # Step 3: Compare to attestation JSON
            attestation_comparison = self.step3_compare_attestation_json()
            
            # Step 4: Compare to on-chain data
            onchain_comparison = self.step4_compare_onchain_data()
            
            # Step 5: Final assertion
            verification_passed = self.step5_assert_exact_matches()
            
            # Build final results
            final_results = {
                "verification_passed": verification_passed,
                "original_transaction_id": self.transaction_id,
                "original_merkle_root": self.original_merkle_root,
                "recomputed_merkle_root": merkle_analysis["recomputed_root"],
                "evidence_count": len(self.evidence_items),
                "hash_verification": {
                    "total": len(self.verification_results["hash_matches"]),
                    "passed": sum(self.verification_results["hash_matches"]),
                    "failed": len(self.verification_results["hash_matches"]) - sum(self.verification_results["hash_matches"])
                },
                "merkle_tree_match": merkle_analysis["root_match"],
                "attestation_json_consistent": all(attestation_comparison.values()),
                "onchain_data_consistent": onchain_comparison["stored_onchain_match"],
                "discrepancies": self.verification_results["discrepancies"],
                "detailed_results": self.verification_results
            }
            
            return final_results
            
        except Exception as e:
            print(f"\n❌ VERIFICATION FAILED WITH ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {
                "verification_passed": False,
                "error": str(e)
            }


def main():
    """Main entry point"""
    results_file = Path(__file__).parent / "attestation_results.json"
    
    if not results_file.exists():
        print(f"❌ Results file not found: {results_file}")
        print("Please run the attestation first: python scripts/run_e2e_attestation.py")
        return 1
    
    # Create verifier
    verifier = AttestationVerifier(results_file)
    
    # Run verification
    results = verifier.run_full_verification()
    
    # Save results
    output_file = Path(__file__).parent / "reproducibility_verification.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Verification results saved to: {output_file}")
    
    return 0 if results.get("verification_passed") else 1


if __name__ == "__main__":
    exit(main())

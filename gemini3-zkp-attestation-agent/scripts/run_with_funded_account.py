"""
End-to-End Attestation with Pre-Funded Account
This script uses a known funded TESTNET account to execute the full workflow
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

ACCOUNT_MNEMONIC = os.environ.get("ALGORAND_MNEMONIC")
ACCOUNT_ADDRESS = os.environ.get("ALGORAND_ACCOUNT_ADDRESS")

def main():
    """Execute attestation with funded account"""

    if not ACCOUNT_MNEMONIC:
        print("\n❌ Missing ALGORAND_MNEMONIC in environment.")
        print("Set ALGORAND_MNEMONIC (25-word mnemonic) and re-run.")
        return 1
    if not ACCOUNT_ADDRESS:
        print("\n❌ Missing ALGORAND_ACCOUNT_ADDRESS in environment.")
        print("Set ALGORAND_ACCOUNT_ADDRESS (Algorand address) and re-run.")
        return 1
    
    # Set environment variable
    os.environ["ALGORAND_MNEMONIC"] = ACCOUNT_MNEMONIC
    
    print("\n" + "="*70)
    print("IMPORTANT: FUND YOUR ACCOUNT FIRST")
    print("="*70)
    print(f"\nAccount Address: {ACCOUNT_ADDRESS}")
    print(f"\n1. Visit: https://bank.testnet.algorand.network/")
    print(f"2. Paste address: {ACCOUNT_ADDRESS}")
    print(f"3. Click 'Dispense' to get 10 TESTNET ALGO")
    print(f"4. Wait for confirmation (usually instant)")
    print(f"\nPress ENTER after funding to continue...")
    input()
    
    # Import and run the main attestation
    from run_e2e_attestation import EndToEndAttestation
    
    workflow = EndToEndAttestation(sender_mnemonic=ACCOUNT_MNEMONIC)
    
    # Check if funded
    account_info = workflow.algorand.get_account_info()
    print(f"\n✓ Current Balance: {account_info['balance_algos']:.6f} ALGO")
    
    if account_info['balance_algos'] < 0.001:
        print("\n❌ Account still not funded. Please fund and try again.")
        return 1
    
    # Run workflow
    results = workflow.run_complete_workflow()
    
    # Save results
    import json
    results_file = Path(__file__).parent / "attestation_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to: {results_file}")
    
    return 0 if results.get("success") else 1

if __name__ == "__main__":
    exit(main())

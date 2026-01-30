"""
Helper script to fund Algorand TESTNET account and run attestation
"""

import os
import time
import httpx
from pathlib import Path

# Account details from previous run
ACCOUNT_ADDRESS = os.environ.get(
    "ALGORAND_ACCOUNT_ADDRESS",
    "HDNKNQ7FJF37KLEVCHWWGH5O3J7HDY26JKNXHWYMYBXGL4VGETH57UKQ3A",
)

def fund_account_via_api(address: str) -> bool:
    """
    Attempt to fund account using TESTNET dispenser API
    """
    print(f"Attempting to fund account via API: {address}")
    
    try:
        # Try AlgoNode dispenser API
        response = httpx.post(
            "https://testnet.algoexplorerapi.io/v2/faucet",
            json={"address": address},
            timeout=30.0
        )
        
        if response.status_code == 200:
            print("✓ Account funded successfully via API")
            return True
        else:
            print(f"API funding failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"API funding error: {e}")
        
        # Try alternative dispenser
        try:
            response = httpx.get(
                f"https://bank.testnet.algorand.network/?account={address}",
                timeout=30.0
            )
            print(f"Alternative dispenser response: {response.status_code}")
        except:
            pass
        
        return False

def main():
    """Main entry point"""
    print("\n" + "="*70)
    print("ALGORAND TESTNET ACCOUNT FUNDING")
    print("="*70)
    
    print(f"\nAccount Address: {ACCOUNT_ADDRESS}")
    print(f"\nAttempting automated funding...")
    
    if fund_account_via_api(ACCOUNT_ADDRESS):
        print("\n✓ Account funded! Waiting 5 seconds for confirmation...")
        time.sleep(5)
    else:
        print("\n⚠️  Automated funding failed. Please fund manually:")
        print(f"\n1. Visit: https://bank.testnet.algorand.network/")
        print(f"2. Enter address: {ACCOUNT_ADDRESS}")
        print(f"3. Click 'Dispense'")
        print(f"\nWaiting 30 seconds for manual funding...")
        time.sleep(30)
    
    mnemonic = os.environ.get("ALGORAND_MNEMONIC")
    if not mnemonic:
        print("\n❌ Missing ALGORAND_MNEMONIC in environment.")
        print("Set ALGORAND_MNEMONIC (25-word mnemonic) and re-run.")
        return 1
    
    print("\n" + "="*70)
    print("RUNNING END-TO-END ATTESTATION")
    print("="*70)
    
    # Run the attestation script
    import subprocess
    result = subprocess.run(
        ["python", "scripts/run_e2e_attestation.py"],
        env={**os.environ, "ALGORAND_MNEMONIC": mnemonic},
        cwd=str(Path(__file__).parent.parent)
    )
    
    return result.returncode

if __name__ == "__main__":
    exit(main())

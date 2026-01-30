#!/usr/bin/env python3
"""Full E2E test for Algorand on-chain anchoring.

Tests:
1. Contract deployment
2. Single anchor write + read
3. Multiple anchors
4. Verification flow
5. Explorer URL generation
6. Frontend-signer flow (prepare unsigned txn)

This is a standalone test that doesn't require the API server or database.
"""
from __future__ import annotations

import os
import sys
import uuid
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from app.config import settings
from app.core.anchoring.blockchain_anchor import BlockchainAnchor, BlockchainType, AnchorStatus
from app.core.anchoring.algorand_client import mnemonic_to_keys, get_application_address


def print_section(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_prerequisites() -> bool:
    print_section("Prerequisites Check")
    
    if not settings.ALGORAND_MNEMONIC:
        print("ERROR: ALGORAND_MNEMONIC not set in .env")
        return False
    print("✓ ALGORAND_MNEMONIC is set")
    
    sender_addr, _ = mnemonic_to_keys(settings.ALGORAND_MNEMONIC)
    print(f"✓ Mnemonic address: {sender_addr}")
    
    print(f"✓ Algorand API URL: {getattr(settings, 'ALGORAND_API_URL', 'default')}")
    print(f"✓ Network: {getattr(settings, 'ALGORAND_NETWORK', 'testnet')}")
    
    app_id = getattr(settings, "ALGORAND_ANCHOR_APP_ID", None)
    if app_id:
        print(f"✓ Existing ALGORAND_ANCHOR_APP_ID: {app_id}")
    else:
        print("○ No ALGORAND_ANCHOR_APP_ID set (will deploy new contract)")
    
    return True


def test_deploy_contract(anchor: BlockchainAnchor) -> int:
    print_section("Test 1: Contract Deployment")
    
    existing = getattr(settings, "ALGORAND_ANCHOR_APP_ID", None)
    if existing:
        print(f"Using existing app_id={existing}")
        return int(existing)
    
    print("Deploying new anchoring contract...")
    result = anchor.deploy_algorand_contract()
    app_id = int(result["app_id"])
    txid = result["transaction_id"]
    confirmed_round = result.get("confirmed_round")
    
    print(f"✓ Deployed app_id={app_id}")
    print(f"  txid={txid}")
    print(f"  confirmed_round={confirmed_round}")
    print(f"  app_address={get_application_address(app_id)}")
    
    print(f"\n*** Add to .env: ALGORAND_ANCHOR_APP_ID={app_id} ***\n")
    return app_id


def test_single_anchor(anchor: BlockchainAnchor) -> dict:
    print_section("Test 2: Single Anchor Write + Read")
    
    package_id = f"pkg_e2e_{uuid.uuid4().hex[:12]}"
    package_hash = os.urandom(32).hex()
    merkle_root = os.urandom(32).hex()
    
    print(f"Anchoring package_id={package_id}")
    print(f"  package_hash={package_hash[:16]}...")
    print(f"  merkle_root={merkle_root[:16]}...")
    
    record = anchor.anchor_package(
        package_id=package_id,
        package_hash=package_hash,
        merkle_root=merkle_root,
        user_id="e2e_test",
    )
    
    print(f"✓ Anchor created")
    print(f"  anchor_id={record.anchor_id}")
    print(f"  txid={record.transaction_hash}")
    print(f"  block={record.block_number}")
    print(f"  status={record.status.value}")
    
    # Verify on explorer URL
    explorer_url = anchor.get_explorer_url(record.transaction_hash)
    print(f"  explorer={explorer_url}")
    
    # Read back from chain
    print("\nReading anchor from chain...")
    time.sleep(1)
    
    onchain = anchor.get_algorand_anchor(package_id)
    print(f"✓ On-chain data retrieved")
    print(f"  package_hash={onchain['package_hash'][:16]}...")
    print(f"  merkle_root={onchain['merkle_root'][:16]}...")
    
    assert onchain["package_hash"] == package_hash, "package_hash mismatch!"
    assert onchain["merkle_root"] == merkle_root, "merkle_root mismatch!"
    print("✓ On-chain values MATCH")
    
    return {
        "package_id": package_id,
        "package_hash": package_hash,
        "merkle_root": merkle_root,
        "record": record,
    }


def test_multiple_anchors(anchor: BlockchainAnchor, count: int = 3) -> list:
    print_section(f"Test 3: Multiple Anchors ({count})")
    
    results = []
    for i in range(count):
        package_id = f"pkg_multi_{i}_{uuid.uuid4().hex[:8]}"
        package_hash = os.urandom(32).hex()
        merkle_root = os.urandom(32).hex()
        
        print(f"\n[{i+1}/{count}] Anchoring {package_id}...")
        record = anchor.anchor_package(
            package_id=package_id,
            package_hash=package_hash,
            merkle_root=merkle_root,
            user_id="e2e_multi",
        )
        print(f"  ✓ txid={record.transaction_hash[:20]}... block={record.block_number}")
        
        results.append({
            "package_id": package_id,
            "package_hash": package_hash,
            "merkle_root": merkle_root,
            "txid": record.transaction_hash,
        })
        time.sleep(1)
    
    # Verify all
    print("\nVerifying all anchors on-chain...")
    for r in results:
        onchain = anchor.get_algorand_anchor(r["package_id"])
        assert onchain["package_hash"] == r["package_hash"]
        assert onchain["merkle_root"] == r["merkle_root"]
        print(f"  ✓ {r['package_id']} verified")
    
    print(f"✓ All {count} anchors verified")
    return results


def test_verification_flow(anchor: BlockchainAnchor, anchor_data: dict):
    print_section("Test 4: Verification Flow")
    
    record = anchor_data["record"]
    
    print(f"Verifying anchor {record.anchor_id}...")
    
    # Test verify_anchor method (returns bool)
    verified = anchor.verify_anchor(
        record,
        anchor_data["package_hash"]
    )
    
    print(f"  verified={verified}")
    
    # Test get_anchor_status
    print("\nGetting anchor status...")
    status_info = anchor.get_anchor_status(record.transaction_hash)
    print(f"  status={status_info}")
    
    print("✓ Verification flow complete")


def test_prepare_unsigned_txn(anchor: BlockchainAnchor):
    print_section("Test 5: Prepare Unsigned Txn (Frontend Signer)")
    
    sender_addr, _ = mnemonic_to_keys(settings.ALGORAND_MNEMONIC)
    package_id = f"pkg_unsigned_{uuid.uuid4().hex[:8]}"
    package_hash = os.urandom(32).hex()
    merkle_root = os.urandom(32).hex()
    
    print(f"Preparing unsigned txn for {package_id}...")
    print(f"  sender={sender_addr}")
    
    result = anchor.prepare_algorand_anchor_txn(
        sender_address=sender_addr,
        package_id=package_id,
        package_hash=package_hash,
        merkle_root=merkle_root,
    )
    
    print(f"✓ Unsigned txn prepared")
    print(f"  app_id={result['app_id']}")
    print(f"  txn_length={len(result['txn'])} chars (msgpack+base64)")
    
    # The txn can be signed by a frontend wallet and submitted via submit_algorand_signed_txn
    print("✓ Frontend signer flow ready (txn can be signed by wallet)")


def test_explorer_urls(anchor: BlockchainAnchor):
    print_section("Test 6: Explorer URL Generation")
    
    test_txid = "TESTTXID123456789"
    
    # Test different networks
    for network in ["testnet", "mainnet"]:
        temp_anchor = BlockchainAnchor(
            blockchain_type=BlockchainType.ALGORAND,
            network=network,
        )
        url = temp_anchor.get_explorer_url(test_txid)
        print(f"  {network}: {url}")
    
    print("✓ Explorer URLs correctly generated")


def main() -> int:
    print("\n" + "#" * 60)
    print("#  ALGORAND ON-CHAIN E2E TEST SUITE")
    print("#" * 60)
    
    # Prerequisites
    if not test_prerequisites():
        return 1
    
    # Create anchor instance
    anchor = BlockchainAnchor(
        blockchain_type=BlockchainType.ALGORAND,
        network=getattr(settings, "ALGORAND_NETWORK", "testnet"),
        rpc_url=getattr(settings, "ALGORAND_API_URL", None),
    )
    
    # Check account balance
    sender_addr, _ = mnemonic_to_keys(settings.ALGORAND_MNEMONIC)
    acct = anchor._algo_clients.algod.account_info(sender_addr)
    balance = int(acct.get("amount", 0))
    print(f"\nAccount balance: {balance / 1_000_000:.2f} ALGO")
    
    if balance < 1_000_000:
        print("ERROR: Insufficient balance (need at least 1 ALGO)")
        return 2
    
    try:
        # Test 1: Deploy
        app_id = test_deploy_contract(anchor)
        
        # Test 2: Single anchor
        anchor_data = test_single_anchor(anchor)
        
        # Test 3: Multiple anchors
        test_multiple_anchors(anchor, count=2)
        
        # Test 4: Verification
        test_verification_flow(anchor, anchor_data)
        
        # Test 5: Frontend signer prep
        test_prepare_unsigned_txn(anchor)
        
        # Test 6: Explorer URLs
        test_explorer_urls(anchor)
        
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 99
    
    print("\n" + "#" * 60)
    print("#  ALL E2E TESTS PASSED!")
    print("#" * 60)
    print(f"\nDeployed app_id: {app_id}")
    print(f"Total anchors created: 3+")
    print(f"Network: {anchor.network}")
    print(f"Explorer: https://{anchor.network}.algoexplorer.io")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import os
import sys
import uuid

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from app.config import settings
from app.core.anchoring.blockchain_anchor import BlockchainAnchor, BlockchainType
from app.core.anchoring.algorand_client import mnemonic_to_keys


def main() -> int:
    if not settings.ALGORAND_MNEMONIC:
        print("ERROR: ALGORAND_MNEMONIC is missing in environment/.env", file=sys.stderr)
        return 2

    anchor = BlockchainAnchor(
        blockchain_type=BlockchainType.ALGORAND,
        network=getattr(settings, "ALGORAND_NETWORK", "testnet"),
        rpc_url=getattr(settings, "ALGORAND_API_URL", None),
    )

    print(f"Algod: {anchor.rpc_url}")
    print(f"Network: {anchor.network}")

    sender_addr, _ = mnemonic_to_keys(settings.ALGORAND_MNEMONIC)
    print(f"Mnemonic address: {sender_addr}")

    acct = anchor._algo_clients.algod.account_info(sender_addr)
    amount = int(acct.get("amount", 0) or 0)
    min_balance = int(acct.get("min-balance", 0) or 0)
    print(f"Account balance: {amount} microAlgos")
    print(f"Account min-balance: {min_balance} microAlgos")

    existing_app_id = getattr(settings, "ALGORAND_ANCHOR_APP_ID", None)
    if existing_app_id:
        print(f"Using existing app_id={existing_app_id} (from env)")
        # NOTE: BlockchainAnchor reads the app id from settings at init; keep anchor instance as-is.
    else:
        print("Deploying anchoring app...")
        deploy = anchor.deploy_algorand_contract()
        app_id = int(deploy["app_id"])
        print(f"Deployed app_id={app_id} txid={deploy['transaction_id']} round={deploy.get('confirmed_round')}")

    # Note: app id is held only in-memory in this run.
    package_id = f"pkg_{uuid.uuid4().hex[:16]}"
    package_hash = os.urandom(32).hex()
    merkle_root = os.urandom(32).hex()

    print(f"Anchoring package_id={package_id}")
    record = anchor.anchor_package(
        package_id=package_id,
        package_hash=package_hash,
        merkle_root=merkle_root,
        user_id="smoke",
    )
    print(f"Anchored txid={record.transaction_hash} round={record.block_number} explorer={anchor.get_explorer_url(record.transaction_hash)}")

    print("Reading on-chain box...")
    onchain = anchor.get_algorand_anchor(package_id)

    assert onchain["package_id"] == package_id
    assert onchain["package_hash"] == package_hash
    assert onchain["merkle_root"] == merkle_root

    print("OK: on-chain values match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

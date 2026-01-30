#!/usr/bin/env python3
"""E2E test for Algorand anchoring API endpoints.

This script tests the full on-chain flow via the FastAPI endpoints:
1. Deploy contract (or use existing)
2. Anchor a package (server signer)
3. Read anchor data back from chain

Run with API server already running on localhost:8000
"""
from __future__ import annotations

import os
import sys
import uuid
import requests
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")


def get_test_token() -> str:
    """Get or generate a test JWT token.
    
    In a real setup you'd authenticate via /auth/login or similar.
    For local testing we generate a minimal token if JWT_SECRET is available.
    """
    from app.config import settings
    from jose import jwt
    from datetime import datetime, timedelta

    payload = {
        "sub": "test_user_e2e",
        "tenant_id": "test_tenant",
        "permissions": ["zkpa:generate", "zkpa:verify", "zkpa:admin"],
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token


def test_health():
    print("Testing /health ...")
    r = requests.get(f"{API_BASE}/health", timeout=10)
    assert r.status_code == 200, f"Health check failed: {r.text}"
    print(f"  OK: {r.json()}")


def test_algorand_deploy(headers: dict) -> dict:
    print("Testing POST /api/v1/anchoring/algorand/contract/deploy ...")
    r = requests.post(f"{API_BASE}/api/v1/anchoring/algorand/contract/deploy", headers=headers, timeout=60)
    if r.status_code == 200:
        data = r.json()
        print(f"  Deployed app_id={data.get('app_id')} txid={data.get('transaction_id')}")
        return data
    else:
        print(f"  Deploy returned {r.status_code}: {r.text}")
        return {}


def test_algorand_anchor_server(headers: dict) -> dict:
    print("Testing POST /api/v1/anchoring/algorand/anchor/server ...")
    package_id = f"pkg_e2e_{uuid.uuid4().hex[:12]}"
    package_hash = os.urandom(32).hex()
    merkle_root = os.urandom(32).hex()

    payload = {
        "package_id": package_id,
        "package_hash": package_hash,
        "merkle_root": merkle_root,
    }
    r = requests.post(f"{API_BASE}/api/v1/anchoring/algorand/anchor/server", headers=headers, json=payload, timeout=60)
    if r.status_code == 200:
        data = r.json()
        print(f"  Anchored package_id={package_id} txid={data.get('transaction_hash')}")
        data["_package_id"] = package_id
        data["_package_hash"] = package_hash
        data["_merkle_root"] = merkle_root
        return data
    else:
        print(f"  Anchor failed {r.status_code}: {r.text}")
        return {}


def test_algorand_get_anchor(headers: dict, package_id: str, expected_hash: str, expected_merkle: str) -> dict:
    print(f"Testing GET /api/v1/anchoring/algorand/anchor/{package_id} ...")
    r = requests.get(f"{API_BASE}/api/v1/anchoring/algorand/anchor/{package_id}", headers=headers, timeout=30)
    if r.status_code == 200:
        data = r.json()
        print(f"  On-chain data: package_hash={data.get('package_hash')[:16]}... merkle_root={data.get('merkle_root')[:16]}...")
        assert data.get("package_hash") == expected_hash, "package_hash mismatch"
        assert data.get("merkle_root") == expected_merkle, "merkle_root mismatch"
        print("  OK: on-chain values match")
        return data
    else:
        print(f"  Get anchor failed {r.status_code}: {r.text}")
        return {}


def main() -> int:
    print("=" * 60)
    print("Algorand On-Chain E2E API Test")
    print("=" * 60)
    print(f"API_BASE: {API_BASE}")

    # Health check (no auth required)
    try:
        test_health()
    except Exception as e:
        print(f"ERROR: API server not reachable at {API_BASE}: {e}")
        print("Make sure to start the server with: python3 -m uvicorn app.main:app --port 8000")
        return 1

    # Get auth token
    print("\nGenerating test JWT token...")
    try:
        token = get_test_token()
        headers = {"Authorization": f"Bearer {token}"}
        print("  Token generated")
    except Exception as e:
        print(f"ERROR generating token: {e}")
        return 2

    # Optional: deploy contract (skip if ALGORAND_ANCHOR_APP_ID is already set)
    from app.config import settings
    if not getattr(settings, "ALGORAND_ANCHOR_APP_ID", None):
        print("\nNo ALGORAND_ANCHOR_APP_ID set, deploying new contract...")
        deploy_result = test_algorand_deploy(headers)
        if not deploy_result.get("app_id"):
            print("ERROR: Deploy failed")
            return 3
        print(f"\n*** Set ALGORAND_ANCHOR_APP_ID={deploy_result['app_id']} in .env to reuse this app ***\n")
        time.sleep(2)
    else:
        print(f"\nUsing existing ALGORAND_ANCHOR_APP_ID={settings.ALGORAND_ANCHOR_APP_ID}")

    # Anchor a package
    anchor_result = test_algorand_anchor_server(headers)
    if not anchor_result.get("transaction_hash"):
        print("ERROR: Anchor failed")
        return 4

    time.sleep(2)

    # Read anchor back
    read_result = test_algorand_get_anchor(
        headers,
        anchor_result["_package_id"],
        anchor_result["_package_hash"],
        anchor_result["_merkle_root"],
    )
    if not read_result:
        print("ERROR: Read anchor failed")
        return 5

    print("\n" + "=" * 60)
    print("E2E TEST PASSED: Deploy -> Anchor -> Read all successful")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

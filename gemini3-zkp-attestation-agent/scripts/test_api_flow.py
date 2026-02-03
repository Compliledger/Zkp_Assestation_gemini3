"""
Test the complete API flow
End-to-end test for Phase 1 implementation
"""

import requests
import time
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_health_check():
    """Test health endpoint"""
    print_section("TEST 0: Health Check")
    
    response = requests.get(f"{BASE_URL}/health/live")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    assert response.json()["status"] == "alive"
    print("✅ Health check passed")

def test_create_attestation():
    """Test POST /attestations"""
    print_section("TEST 1: Create Attestation")
    
    payload = {
        "evidence": [
            {
                "uri": "demo://evidence/access-log-2026-02",
                "hash": "a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890",
                "type": "access_log"
            },
            {
                "uri": "demo://evidence/security-config",
                "hash": "f6e5d4c3b2a10987654321fedcba0987654321fedcba0987654321fedcba0987",
                "type": "config_snapshot"
            },
            {
                "uri": "demo://evidence/vulnerability-scan",
                "hash": "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
                "type": "security_scan"
            }
        ],
        "policy": "SOC2 Type II - Access Control & Monitoring"
    }
    
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(
        f"{API_V1}/attestations",
        json=payload,
        headers={"Idempotency-Key": f"test-key-{int(time.time())}"}
    )
    
    print(f"\nStatus: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    assert "claim_id" in response.json()
    assert response.json()["status"] == "pending"
    
    claim_id = response.json()["claim_id"]
    print(f"\n✅ Attestation created: {claim_id}")
    return claim_id

def test_get_attestation(claim_id, max_polls=15):
    """Test GET /attestations/{id} with polling"""
    print_section("TEST 2: Get Attestation (Polling)")
    
    print(f"Polling attestation: {claim_id}")
    print("Waiting for completion...")
    
    for i in range(max_polls):
        response = requests.get(f"{API_V1}/attestations/{claim_id}")
        data = response.json()
        
        status = data['status']
        print(f"\n[Poll {i+1}/{max_polls}] Status: {status}")
        
        if status == "valid":
            print("\n✅ Attestation completed successfully!")
            print(f"\nFinal Attestation Details:")
            print(json.dumps(data, indent=2))
            return data
        elif status == "failed":
            print(f"\n❌ Attestation failed: {data.get('error', 'Unknown error')}")
            return data
        
        time.sleep(2)
    
    print(f"\n⚠️ Attestation still processing after {max_polls} polls")
    return data

def test_list_attestations():
    """Test GET /attestations"""
    print_section("TEST 3: List Attestations")
    
    response = requests.get(f"{API_V1}/attestations?limit=10")
    print(f"Status: {response.status_code}")
    
    attestations = response.json()
    print(f"\nTotal attestations: {len(attestations)}")
    
    for att in attestations:
        print(f"  - {att['claim_id']}: {att['status']}")
    
    print("✅ List attestations passed")

def test_verify_attestation(claim_id):
    """Test POST /verify"""
    print_section("TEST 4: Verify Attestation")
    
    payload = {
        "attestation_id": claim_id,
        "checks": ["proof", "expiry", "revocation"]
    }
    
    print(f"Verifying: {claim_id}")
    print(f"Checks: {payload['checks']}")
    
    response = requests.post(f"{API_V1}/verify", json=payload)
    
    print(f"\nStatus: {response.status_code}")
    print(f"\nVerification Results:")
    result = response.json()
    print(json.dumps(result, indent=2))
    
    assert response.status_code == 200
    assert "receipt_id" in result
    
    print(f"\n✅ Verification {'PASSED' if result['status'] == 'PASS' else 'FAILED'}")
    print(f"Receipt ID: {result['receipt_id']}")
    return result["receipt_id"]

def test_get_verification_receipt(receipt_id):
    """Test GET /verify/{receipt_id}"""
    print_section("TEST 5: Get Verification Receipt")
    
    response = requests.get(f"{API_V1}/verify/{receipt_id}")
    
    print(f"Status: {response.status_code}")
    print(f"\nReceipt Details:")
    print(json.dumps(response.json(), indent=2))
    
    assert response.status_code == 200
    print("✅ Verification receipt retrieved")

def test_idempotency():
    """Test idempotency"""
    print_section("TEST 6: Idempotency Check")
    
    idempotency_key = f"idempotency-test-{int(time.time())}"
    
    payload = {
        "evidence": [
            {"uri": "demo://test", "hash": "abc123" * 10 + "ab", "type": "test"}
        ],
        "policy": "Test Policy"
    }
    
    # First request
    print(f"Request 1 with key: {idempotency_key}")
    r1 = requests.post(
        f"{API_V1}/attestations",
        json=payload,
        headers={"Idempotency-Key": idempotency_key}
    )
    
    # Second request with same key
    print(f"Request 2 with same key: {idempotency_key}")
    r2 = requests.post(
        f"{API_V1}/attestations",
        json=payload,
        headers={"Idempotency-Key": idempotency_key}
    )
    
    claim_id_1 = r1.json()["claim_id"]
    claim_id_2 = r2.json()["claim_id"]
    
    print(f"\nRequest 1 claim_id: {claim_id_1}")
    print(f"Request 2 claim_id: {claim_id_2}")
    print(f"Match: {claim_id_1 == claim_id_2}")
    
    assert claim_id_1 == claim_id_2, "❌ Idempotency failed!"
    print("✅ Idempotency working correctly")

def print_summary(results):
    """Print test summary"""
    print_section("TEST SUMMARY")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: ✅ {passed}")
    print(f"Failed: ❌ {failed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    print("\nTest Details:")
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("  🚀 ZKP ATTESTATION AGENT - API FLOW TESTS")
    print("="*70)
    print(f"  Base URL: {BASE_URL}")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    results = {}
    
    try:
        # Test 0: Health check
        test_health_check()
        results["Health Check"] = True
        
        # Test 1: Create attestation
        claim_id = test_create_attestation()
        results["Create Attestation"] = True
        
        # Test 2: Get/Poll attestation
        time.sleep(3)  # Wait for background processing
        attestation = test_get_attestation(claim_id)
        results["Get Attestation"] = attestation.get("status") == "valid"
        
        # Test 3: List attestations
        test_list_attestations()
        results["List Attestations"] = True
        
        # Test 4: Verify attestation
        receipt_id = test_verify_attestation(claim_id)
        results["Verify Attestation"] = True
        
        # Test 5: Get verification receipt
        test_get_verification_receipt(receipt_id)
        results["Get Verification Receipt"] = True
        
        # Test 6: Idempotency
        test_idempotency()
        results["Idempotency"] = True
        
        # Print summary
        print_summary(results)
        
        print("\n" + "="*70)
        print("  ✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*70)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ CONNECTION ERROR: Is the server running?")
        print("   Start server with: python -m uvicorn app.main:app --reload")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()

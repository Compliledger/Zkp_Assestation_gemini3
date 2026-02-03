"""
Quick Phase 3 Test - Demo Features
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_demo_policies():
    """Test getting demo policies"""
    print("Testing GET /demo/policies...")
    response = requests.get(f"{BASE_URL}/demo/policies")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Policies endpoint works: {data['count']} policies available")
        for policy in data['policies']:
            print(f"   - {policy['name']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        return False


def test_demo_scenarios():
    """Test getting demo scenarios"""
    print("\nTesting GET /demo/scenarios...")
    response = requests.get(f"{BASE_URL}/demo/scenarios")
    
    if response.status_code == 200:
        scenarios = response.json()
        print(f"✅ Scenarios endpoint works: {len(scenarios)} scenarios")
        for scenario in scenarios:
            print(f"   - {scenario['name']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        return False


def test_quick_attestation():
    """Test quick demo attestation"""
    print("\nTesting POST /demo/quick...")
    
    payload = {
        "policy": "SOC2_TYPE_II",
        "evidence_count": 3
    }
    
    response = requests.post(f"{BASE_URL}/demo/quick", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Quick attestation works!")
        print(f"   Claim ID: {data['claim_id']}")
        print(f"   Status: {data['status']}")
        print(f"   Policy: {data['policy_used']}")
        print(f"   Evidence: {data['evidence_count']} items")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return False


def test_demo_stats():
    """Test demo stats"""
    print("\nTesting GET /demo/stats...")
    response = requests.get(f"{BASE_URL}/demo/stats")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Stats endpoint works!")
        print(f"   Total attestations: {data['total_attestations']}")
        print(f"   Storage type: {data['storage_type']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("Phase 3 Demo Features Test")
    print("="*60)
    
    try:
        results = []
        results.append(test_demo_policies())
        results.append(test_demo_scenarios())
        results.append(test_quick_attestation())
        results.append(test_demo_stats())
        
        print("\n" + "="*60)
        passed = sum(results)
        total = len(results)
        print(f"Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("✅ ALL PHASE 3 FEATURES WORKING!")
        else:
            print(f"⚠️ {total - passed} test(s) failed")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Server not running!")
        print("Start with: python -m uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

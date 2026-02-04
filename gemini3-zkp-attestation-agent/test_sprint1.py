"""
Test Sprint 1: Sample Controls & Enhanced Responses
Tests the new sample controls and enhanced response features
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"


def test_sample_controls():
    """Test getting sample controls"""
    print("\n" + "="*60)
    print("TEST 1: Get Sample Controls")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/samples/controls")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Found {data['count']} sample controls")
        print(f"   Frameworks: {', '.join(data['frameworks'])}")
        
        # Show first control
        if data['controls']:
            control = data['controls'][0]
            print(f"\n   Example Control:")
            print(f"   - ID: {control['control_id']}")
            print(f"   - Framework: {control['framework']}")
            print(f"   - Title: {control['title']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return False


def test_frameworks():
    """Test getting frameworks"""
    print("\n" + "="*60)
    print("TEST 2: Get Frameworks")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/samples/frameworks")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Found {data['count']} frameworks")
        
        for name, info in data['frameworks'].items():
            print(f"\n   {name}:")
            print(f"   - Controls: {info['control_count']}")
            print(f"   - Description: {info['description'][:60]}...")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        return False


def test_quick_attest():
    """Test quick attestation from sample control"""
    print("\n" + "="*60)
    print("TEST 3: Quick Attestation from Sample Control")
    print("="*60)
    
    # Use AC-2 control
    control_id = "AC-2"
    print(f"\nCreating attestation from control: {control_id}")
    
    response = requests.post(f"{BASE_URL}/samples/quick-attest/{control_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Created attestation")
        print(f"   Claim ID: {data['claim_id']}")
        print(f"   Status: {data['status']}")
        print(f"   Control: {data['control']['control_id']} - {data['control']['title']}")
        print(f"   Evidence: {data['evidence_count']} items")
        
        claim_id = data['claim_id']
        
        # Wait for processing
        print("\n   Waiting for processing...")
        time.sleep(2)
        
        return claim_id
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return None


def test_enhanced_response(claim_id):
    """Test enhanced attestation response"""
    print("\n" + "="*60)
    print("TEST 4: Enhanced Attestation Response")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/attestations/{claim_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Got enhanced response")
        
        # Check for enhanced fields
        if "summary" in data:
            print(f"\n   Summary:")
            print(f"   - Framework: {data['summary']['framework']}")
            print(f"   - Control: {data['summary']['control_id']}")
            print(f"   - Claim Type: {data['summary']['claim_type']}")
            print(f"   - Valid: {data['summary']['validity_window']['is_valid']}")
        
        if "cryptographic_proof" in data:
            print(f"\n   Cryptographic Proof:")
            print(f"   - Proof Hash: {data['cryptographic_proof']['proof_hash'][:32]}...")
            print(f"   - Merkle Root: {data['cryptographic_proof']['merkle_root'][:32]}...")
            print(f"   - Algorithm: {data['cryptographic_proof']['algorithm']}")
        
        if "verification_status" in data:
            print(f"\n   Verification Status:")
            print(f"   - Proof Valid: {data['verification_status']['proof_valid']}")
            print(f"   - Not Expired: {data['verification_status']['not_expired']}")
            print(f"   - Not Revoked: {data['verification_status']['not_revoked']}")
            print(f"   - Overall: {data['verification_status']['overall']}")
        
        if "privacy" in data:
            print(f"\n   Privacy:")
            print(f"   - Evidence Exposed: {data['privacy']['evidence_exposed']}")
            print(f"   - Proof Type: {data['privacy']['proof_type']}")
            print(f"   - Message: {data['privacy']['message']}")
        
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        return False


def test_download(claim_id):
    """Test download endpoint"""
    print("\n" + "="*60)
    print("TEST 5: Download Attestation")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/attestations/{claim_id}/download")
    
    if response.status_code == 200:
        print(f"✅ Success! Downloaded attestation")
        
        # Check headers
        if 'Content-Disposition' in response.headers:
            print(f"   Content-Disposition: {response.headers['Content-Disposition']}")
        
        # Check content
        data = response.json()
        print(f"   Size: {len(json.dumps(data))} bytes")
        
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        return False


def test_enhanced_verification(claim_id):
    """Test enhanced verification response"""
    print("\n" + "="*60)
    print("TEST 6: Enhanced Verification Response")
    print("="*60)
    
    payload = {
        "attestation_id": claim_id,
        "checks": ["proof", "expiry", "revocation"]
    }
    
    response = requests.post(f"{BASE_URL}/verify", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Verification complete")
        print(f"   Receipt ID: {data['receipt_id']}")
        print(f"   Status: {data['status']}")
        
        # Check for enhanced fields
        if "checks_detailed" in data:
            print(f"\n   Detailed Checks:")
            for check in data['checks_detailed']:
                print(f"   {check['icon']} {check['name']}: {check['status']}")
                print(f"      {check['details']}")
        
        if "privacy_preserved" in data:
            print(f"\n   Privacy Preserved:")
            print(f"   - Evidence Disclosed: {data['privacy_preserved']['evidence_disclosed']}")
            print(f"   - Proof Method: {data['privacy_preserved']['proof_method']}")
            print(f"   - Compliance Proven: {data['privacy_preserved']['compliance_proven']}")
        
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return False


def test_sample_stats():
    """Test sample stats endpoint"""
    print("\n" + "="*60)
    print("TEST 7: Sample Statistics")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/samples/stats")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Got sample statistics")
        print(f"   Total Controls: {data['total_controls']}")
        print(f"   Total Frameworks: {data['total_frameworks']}")
        
        print(f"\n   By Framework:")
        for framework, count in data['by_framework'].items():
            print(f"   - {framework}: {count} controls")
        
        print(f"\n   By Claim Type:")
        for claim_type, count in data['by_claim_type'].items():
            print(f"   - {claim_type}: {count}")
        
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("SPRINT 1 FEATURE TESTS")
    print("Sample Controls & Enhanced Responses")
    print("="*60)
    
    try:
        results = []
        
        # Test 1: Sample controls
        results.append(test_sample_controls())
        
        # Test 2: Frameworks
        results.append(test_frameworks())
        
        # Test 3: Quick attest
        claim_id = test_quick_attest()
        results.append(claim_id is not None)
        
        if claim_id:
            # Test 4: Enhanced response
            results.append(test_enhanced_response(claim_id))
            
            # Test 5: Download
            results.append(test_download(claim_id))
            
            # Test 6: Enhanced verification
            results.append(test_enhanced_verification(claim_id))
        
        # Test 7: Sample stats
        results.append(test_sample_stats())
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        passed = sum(results)
        total = len(results)
        print(f"Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("✅ ALL SPRINT 1 FEATURES WORKING!")
        else:
            print(f"⚠️ {total - passed} test(s) failed")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ CONNECTION ERROR: Server not running!")
        print("Start with: python -m uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

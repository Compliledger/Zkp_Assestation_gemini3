"""
Test Sprint 2: Judge Mode
Tests judge mode features including guided flow and fast responses
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"


def test_judge_mode_status():
    """Test getting judge mode status"""
    print("\n" + "="*60)
    print("TEST 1: Judge Mode Status")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/judge/status")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Judge mode status retrieved")
        print(f"   Enabled: {data['enabled']}")
        print(f"   Fast Responses: {data['fast_responses']}")
        print(f"   Mock Anchor: {data['mock_anchor']}")
        print(f"   Demo Mode: {data['demo_mode']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        return False


def test_enable_judge_mode():
    """Test enabling judge mode"""
    print("\n" + "="*60)
    print("TEST 2: Enable Judge Mode")
    print("="*60)
    
    response = requests.post(f"{BASE_URL}/judge/enable")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Judge mode enabled")
        print(f"   Message: {data['message']}")
        print(f"\n   Optimizations:")
        for opt in data['optimizations']:
            print(f"   {opt}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        return False


def test_guided_flow():
    """Test guided demo flow"""
    print("\n" + "="*60)
    print("TEST 3: Guided Demo Flow")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/judge/guided-flow")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Got guided flow")
        print(f"   Title: {data['title']}")
        print(f"   Steps: {data['total_steps']}")
        print(f"   Est. Time: {data['estimated_time']}")
        print(f"   Judge Mode Active: {data['judge_mode_active']}")
        
        print(f"\n   Flow Steps:")
        for step in data['steps']:
            print(f"   {step['step']}. {step['title']}")
            print(f"      → {step['endpoint']}")
            if step.get('gemini_usage'):
                print(f"      💡 {step['gemini_usage'][:60]}...")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        return False


def test_fast_attestation():
    """Test fast attestation in judge mode"""
    print("\n" + "="*60)
    print("TEST 4: Fast Attestation (Judge Mode)")
    print("="*60)
    
    # Create attestation and measure time
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/samples/quick-attest/CC6.1")
    
    if response.status_code == 200:
        data = response.json()
        claim_id = data['claim_id']
        print(f"✅ Success! Created attestation: {claim_id}")
        
        # Wait for completion and measure total time
        max_wait = 5
        for i in range(max_wait):
            time.sleep(0.5)
            status_response = requests.get(f"{BASE_URL}/attestations/{claim_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data.get('status') == 'valid':
                    elapsed = time.time() - start_time
                    print(f"\n   ⚡ Completed in {elapsed:.2f} seconds")
                    
                    if elapsed < 2.0:
                        print(f"   ✅ FAST MODE SUCCESS (<2s)")
                    else:
                        print(f"   ⚠️ Slower than expected (target: <2s)")
                    
                    # Check for mock anchor
                    if status_data.get('anchor', {}).get('mock'):
                        print(f"   ✅ Mock anchor used: {status_data['anchor']['chain']}")
                    
                    return claim_id
        
        print(f"   ⚠️ Still processing after {max_wait}s")
        return claim_id
    else:
        print(f"❌ Failed: {response.status_code}")
        return None


def test_judge_stats():
    """Test judge mode statistics"""
    print("\n" + "="*60)
    print("TEST 5: Judge Mode Statistics")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/judge/stats")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Got judge mode stats")
        print(f"   Judge Mode: {data['judge_mode_enabled']}")
        print(f"   Total Attestations: {data['total_attestations']}")
        print(f"   Total Verifications: {data['total_verifications']}")
        
        print(f"\n   Performance:")
        print(f"   - Fast Responses: {data['performance']['fast_responses']}")
        print(f"   - Mock Anchor: {data['performance']['mock_anchor']}")
        print(f"   - Avg Response Time: {data['performance']['avg_response_time']}")
        
        if data['recent_attestations']:
            print(f"\n   Recent Attestations:")
            for att in data['recent_attestations'][:3]:
                print(f"   - {att['claim_id']}: {att['status']} ({att.get('framework')} {att.get('control_id')})")
        
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        return False


def test_reset_demo():
    """Test demo data reset"""
    print("\n" + "="*60)
    print("TEST 6: Reset Demo Data")
    print("="*60)
    
    response = requests.post(f"{BASE_URL}/judge/reset")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Demo data reset")
        print(f"   Message: {data['message']}")
        print(f"   Ready for Demo: {data['ready_for_demo']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        return False


def test_disable_judge_mode():
    """Test disabling judge mode"""
    print("\n" + "="*60)
    print("TEST 7: Disable Judge Mode")
    print("="*60)
    
    response = requests.post(f"{BASE_URL}/judge/disable")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Judge mode disabled")
        print(f"   Message: {data['message']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("SPRINT 2 FEATURE TESTS")
    print("Judge Mode & Fast Responses")
    print("="*60)
    
    try:
        results = []
        
        # Test 1: Get judge mode status
        results.append(test_judge_mode_status())
        
        # Test 2: Enable judge mode
        results.append(test_enable_judge_mode())
        
        # Test 3: Get guided flow
        results.append(test_guided_flow())
        
        # Test 4: Fast attestation
        claim_id = test_fast_attestation()
        results.append(claim_id is not None)
        
        # Test 5: Judge stats
        results.append(test_judge_stats())
        
        # Test 6: Reset demo data
        results.append(test_reset_demo())
        
        # Test 7: Disable judge mode
        results.append(test_disable_judge_mode())
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        passed = sum(results)
        total = len(results)
        print(f"Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("✅ ALL SPRINT 2 FEATURES WORKING!")
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

"""
Test Sprint 3: Gemini 3 Integration
Tests AI-powered control interpretation and proof template selection
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"


def test_gemini_status():
    """Test Gemini integration status"""
    print("\n" + "="*60)
    print("TEST 1: Gemini Status")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/gemini/status")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Gemini status retrieved")
        print(f"   Mode: {data['mode']}")
        print(f"   Gemini Available: {data['gemini_available']}")
        print(f"   API Key Configured: {data['api_key_configured']}")
        print(f"   Message: {data['message']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        return False


def test_interpret_control():
    """Test control interpretation"""
    print("\n" + "="*60)
    print("TEST 2: Interpret Control with Gemini")
    print("="*60)
    
    payload = {
        "control_statement": "The organization manages user accounts and enforces least privilege access controls",
        "framework": "NIST 800-53",
        "control_id": "AC-2"
    }
    
    response = requests.post(f"{BASE_URL}/gemini/interpret", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        interpretation = data['interpretation']
        print(f"✅ Success! Control interpreted")
        print(f"   Claim Type: {interpretation['claim_type']}")
        print(f"   Proof Template: {interpretation['proof_template']}")
        print(f"   Risk Level: {interpretation['risk_level']}")
        print(f"   Confidence: {interpretation['confidence']}")
        print(f"   Interpreted By: {interpretation['interpreted_by']}")
        print(f"\n   Reasoning:")
        print(f"   {interpretation['reasoning']}")
        print(f"\n   Evidence Requirements:")
        for req in interpretation['evidence_requirements']:
            print(f"   - {req}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   {response.text}")
        return False


def test_get_proof_templates():
    """Test getting proof templates"""
    print("\n" + "="*60)
    print("TEST 3: Get Proof Templates")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/gemini/templates")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Got {data['count']} proof templates")
        
        for template in data['templates']:
            print(f"\n   📋 {template['name'].upper()}")
            print(f"      Description: {template['description']}")
            print(f"      Complexity: {template['complexity']}")
            print(f"      Privacy Level: {template['privacy_level']}")
            print(f"      Use Cases: {', '.join(template['use_cases'][:2])}...")
        
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        return False


def test_select_template():
    """Test proof template selection"""
    print("\n" + "="*60)
    print("TEST 4: Select Proof Template")
    print("="*60)
    
    response = requests.post(
        f"{BASE_URL}/gemini/select-template",
        params={
            "claim_type": "control_effectiveness",
            "risk_level": "high",
            "data_sensitivity": "high"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        template = data['recommended_template']
        print(f"✅ Success! Template selected")
        print(f"   Recommended: {template['name']}")
        print(f"   Reasoning: {data['reasoning']}")
        print(f"   Privacy Level: {data['privacy_level']}")
        print(f"   Complexity: {data['complexity']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        return False


def test_quick_attest_with_gemini():
    """Test quick attestation with Gemini interpretation"""
    print("\n" + "="*60)
    print("TEST 5: Quick Attestation with Gemini")
    print("="*60)
    
    response = requests.post(f"{BASE_URL}/samples/quick-attest/AC-2")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Created attestation with Gemini")
        print(f"   Claim ID: {data['claim_id']}")
        print(f"   Message: {data['message']}")
        
        if 'gemini_insights' in data:
            insights = data['gemini_insights']
            print(f"\n   🤖 Gemini Insights:")
            print(f"      Claim Type: {insights['claim_type']}")
            print(f"      Proof Template: {insights['proof_template']}")
            print(f"      Risk Level: {insights['risk_level']}")
            print(f"      Reasoning: {insights['reasoning'][:60]}...")
            print(f"      Interpreted By: {insights['interpreted_by']}")
        
        # Wait a bit and check if gemini_interpretation is in attestation
        time.sleep(2)
        att_response = requests.get(f"{BASE_URL}/attestations/{data['claim_id']}")
        if att_response.status_code == 200:
            att_data = att_response.json()
            if 'gemini_interpretation' in att_data:
                print(f"\n   ✅ Gemini interpretation stored in attestation")
        
        return data['claim_id']
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   {response.text}")
        return None


def test_batch_interpret():
    """Test batch interpretation"""
    print("\n" + "="*60)
    print("TEST 6: Batch Control Interpretation")
    print("="*60)
    
    controls = [
        {
            "control_statement": "The organization maintains audit logs for security events",
            "framework": "SOC 2",
            "control_id": "CC7.2"
        },
        {
            "control_statement": "The organization encrypts sensitive data at rest and in transit",
            "framework": "HIPAA",
            "control_id": "164.312(a)(2)(iv)"
        }
    ]
    
    response = requests.post(f"{BASE_URL}/gemini/batch-interpret", json=controls)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Batch interpretation complete")
        print(f"   Total: {data['total']}")
        print(f"   Successful: {data['successful']}")
        print(f"   Failed: {data['failed']}")
        
        for result in data['results']:
            if result['status'] == 'success':
                interp = result['interpretation']
                print(f"\n   ✓ {result['framework']} {result['control_id']}")
                print(f"     → {interp['claim_type']} | {interp['proof_template']} | {interp['risk_level']}")
        
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        return False


def test_gemini_in_enhanced_response():
    """Test that Gemini interpretation appears in enhanced attestation response"""
    print("\n" + "="*60)
    print("TEST 7: Gemini in Enhanced Response")
    print("="*60)
    
    # Create attestation
    response = requests.post(f"{BASE_URL}/samples/quick-attest/CC6.1")
    
    if response.status_code != 200:
        print(f"❌ Failed to create attestation: {response.status_code}")
        return False
    
    claim_id = response.json()['claim_id']
    
    # Wait for completion
    time.sleep(2)
    
    # Get enhanced response
    att_response = requests.get(f"{BASE_URL}/attestations/{claim_id}")
    
    if att_response.status_code == 200:
        data = att_response.json()
        
        if 'gemini_interpretation' in data:
            gemini = data['gemini_interpretation']
            print(f"✅ Success! Gemini interpretation in response")
            print(f"   Claim Type: {gemini['claim_type']}")
            print(f"   Proof Template: {gemini['proof_template']}")
            print(f"   Risk Level: {gemini['risk_level']}")
            print(f"   Confidence: {gemini['confidence']}")
            print(f"   Interpreted By: {gemini['interpreted_by']}")
            return True
        else:
            print(f"⚠️ Gemini interpretation not found in response")
            return False
    else:
        print(f"❌ Failed: {att_response.status_code}")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("SPRINT 3 FEATURE TESTS")
    print("Gemini 3 AI Integration")
    print("="*60)
    
    try:
        results = []
        
        # Test 1: Gemini status
        results.append(test_gemini_status())
        
        # Test 2: Interpret control
        results.append(test_interpret_control())
        
        # Test 3: Get proof templates
        results.append(test_get_proof_templates())
        
        # Test 4: Select template
        results.append(test_select_template())
        
        # Test 5: Quick attest with Gemini
        claim_id = test_quick_attest_with_gemini()
        results.append(claim_id is not None)
        
        # Test 6: Batch interpret
        results.append(test_batch_interpret())
        
        # Test 7: Gemini in enhanced response
        results.append(test_gemini_in_enhanced_response())
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        passed = sum(results)
        total = len(results)
        print(f"Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("✅ ALL SPRINT 3 FEATURES WORKING!")
        else:
            print(f"⚠️ {total - passed} test(s) failed")
        
        print("\n" + "="*60)
        print("NOTE: If 'rule-based-fallback' is shown, that's OK!")
        print("Set GEMINI_API_KEY environment variable for real AI.")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ CONNECTION ERROR: Server not running!")
        print("Start with: python -m uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

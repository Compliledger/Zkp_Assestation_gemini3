"""
Interactive Hackathon Demo Script
Quick demonstrations of ZKP Attestation Agent capabilities
"""

import requests
import json
import time
from datetime import datetime
from typing import Optional

BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"


def print_header(text: str):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def print_json(data: dict, title: str = "Response"):
    """Print formatted JSON"""
    print(f"\n{title}:")
    print(json.dumps(data, indent=2))


def demo_1_quick_attestation():
    """Demo 1: Quick attestation with auto-generated evidence"""
    print_header("DEMO 1: Quick Attestation (Auto-Generated Evidence)")
    
    print("\n📝 Creating attestation with SOC2 Type II policy...")
    print("   Using quick demo endpoint with 5 auto-generated evidence items")
    
    payload = {
        "policy": "SOC2_TYPE_II",
        "evidence_count": 5
    }
    
    response = requests.post(f"{API_V1}/demo/quick", json=payload)
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None
    
    data = response.json()
    print_json(data, "Attestation Created")
    
    claim_id = data["claim_id"]
    print(f"\n✅ Attestation created: {claim_id}")
    print(f"   Status: {data['status']}")
    print(f"   Policy: {data['policy_used']}")
    print(f"   Evidence: {data['evidence_count']} items")
    
    # Wait and check status
    print("\n⏳ Waiting for processing...")
    time.sleep(2)
    
    response = requests.get(f"{API_V1}/attestations/{claim_id}")
    if response.status_code == 200:
        attestation = response.json()
        print(f"\n📊 Final Status: {attestation['status']}")
        
        if attestation.get('proof'):
            print(f"   Proof Hash: {attestation['proof']['proof_hash'][:16]}...")
        if attestation.get('package'):
            print(f"   Package Hash: {attestation['package']['package_hash'][:16]}...")
    
    return claim_id


def demo_2_available_policies():
    """Demo 2: Show available compliance policies"""
    print_header("DEMO 2: Available Compliance Policies")
    
    response = requests.get(f"{API_V1}/demo/policies")
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        return
    
    data = response.json()
    print(f"\n📋 Available Policies: {data['count']}")
    
    for policy in data['policies']:
        print(f"\n   • {policy['name']}")
        print(f"     {policy['description']}")
    
    print("\n💡 You can use any of these in /demo/quick endpoint!")


def demo_3_test_scenarios():
    """Demo 3: Pre-configured test scenarios"""
    print_header("DEMO 3: Pre-Configured Test Scenarios")
    
    response = requests.get(f"{API_V1}/demo/scenarios")
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        return
    
    scenarios = response.json()
    print(f"\n📦 Available Scenarios: {len(scenarios)}")
    
    for idx, scenario in enumerate(scenarios):
        print(f"\n   [{idx}] {scenario['name']}")
        print(f"       {scenario['description']}")
        print(f"       Policy: {scenario['policy']}")
        print(f"       Evidence: {scenario['evidence_count']} items")


def demo_4_run_scenario():
    """Demo 4: Run a specific scenario"""
    print_header("DEMO 4: Run Scenario - GDPR Privacy Check")
    
    scenario_index = 2  # GDPR scenario
    
    print(f"\n🚀 Running scenario {scenario_index}: GDPR Privacy Check")
    
    response = requests.post(f"{API_V1}/demo/scenario/{scenario_index}")
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None
    
    data = response.json()
    print_json(data, "Scenario Result")
    
    claim_id = data["claim_id"]
    print(f"\n✅ Scenario completed: {claim_id}")
    
    return claim_id


def demo_5_verification():
    """Demo 5: Verify an attestation"""
    print_header("DEMO 5: Attestation Verification")
    
    # First create an attestation
    print("\n📝 Creating attestation to verify...")
    payload = {
        "policy": "HIPAA",
        "evidence_count": 3
    }
    
    response = requests.post(f"{API_V1}/demo/quick", json=payload)
    claim_id = response.json()["claim_id"]
    print(f"   Created: {claim_id}")
    
    # Wait for processing
    time.sleep(2)
    
    # Verify it
    print(f"\n🔍 Verifying attestation {claim_id}...")
    
    verify_payload = {
        "claim_id": claim_id,
        "check_expiry": True,
        "check_revocation": True,
        "check_anchor": False
    }
    
    response = requests.post(f"{API_V1}/verify", json=verify_payload)
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return
    
    data = response.json()
    print_json(data, "Verification Result")
    
    print(f"\n✅ Verification Status: {data['status']}")
    print(f"   Receipt ID: {data['receipt_id']}")
    
    checks = data.get('checks', {})
    for check_name, result in checks.items():
        status_icon = "✅" if result else "❌"
        print(f"   {status_icon} {check_name}: {result}")


def demo_6_stats():
    """Demo 6: System statistics"""
    print_header("DEMO 6: System Statistics")
    
    response = requests.get(f"{API_V1}/demo/stats")
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        return
    
    data = response.json()
    print_json(data, "Demo Statistics")
    
    print(f"\n📊 Total Attestations: {data['total_attestations']}")
    print(f"📊 Total Verifications: {data['total_verifications']}")
    
    if data.get('status_breakdown'):
        print("\n📈 Status Breakdown:")
        for status, count in data['status_breakdown'].items():
            print(f"   • {status}: {count}")


def demo_7_full_workflow():
    """Demo 7: Complete end-to-end workflow"""
    print_header("DEMO 7: Complete End-to-End Workflow")
    
    print("\n🎯 Full Attestation Lifecycle Demo")
    print("   1. Create attestation with custom evidence")
    print("   2. Poll for completion")
    print("   3. Verify the attestation")
    print("   4. Check verification receipt")
    
    # Step 1: Create
    print("\n[Step 1] Creating attestation...")
    payload = {
        "evidence": [
            {
                "uri": "demo://audit/access-controls",
                "hash": "a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd",
                "type": "access_control_audit"
            },
            {
                "uri": "demo://audit/encryption-at-rest",
                "hash": "b2c3d4e5f6789012345678901234567890123456789012345678901234abcde",
                "type": "encryption_audit"
            },
            {
                "uri": "demo://audit/security-training",
                "hash": "c3d4e5f6789012345678901234567890123456789012345678901234abcdef",
                "type": "training_records"
            }
        ],
        "policy": "SOC2 Type II - Security Controls"
    }
    
    response = requests.post(f"{API_V1}/attestations", json=payload)
    claim_id = response.json()["claim_id"]
    print(f"   ✅ Created: {claim_id}")
    
    # Step 2: Poll
    print("\n[Step 2] Polling for completion...")
    for i in range(5):
        time.sleep(1)
        response = requests.get(f"{API_V1}/attestations/{claim_id}")
        attestation = response.json()
        status = attestation["status"]
        print(f"   [{i+1}] Status: {status}")
        
        if status == "valid":
            print(f"   ✅ Attestation completed!")
            break
    
    # Step 3: Verify
    print("\n[Step 3] Verifying attestation...")
    verify_payload = {
        "claim_id": claim_id,
        "check_expiry": True,
        "check_revocation": True
    }
    
    response = requests.post(f"{API_V1}/verify", json=verify_payload)
    receipt_id = response.json()["receipt_id"]
    print(f"   ✅ Verified: {receipt_id}")
    
    # Step 4: Check receipt
    print("\n[Step 4] Checking verification receipt...")
    response = requests.get(f"{API_V1}/verify/{receipt_id}")
    receipt = response.json()
    
    print(f"\n📜 Verification Receipt:")
    print(f"   Receipt ID: {receipt['receipt_id']}")
    print(f"   Claim ID: {receipt['claim_id']}")
    print(f"   Status: {receipt['status']}")
    print(f"   Verified At: {receipt['verified_at']}")
    
    print("\n✅ Complete workflow finished!")


def main():
    """Run interactive demo menu"""
    print("\n" + "="*70)
    print("  🚀 ZKP ATTESTATION AGENT - INTERACTIVE DEMO")
    print("="*70)
    print(f"  Base URL: {BASE_URL}")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    demos = [
        ("Quick Attestation (Auto-Generated)", demo_1_quick_attestation),
        ("Available Policies", demo_2_available_policies),
        ("Test Scenarios", demo_3_test_scenarios),
        ("Run GDPR Scenario", demo_4_run_scenario),
        ("Verification Demo", demo_5_verification),
        ("System Statistics", demo_6_stats),
        ("Full Workflow", demo_7_full_workflow),
    ]
    
    print("\n📋 Available Demos:")
    for idx, (name, _) in enumerate(demos, 1):
        print(f"   {idx}. {name}")
    print("   0. Run All Demos")
    print("   q. Quit")
    
    while True:
        choice = input("\n👉 Select demo (0-7, q to quit): ").strip()
        
        if choice.lower() == 'q':
            print("\n👋 Goodbye!")
            break
        
        try:
            choice_num = int(choice)
            
            if choice_num == 0:
                print("\n🎬 Running all demos...")
                for name, demo_func in demos:
                    try:
                        demo_func()
                        time.sleep(1)
                    except Exception as e:
                        print(f"\n❌ Demo failed: {e}")
                print("\n✅ All demos completed!")
            elif 1 <= choice_num <= len(demos):
                name, demo_func = demos[choice_num - 1]
                try:
                    demo_func()
                except Exception as e:
                    print(f"\n❌ Demo failed: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("❌ Invalid choice")
        
        except ValueError:
            print("❌ Please enter a number or 'q'")
        except requests.exceptions.ConnectionError:
            print("\n❌ CONNECTION ERROR: Server not running?")
            print("   Start with: cd gemini3-zkp-attestation-agent && python -m uvicorn app.main:app")
            break
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break


if __name__ == "__main__":
    main()

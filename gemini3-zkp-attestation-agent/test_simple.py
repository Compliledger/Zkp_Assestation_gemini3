import requests
import json

url = "http://localhost:8000/api/v1/attestations"
payload = {
    "evidence": [{
        "uri": "demo://test",
        "hash": "a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890",
        "type": "test"
    }],
    "policy": "SOC2"
}

print("Sending request...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(url, json=payload)
    print(f"\nStatus: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"\nError: {e}")
    print(f"Response text: {response.text if 'response' in locals() else 'N/A'}")

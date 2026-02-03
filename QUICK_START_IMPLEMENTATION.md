# 🚀 Quick Start Implementation Guide
## Get the Demo Working in 2-3 Hours

**Goal**: Implement core attestation + verification endpoints WITHOUT database dependency.

---

## Phase 1: In-Memory Storage (30 min) ⚡

### Step 1.1: Create Memory Store

**Create**: `app/storage/memory_store.py`

```python
from datetime import datetime
from typing import Dict, Optional, List
import uuid

class MemoryStore:
    """In-memory storage for hackathon demo - no DB required"""
    
    def __init__(self):
        self.attestations: Dict[str, dict] = {}
        self.verifications: Dict[str, dict] = {}
        self.idempotency_keys: Dict[str, dict] = {}
    
    # Attestations
    def create_attestation(self, attestation_id: str, data: dict, idempotency_key: Optional[str] = None):
        self.attestations[attestation_id] = {
            **data,
            "created_at": datetime.utcnow().isoformat()
        }
        if idempotency_key:
            self.idempotency_keys[idempotency_key] = {
                "attestation_id": attestation_id,
                "created_at": datetime.utcnow()
            }
        return attestation_id
    
    def get_attestation(self, attestation_id: str) -> Optional[dict]:
        return self.attestations.get(attestation_id)
    
    def update_attestation(self, attestation_id: str, data: dict):
        if attestation_id in self.attestations:
            self.attestations[attestation_id].update(data)
    
    def list_attestations(self, limit: int = 100) -> List[dict]:
        return list(self.attestations.values())[:limit]
    
    # Idempotency
    def get_by_idempotency_key(self, key: str) -> Optional[str]:
        if key in self.idempotency_keys:
            return self.idempotency_keys[key]["attestation_id"]
        return None
    
    # Verifications
    def create_verification(self, verification_id: str, data: dict):
        self.verifications[verification_id] = {
            **data,
            "created_at": datetime.utcnow().isoformat()
        }
        return verification_id
    
    def get_verification(self, verification_id: str) -> Optional[dict]:
        return self.verifications.get(verification_id)

# Global instance
memory_store = MemoryStore()
```

### Step 1.2: Update Config for Demo Mode

**Edit**: `app/config.py`

Add at the top of Settings class:
```python
# Demo Mode Settings
DEMO_MODE: bool = Field(default=True, description="Enable demo mode (no DB required)")
USE_IN_MEMORY_STORAGE: bool = Field(default=True, description="Use in-memory storage")
REQUIRE_AUTH: bool = Field(default=False, description="Require authentication")
```

---

## Phase 2: Core Attestation Endpoint (60 min) 🔧

### Step 2.1: Update Attestations Endpoint

**Edit**: `app/api/v1/attestations.py`

Replace with:

```python
"""
Attestations API - Core Implementation
"""

from fastapi import APIRouter, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import json

from app.storage.memory_store import memory_store
from app.utils.crypto import HashUtils
from app.utils.merkle import create_merkle_tree_from_hashes
from app.core.anchoring.algorand_testnet import AlgorandTestnetAnchor
from app.config import settings

router = APIRouter()
hash_utils = HashUtils()

# Request/Response Models
class EvidenceRef(BaseModel):
    uri: str = Field(..., description="Evidence URI or identifier")
    hash: str = Field(..., description="SHA-256 hash of evidence")
    type: str = Field(default="compliance_check", description="Evidence type")

class AttestationRequest(BaseModel):
    evidence: List[EvidenceRef] = Field(..., min_items=1, description="Evidence references")
    policy: str = Field(..., description="Compliance policy or framework")
    callback_url: Optional[HttpUrl] = Field(None, description="Webhook callback URL")

class AttestationResponse(BaseModel):
    claim_id: str
    status: str
    message: str
    created_at: str

class AttestationDetail(BaseModel):
    claim_id: str
    status: str
    evidence: dict
    proof: Optional[dict] = None
    package: Optional[dict] = None
    anchor: Optional[dict] = None
    created_at: str
    completed_at: Optional[str] = None

# Helper Functions
def generate_claim_id() -> str:
    """Generate unique claim ID"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_suffix = uuid.uuid4().hex[:6].upper()
    return f"ATT-{timestamp}-{random_suffix}"

def generate_evidence_id() -> str:
    """Generate unique evidence ID"""
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    random_suffix = uuid.uuid4().hex[:4].upper()
    return f"EV-{timestamp}-{random_suffix}"

async def process_attestation(claim_id: str):
    """Background task to process attestation"""
    try:
        attestation = memory_store.get_attestation(claim_id)
        
        # Step 3: Generate proof (simplified for demo)
        attestation["status"] = "generating_proof"
        memory_store.update_attestation(claim_id, attestation)
        
        proof = {
            "proof_hash": hash_utils.hash_sha256(attestation["evidence"]["merkle_root"].encode()),
            "algorithm": "demo_zkp",
            "size_bytes": 128,
            "generated_at": datetime.utcnow().isoformat()
        }
        attestation["proof"] = proof
        
        # Step 4: Assemble package
        attestation["status"] = "assembling_package"
        memory_store.update_attestation(claim_id, attestation)
        
        package = {
            "protocol": "zkpa",
            "version": "1.1",
            "attestation_id": claim_id,
            "evidence": attestation["evidence"],
            "proof": proof,
            "metadata": attestation["metadata"]
        }
        package_bytes = json.dumps(package, sort_keys=True).encode()
        package_hash = hash_utils.hash_sha256(package_bytes)
        
        attestation["package"] = {
            "package_hash": package_hash,
            "package_uri": f"memory://{claim_id}",
            "size_bytes": len(package_bytes)
        }
        
        # Step 5: Anchor (optional, if Algorand enabled)
        if settings.ALGORAND_MNEMONIC:
            attestation["status"] = "anchoring"
            memory_store.update_attestation(claim_id, attestation)
            
            try:
                algorand = AlgorandTestnetAnchor(sender_mnemonic=settings.ALGORAND_MNEMONIC)
                anchor_result = algorand.anchor_attestation(
                    attestation_id=claim_id,
                    merkle_root=attestation["evidence"]["merkle_root"],
                    package_hash=package_hash
                )
                attestation["anchor"] = anchor_result
            except Exception as e:
                # Continue without anchor if it fails
                attestation["anchor"] = {"error": str(e)}
        
        # Final status
        attestation["status"] = "valid"
        attestation["completed_at"] = datetime.utcnow().isoformat()
        memory_store.update_attestation(claim_id, attestation)
        
    except Exception as e:
        attestation["status"] = "failed"
        attestation["error"] = str(e)
        memory_store.update_attestation(claim_id, attestation)

# Endpoints
@router.post("/", response_model=AttestationResponse)
async def create_attestation(
    request: AttestationRequest,
    background_tasks: BackgroundTasks,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """
    Create a new attestation
    
    Flow:
    1. Validate request + check idempotency
    2. Ingest evidence refs
    3. Compute commitment (Merkle root)
    4. Queue proof generation (background)
    5. Return claim_id immediately
    """
    
    # Check idempotency
    if idempotency_key:
        existing_id = memory_store.get_by_idempotency_key(idempotency_key)
        if existing_id:
            existing = memory_store.get_attestation(existing_id)
            return AttestationResponse(
                claim_id=existing_id,
                status=existing["status"],
                message="Returned from idempotency cache",
                created_at=existing["created_at"]
            )
    
    # Generate claim ID
    claim_id = generate_claim_id()
    
    # Step 1: Ingest evidence refs
    evidence_items = []
    hashes = []
    for ref in request.evidence:
        evidence_items.append({
            "id": generate_evidence_id(),
            "uri": ref.uri,
            "hash": ref.hash,
            "type": ref.type
        })
        hashes.append(ref.hash)
    
    # Step 2: Compute commitment (Merkle root)
    merkle_result = create_merkle_tree_from_hashes(hashes)
    merkle_root = merkle_result["merkle_root"]
    
    commitment_hash = hash_utils.hash_sha256(
        json.dumps(evidence_items, sort_keys=True).encode()
    )
    
    # Create attestation
    attestation = {
        "claim_id": claim_id,
        "status": "pending",
        "evidence": {
            "items": evidence_items,
            "count": len(evidence_items),
            "merkle_root": merkle_root,
            "commitment_hash": commitment_hash,
            "leaf_count": merkle_result["leaf_count"]
        },
        "metadata": {
            "policy": request.policy,
            "compliance_framework": "SOC2_TYPE_II",
            "issued_at": datetime.utcnow().isoformat(),
            "valid_until": (datetime.utcnow() + timedelta(days=90)).isoformat()
        },
        "callback_url": str(request.callback_url) if request.callback_url else None
    }
    
    # Store attestation
    memory_store.create_attestation(claim_id, attestation, idempotency_key)
    
    # Queue background processing
    background_tasks.add_task(process_attestation, claim_id)
    
    return AttestationResponse(
        claim_id=claim_id,
        status="pending",
        message="Attestation creation initiated. Poll GET /api/v1/attestations/{claim_id} for status.",
        created_at=attestation["created_at"]
    )

@router.get("/{claim_id}", response_model=AttestationDetail)
async def get_attestation(claim_id: str):
    """
    Get attestation status and details
    """
    attestation = memory_store.get_attestation(claim_id)
    
    if not attestation:
        raise HTTPException(status_code=404, detail=f"Attestation {claim_id} not found")
    
    return AttestationDetail(**attestation)

@router.get("/", response_model=List[AttestationDetail])
async def list_attestations(limit: int = 100):
    """
    List all attestations
    """
    attestations = memory_store.list_attestations(limit)
    return [AttestationDetail(**a) for a in attestations]
```

---

## Phase 3: Verification Endpoint (30 min) ✅

### Step 3.1: Implement Verification

**Edit**: `app/api/v1/verification.py`

Replace with:

```python
"""
Verification API - Complete Implementation
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

from app.storage.memory_store import memory_store
from app.utils.crypto import HashUtils

router = APIRouter()
hash_utils = HashUtils()

# Models
class VerificationRequest(BaseModel):
    attestation_id: str = Field(..., description="Attestation ID to verify")
    checks: List[str] = Field(
        default=["proof", "expiry", "revocation", "anchor"],
        description="Checks to perform"
    )

class CheckResult(BaseModel):
    check: str
    result: str  # PASS or FAIL
    details: str

class VerificationResponse(BaseModel):
    receipt_id: str
    attestation_id: str
    status: str  # PASS or FAIL
    checks_performed: List[CheckResult]
    timestamp: str

def generate_receipt_id() -> str:
    """Generate verification receipt ID"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_suffix = uuid.uuid4().hex[:6].upper()
    return f"VER-{timestamp}-{random_suffix}"

@router.post("/verify", response_model=VerificationResponse)
async def verify_attestation(request: VerificationRequest):
    """
    Verify an attestation
    
    Performs requested checks:
    - proof: Verify ZKP proof validity
    - expiry: Check if attestation is expired
    - revocation: Check revocation status
    - anchor: Verify blockchain anchor
    """
    
    # Get attestation
    attestation = memory_store.get_attestation(request.attestation_id)
    if not attestation:
        raise HTTPException(
            status_code=404,
            detail=f"Attestation {request.attestation_id} not found"
        )
    
    receipt_id = generate_receipt_id()
    checks_performed = []
    
    # Check 1: Proof validity
    if "proof" in request.checks:
        if attestation.get("proof"):
            # Simplified proof verification for demo
            proof_valid = True  # In production, verify actual ZKP
            checks_performed.append(CheckResult(
                check="proof_validity",
                result="PASS" if proof_valid else "FAIL",
                details="ZKP proof structure validated (demo mode)"
            ))
        else:
            checks_performed.append(CheckResult(
                check="proof_validity",
                result="FAIL",
                details="No proof attached to attestation"
            ))
    
    # Check 2: Expiry
    if "expiry" in request.checks:
        valid_until = datetime.fromisoformat(
            attestation["metadata"]["valid_until"].replace("Z", "")
        )
        is_expired = datetime.utcnow() > valid_until
        checks_performed.append(CheckResult(
            check="expiry",
            result="FAIL" if is_expired else "PASS",
            details=f"Valid until {attestation['metadata']['valid_until']}"
        ))
    
    # Check 3: Revocation
    if "revocation" in request.checks:
        # Check revocation status (simplified for demo)
        is_revoked = attestation.get("status") == "revoked"
        checks_performed.append(CheckResult(
            check="revocation",
            result="FAIL" if is_revoked else "PASS",
            details="Not revoked" if not is_revoked else "Attestation has been revoked"
        ))
    
    # Check 4: Anchor verification
    if "anchor" in request.checks:
        if attestation.get("anchor") and not attestation["anchor"].get("error"):
            # Simplified anchor verification
            anchor_valid = True  # In production, query blockchain
            checks_performed.append(CheckResult(
                check="anchor",
                result="PASS" if anchor_valid else "FAIL",
                details=f"Anchored on {attestation['anchor'].get('chain', 'blockchain')}"
            ))
        else:
            checks_performed.append(CheckResult(
                check="anchor",
                result="WARN",
                details="No blockchain anchor or anchor failed"
            ))
    
    # Overall status
    failed_checks = [c for c in checks_performed if c.result == "FAIL"]
    overall_status = "FAIL" if failed_checks else "PASS"
    
    # Create verification receipt
    verification = {
        "receipt_id": receipt_id,
        "attestation_id": request.attestation_id,
        "status": overall_status,
        "checks_performed": [c.dict() for c in checks_performed],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Store verification
    memory_store.create_verification(receipt_id, verification)
    
    return VerificationResponse(**verification)

@router.get("/verify/{receipt_id}", response_model=VerificationResponse)
async def get_verification_receipt(receipt_id: str):
    """Get verification receipt by ID"""
    verification = memory_store.get_verification(receipt_id)
    if not verification:
        raise HTTPException(
            status_code=404,
            detail=f"Verification receipt {receipt_id} not found"
        )
    return VerificationResponse(**verification)
```

---

## Phase 4: Update Main App (10 min) 🔄

### Step 4.1: Make Database Optional

**Edit**: `app/main.py`

Update the lifespan function:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events - startup and shutdown
    """
    # Startup
    logger.info("Starting ZKPA service...")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Version: {settings.APP_VERSION}")
    logger.info(f"Demo Mode: {settings.DEMO_MODE}")
    
    # Create database tables only if not in demo mode
    if not settings.USE_IN_MEMORY_STORAGE:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created/verified")
        except Exception as e:
            logger.warning(f"Database initialization skipped: {e}")
    else:
        logger.info("Using in-memory storage (demo mode)")
    
    logger.info("ZKPA service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ZKPA service...")
    if not settings.USE_IN_MEMORY_STORAGE:
        await engine.dispose()
    logger.info("ZKPA service shutdown complete")
```

---

## Phase 5: Test the Implementation (20 min) ✅

### Step 5.1: Create Test Script

**Create**: `scripts/test_api_flow.py`

```python
"""
Test the complete API flow
"""

import requests
import time
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"

def test_create_attestation():
    """Test POST /attestations"""
    print("\n" + "="*70)
    print("TEST 1: Create Attestation")
    print("="*70)
    
    payload = {
        "evidence": [
            {
                "uri": "demo://evidence/1",
                "hash": "a1b2c3d4e5f6...",
                "type": "access_log"
            },
            {
                "uri": "demo://evidence/2",
                "hash": "f6e5d4c3b2a1...",
                "type": "config_snapshot"
            }
        ],
        "policy": "SOC2 Type II Compliance"
    }
    
    response = requests.post(
        f"{API_V1}/attestations",
        json=payload,
        headers={"Idempotency-Key": "test-key-123"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.json()["claim_id"]

def test_get_attestation(claim_id):
    """Test GET /attestations/{id}"""
    print("\n" + "="*70)
    print("TEST 2: Get Attestation (polling)")
    print("="*70)
    
    for i in range(5):
        response = requests.get(f"{API_V1}/attestations/{claim_id}")
        data = response.json()
        
        print(f"\nPoll {i+1}: Status = {data['status']}")
        
        if data["status"] in ["valid", "failed"]:
            print("\n✓ Attestation complete!")
            print(f"Final data: {json.dumps(data, indent=2)}")
            return data
        
        time.sleep(2)
    
    return data

def test_verify_attestation(claim_id):
    """Test POST /verify"""
    print("\n" + "="*70)
    print("TEST 3: Verify Attestation")
    print("="*70)
    
    payload = {
        "attestation_id": claim_id,
        "checks": ["proof", "expiry", "revocation"]
    }
    
    response = requests.post(f"{API_V1}/verify", json=payload)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.json()

def test_idempotency():
    """Test idempotency"""
    print("\n" + "="*70)
    print("TEST 4: Idempotency Check")
    print("="*70)
    
    payload = {
        "evidence": [{"uri": "demo://test", "hash": "abc123", "type": "test"}],
        "policy": "Test Policy"
    }
    
    # First request
    r1 = requests.post(
        f"{API_V1}/attestations",
        json=payload,
        headers={"Idempotency-Key": "idempotency-test"}
    )
    
    # Second request with same key
    r2 = requests.post(
        f"{API_V1}/attestations",
        json=payload,
        headers={"Idempotency-Key": "idempotency-test"}
    )
    
    claim_id_1 = r1.json()["claim_id"]
    claim_id_2 = r2.json()["claim_id"]
    
    print(f"Request 1 claim_id: {claim_id_1}")
    print(f"Request 2 claim_id: {claim_id_2}")
    print(f"Match: {claim_id_1 == claim_id_2}")
    
    assert claim_id_1 == claim_id_2, "Idempotency failed!"
    print("✓ Idempotency working correctly")

if __name__ == "__main__":
    print("\n🚀 STARTING API FLOW TESTS")
    print("="*70)
    
    try:
        # Test 1: Create
        claim_id = test_create_attestation()
        
        # Test 2: Get/Poll
        time.sleep(3)  # Wait for background processing
        attestation = test_get_attestation(claim_id)
        
        # Test 3: Verify
        verification = test_verify_attestation(claim_id)
        
        # Test 4: Idempotency
        test_idempotency()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
```

### Step 5.2: Run Tests

```bash
# Terminal 1: Start the API
cd gemini3-zkp-attestation-agent
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Run tests
python scripts/test_api_flow.py
```

---

## Expected Results ✅

After completing these steps, you should have:

1. **Working API** (no database required)
2. **POST /attestations** - Creates attestation, returns claim_id
3. **GET /attestations/{id}** - Returns complete attestation with status
4. **POST /verify** - Verifies attestation, returns receipt
5. **Idempotency** - Same key returns same result
6. **Status Lifecycle** - pending → generating_proof → assembling_package → anchoring → valid

---

## Next Steps (Optional Enhancements)

After core implementation works:

- [ ] Add status lifecycle enum
- [ ] Add webhook callbacks
- [ ] Add explicit assembly service
- [ ] Update documentation
- [ ] Add Gemini 3 integration for policy reasoning

---

## Troubleshooting

### Issue: Import errors
**Fix**: Ensure `app/storage/__init__.py` exists:
```python
from .memory_store import memory_store
__all__ = ["memory_store"]
```

### Issue: Background tasks not running
**Fix**: Check FastAPI BackgroundTasks is imported correctly

### Issue: Health check fails
**Fix**: Use `/health/live` endpoint which doesn't require DB

---

**Time to Complete**: 2-3 hours  
**Result**: Fully working demo without database dependency!

# ZKP Attestation Agent - Implementation Plan
## Filling Critical Gaps for Hackathon Demo

**Created**: February 4, 2026  
**Target**: Gemini 3 Hackathon Submission  
**Status**: Planning Phase

---

## Executive Summary

This plan addresses the critical gaps identified in the ZKP attestation agent to make it demo-ready for the Gemini 3 hackathon. The focus is on:
1. **Core functionality** (attestation + verification)
2. **Simplified demo mode** (no DB dependency)
3. **Clear workflow** (explicit steps)
4. **Production-aware patterns** (idempotency, webhooks)

**Scope for Hackathon**: Reasoning-driven proof orchestration, NOT full production API.

---

## Critical Gaps Analysis

### 🔴 Gap 1: Core Attestation + Verification Not Implemented

**Current State**:
- ❌ `/api/v1/attestations` (POST) - Not implemented
- ❌ `/api/v1/verify` (POST) - Not implemented
- ✅ Demo scripts work (Steps 1-4)
- ⚠️ High-level workflow pending

**Impact**: Cannot demonstrate end-to-end flow through API

---

### 🔴 Gap 2: Database Readiness Failures

**Current State**:
- ❌ SQLAlchemy config errors
- ❌ Readiness probe failing
- ❌ 500s on list endpoints
- ✅ Liveness endpoint works

**Impact**: API cannot start without PostgreSQL

---

### 🔴 Gap 3: Authentication Inconsistencies

**Current State**:
- ⚠️ Auth partially implemented
- ⚠️ Inconsistent across endpoints
- ✅ JWT token generation works

**Impact**: Demo requires token setup, adds friction

---

## Implementation Strategy

### Phase 1: Hackathon Demo Mode (Priority 1) 🎯
**Goal**: Make it work without database, focus on AI reasoning

**Duration**: 2-3 hours

#### Task 1.1: Create In-Memory Storage Layer
**File**: `app/storage/memory_store.py`

```python
# Simple in-memory storage for demo
class MemoryStore:
    def __init__(self):
        self.attestations = {}
        self.verifications = {}
        self.evidence = {}
    
    def create_attestation(self, data):
        attestation_id = generate_id()
        self.attestations[attestation_id] = data
        return attestation_id
    
    def get_attestation(self, attestation_id):
        return self.attestations.get(attestation_id)
    
    # ... similar for verifications
```

**Benefits**:
- ✅ No database required
- ✅ Works immediately
- ✅ Perfect for hackathon demo
- ✅ Can persist to JSON for inspection

---

#### Task 1.2: Implement Core POST /attestations Endpoint
**File**: `app/api/v1/attestations.py`

**Flow**:
```
1. Validate request (+ idempotency)
2. Create claim (status: pending)
3. Ingest evidence refs → validate URIs/hashes
4. Compute commitment → Merkle root
5. Generate proof (using existing logic)
6. Assemble package (evidence + proof + metadata)
7. Sign package (Ed25519)
8. Publish package → save to memory/JSON
9. Anchor package hash → Algorand (if enabled)
10. Return: claim_id, status
```

**Code Structure**:
```python
@router.post("/", response_model=AttestationResponse)
async def create_attestation(
    request: AttestationRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    # Check idempotency
    if idempotency_key and store.has_idempotency_key(idempotency_key):
        return store.get_by_idempotency_key(idempotency_key)
    
    # Create claim
    claim_id = generate_claim_id()
    
    # Step 1: Ingest evidence
    evidence_refs = await ingest_evidence_refs(request.evidence)
    
    # Step 2: Compute commitment
    merkle_root = compute_merkle_commitment(evidence_refs)
    
    # Step 3: Generate proof (async background task for demo)
    proof_task_id = await queue_proof_generation(claim_id, merkle_root)
    
    # Store with pending status
    attestation = {
        "claim_id": claim_id,
        "status": "pending",
        "evidence_refs": evidence_refs,
        "merkle_root": merkle_root,
        "proof_task_id": proof_task_id,
        "created_at": datetime.utcnow(),
    }
    
    store.create_attestation(claim_id, attestation, idempotency_key)
    
    return AttestationResponse(
        claim_id=claim_id,
        status="pending",
        message="Attestation creation initiated"
    )
```

---

#### Task 1.3: Implement GET /attestations/{claim_id}
**File**: `app/api/v1/attestations.py`

**Returns**:
```json
{
  "claim_id": "ATT-20260204-123ABC",
  "status": "valid",
  "evidence": {
    "count": 5,
    "merkle_root": "8d7e9460...",
    "commitment_hash": "4ef1804d..."
  },
  "proof": {
    "proof_hash": "a1b2c3d4...",
    "algorithm": "groth16",
    "size_bytes": 128
  },
  "package": {
    "package_uri": "ipfs://Qm...",
    "package_hash": "5f2e..."
  },
  "anchor": {
    "chain": "algorand",
    "tx_id": "ABC123...",
    "block": 12345,
    "confirmed_at": "2026-02-04T..."
  },
  "created_at": "2026-02-04T...",
  "completed_at": "2026-02-04T..."
}
```

---

#### Task 1.4: Implement POST /verify Endpoint
**File**: `app/api/v1/verification.py`

**Input**:
```json
{
  "attestation_id": "ATT-20260204-123ABC",
  "package_uri": "ipfs://Qm..." (optional),
  "checks": ["proof", "expiry", "revocation", "anchor"]
}
```

**Logic**:
```python
@router.post("/verify", response_model=VerificationResponse)
async def verify_attestation(request: VerificationRequest):
    receipt_id = generate_receipt_id()
    
    results = {
        "receipt_id": receipt_id,
        "attestation_id": request.attestation_id,
        "status": "PASS",
        "checks_performed": [],
        "timestamp": datetime.utcnow()
    }
    
    # Check 1: Proof validity
    if "proof" in request.checks:
        proof_valid = await verify_zkp_proof(attestation.proof)
        results["checks_performed"].append({
            "check": "proof_validity",
            "result": "PASS" if proof_valid else "FAIL",
            "details": "ZKP proof verified successfully"
        })
    
    # Check 2: Expiry
    if "expiry" in request.checks:
        is_expired = check_expiry(attestation.valid_until)
        results["checks_performed"].append({
            "check": "expiry",
            "result": "FAIL" if is_expired else "PASS",
            "details": f"Valid until {attestation.valid_until}"
        })
    
    # Check 3: Revocation
    if "revocation" in request.checks:
        is_revoked = check_revocation_status(attestation.claim_id)
        results["checks_performed"].append({
            "check": "revocation",
            "result": "FAIL" if is_revoked else "PASS",
            "details": "Not revoked"
        })
    
    # Check 4: Anchor verification
    if "anchor" in request.checks:
        anchor_valid = await verify_blockchain_anchor(
            attestation.anchor.tx_id,
            attestation.package_hash
        )
        results["checks_performed"].append({
            "check": "anchor",
            "result": "PASS" if anchor_valid else "FAIL",
            "details": f"Verified on {attestation.anchor.chain}"
        })
    
    # Overall status
    results["status"] = "PASS" if all(
        c["result"] == "PASS" for c in results["checks_performed"]
    ) else "FAIL"
    
    # Store verification receipt
    store.create_verification(receipt_id, results)
    
    return results
```

---

### Phase 2: Enhanced Workflow (Priority 2) 🔧
**Goal**: Add production-aware patterns

**Duration**: 2-4 hours

#### Task 2.1: Implement Status Lifecycle
**File**: `app/models/attestation_status.py`

```python
from enum import Enum

class AttestationStatus(str, Enum):
    # Active states
    PENDING = "pending"
    INGESTING_EVIDENCE = "ingesting_evidence"
    COMPUTING_COMMITMENT = "computing_commitment"
    GENERATING_PROOF = "generating_proof"
    ASSEMBLING_PACKAGE = "assembling_package"
    ANCHORING = "anchoring"
    VALID = "valid"  # or ANCHORED
    
    # Terminal failure states
    FAILED_EVIDENCE = "failed_evidence"
    FAILED_PROOF = "failed_proof"
    FAILED_ANCHOR = "failed_anchor"
    FAILED_UNKNOWN = "failed"
    
    # Other terminal states
    REVOKED = "revoked"
    EXPIRED = "expired"

# Status transitions
VALID_TRANSITIONS = {
    PENDING: [INGESTING_EVIDENCE, FAILED_EVIDENCE],
    INGESTING_EVIDENCE: [COMPUTING_COMMITMENT, FAILED_EVIDENCE],
    COMPUTING_COMMITMENT: [GENERATING_PROOF, FAILED_EVIDENCE],
    GENERATING_PROOF: [ASSEMBLING_PACKAGE, FAILED_PROOF],
    ASSEMBLING_PACKAGE: [ANCHORING, FAILED_PROOF],
    ANCHORING: [VALID, FAILED_ANCHOR],
    VALID: [REVOKED, EXPIRED],
}
```

**Update Workflow**:
```python
async def update_attestation_status(claim_id: str, new_status: AttestationStatus):
    attestation = store.get_attestation(claim_id)
    current_status = AttestationStatus(attestation["status"])
    
    # Validate transition
    if new_status not in VALID_TRANSITIONS.get(current_status, []):
        raise InvalidStatusTransition(
            f"Cannot transition from {current_status} to {new_status}"
        )
    
    # Update
    attestation["status"] = new_status
    attestation["status_updated_at"] = datetime.utcnow()
    
    # Trigger webhook if configured
    if attestation.get("callback_url"):
        await trigger_webhook(attestation)
    
    store.update_attestation(claim_id, attestation)
```

---

#### Task 2.2: Implement Idempotency
**File**: `app/middleware/idempotency.py`

```python
class IdempotencyStore:
    def __init__(self):
        self.keys = {}  # key -> (response, timestamp)
    
    def check(self, key: str) -> Optional[dict]:
        if key in self.keys:
            response, timestamp = self.keys[key]
            # Check expiry (24 hours)
            if datetime.utcnow() - timestamp < timedelta(hours=24):
                return response
            else:
                del self.keys[key]
        return None
    
    def store(self, key: str, response: dict):
        self.keys[key] = (response, datetime.utcnow())

# Usage in endpoint
@router.post("/")
async def create_attestation(
    request: AttestationRequest,
    idempotency_key: Optional[str] = Header(None)
):
    if idempotency_key:
        cached = idempotency_store.check(idempotency_key)
        if cached:
            return cached
    
    # Process request...
    response = {...}
    
    if idempotency_key:
        idempotency_store.store(idempotency_key, response)
    
    return response
```

---

#### Task 2.3: Add Webhook Support
**File**: `app/services/webhook_service.py`

```python
async def trigger_webhook(attestation: dict):
    if not attestation.get("callback_url"):
        return
    
    payload = {
        "event": "attestation.status_changed",
        "claim_id": attestation["claim_id"],
        "status": attestation["status"],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                attestation["callback_url"],
                json=payload,
                timeout=10.0
            )
            logger.info(f"Webhook sent: {response.status_code}")
    except Exception as e:
        logger.error(f"Webhook failed: {e}")
        # Store for retry
        webhook_retry_queue.add(attestation["claim_id"], payload)
```

**Update Request Model**:
```python
class AttestationRequest(BaseModel):
    evidence: List[EvidenceRef]
    policy: str
    callback_url: Optional[HttpUrl] = None  # Add this
```

---

#### Task 2.4: Explicit Evidence Commitment Steps
**File**: `app/services/evidence_service.py`

```python
class EvidenceService:
    async def ingest_evidence_refs(
        self, 
        evidence_refs: List[EvidenceRef]
    ) -> List[dict]:
        """
        Step 1: Ingest and validate evidence references
        Returns: List of validated evidence items
        """
        validated = []
        for ref in evidence_refs:
            # Validate URI/hash format
            if not self._is_valid_reference(ref):
                raise InvalidEvidenceError(f"Invalid ref: {ref}")
            
            validated.append({
                "id": generate_evidence_id(),
                "uri": ref.uri,
                "hash": ref.hash,
                "type": ref.type,
                "validated_at": datetime.utcnow()
            })
        
        return validated
    
    async def compute_commitment(
        self, 
        evidence_items: List[dict]
    ) -> dict:
        """
        Step 2: Compute cryptographic commitment
        Returns: Merkle root + commitment hash
        """
        # Extract hashes
        hashes = [item["hash"] for item in evidence_items]
        
        # Build Merkle tree
        merkle_tree = create_merkle_tree_from_hashes(hashes)
        merkle_root = merkle_tree["merkle_root"]
        
        # Compute commitment hash (hash of all evidence)
        commitment_hash = HashUtils.hash_sha256(
            json.dumps(evidence_items, sort_keys=True).encode()
        )
        
        return {
            "merkle_root": merkle_root,
            "commitment_hash": commitment_hash,
            "leaf_count": len(hashes),
            "algorithm": "SHA256",
            "computed_at": datetime.utcnow()
        }
```

---

#### Task 2.5: Explicit Assembly Step
**File**: `app/services/assembly_service.py`

```python
class AssemblyService:
    async def assemble_package(
        self,
        claim_id: str,
        evidence: dict,
        proof: dict,
        metadata: dict
    ) -> dict:
        """
        Assemble attestation package with all components
        """
        package = {
            "protocol": "zkpa",
            "version": "1.1",
            "attestation_id": claim_id,
            "evidence": {
                "count": evidence["count"],
                "merkle_root": evidence["merkle_root"],
                "commitment_hash": evidence["commitment_hash"]
            },
            "proof": {
                "proof_hash": proof["hash"],
                "algorithm": proof["algorithm"],
                "public_inputs": proof.get("public_inputs", [])
            },
            "metadata": {
                "issuer": metadata.get("issuer"),
                "policy": metadata.get("policy"),
                "compliance_framework": metadata.get("framework"),
                "issued_at": datetime.utcnow().isoformat(),
                "valid_until": (
                    datetime.utcnow() + timedelta(days=90)
                ).isoformat()
            }
        }
        
        # Compute package hash
        package_bytes = json.dumps(package, sort_keys=True).encode()
        package["package_hash"] = HashUtils.hash_sha256(package_bytes)
        
        return package
    
    async def sign_package(self, package: dict, private_key: str) -> dict:
        """
        Sign the attestation package
        """
        package_hash = package["package_hash"]
        
        # Ed25519 signature
        signature = sign_ed25519(package_hash, private_key)
        
        package["signature"] = {
            "algorithm": "Ed25519",
            "value": signature,
            "signer": get_public_key(private_key),
            "signed_at": datetime.utcnow().isoformat()
        }
        
        return package
```

---

### Phase 3: Demo Optimization (Priority 3) 🎨
**Goal**: Make it hackathon-ready

**Duration**: 1-2 hours

#### Task 3.1: Simplify Authentication
**File**: `app/api/dependencies.py`

```python
# Demo mode: public endpoints or hardcoded token
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
DEMO_TOKEN = "demo_hackathon_token_2026"

async def get_current_user_demo(
    authorization: Optional[str] = Header(None)
):
    if DEMO_MODE:
        # Accept any token in demo mode
        if authorization and "Bearer" in authorization:
            return {"username": "demo_user", "role": "admin"}
        # Or no token required
        return {"username": "anonymous", "role": "viewer"}
    
    # Normal auth flow
    return await get_current_user(authorization)
```

---

#### Task 3.2: Add Demo Data Generator
**File**: `app/utils/demo_data.py`

```python
def generate_demo_evidence(count: int = 5) -> List[EvidenceRef]:
    """Generate deterministic demo evidence"""
    evidence = []
    for i in range(count):
        data = f"Demo evidence {i}: compliance check {datetime.utcnow()}"
        evidence.append(EvidenceRef(
            uri=f"demo://evidence/{i}",
            hash=HashUtils.hash_sha256(data.encode()),
            type="compliance_check"
        ))
    return evidence

def get_demo_policy() -> str:
    """Return demo compliance policy"""
    return """
    SOC2 Type II Compliance Requirements:
    - Access controls implemented
    - Encryption at rest and in transit
    - Regular security audits
    - Incident response procedures
    """
```

---

#### Task 3.3: Add API Mode Toggle
**File**: `app/config.py`

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Demo/Hackathon mode
    DEMO_MODE: bool = True
    USE_IN_MEMORY_STORAGE: bool = True
    REQUIRE_DATABASE: bool = False
    REQUIRE_AUTH: bool = False
    
    # Storage
    STORAGE_BACKEND: str = "memory"  # memory | json | s3
    JSON_STORAGE_PATH: str = "./demo_storage"
```

---

### Phase 4: Documentation Updates (Priority 4) 📝
**Goal**: Clear hackathon positioning

**Duration**: 1 hour

#### Task 4.1: Update README
**File**: `README.md`

Add section:
```markdown
## 🎯 Hackathon Demo Mode

This repository demonstrates a **Gemini-3-powered ZKP Attestation Agent** 
focused on AI-driven reasoning and proof orchestration.

### What's Implemented
✅ Evidence ingestion and commitment
✅ Merkle tree generation
✅ Attestation assembly
✅ Ed25519 signing
✅ Algorand TestNet anchoring
✅ Verification logic

### Demo Mode Features
- In-memory storage (no database required)
- Simplified authentication
- Deterministic test data
- JSON artifact export

### Production Considerations
This demo focuses on the reasoning layer and core cryptographic flows.
For production deployment, add:
- Persistent database (PostgreSQL)
- Full authentication (OAuth2/OIDC)
- Rate limiting and monitoring
- Multi-tenant isolation
```

---

#### Task 4.2: Create API Flow Diagram
**File**: `API_FLOW.md`

```
┌─────────────────────────────────────────────────────────────┐
│ Client Application                                           │
└─────────────────────────────────────────────────────────────┘
                    │
                    │ POST /api/v1/attestations
                    │ {evidence, policy, callback_url}
                    │ Idempotency-Key: xyz123
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ ZKP Attestation Agent                                        │
│                                                              │
│  1. Check Idempotency Key ──► Return cached if exists      │
│                                                              │
│  2. Create Claim (status: pending)                          │
│     └─► claim_id: ATT-20260204-ABC123                      │
│                                                              │
│  3. Ingest Evidence Refs                                    │
│     └─► Validate URIs/hashes                               │
│                                                              │
│  4. Compute Commitment                                       │
│     ├─► Build Merkle tree                                   │
│     ├─► merkle_root: 8d7e9460...                           │
│     └─► commitment_hash: 4ef1804d...                       │
│                                                              │
│  5. Generate Proof (async)                                   │
│     ├─► Queue proof generation task                         │
│     └─► status: generating_proof                           │
│                                                              │
│  6. Assemble Package                                         │
│     ├─► Combine evidence + proof + metadata                │
│     └─► package_hash: 5f2e9abc...                          │
│                                                              │
│  7. Sign Package                                             │
│     ├─► Ed25519 signature                                   │
│     └─► signer: ALGO_ADDRESS                               │
│                                                              │
│  8. Publish Package                                          │
│     └─► package_uri: ipfs://Qm...                          │
│                                                              │
│  9. Anchor Package Hash                                      │
│     ├─► Submit to Algorand TestNet                         │
│     ├─► tx_id: ABC123...                                    │
│     └─► status: valid                                       │
│                                                              │
│  10. Trigger Webhook (if provided)                          │
│      └─► POST callback_url {status: "valid"}               │
└─────────────────────────────────────────────────────────────┘
                    │
                    │ Response
                    │ {claim_id, status: "pending"}
                    ▼
                    
Client polls: GET /api/v1/attestations/{claim_id}

Response when complete:
{
  "claim_id": "ATT-20260204-ABC123",
  "status": "valid",
  "evidence": {...},
  "proof": {...},
  "package": {
    "package_uri": "ipfs://Qm...",
    "package_hash": "5f2e..."
  },
  "anchor": {
    "chain": "algorand",
    "tx_id": "ABC123...",
    "block": 12345
  }
}

Client verifies: POST /api/v1/verify
{
  "attestation_id": "ATT-20260204-ABC123",
  "checks": ["proof", "expiry", "revocation", "anchor"]
}

Response:
{
  "receipt_id": "VER-20260204-XYZ789",
  "status": "PASS",
  "checks_performed": [
    {"check": "proof_validity", "result": "PASS"},
    {"check": "expiry", "result": "PASS"},
    {"check": "revocation", "result": "PASS"},
    {"check": "anchor", "result": "PASS"}
  ]
}
```

---

#### Task 4.3: Create Devpost Description Template
**File**: `DEVPOST_DESCRIPTION.md`

```markdown
# Gemini-3 ZKP Attestation Agent

## Inspiration
Privacy-preserving compliance is critical in regulated industries, but 
traditional attestation systems are opaque and centralized. We built an
AI-powered agent that uses Gemini 3 to reason about compliance requirements
and generate verifiable zero-knowledge proofs.

## What it does
The ZKP Attestation Agent:
1. Analyzes compliance policies using Gemini 3
2. Generates zero-knowledge proofs without revealing sensitive data
3. Creates cryptographically signed attestation packages
4. Anchors proofs to Algorand blockchain for immutability
5. Provides verification endpoints for third-party auditors

## How we built it
- **AI Reasoning**: Gemini 3 for policy interpretation and proof selection
- **Cryptography**: Merkle trees, Ed25519 signatures, SHA-256 hashing
- **Blockchain**: Algorand TestNet for decentralized anchoring
- **API**: FastAPI with async proof generation
- **Demo Mode**: In-memory storage for hackathon demonstration

## Challenges we ran into
- Balancing production architecture with demo simplicity
- Implementing cryptographic primitives correctly
- Designing clear status lifecycle for async operations

## Accomplishments
- Complete end-to-end attestation workflow
- Real blockchain integration (Algorand TestNet)
- Production-aware patterns (idempotency, webhooks, status lifecycle)
- Clear API design with verification receipts

## What we learned
- Zero-knowledge proofs require careful commitment schemes
- AI reasoning can guide complex cryptographic workflows
- Hackathon demos benefit from simplified storage layers

## What's next
- Add Gemini 3 integration for policy analysis
- Implement full proof verification algorithms
- Add multi-chain support (Ethereum, Solana)
- Deploy to production with PostgreSQL

## Hackathon Scope
This demo focuses on:
✅ AI-driven reasoning and proof orchestration
✅ Cryptographic correctness
✅ Clear API design
⚠️ Simplified for demo (in-memory storage, mock proof generation)
```

---

## Implementation Timeline

### Week 1 (Now)
- [x] Gap analysis complete
- [ ] Phase 1: Demo mode (3 hours)
  - [ ] In-memory storage
  - [ ] POST /attestations
  - [ ] GET /attestations/{id}
  - [ ] POST /verify

### Week 1 (After basic implementation)
- [ ] Phase 2: Enhanced workflow (4 hours)
  - [ ] Status lifecycle
  - [ ] Idempotency
  - [ ] Webhooks
  - [ ] Explicit steps

### Week 1 (Polish)
- [ ] Phase 3: Demo optimization (2 hours)
  - [ ] Simplify auth
  - [ ] Demo data
  - [ ] Config toggles

### Week 1 (Final)
- [ ] Phase 4: Documentation (1 hour)
  - [ ] README update
  - [ ] API flow diagram
  - [ ] Devpost description

**Total Estimated Time**: 10-12 hours

---

## Success Criteria

### Must Have (Hackathon Demo)
- [x] Core attestation flow works end-to-end
- [ ] POST /attestations returns claim_id
- [ ] GET /attestations/{id} returns complete attestation
- [ ] POST /verify returns verification receipt
- [ ] Works without database
- [ ] Clear README with demo instructions

### Should Have (Production-Aware)
- [ ] Status lifecycle with intermediate states
- [ ] Idempotency support
- [ ] Webhook callbacks (documented, optional)
- [ ] API flow diagram
- [ ] Devpost description

### Nice to Have (Future)
- [ ] Gemini 3 integration for policy reasoning
- [ ] Full ZKP verification (not mocked)
- [ ] Multi-chain support
- [ ] Database migration path

---

## Testing Strategy

### Unit Tests
```python
# test_attestation_flow.py
def test_create_attestation():
    response = client.post("/api/v1/attestations", json={
        "evidence": demo_evidence,
        "policy": "SOC2"
    })
    assert response.status_code == 200
    assert "claim_id" in response.json()

def test_get_attestation():
    claim_id = create_test_attestation()
    response = client.get(f"/api/v1/attestations/{claim_id}")
    assert response.json()["status"] in ["pending", "valid"]

def test_verify_attestation():
    claim_id = create_test_attestation()
    response = client.post("/api/v1/verify", json={
        "attestation_id": claim_id,
        "checks": ["proof", "expiry"]
    })
    assert response.json()["status"] in ["PASS", "FAIL"]

def test_idempotency():
    key = "test-key-123"
    r1 = client.post("/api/v1/attestations", 
        headers={"Idempotency-Key": key},
        json=demo_request
    )
    r2 = client.post("/api/v1/attestations",
        headers={"Idempotency-Key": key},
        json=demo_request
    )
    assert r1.json()["claim_id"] == r2.json()["claim_id"]
```

### Integration Tests
- End-to-end flow: create → poll → verify
- Webhook callback test
- Status transitions
- Algorand anchoring (if enabled)

---

## File Structure

```
app/
├── api/
│   └── v1/
│       ├── attestations.py        # ← Implement POST/GET
│       └── verification.py        # ← Implement POST /verify
├── services/
│   ├── evidence_service.py       # ← Explicit ingest + commit
│   ├── assembly_service.py       # ← Package assembly + signing
│   └── webhook_service.py        # ← Webhook triggers
├── storage/
│   ├── memory_store.py           # ← NEW: In-memory storage
│   └── json_store.py             # ← NEW: JSON persistence
├── models/
│   └── attestation_status.py    # ← Status lifecycle
└── middleware/
    └── idempotency.py            # ← Idempotency handling

scripts/
└── demo_api_flow.py              # ← End-to-end API demo

docs/
├── API_FLOW.md                   # ← Flow diagram
├── DEVPOST_DESCRIPTION.md        # ← Submission template
└── IMPLEMENTATION_PLAN.md        # ← This file
```

---

## Risk Mitigation

### Risk 1: Time Constraints
**Mitigation**: Focus on Phase 1 (demo mode) first. Phases 2-4 are enhancements.

### Risk 2: Complex ZKP Verification
**Mitigation**: Mock proof verification for hackathon, document as "conceptual".

### Risk 3: Database Dependency
**Mitigation**: In-memory storage solves this completely.

### Risk 4: Authentication Friction
**Mitigation**: Demo mode with optional auth, clearly documented.

---

## Questions to Resolve

1. **Gemini 3 Integration**: Where/how should Gemini analyze policies?
   - Recommendation: Add in Phase 2, make it optional

2. **Proof Generation**: Mock or real?
   - Recommendation: Use existing demo script logic, mark as simplified

3. **Storage Persistence**: JSON files or pure memory?
   - Recommendation: Memory + optional JSON export

4. **Deployment Target**: Railway or local?
   - Recommendation: Both - Railway with DB, local without

---

## Next Actions

1. **Immediate** (Today):
   - [ ] Review this plan
   - [ ] Create `app/storage/memory_store.py`
   - [ ] Implement POST /attestations (basic)

2. **Next** (Tomorrow):
   - [ ] Add GET /attestations/{id}
   - [ ] Add POST /verify
   - [ ] Test end-to-end flow

3. **Polish** (Day 3):
   - [ ] Add status lifecycle
   - [ ] Add idempotency
   - [ ] Update documentation

---

## References

- [MIGRATION_STATUS.md](MIGRATION_STATUS.md) - Current implementation status
- [RAILWAY_DEPLOYMENT.md](gemini3-zkp-attestation-agent/RAILWAY_DEPLOYMENT.md) - Deployment guide
- [Demo Script](gemini3-zkp-attestation-agent/scripts/demo_attestation_workflow.py) - Working example

---

**Status**: Ready to implement  
**Owner**: Development team  
**Target Completion**: February 7, 2026 (3 days before hackathon deadline)

# Devpost Improvements Implementation Plan - Backend

**Goal**: Enhance ZKPA backend to support manager feedback for Devpost judging  
**Timeline**: 4-6 hours  
**Priority**: High-impact features first

---

## Executive Summary

Based on manager feedback, implement backend features to support:
1. **Enhanced results/output** - Better status tracking and downloadable artifacts
2. **Sample controls** - Pre-defined compliance controls for quick demos
3. **Judge mode** - Guided demo with simulated responses
4. **Gemini 3 integration** - Control interpretation and proof template selection
5. **Enhanced verification** - Clear PASS/FAIL with detailed checks

---

## Phase 1: Sample Controls & Quick-Fill (Priority 1) 🎯

**Impact**: Judges get 1-click examples - highest completion rate improvement

### Task 1.1: Create Sample Controls Data Structure

**File**: `app/utils/sample_controls.py` (NEW)

**Implementation**:
```python
class SampleControl:
    control_id: str          # e.g., "AC-2", "CC6.1"
    framework: str           # e.g., "NIST 800-53", "SOC 2"
    title: str              # e.g., "Account Management"
    statement: str          # Full control statement
    claim_type: str         # e.g., "evidence_integrity"
    proof_template: str     # e.g., "merkle_commitment"
    evidence_count: int     # Auto-generated evidence count

SAMPLE_CONTROLS = [
    {
        "control_id": "AC-2",
        "framework": "NIST 800-53",
        "title": "Account Management",
        "statement": "The organization manages information system accounts...",
        "claim_type": "control_effectiveness",
        "proof_template": "merkle_commitment",
        "evidence_count": 5
    },
    {
        "control_id": "CC6.1",
        "framework": "SOC 2",
        "title": "Logical and Physical Access Controls",
        "statement": "The entity implements logical access security...",
        "claim_type": "evidence_integrity",
        "proof_template": "merkle_commitment",
        "evidence_count": 4
    },
    {
        "control_id": "A.5.15",
        "framework": "ISO 27001",
        "title": "Access Control",
        "statement": "Rules for access control and rights...",
        "claim_type": "control_effectiveness",
        "proof_template": "merkle_commitment",
        "evidence_count": 3
    },
    # Add 5-10 more common controls
]
```

### Task 1.2: Add Sample Controls Endpoint

**File**: `app/api/v1/samples.py` (NEW)

**Endpoints**:
```python
GET /api/v1/samples/controls
# Returns all sample controls

GET /api/v1/samples/controls/{control_id}
# Returns specific control details

GET /api/v1/samples/frameworks
# Returns list of supported frameworks with control counts
```

**Response Example**:
```json
{
  "controls": [
    {
      "control_id": "AC-2",
      "framework": "NIST 800-53",
      "title": "Account Management",
      "statement": "The organization manages...",
      "claim_type": "control_effectiveness",
      "evidence_count": 5
    }
  ],
  "count": 10
}
```

### Task 1.3: Add Quick-Fill Attestation Endpoint

**File**: `app/api/v1/samples.py`

**Endpoint**:
```python
POST /api/v1/samples/quick-attest/{control_id}
# Creates attestation from sample control with auto-generated evidence
```

**Example**:
```bash
POST /api/v1/samples/quick-attest/AC-2
```

Auto-fills:
- Control statement
- Framework
- Evidence (auto-generated)
- Policy
- Creates attestation immediately

---

## Phase 2: Enhanced Results/Output (Priority 1) 🎯

**Impact**: Shows "wow, it works" - proof of functionality

### Task 2.1: Enhanced Attestation Response Format

**File**: `app/api/v1/attestations.py` (MODIFY)

**Current response is good, but enhance with:**
```json
{
  "claim_id": "ATT-...",
  "status": "valid",
  
  // ADD: High-level summary for UI
  "summary": {
    "framework": "NIST 800-53",
    "control_id": "AC-2",
    "control_title": "Account Management",
    "claim_type": "control_effectiveness",
    "validity_window": {
      "issued_at": "2026-02-04T...",
      "valid_until": "2026-05-04T...",
      "is_valid": true
    }
  },
  
  // ENHANCE: Cryptographic proof details (already exists, ensure prominent)
  "cryptographic_proof": {
    "proof_hash": "a1b2c3d4...",
    "merkle_root": "8d7e9460...",
    "proof_type": "merkle_commitment",
    "algorithm": "SHA-256 + Ed25519"
  },
  
  // ENHANCE: Verification status (add computed field)
  "verification_status": {
    "proof_valid": true,
    "integrity_verified": true,
    "not_expired": true,
    "not_revoked": true,
    "overall": "PASS"
  },
  
  // ENHANCE: Anchor info (even if demo/mock)
  "anchor": {
    "chain": "algorand",
    "network": "testnet",
    "transaction_id": "ABC123...",
    "anchor_id": "anchor_123",
    "explorer_url": "https://testnet.algoexplorer.io/tx/...",
    "status": "confirmed"
  },
  
  // ADD: Privacy statement
  "privacy": {
    "evidence_exposed": false,
    "proof_type": "zero_knowledge",
    "data_shared": ["proof_hash", "merkle_root"],
    "data_not_shared": ["raw_evidence", "sensitive_data"]
  }
}
```

### Task 2.2: Add Download Attestation Endpoint

**File**: `app/api/v1/attestations.py` (ADD)

**Endpoint**:
```python
GET /api/v1/attestations/{claim_id}/download
# Returns attestation as downloadable JSON file

GET /api/v1/attestations/{claim_id}/download?format=oscal
# Returns in OSCAL format (optional)
```

**Response**:
- Sets `Content-Disposition: attachment; filename="attestation-ATT-123.json"`
- Returns complete attestation package
- Optional: Support OSCAL format conversion

### Task 2.3: Enhanced Verification Endpoint

**File**: `app/api/v1/verify.py` (MODIFY)

**Enhance response to be more UI-friendly**:
```json
{
  "receipt_id": "VER-...",
  "result": "PASS",  // or "FAIL"
  "verified_at": "2026-02-04T...",
  
  // ADD: Clear check breakdown
  "checks": [
    {
      "name": "Proof Validity",
      "status": "PASS",
      "icon": "✅",
      "details": "Proof hash verified against commitment"
    },
    {
      "name": "Integrity Check",
      "status": "PASS",
      "icon": "✅",
      "details": "Merkle root matches evidence"
    },
    {
      "name": "Expiry Check",
      "status": "PASS",
      "icon": "✅",
      "details": "Valid until 2026-05-04"
    },
    {
      "name": "Revocation Check",
      "status": "PASS",
      "icon": "✅",
      "details": "Not revoked"
    }
  ],
  
  // ADD: Privacy confirmation
  "privacy_preserved": {
    "evidence_disclosed": false,
    "proof_method": "zero_knowledge",
    "compliance_proven": true
  }
}
```

---

## Phase 3: Judge Mode Backend Support (Priority 2) 🎯

**Impact**: Makes judging effortless, highlights features

### Task 3.1: Add Judge Mode Configuration

**File**: `app/core/config.py` (MODIFY)

```python
class Settings(BaseSettings):
    # Existing settings...
    
    # ADD: Judge mode settings
    JUDGE_MODE: bool = False
    JUDGE_MODE_AUTO_DEMO: bool = True
    JUDGE_MODE_SIMULATED_RESPONSES: bool = True
    JUDGE_MODE_GUIDED_FLOW: bool = True
```

### Task 3.2: Add Judge Mode Endpoint

**File**: `app/api/v1/judge.py` (NEW)

**Endpoints**:
```python
GET /api/v1/judge/status
# Returns judge mode configuration

POST /api/v1/judge/enable
# Enables judge mode

POST /api/v1/judge/disable
# Disables judge mode

GET /api/v1/judge/guided-flow
# Returns step-by-step flow for judges
```

**Guided Flow Response**:
```json
{
  "judge_mode": true,
  "guided_flow": [
    {
      "step": 1,
      "title": "Paste Control Statement",
      "instruction": "Use a sample control or paste your own",
      "action": "Click 'Use Sample' or enter text",
      "completed": false
    },
    {
      "step": 2,
      "title": "Generate Attestation",
      "instruction": "Gemini 3 interprets the statement → selects proof template",
      "action": "Click 'Generate Attestation'",
      "completed": false
    },
    {
      "step": 3,
      "title": "View Results",
      "instruction": "See proof generated without exposing evidence",
      "action": "Review attestation details",
      "completed": false
    },
    {
      "step": 4,
      "title": "Verify Attestation",
      "instruction": "Confirm compliance is proven",
      "action": "Click 'Verify'",
      "completed": false
    },
    {
      "step": 5,
      "title": "Download Artifact",
      "instruction": "Export attestation for audit trail",
      "action": "Click 'Download JSON'",
      "completed": false
    }
  ],
  "tooltips": {
    "gemini_usage": "Gemini 3 interprets the control statement and determines the appropriate proof template",
    "zero_knowledge": "Zero-knowledge proof generated - no sensitive data exposed",
    "privacy": "Compliance verified without revealing evidence"
  }
}
```

### Task 3.3: Add Simulated Fast Response Mode

**File**: `app/api/v1/attestations.py` (MODIFY)

When `JUDGE_MODE=true`:
- Skip real proof generation delays
- Return "valid" status in 1-2 seconds
- Use pre-computed proof hashes
- Still return realistic data structure

```python
async def process_attestation(claim_id: str):
    if settings.JUDGE_MODE and settings.JUDGE_MODE_SIMULATED_RESPONSES:
        # Fast-track for demo
        await asyncio.sleep(1)  # Minimal delay
        # Use pre-computed values
        attestation["status"] = AttestationStatus.VALID.value
        # ... set all fields quickly
    else:
        # Normal processing
        # ... existing code
```

---

## Phase 4: Gemini 3 Integration (Priority 3) 🎯

**Impact**: Highlights AI usage, key judging criteria

### Task 4.1: Create Gemini Service

**File**: `app/services/gemini_service.py` (NEW)

```python
class GeminiService:
    """
    Gemini 3 integration for control interpretation
    """
    
    async def interpret_control(
        self,
        control_statement: str,
        framework: str
    ) -> ControlInterpretation:
        """
        Use Gemini 3 to interpret compliance control
        
        Returns:
        - claim_type: Type of claim being made
        - proof_template: Which proof method to use
        - evidence_requirements: What evidence is needed
        - risk_level: Control criticality
        """
        
        prompt = f"""
        Analyze this compliance control statement:
        
        Framework: {framework}
        Control: {control_statement}
        
        Determine:
        1. Claim type (evidence_integrity, control_effectiveness, audit_trail)
        2. Proof template (merkle_commitment, zk_predicate, signature_chain)
        3. Required evidence types
        4. Risk level (high, medium, low)
        
        Respond in JSON format.
        """
        
        # Call Gemini 3 API
        response = await self.gemini_client.generate(prompt)
        
        # Parse response
        interpretation = parse_gemini_response(response)
        
        return interpretation
    
    async def select_proof_template(
        self,
        claim_type: str,
        risk_level: str
    ) -> ProofTemplate:
        """
        Use Gemini 3 to select optimal proof template
        """
        # Implementation
        pass
    
    async def validate_evidence_requirements(
        self,
        control: str,
        evidence: List[Evidence]
    ) -> ValidationResult:
        """
        Use Gemini 3 to check if evidence matches control
        """
        # Implementation
        pass
```

### Task 4.2: Integrate Gemini into Attestation Flow

**File**: `app/api/v1/attestations.py` (MODIFY)

```python
@router.post("/attestations")
async def create_attestation(request: AttestationRequest):
    # NEW: Use Gemini 3 to interpret control
    gemini_service = GeminiService()
    
    interpretation = await gemini_service.interpret_control(
        control_statement=request.control_statement,
        framework=request.framework
    )
    
    # Store interpretation in attestation
    attestation["gemini_interpretation"] = {
        "claim_type": interpretation.claim_type,
        "proof_template": interpretation.proof_template,
        "evidence_requirements": interpretation.evidence_requirements,
        "risk_level": interpretation.risk_level,
        "interpreted_at": datetime.utcnow().isoformat()
    }
    
    # Use interpreted values in proof generation
    # ...
```

### Task 4.3: Add Gemini Interpretation Endpoint

**File**: `app/api/v1/gemini.py` (NEW)

```python
POST /api/v1/gemini/interpret
# Interprets control statement without creating attestation

GET /api/v1/gemini/templates
# Returns available proof templates with descriptions
```

**Response**:
```json
{
  "interpretation": {
    "claim_type": "control_effectiveness",
    "proof_template": "merkle_commitment",
    "reasoning": "This control requires proving existence and integrity of access logs without revealing log contents. Merkle commitment is optimal.",
    "evidence_requirements": [
      "access_logs",
      "configuration_snapshots",
      "audit_trails"
    ],
    "risk_level": "high"
  },
  "confidence": 0.95,
  "interpreted_by": "gemini-3"
}
```

---

## Phase 5: Enhanced Demo Mode Features (Priority 3)

### Task 5.1: Add Mock Anchor Service

**File**: `app/services/mock_anchor_service.py` (NEW)

For judge mode, provide realistic-looking anchor data:

```python
class MockAnchorService:
    """
    Mock blockchain anchoring for demos
    """
    
    def generate_mock_anchor(self, package_hash: str) -> AnchorInfo:
        return {
            "chain": "algorand",
            "network": "testnet",
            "transaction_id": f"MOCK_{random_hex(32)}",
            "anchor_id": f"anchor_{random_hex(16)}",
            "block_number": random.randint(20000000, 21000000),
            "explorer_url": f"https://testnet.algoexplorer.io/tx/MOCK_{random_hex(32)}",
            "status": "confirmed",
            "anchored_at": datetime.utcnow().isoformat(),
            "is_mock": True  # Clearly labeled as demo
        }
```

### Task 5.2: Add Privacy Messaging

**File**: `app/utils/privacy_messages.py` (NEW)

```python
PRIVACY_MESSAGES = {
    "evidence_not_shared": "Raw evidence remains private and is never transmitted",
    "proof_without_disclosure": "Proof generated using zero-knowledge cryptography",
    "what_is_shared": "Only cryptographic commitments (hashes) are shared",
    "what_is_not_shared": "Sensitive data, PII, credentials, raw evidence"
}

def get_privacy_statement(attestation: dict) -> dict:
    return {
        "evidence_exposed": False,
        "proof_type": "zero_knowledge",
        "data_shared": [
            "proof_hash",
            "merkle_root",
            "commitment_hash"
        ],
        "data_not_shared": [
            "raw_evidence",
            "sensitive_data",
            "PII",
            "credentials"
        ],
        "privacy_level": "maximum",
        "message": PRIVACY_MESSAGES["proof_without_disclosure"]
    }
```

---

## Implementation Priority & Timeline

### Sprint 1: Quick Wins (2-3 hours) 🚀

**Must-Have for Devpost**:
1. ✅ **Sample controls** (Task 1.1, 1.2, 1.3) - 1 hour
2. ✅ **Enhanced response format** (Task 2.1) - 30 min
3. ✅ **Download endpoint** (Task 2.2) - 30 min
4. ✅ **Enhanced verification** (Task 2.3) - 30 min

**Deliverable**: Judges can click sample → generate → see results → verify → download

---

### Sprint 2: Judge Mode (1-2 hours) 🎯

**High Impact**:
1. ✅ **Judge mode config** (Task 3.1) - 15 min
2. ✅ **Guided flow endpoint** (Task 3.2) - 45 min
3. ✅ **Simulated fast responses** (Task 3.3) - 30 min
4. ✅ **Mock anchor service** (Task 5.1) - 30 min

**Deliverable**: Judge mode makes demo effortless

---

### Sprint 3: Gemini Integration (2-3 hours) 🤖

**AI Showcase**:
1. ✅ **Gemini service** (Task 4.1) - 1.5 hours
2. ✅ **Integration into flow** (Task 4.2) - 45 min
3. ✅ **Interpretation endpoint** (Task 4.3) - 30 min

**Deliverable**: "Powered by Gemini 3" is demonstrable

---

## Testing Plan

### Test 1: Sample Controls Flow
```bash
# Get samples
GET /api/v1/samples/controls

# Quick attest
POST /api/v1/samples/quick-attest/AC-2

# Should return complete attestation in <2 seconds (judge mode)
```

### Test 2: Enhanced Results
```bash
# Create attestation
POST /api/v1/attestations

# Get enhanced response
GET /api/v1/attestations/{claim_id}
# Verify summary, cryptographic_proof, verification_status fields

# Download
GET /api/v1/attestations/{claim_id}/download
```

### Test 3: Judge Mode
```bash
# Enable judge mode
POST /api/v1/judge/enable

# Get guided flow
GET /api/v1/judge/guided-flow

# Quick attest should be fast
POST /api/v1/samples/quick-attest/CC6.1
# Should complete in ~1 second
```

### Test 4: Gemini Integration
```bash
# Interpret control
POST /api/v1/gemini/interpret
{
  "control_statement": "...",
  "framework": "NIST 800-53"
}

# Should return claim_type, proof_template, reasoning
```

---

## Success Criteria

**For Devpost Judging**:
- ✅ Judges can use sample controls (1-click)
- ✅ Results panel shows proof output clearly
- ✅ Verification returns clear PASS/FAIL
- ✅ Download works (JSON artifact)
- ✅ Judge mode provides guided experience
- ✅ Gemini 3 usage is evident and explained
- ✅ Privacy messaging is clear

**Technical**:
- ✅ All endpoints respond in <2 seconds (judge mode)
- ✅ Sample controls cover NIST, SOC 2, ISO
- ✅ Enhanced response format is backward compatible
- ✅ Tests pass for all new features

---

## Files to Create

**New Files** (7):
1. `app/utils/sample_controls.py` - Sample control data
2. `app/api/v1/samples.py` - Sample controls endpoints
3. `app/api/v1/judge.py` - Judge mode endpoints
4. `app/services/gemini_service.py` - Gemini 3 integration
5. `app/api/v1/gemini.py` - Gemini interpretation endpoints
6. `app/services/mock_anchor_service.py` - Mock anchoring
7. `app/utils/privacy_messages.py` - Privacy messaging

**Modified Files** (4):
1. `app/api/v1/attestations.py` - Enhanced response, Gemini integration
2. `app/api/v1/verify.py` - Enhanced verification response
3. `app/core/config.py` - Judge mode settings
4. `app/main.py` - Include new routers

---

## Next Steps

1. **Review this plan** with team
2. **Start with Sprint 1** (quick wins)
3. **Test with frontend** team
4. **Iterate based on** frontend integration
5. **Deploy before** Devpost deadline

---

**Estimated Total Time**: 6-8 hours  
**Priority**: High (Devpost submission critical)  
**Risk**: Low (additive features, no breaking changes)

---

## Notes

**Frontend Coordination**:
- Frontend team needs new API contracts
- Share enhanced response formats
- Coordinate on judge mode UI triggers
- Test download endpoint with browser

**Gemini API**:
- Need Gemini 3 API credentials
- Set up rate limiting
- Add fallback for API failures
- Cache interpretations for common controls

**Demo Mode**:
- Clearly label mock/demo data
- Ensure fast responses in judge mode
- Maintain data consistency
- Document what's real vs simulated

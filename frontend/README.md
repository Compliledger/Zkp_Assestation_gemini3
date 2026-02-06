# ZKPA Demo - Zero-Knowledge Proof Attestation Agent

A public interactive demo for the **ZKP Attestation Agent (ZKPA)** hackathon project. This frontend allows judges to generate and verify zero-knowledge attestations without requiring login.

## 🎯 What This Demo Does

Judges can:
1. **Paste or select** a compliance requirement / control statement
2. **Click "Generate Attestation"** to create a ZK proof
3. **See outputs**: `claim_id`, `proof_id`, `attestation.json`, verification result (PASS/FAIL)
4. **Read** a plain-English explanation of what was proven without revealing private evidence

## ✨ Features

### Core Functionality
- **Single-page demo** - No auth, no navigation complexity
- **Sample requirements** - Pre-loaded NIST 800-53, ISO 27001, and custom policy examples
- **Real-time progress** - Visual stepper showing Commit → Prove → Verify → Anchor stages
- **Tabbed output** - Verification checks, JSON artifact (with download), Proof IDs (with copy)

### Creative Polish
- **Judge Mode** toggle - Simplifies UI to just the happy path
- **Proof Timeline** - Mini-stepper showing progress states with animations
- **Privacy Meter** badge - "No raw evidence shown ✅"
- **Shareable result link** - URL with claim_id for reloading results
- **Copy buttons** - One-click copy for claim_id, proof_id, JSON
- **Auto Demo** button - Loads sample + auto-runs generation
- **Auditor vs Engineer** toggle - Changes explanation formatting

### Error Handling
- Backend unreachable → "Service unavailable" + retry
- Timeout after 45s → "Still processing" + continue polling
- Validation → Button disabled until input >10 chars
- Failed status → Shows server error message

## 🛠 Tech Stack

- **React 18** + TypeScript
- **Vite** for fast builds
- **Tailwind CSS** + shadcn/ui components
- **Dark mode** cryptographic aesthetic

## 🚀 Local Development

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build
```

## ⚙️ Configuration

Create a `.env` file (or set environment variables):

```env
# Backend API base URL (leave empty for demo mode with mock responses)
VITE_API_BASE=https://your-backend.example.com

# Optional demo key for backend authentication
VITE_DEMO_KEY=your-demo-key
```

### Demo Mode
If `VITE_API_BASE` is not set, the app runs in **demo mode** with simulated responses. This is perfect for showcasing the UI without a live backend.

## 📡 Backend API Contract

The demo expects these endpoints:

### POST `${API_BASE}/demo/attest`
**Request:**
```json
{
  "requirement_text": "The organization manages system accounts...",
  "framework": "NIST_800_53"
}
```

**Response:**
```json
{
  "claim_id": "claim_123",
  "proof_id": "proof_456",
  "status": "pending|ready|failed",
  "attestation": { ... },
  "verification": {
    "result": "valid|invalid",
    "checks_passed": ["Proof structure valid", ...]
  },
  "explanation": "This attestation proves..."
}
```

### GET `${API_BASE}/demo/attest/{claim_id}`
Returns the same response structure. Poll every 2s while `status === "pending"` (max 45s).

### Authentication
If `VITE_DEMO_KEY` is set, requests include header: `X-DEMO-KEY: <key>`

## 🎬 Demo Recording Script (60 seconds)

1. **0:00** - "This is ZKPA, a zero-knowledge proof attestation agent."
2. **0:08** - Click sample button (AC-2) to load requirement
3. **0:12** - "We're attesting to this NIST 800-53 control"
4. **0:15** - Click "Generate Attestation"
5. **0:18** - "Watch the proof generation timeline..."
6. **0:25** - Results appear - "VERIFIED! All 5 checks passed"
7. **0:30** - Show Verification tab - "Cryptographic verification without exposing evidence"
8. **0:38** - Show Artifact tab - "Full attestation JSON, downloadable"
9. **0:45** - Show Proof IDs tab - "Unique identifiers for audit trails"
10. **0:50** - Read explanation - "Privacy-safe summary for auditors"
11. **0:55** - Toggle "Engineer" mode - "Technical details for developers"
12. **0:58** - "Zero-knowledge compliance attestation. Thank you!"

## 📁 Project Structure

```
src/
├── components/
│   └── zkpa/
│       ├── Header.tsx         # Nav + Judge Mode toggle
│       ├── InputBlock.tsx     # Requirement textarea + framework select
│       ├── ActionBlock.tsx    # Generate button + timeline
│       ├── OutputBlock.tsx    # Tabs: Verification, Artifact, IDs
│       ├── ExplanationBlock.tsx  # Privacy summary + mode toggle
│       ├── ProofTimeline.tsx  # Progress stepper
│       └── ErrorState.tsx     # Error display + retry
├── hooks/
│   └── useAttestation.ts      # API logic + polling + mock responses
├── types/
│   └── zkpa.ts                # TypeScript interfaces
└── pages/
    └── ZKPADemo.tsx           # Main demo page
```

## 🔐 Assumptions Made

- Backend handles all ZK proof generation (this is frontend-only)
- Demo mode provides realistic mock responses for UI testing
- No user authentication required for public demo access
- All sensitive evidence remains server-side; only proofs are transmitted

## 📄 License

MIT - Built for hackathon demonstration purposes.

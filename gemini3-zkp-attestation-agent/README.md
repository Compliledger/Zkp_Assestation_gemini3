# ZKP Attestation Agent (Hackathon Demo Repo)

This repo is a **hackathon-packaged subset** of the internal `ZKP-Agent-main` workspace, containing only what’s needed to run the demo end-to-end.

## What it does

Pipeline:
1. Collect mock evidence and hash it (SHA-256)
2. Build a Merkle tree commitment (Merkle root)
3. Assemble an attestation package (ZKPA v1.1 format)
4. (Optional) Anchor the attestation on Algorand TestNet
5. Verify results (local + on-chain verification scripts)

## Gemini 3 integration (status)

There is **no Gemini integration present in this codebase** at the moment (no client wrapper, no prompts, no parsing/validation).

If you want the repo to meet the “Gemini 3 usage” judging checklist, you need to either:
- **Provide the existing Gemini module** you want included, or
- Allow me to add a **minimal Gemini wrapper + prompt** (small amount of new code).

## 🚀 Quick Start (Demo Mode)

### 1. Setup

```bash
# Clone repository
git clone https://github.com/Compliledger/Zkp_Assestation_gemini3.git
cd Zkp_Assestation_gemini3/gemini3-zkp-attestation-agent

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Mac/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file (demo mode is already enabled)
cp .env.example .env
```

### 2. Start the API Server

```bash
# Start with auto-reload
python -m uvicorn app.main:app --reload

# Server runs on http://localhost:8000
```

### 3. Test the API

**Option A: Interactive Demo Script** (Recommended)
```bash
python scripts/interactive_demo.py

# Interactive menu with 7 demo scenarios
# - Quick attestation
# - Available policies
# - Test scenarios
# - Verification demo
# - Full workflow
```

**Option B: Swagger UI**
```bash
# Open in browser
http://localhost:8000/docs

# Navigate to "Demo & Testing" section
# Try POST /api/v1/demo/quick
```

**Option C: Quick Test Script**
```bash
python scripts/test_api_flow.py

# Runs complete end-to-end tests:
# - Health checks
# - Attestation creation
# - Status polling
# - Verification
# - Idempotency
```

### 4. Quick Demo API Examples

**Create Attestation with Auto-Generated Evidence**:
```bash
curl -X POST http://localhost:8000/api/v1/demo/quick \
  -H "Content-Type: application/json" \
  -d '{
    "policy": "SOC2_TYPE_II",
    "evidence_count": 5
  }'

# Response:
# {
#   "claim_id": "ATT-20260204-ABC123",
#   "status": "pending",
#   "message": "Quick demo attestation created with auto-generated evidence"
# }
```

**Get Attestation Status**:
```bash
curl http://localhost:8000/api/v1/attestations/ATT-20260204-ABC123
```

**Verify Attestation**:
```bash
curl -X POST http://localhost:8000/api/v1/verify \
  -H "Content-Type: application/json" \
  -d '{
    "claim_id": "ATT-20260204-ABC123",
    "check_expiry": true,
    "check_revocation": true
  }'
```

**View Available Policies**:
```bash
curl http://localhost:8000/api/v1/demo/policies
```

**Get Statistics**:
```bash
curl http://localhost:8000/api/v1/demo/stats
```

### 4) JWT for calling protected endpoints

Most endpoints require a Bearer token. For local demo you can generate one like:

```bash
python -c "from app.core.auth import create_token_for_user; print(create_token_for_user('judge','demo',['zkpa:admin']))"
```

Paste the token into Swagger UI via **Authorize**.

## Samples

See `samples/` for example output JSON artifacts from the workflow.

## Privacy / No-secrets

- This repo is designed to be **public hackathon-safe** and uses **mock/demo evidence**.
- Do **not** commit `.env` files or real credentials/mnemonics. Use `.env.example` as a template.
- If you enable Algorand anchoring, use a **TestNet** account and fund it via the TestNet dispenser.

## 🚀 Deploy to Railway

**Quick Deploy**: [![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/Compliledger/Zkp_Assestation_gemini3)

**Manual Deployment**: See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for complete deployment guide.

**Key Steps**:
1. Add PostgreSQL database in Railway
2. Set required environment variables (JWT_SECRET, ENCRYPTION_KEY)
3. Deploy from GitHub repository
4. Access at: `https://your-app.railway.app/docs`

## Demo link (for Devpost)

- Railway deployment: See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)
- Swagger UI at `/docs` is accessible once deployed

## Repo layout

```
.
├── app/                 # FastAPI service code
├── scripts/             # End-to-end demo scripts
├── samples/             # Example inputs/outputs
├── requirements.txt
├── .env.example
└── Procfile             # Handy for deployment
```
```bash
python scripts/demo_attestation_workflow.py
```

### 4) JWT for calling protected endpoints

Most endpoints require a Bearer token. For local demo you can generate one like:

```bash
python -c "from app.core.auth import create_token_for_user; print(create_token_for_user('judge','demo',['zkpa:admin']))"
```

Paste the token into Swagger UI via **Authorize**.

## Samples

See `samples/` for example output JSON artifacts from the workflow.

## Privacy / No-secrets

- This repo is designed to be **public hackathon-safe** and uses **mock/demo evidence**.
- Do **not** commit `.env` files or real credentials/mnemonics. Use `.env.example` as a template.
- If you enable Algorand anchoring, use a **TestNet** account and fund it via the TestNet dispenser.

## 🚀 Deploy to Railway

**Quick Deploy**: [![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/Compliledger/Zkp_Assestation_gemini3)

**Manual Deployment**: See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for complete deployment guide.

**Key Steps**:
1. Add PostgreSQL database in Railway
2. Set required environment variables (JWT_SECRET, ENCRYPTION_KEY)
3. Deploy from GitHub repository
4. Access at: `https://your-app.railway.app/docs`

## Demo link (for Devpost)

- Railway deployment: See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)
- Swagger UI at `/docs` is accessible once deployed

## Repo layout

```
.
├── app/                 # FastAPI service code
├── scripts/             # End-to-end demo scripts
├── samples/             # Example inputs/outputs
├── requirements.txt
├── .env.example
└── Procfile             # Handy for deployment
```

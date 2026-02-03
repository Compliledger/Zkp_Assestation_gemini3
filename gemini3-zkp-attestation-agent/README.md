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

## Run locally

### 1) Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2) Start the API (Swagger UI)

This service uses Postgres by default. For local dev, set `DATABASE_URL` in `.env`.

```bash
uvicorn app.main:app --reload --port 8000
```

Open:
- `http://localhost:8000/docs`

### 3) Quick demo (no API required)

This runs Steps 1–4 locally and prints a complete attestation package:

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

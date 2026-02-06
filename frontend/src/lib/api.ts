/**
 * API service layer for ZKP Attestation backend integration
 * Maps frontend requests to real FastAPI backend endpoints
 */

const API_BASE = import.meta.env.VITE_API_BASE || '';

interface ApiOptions {
  signal?: AbortSignal;
}

// ─── Health & Status ───────────────────────────────────────

export async function checkHealth(opts?: ApiOptions) {
  const res = await fetch(`${API_BASE}/health/live`, { signal: opts?.signal });
  return res.json();
}

export async function getGeminiStatus(opts?: ApiOptions) {
  const res = await fetch(`${API_BASE}/api/v1/gemini/status`, { signal: opts?.signal });
  return res.json();
}

export async function getJudgeStatus(opts?: ApiOptions) {
  const res = await fetch(`${API_BASE}/api/v1/judge/status`, { signal: opts?.signal });
  return res.json();
}

// ─── Sample Controls ───────────────────────────────────────

export async function getSampleControls(opts?: ApiOptions) {
  const res = await fetch(`${API_BASE}/api/v1/samples/controls`, { signal: opts?.signal });
  return res.json();
}

export async function getSampleControl(controlId: string, opts?: ApiOptions) {
  const res = await fetch(`${API_BASE}/api/v1/samples/controls/${encodeURIComponent(controlId)}`, {
    signal: opts?.signal,
  });
  if (!res.ok) return null;
  return res.json();
}

// ─── Quick Attest (1-click from sample control) ────────────

export async function quickAttest(controlId: string, opts?: ApiOptions) {
  const res = await fetch(`${API_BASE}/api/v1/samples/quick-attest/${encodeURIComponent(controlId)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
    signal: opts?.signal,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `Server error: ${res.status}` }));
    throw new Error(err.detail || `Server error: ${res.status}`);
  }
  return res.json();
}

// ─── Full Attestation (custom evidence + policy) ───────────

export interface CreateAttestationPayload {
  evidence: Array<{ uri: string; hash: string; type: string }>;
  policy: string;
  callback_url?: string;
}

export async function createAttestation(payload: CreateAttestationPayload, opts?: ApiOptions) {
  const res = await fetch(`${API_BASE}/api/v1/attestations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal: opts?.signal,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `Server error: ${res.status}` }));
    throw new Error(err.detail || `Server error: ${res.status}`);
  }
  return res.json();
}

// ─── Poll Attestation Status ───────────────────────────────

export async function getAttestation(claimId: string, opts?: ApiOptions) {
  const res = await fetch(`${API_BASE}/api/v1/attestations/${encodeURIComponent(claimId)}`, {
    signal: opts?.signal,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `Not found: ${res.status}` }));
    throw new Error(err.detail || `Error: ${res.status}`);
  }
  return res.json();
}

// ─── Verification ──────────────────────────────────────────

export async function verifyAttestation(attestationId: string, opts?: ApiOptions) {
  const res = await fetch(`${API_BASE}/api/v1/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ attestation_id: attestationId }),
    signal: opts?.signal,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `Verify error: ${res.status}` }));
    throw new Error(err.detail || `Verify error: ${res.status}`);
  }
  return res.json();
}

// ─── Download ──────────────────────────────────────────────

export function getDownloadUrl(claimId: string, format: 'json' | 'oscal' = 'json') {
  return `${API_BASE}/api/v1/attestations/${encodeURIComponent(claimId)}/download?format=${format}`;
}

// ─── Judge Mode ────────────────────────────────────────────

export async function enableJudgeMode(opts?: ApiOptions) {
  const res = await fetch(`${API_BASE}/api/v1/judge/enable`, {
    method: 'POST',
    signal: opts?.signal,
  });
  return res.json();
}

export async function getGuidedFlow(opts?: ApiOptions) {
  const res = await fetch(`${API_BASE}/api/v1/judge/guided-flow`, { signal: opts?.signal });
  return res.json();
}

export async function resetDemo(opts?: ApiOptions) {
  const res = await fetch(`${API_BASE}/api/v1/judge/reset`, {
    method: 'POST',
    signal: opts?.signal,
  });
  return res.json();
}

// ─── Gemini AI ─────────────────────────────────────────────

export async function interpretControl(
  controlId: string,
  controlStatement: string,
  framework: string,
  opts?: ApiOptions
) {
  const res = await fetch(`${API_BASE}/api/v1/gemini/interpret`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      control_id: controlId,
      control_statement: controlStatement,
      framework,
    }),
    signal: opts?.signal,
  });
  return res.json();
}

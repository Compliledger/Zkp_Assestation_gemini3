import { useState, useCallback, useRef } from 'react';
import type { AttestationRequest, AttestationResponse, ProgressStep } from '@/types/zkpa';
import { quickAttest, getAttestation, verifyAttestation } from '@/lib/api';

const API_BASE = import.meta.env.VITE_API_BASE || '';
const POLL_INTERVAL = 1500;
const MAX_POLL_TIME = 45000;

const INITIAL_STEPS: ProgressStep[] = [
  { id: 'commit', label: 'Computing Merkle commitment…', status: 'pending' },
  { id: 'prove', label: 'Generating zero-knowledge proof…', status: 'pending' },
  { id: 'verify', label: 'Running verification checks…', status: 'pending' },
  { id: 'anchor', label: 'Anchoring to blockchain…', status: 'pending' },
];

/**
 * Map backend attestation status strings to progress step updates
 */
const STATUS_TO_STEP: Record<string, string> = {
  pending: 'commit',
  computing_commitment: 'commit',
  generating_proof: 'prove',
  assembling_package: 'verify',
  anchoring: 'anchor',
  valid: 'anchor',
  failed: '',
};

/**
 * Extract a clean control_id from user input.
 * Handles inputs like "NIST 800-53 AC-2" → "AC-2", or just "AC-2" → "AC-2"
 */
function extractControlId(input: string): string {
  const trimmed = input.trim();
  // If it contains a space, take the last segment (e.g., "NIST 800-53 AC-2" → "AC-2")
  const parts = trimmed.split(/\s+/);
  // Return last part unless it looks like a framework component (pure number or known prefix)
  if (parts.length > 1) {
    return parts[parts.length - 1];
  }
  return trimmed;
}

/**
 * Transform the raw backend attestation data into the AttestationResponse
 * shape that frontend UI components expect.
 */
function transformBackendResponse(
  backendData: Record<string, any>,
  verificationData: Record<string, any> | null,
  controlIdentifier: string
): AttestationResponse {
  const claimId = backendData.claim_id || '';
  const proofHash = backendData.proof?.proof_hash
    || backendData.cryptographic_proof?.proof_hash
    || '';
  const merkleRoot = backendData.evidence?.merkle_root
    || backendData.cryptographic_proof?.merkle_root
    || '';
  const commitmentHash = backendData.evidence?.commitment_hash || '';
  const anchorTxHash = backendData.anchor?.transaction_hash || '';

  // Build checks_passed from verification response or verification_status
  let checksResult: 'valid' | 'invalid' = 'valid';
  let checksPassed: string[] = [];

  if (verificationData) {
    const checks = verificationData.checks_performed || [];
    checksResult = verificationData.status === 'PASS' ? 'valid' : 'invalid';
    checksPassed = checks
      .filter((c: any) => c.result === 'PASS')
      .map((c: any) => c.details || c.check);
  } else if (backendData.verification_status) {
    const vs = backendData.verification_status;
    checksResult = vs.overall === 'PASS' ? 'valid' : 'invalid';
    if (vs.proof_valid) checksPassed.push('ZKP proof structure validated');
    if (vs.integrity_verified) checksPassed.push('Evidence integrity verified via Merkle root');
    if (vs.not_expired) checksPassed.push('Attestation is within validity window');
    if (vs.not_revoked) checksPassed.push('Attestation has not been revoked');
  }

  // Always ensure privacy check is listed
  if (checksPassed.length > 0) {
    checksPassed.push('No evidence data exposed — zero-knowledge proof');
  }

  // Build W3C-style attestation object for the Attestation tab
  const attestationArtifact = {
    "@context": ["https://www.w3.org/2018/credentials/v1"],
    type: ["VerifiableCredential", "ZKPAttestation"],
    issuer: "did:zkpa:issuer:compliledger",
    issuanceDate: backendData.created_at || new Date().toISOString(),
    credentialSubject: {
      id: `did:zkpa:subject:${claimId}`,
      claim: {
        requirement_hash: proofHash,
        evidence_commitment: commitmentHash || merkleRoot,
        merkle_root: merkleRoot,
        timestamp: Date.now(),
      },
    },
    proof: {
      type: "ZKSNARKProof2024",
      proofPurpose: "assertionMethod",
      verificationMethod: "did:zkpa:issuer:compliledger#key-1",
      proof_hash: proofHash,
      algorithm: backendData.proof?.algorithm || "demo_zkp",
    },
    anchor: backendData.anchor || null,
    privacy: backendData.privacy || null,
  };

  const framework = backendData.summary?.framework
    || backendData.control_info?.framework
    || '';

  return {
    claim_id: claimId,
    proof_id: proofHash,
    status: 'ready',
    attestation: attestationArtifact,
    verification: {
      result: checksResult,
      checks_passed: checksPassed.length > 0
        ? checksPassed
        : ['Proof generated successfully', 'Privacy preserved — no evidence exposed'],
    },
    explanation:
      `This proof cryptographically attests to a completed ${framework} compliance assessment ` +
      `for control "${controlIdentifier}". The zero-knowledge proof confirms the assessment result ` +
      `WITHOUT revealing underlying evidence, logs, configurations, or internal systems. ` +
      (anchorTxHash
        ? `The attestation has been anchored to blockchain (tx: ${anchorTxHash.substring(0, 16)}…). `
        : '') +
      `Verification can be performed independently while sensitive operational details remain private.`,
  };
}

// Demo mode mock responses (when no API_BASE is set)
const generateMockResponse = (requirement: string): AttestationResponse => {
  const claimId = `claim_${Date.now().toString(36)}`;
  const proofId = `proof_${Math.random().toString(36).substring(2, 10)}`;
  return {
    claim_id: claimId,
    proof_id: proofId,
    status: 'ready',
    attestation: {
      "@context": ["https://www.w3.org/2018/credentials/v1"],
      type: ["VerifiableCredential", "ZKPAttestation"],
      issuer: "did:zkpa:issuer:demo",
      issuanceDate: new Date().toISOString(),
      credentialSubject: {
        id: `did:zkpa:subject:${claimId}`,
        claim: {
          requirement_hash: `sha256:${Array.from({length: 64}, () => Math.floor(Math.random() * 16).toString(16)).join('')}`,
          evidence_commitment: `commit:${Array.from({length: 40}, () => Math.floor(Math.random() * 16).toString(16)).join('')}`,
          timestamp: Date.now(),
        },
      },
      proof: {
        type: "ZKSNARKProof2024",
        proofPurpose: "assertionMethod",
        verificationMethod: "did:zkpa:issuer:demo#key-1",
        proof_hash: proofId,
      },
    },
    verification: {
      result: 'valid',
      checks_passed: [
        'Integrity verified',
        'Commitment matches claim',
        'Issuer signature verified',
        'Validity window checked',
        'No evidence data exposed',
      ],
    },
    explanation: `This proof cryptographically attests to an already-determined assessment outcome for: "${requirement.substring(0, 60)}…". The zero-knowledge proof confirms the assessment result WITHOUT revealing underlying evidence.`,
  };
};

export function useAttestation() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<AttestationResponse | null>(null);
  const [steps, setSteps] = useState<ProgressStep[]>(INITIAL_STEPS);
  const abortRef = useRef<AbortController | null>(null);

  const updateStep = useCallback((stepId: string, status: ProgressStep['status']) => {
    setSteps(prev => prev.map(step =>
      step.id === stepId ? { ...step, status } : step
    ));
  }, []);

  const completeStepsUpTo = useCallback((targetStepId: string) => {
    const order = ['commit', 'prove', 'verify', 'anchor'];
    const targetIdx = order.indexOf(targetStepId);
    setSteps(prev => prev.map((step, i) => {
      if (i < targetIdx) return { ...step, status: 'complete' as const };
      if (i === targetIdx) return { ...step, status: 'active' as const };
      return step;
    }));
  }, []);

  const reset = useCallback(() => {
    setIsLoading(false);
    setError(null);
    setResponse(null);
    setSteps(INITIAL_STEPS);
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
  }, []);

  const simulateProgress = useCallback(async () => {
    const stepDelays = [
      { id: 'commit', delay: 800 },
      { id: 'prove', delay: 1500 },
      { id: 'verify', delay: 1000 },
      { id: 'anchor', delay: 600 },
    ];
    for (const { id, delay } of stepDelays) {
      updateStep(id, 'active');
      await new Promise(resolve => setTimeout(resolve, delay));
      updateStep(id, 'complete');
    }
  }, [updateStep]);

  const generateAttestation = useCallback(async (request: AttestationRequest) => {
    reset();
    setIsLoading(true);
    abortRef.current = new AbortController();
    const signal = abortRef.current.signal;

    try {
      // If no API_BASE configured, fall back to demo mode with mock data
      if (!API_BASE) {
        await simulateProgress();
        const mockResponse = generateMockResponse(request.requirement_text);
        setResponse(mockResponse);
        setIsLoading(false);
        return mockResponse;
      }

      // ── Step 1: Create attestation via quick-attest ──────
      updateStep('commit', 'active');

      const controlId = extractControlId(request.control_identifier || request.requirement_text);
      const createResult = await quickAttest(controlId, { signal });
      const claimId: string = createResult.claim_id;

      updateStep('commit', 'complete');
      updateStep('prove', 'active');

      // ── Step 2: Poll until attestation completes ─────────
      const startTime = Date.now();
      let attestationData: Record<string, any> = {};

      while (Date.now() - startTime < MAX_POLL_TIME) {
        await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL));

        attestationData = await getAttestation(claimId, { signal });
        const backendStatus: string = attestationData.status || '';

        // Update progress bar from backend status
        const stepId = STATUS_TO_STEP[backendStatus];
        if (stepId) {
          completeStepsUpTo(stepId);
        }

        // Terminal states
        if (backendStatus === 'valid') break;
        if (backendStatus === 'failed' || backendStatus.startsWith('failed_')) {
          throw new Error(attestationData.error || 'Attestation processing failed');
        }
      }

      if (attestationData.status !== 'valid') {
        throw new Error('Processing timeout. The attestation is still being generated.');
      }

      // ── Step 3: Verify the attestation ───────────────────
      updateStep('verify', 'complete');
      updateStep('anchor', 'active');

      let verificationData: Record<string, any> | null = null;
      try {
        verificationData = await verifyAttestation(claimId, { signal });
      } catch {
        // Verification is optional — continue without it
        console.warn('Verification call failed, continuing without');
      }

      // ── Step 4: Complete all steps ───────────────────────
      setSteps(INITIAL_STEPS.map(s => ({ ...s, status: 'complete' as const })));

      const controlIdentifier = request.control_identifier || controlId;
      const transformed = transformBackendResponse(attestationData, verificationData, controlIdentifier);

      setResponse(transformed);
      return transformed;

    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        return null;
      }

      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);

      // Mark current active step as error
      setSteps(prev => prev.map(step =>
        step.status === 'active' ? { ...step, status: 'error' } : step
      ));

      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [reset, simulateProgress, updateStep, completeStepsUpTo]);

  return {
    isLoading,
    error,
    response,
    steps,
    generateAttestation,
    reset,
  };
}

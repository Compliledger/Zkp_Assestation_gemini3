import { useState, useCallback, useRef } from 'react';
import type { AttestationRequest, AttestationResponse, AttestationStatus, ProgressStep } from '@/types/zkpa';

const API_BASE = import.meta.env.VITE_API_BASE || '';
const DEMO_KEY = import.meta.env.VITE_DEMO_KEY || '';
const POLL_INTERVAL = 2000;
const MAX_POLL_TIME = 45000;

const INITIAL_STEPS: ProgressStep[] = [
  { id: 'commit', label: 'Normalizing assessment claim…', status: 'pending' },
  { id: 'prove', label: 'Generating verifiable credential…', status: 'pending' },
  { id: 'verify', label: 'Creating zero-knowledge proof…', status: 'pending' },
  { id: 'anchor', label: 'Finalizing attestation…', status: 'pending' },
];

// Demo mode mock responses
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
    explanation: `This proof cryptographically attests to an already-determined assessment outcome for: "${requirement.substring(0, 60)}...". The zero-knowledge proof confirms the assessment result WITHOUT revealing underlying evidence, logs, configurations, or internal systems. Verification can be performed independently while sensitive operational details remain private.`,
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

    try {
      // If no API_BASE configured, use demo mode
      if (!API_BASE) {
        await simulateProgress();
        const mockResponse = generateMockResponse(request.requirement_text);
        setResponse(mockResponse);
        setIsLoading(false);
        return mockResponse;
      }

      // Real API call
      updateStep('commit', 'active');
      
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      if (DEMO_KEY) {
        headers['X-DEMO-KEY'] = DEMO_KEY;
      }

      const initialResponse = await fetch(`${API_BASE}/demo/attest`, {
        method: 'POST',
        headers,
        body: JSON.stringify(request),
        signal: abortRef.current.signal,
      });

      if (!initialResponse.ok) {
        throw new Error(`Server error: ${initialResponse.status}`);
      }

      let data: AttestationResponse = await initialResponse.json();
      updateStep('commit', 'complete');
      updateStep('prove', 'active');

      // Poll if pending
      const startTime = Date.now();
      while (data.status === 'pending' && Date.now() - startTime < MAX_POLL_TIME) {
        await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL));
        
        const pollResponse = await fetch(`${API_BASE}/demo/attest/${data.claim_id}`, {
          headers,
          signal: abortRef.current.signal,
        });
        
        if (!pollResponse.ok) {
          throw new Error(`Polling error: ${pollResponse.status}`);
        }
        
        data = await pollResponse.json();
        
        // Update progress based on response hints or time elapsed
        const elapsed = Date.now() - startTime;
        if (elapsed > 3000) {
          updateStep('prove', 'complete');
          updateStep('verify', 'active');
        }
        if (elapsed > 6000) {
          updateStep('verify', 'complete');
          updateStep('anchor', 'active');
        }
      }

      if (data.status === 'pending') {
        throw new Error('Processing timeout. The attestation is still being generated.');
      }

      if (data.status === 'failed') {
        throw new Error(data.error || 'Attestation generation failed');
      }

      // Complete all steps
      setSteps(INITIAL_STEPS.map(s => ({ ...s, status: 'complete' as const })));
      setResponse(data);
      return data;

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
  }, [reset, simulateProgress, updateStep]);

  return {
    isLoading,
    error,
    response,
    steps,
    generateAttestation,
    reset,
  };
}

export type Framework = 'NIST_800_53' | 'ISO_27001' | 'SOC2' | 'HIPAA' | 'PCI_DSS' | 'CUSTOM';

export type AssessmentResult = 'PASS' | 'FAIL' | 'PARTIAL';

export type AttestationStatus = 'pending' | 'ready' | 'failed';

export type VerificationResult = 'valid' | 'invalid';

export interface AttestationRequest {
  requirement_text: string;
  framework: Framework;
  control_identifier?: string;
  assessment_result?: AssessmentResult;
  assessment_window?: string;
}

export interface AttestationResponse {
  claim_id: string;
  proof_id: string;
  status: AttestationStatus;
  attestation: Record<string, unknown>;
  verification: {
    result: VerificationResult;
    checks_passed: string[];
  };
  explanation: string;
  error?: string;
}

export interface ProgressStep {
  id: string;
  label: string;
  status: 'pending' | 'active' | 'complete' | 'error';
}

/** Backend control IDs that map to quick-attest */
export const SAMPLE_REQUIREMENTS = [
  {
    id: 'AC-2',
    name: 'AC-2 Account Management',
    framework: 'NIST_800_53' as Framework,
    text: 'AC-2',
  },
  {
    id: 'AC-3',
    name: 'AC-3 Access Enforcement',
    framework: 'NIST_800_53' as Framework,
    text: 'AC-3',
  },
  {
    id: 'CC6.1',
    name: 'CC6.1 Logical Access Security',
    framework: 'SOC2' as Framework,
    text: 'CC6.1',
  },
  {
    id: 'A.5.15',
    name: 'A.5.15 Access Control',
    framework: 'ISO_27001' as Framework,
    text: 'A.5.15',
  },
  {
    id: '164.308(a)(1)(ii)(D)',
    name: 'HIPAA Security Management',
    framework: 'HIPAA' as Framework,
    text: '164.308(a)(1)(ii)(D)',
  },
  {
    id: 'PCI-10.2',
    name: 'PCI-DSS Audit Trails',
    framework: 'PCI_DSS' as Framework,
    text: 'PCI-10.2',
  },
];

export const FRAMEWORK_OPTIONS = [
  { value: 'NIST_800_53', label: 'NIST 800-53' },
  { value: 'ISO_27001', label: 'ISO 27001' },
  { value: 'SOC2', label: 'SOC 2' },
  { value: 'HIPAA', label: 'HIPAA' },
  { value: 'PCI_DSS', label: 'PCI-DSS' },
  { value: 'CUSTOM', label: 'Custom' },

];

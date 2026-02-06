export type Framework = 'NIST_800_53' | 'ISO_27001' | 'SOC2' | 'CUSTOM';

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

export const SAMPLE_REQUIREMENTS = [
  {
    id: 'ac-2',
    name: 'AC-2 Account Management',
    framework: 'NIST_800_53' as Framework,
    text: 'NIST 800-53 AC-2',
  },
  {
    id: 'iso-vuln',
    name: 'ISO 27001 Vulnerability Management',
    framework: 'ISO_27001' as Framework,
    text: 'ISO 27001 A.12.6.1',
  },
  {
    id: 'threshold',
    name: 'Threshold Policy Compliance',
    framework: 'CUSTOM' as Framework,
    text: 'CUSTOM CONTROL-001',
  },
];

export const FRAMEWORK_OPTIONS = [
  { value: 'NIST_800_53', label: 'NIST 800-53' },
  { value: 'ISO_27001', label: 'ISO 27001' },
  { value: 'SOC2', label: 'SOC 2' },
  { value: 'CUSTOM', label: 'Custom' },
];

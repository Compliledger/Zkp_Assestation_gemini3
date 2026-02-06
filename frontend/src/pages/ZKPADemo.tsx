import React, { useState, useCallback, useEffect } from 'react';
import { Header } from '@/components/zkpa/Header';
import { InputBlock } from '@/components/zkpa/InputBlock';
import { ActionBlock } from '@/components/zkpa/ActionBlock';
import { OutputBlock } from '@/components/zkpa/OutputBlock';
import { ExplanationBlock } from '@/components/zkpa/ExplanationBlock';
import { ErrorState } from '@/components/zkpa/ErrorState';
import { useAttestation } from '@/hooks/useAttestation';
import { SAMPLE_REQUIREMENTS, type AssessmentResult, type Framework } from '@/types/zkpa';
import { useSearchParams } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { Lock, Shield, Zap } from 'lucide-react';

const ZKPADemo: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [judgeMode, setJudgeMode] = useState(false);
  const [controlIdentifier, setControlIdentifier] = useState('');
  const [framework, setFramework] = useState<Framework>('NIST_800_53');
  const [assessmentResult, setAssessmentResult] = useState<AssessmentResult>('PASS');
  const [assessmentWindow, setAssessmentWindow] = useState('');
  
  const { 
    isLoading, 
    error, 
    response, 
    steps, 
    generateAttestation, 
    reset 
  } = useAttestation();

  // Handle shareable URL with claim_id
  useEffect(() => {
    const claimId = searchParams.get('claim_id');
    if (claimId) {
      console.log('Loading attestation for claim:', claimId);
    }
  }, [searchParams]);

  const handleGenerate = useCallback(async () => {
    if (!controlIdentifier.trim()) return;

    try {
      const requirementText = [
        `Control Identifier: ${controlIdentifier}`,
        `Compliance Framework: ${framework}`,
        `Assessment Result: ${assessmentResult}`,
        assessmentWindow ? `Assessment Time Window: ${assessmentWindow}` : undefined,
      ]
        .filter(Boolean)
        .join('\n');

      await generateAttestation({
        requirement_text: requirementText,
        framework,
        control_identifier: controlIdentifier,
        assessment_result: assessmentResult,
        assessment_window: assessmentWindow,
      });
    } catch (err) {
      console.error('Generation failed:', err);
    }
  }, [controlIdentifier, framework, assessmentResult, assessmentWindow, generateAttestation]);

  const handleAutoDemo = useCallback(() => {
    const sample = SAMPLE_REQUIREMENTS[0];
    setControlIdentifier(sample.text);
    setFramework(sample.framework);
    setAssessmentResult('PASS');
    setAssessmentWindow('Jan 1, 2026 – Jan 31, 2026');

    setTimeout(async () => {
      try {
        const requirementText = [
          `Control Identifier: ${sample.text}`,
          `Compliance Framework: ${sample.framework}`,
          `Assessment Result: PASS`,
          `Assessment Time Window: Jan 1, 2026 – Jan 31, 2026`,
        ].join('\n');

        await generateAttestation({
          requirement_text: requirementText,
          framework: sample.framework,
          control_identifier: sample.text,
          assessment_result: 'PASS',
          assessment_window: 'Jan 1, 2026 – Jan 31, 2026',
        });
      } catch (err) {
        console.error('Auto demo failed:', err);
      }
    }, 300);
  }, [generateAttestation]);

  const handleReset = useCallback(() => {
    reset();
    setControlIdentifier('');
    setFramework('NIST_800_53');
    setAssessmentResult('PASS');
    setAssessmentWindow('');
  }, [reset]);

  const canGenerate = controlIdentifier.trim().length > 0;

  return (
    <>
      <Helmet>
        <title>ZKPA Demo - Zero-Knowledge Proof Attestation Agent</title>
        <meta 
          name="description" 
          content="Interactive demo of Zero-Knowledge Proof Attestation Agent. Generate cryptographic attestations that prove compliance without revealing sensitive evidence." 
        />
      </Helmet>
      
      <div className="min-h-screen flex flex-col proof-grid noise">
        <Header judgeMode={judgeMode} onJudgeModeChange={setJudgeMode} />
        
        <main className="flex-1 py-12 px-6">
          <div className="max-w-4xl mx-auto space-y-8">
            {/* Hero Text - Only show in non-judge mode */}
            {!judgeMode && !response && (
              <div className="text-center mb-12 space-y-6">
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-secondary/50 rounded-full border border-border/50 text-sm text-muted-foreground mb-4">
                  <Lock className="h-4 w-4" />
                  <span>Post-Assessment Proof Layer</span>
                </div>
                
                <h2 className="text-5xl font-bold tracking-tightest leading-tight">
                  <span className="text-gradient">Prove Assessed Compliance</span>
                  <br />
                  <span className="text-muted-foreground">Without Exposing Evidence</span>
                </h2>
                
                <p className="text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
                  Transform completed compliance assessments into cryptographically verifiable, privacy-preserving proofs.
                </p>

                <p className="text-sm text-muted-foreground max-w-2xl mx-auto leading-relaxed">
                  This agent operates after control assessment and generates zero-knowledge attestations of assessment results.
                </p>

                <div className="flex items-center justify-center gap-8 pt-4">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Shield className="h-4 w-4" />
                    <span>Privacy Preserved</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Zap className="h-4 w-4" />
                    <span>Instant Verification</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Lock className="h-4 w-4" />
                    <span>Tamper-Proof</span>
                  </div>
                </div>
              </div>
            )}

            <div className="glass-card rounded-2xl p-5 border border-border/40">
              <div className="text-sm font-semibold tracking-tight">Post-Assessment Proof Layer</div>
              <div className="text-xs text-muted-foreground mt-1">
                This demo assumes controls have already been assessed. Assessment inputs are simulated for demonstration purposes.
              </div>
            </div>

            {/* Input Block */}
            <InputBlock
              controlIdentifier={controlIdentifier}
              framework={framework}
              assessmentResult={assessmentResult}
              assessmentWindow={assessmentWindow}
              onControlIdentifierChange={setControlIdentifier}
              onFrameworkChange={setFramework}
              onAssessmentResultChange={setAssessmentResult}
              onAssessmentWindowChange={setAssessmentWindow}
              disabled={isLoading}
              judgeMode={judgeMode}
            />

            {/* Action Block */}
            <ActionBlock
              onGenerate={handleGenerate}
              onReset={handleReset}
              isLoading={isLoading}
              canGenerate={canGenerate}
              steps={steps}
              hasResult={!!response}
              onAutoDemo={handleAutoDemo}
              judgeMode={judgeMode}
            />

            {/* Error State */}
            {error && (
              <ErrorState 
                error={error} 
                onRetry={handleGenerate}
                isTimeout={error.includes('timeout') || error.includes('processing')}
              />
            )}

            {/* Results */}
            {response && !error && (
              <div className="space-y-8">
                <OutputBlock
                  response={response}
                  judgeMode={judgeMode}
                  controlIdentifier={controlIdentifier}
                  framework={framework}
                  assessmentResult={assessmentResult}
                  assessmentWindow={assessmentWindow}
                />
                <ExplanationBlock explanation={response.explanation} judgeMode={judgeMode} />
              </div>
            )}

            {/* Demo Mode Notice */}
            {!import.meta.env.VITE_API_BASE && !judgeMode && (
              <div className="text-center pt-8">
                <span className="inline-flex items-center gap-2 px-4 py-2 bg-secondary/30 rounded-full text-xs text-muted-foreground border border-border/30">
                  <div className="w-2 h-2 rounded-full bg-muted-foreground animate-pulse" />
                  Demo Mode — Simulated Responses
                </span>
              </div>
            )}
          </div>
        </main>

        {/* Footer */}
        <footer className="border-t border-border/30 py-6 px-6">
          <div className="max-w-4xl mx-auto flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 text-xs text-muted-foreground">
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4" />
              <span className="font-semibold">ZKPA</span>
              <span className="text-muted-foreground/50">•</span>
              <span>Zero-Knowledge Proof Attestation Agent</span>
            </div>
            <span className="text-muted-foreground">Privacy by Design — No logs, configurations, or system data are collected or exposed. This agent generates proofs of assessment outcomes only.</span>
          </div>
        </footer>
      </div>
    </>
  );
};

export default ZKPADemo;

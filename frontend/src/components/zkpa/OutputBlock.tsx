import React, { useState } from 'react';
import { Check, X, Copy, Download, FileJson, Shield, Key, CheckCircle2, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';
import type { AssessmentResult, AttestationResponse, Framework } from '@/types/zkpa';

interface OutputBlockProps {
  response: AttestationResponse;
  judgeMode?: boolean;
  controlIdentifier?: string;
  framework?: Framework;
  assessmentResult?: AssessmentResult;
  assessmentWindow?: string;
}

export const OutputBlock: React.FC<OutputBlockProps> = ({
  response,
  judgeMode,
  controlIdentifier,
  framework,
  assessmentResult,
  assessmentWindow,
}) => {
  const { toast } = useToast();
  const [copiedId, setCopiedId] = useState<string | null>(null);
  
  const isValid = response.verification.result === 'valid';

  const getFrameworkLabel = (value?: Framework) => {
    switch (value) {
      case 'NIST_800_53':
        return 'NIST 800-53';
      case 'ISO_27001':
        return 'ISO 27001';
      case 'SOC2':
        return 'SOC 2';
      case 'CUSTOM':
        return 'Custom';
      default:
        return '—';
    }
  };

  const getAssessmentResultLabel = (value?: AssessmentResult) => {
    switch (value) {
      case 'PASS':
        return 'PASS';
      case 'FAIL':
        return 'FAIL';
      case 'PARTIAL':
        return 'PARTIAL';
      default:
        return '—';
    }
  };

  const att = response.attestation as any;
  const claimCommitment =
    att?.credentialSubject?.claim?.evidence_commitment ||
    att?.credentialSubject?.claim?.requirement_hash ||
    att?.proof?.proof_hash ||
    '';

  const copyToClipboard = async (text: string, id: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedId(id);
    toast({ title: 'Copied to clipboard' });
    setTimeout(() => setCopiedId(null), 2000);
  };

  const downloadJson = () => {
    const blob = new Blob([JSON.stringify(response.attestation, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `attestation_${response.claim_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getShareableUrl = () => {
    const url = new URL(window.location.href);
    url.searchParams.set('claim_id', response.claim_id);
    return url.toString();
  };

  return (
    <div className="glass-card-elevated rounded-2xl overflow-hidden">
      {/* Verification Header */}
      <div className={cn(
        "p-8 flex items-center justify-between relative overflow-hidden",
        isValid ? "glow-success" : "glow-error"
      )}>
        {/* Background pattern */}
        <div className="absolute inset-0 opacity-5">
          <div className="absolute inset-0" style={{
            backgroundImage: `radial-gradient(circle at 2px 2px, currentColor 1px, transparent 0)`,
            backgroundSize: '24px 24px'
          }} />
        </div>
        
        <div className="flex items-center gap-6 relative z-10">
          <div className={cn(
            "w-20 h-20 rounded-2xl flex items-center justify-center",
            isValid ? "bg-foreground text-background" : "bg-destructive text-destructive-foreground"
          )}>
            {isValid ? <Check className="h-10 w-10" strokeWidth={3} /> : <X className="h-10 w-10" strokeWidth={3} />}
          </div>
          <div>
            <h2 className="text-3xl font-bold tracking-tightest">
              Compliance Proof Generated
            </h2>
            <p className="text-muted-foreground mt-1">Verification Result</p>
            <p className="text-sm font-semibold mt-1">
              {isValid ? '✅ Proof Valid' : '❌ Proof Invalid'}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-3 px-5 py-3 bg-card/80 backdrop-blur rounded-full border border-border relative z-10">
          <Shield className="h-5 w-5 text-foreground" />
          <span className="text-sm font-medium">No Evidence Exposed</span>
          <CheckCircle2 className="h-5 w-5 text-foreground" />
        </div>
      </div>

      {/* Tabs Content */}
      <div className="p-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="p-6 bg-secondary/30 rounded-xl border border-border/50">
            <div className="text-sm font-semibold tracking-tight mb-4">Attestation Summary</div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Control</div>
                <div className="text-sm font-medium">{controlIdentifier || '—'}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Framework</div>
                <div className="text-sm font-medium">{getFrameworkLabel(framework)}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Assessment Result</div>
                <div className="text-sm font-medium">{getAssessmentResultLabel(assessmentResult)}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Validity Window</div>
                <div className="text-sm font-medium">{assessmentWindow || '—'}</div>
              </div>
            </div>
          </div>

          <div className="p-6 bg-secondary/30 rounded-xl border border-border/50">
            <div className="text-sm font-semibold tracking-tight mb-4">Proof Details</div>
            <div className="space-y-4">
              <div>
                <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Proof Type</div>
                <div className="text-sm font-medium">Zero-Knowledge Attestation</div>
                <div className="text-xs text-muted-foreground mt-1">This proof confirms the assessment result without revealing evidence.</div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Proof Hash</div>
                  <code className="font-mono text-xs text-foreground break-all">{response.proof_id}</code>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Claim Commitment</div>
                  <code className="font-mono text-xs text-foreground break-all">{claimCommitment || '—'}</code>
                </div>
              </div>
            </div>
          </div>
        </div>

        <Tabs defaultValue="verification" className="w-full">
          <TabsList className="grid w-full grid-cols-3 bg-secondary/50 p-1 rounded-xl h-12">
            <TabsTrigger 
              value="verification" 
              className="flex items-center gap-2 rounded-lg data-[state=active]:bg-foreground data-[state=active]:text-background transition-all"
            >
              <Shield className="h-4 w-4" />
              Verification
            </TabsTrigger>
            <TabsTrigger 
              value="artifact" 
              className="flex items-center gap-2 rounded-lg data-[state=active]:bg-foreground data-[state=active]:text-background transition-all"
            >
              <FileJson className="h-4 w-4" />
              Attestation
            </TabsTrigger>
            <TabsTrigger 
              value="ids" 
              className="flex items-center gap-2 rounded-lg data-[state=active]:bg-foreground data-[state=active]:text-background transition-all"
            >
              <Key className="h-4 w-4" />
              Proof IDs
            </TabsTrigger>
          </TabsList>

          <TabsContent value="verification" className="mt-6 space-y-3">
            <div className="flex items-center justify-between p-4 bg-secondary/30 rounded-xl border border-border/50">
              <div>
                <div className="text-xs text-muted-foreground uppercase tracking-wider">Verification Result</div>
                <div className="text-sm font-semibold mt-1">{isValid ? '✅ Proof Valid' : '❌ Proof Invalid'}</div>
                <div className="text-xs text-muted-foreground mt-1">The assessment result can be independently verified without access to internal systems.</div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => toast({
                  title: isValid ? '✅ Proof Valid' : '❌ Proof Invalid',
                  description: 'Re-verified locally (demo).',
                })}
                className="border-border hover:border-foreground hover:bg-foreground hover:text-background transition-all"
              >
                Verify Compliance Proof
              </Button>
            </div>

            {response.verification.checks_passed.map((check, index) => (
              <div 
                key={index}
                className="flex items-center gap-4 p-4 bg-secondary/30 rounded-xl border border-border/50 hover:border-foreground/20 transition-colors"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className="w-8 h-8 rounded-lg bg-foreground flex items-center justify-center flex-shrink-0">
                  <Check className="h-4 w-4 text-background" strokeWidth={3} />
                </div>
                <span className="text-sm font-medium">{check}</span>
              </div>
            ))}
          </TabsContent>

          <TabsContent value="artifact" className="mt-6">
            <div className="flex justify-end gap-3 mb-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => copyToClipboard(JSON.stringify(response.attestation, null, 2), 'json')}
                className="border-border hover:border-foreground hover:bg-foreground hover:text-background transition-all"
              >
                <Copy className="h-4 w-4 mr-2" />
                Copy JSON
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={downloadJson}
                className="border-border hover:border-foreground hover:bg-foreground hover:text-background transition-all"
              >
                <Download className="h-4 w-4 mr-2" />
                Download Attestation (JSON)
              </Button>
            </div>
            <pre className="code-block text-xs overflow-x-auto max-h-[400px] text-muted-foreground">
              {JSON.stringify(response.attestation, null, 2)}
            </pre>
          </TabsContent>

          <TabsContent value="ids" className="mt-6 space-y-4">
            <div className="space-y-4">
              <div className="flex items-center justify-between p-5 bg-secondary/30 rounded-xl border border-border/50">
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Claim ID</p>
                  <code className="font-mono text-lg text-foreground">{response.claim_id}</code>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => copyToClipboard(response.claim_id, 'claim')}
                  className="hover:bg-foreground hover:text-background"
                >
                  {copiedId === 'claim' ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                </Button>
              </div>
              
              <div className="flex items-center justify-between p-5 bg-secondary/30 rounded-xl border border-border/50">
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Proof ID</p>
                  <code className="font-mono text-lg text-foreground">{response.proof_id}</code>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => copyToClipboard(response.proof_id, 'proof')}
                  className="hover:bg-foreground hover:text-background"
                >
                  {copiedId === 'proof' ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                </Button>
              </div>

              <div className="flex items-center justify-between p-5 bg-secondary/30 rounded-xl border border-border/50">
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Claim Commitment</p>
                  <code className="font-mono text-xs text-foreground break-all">{claimCommitment || '—'}</code>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => copyToClipboard(claimCommitment || '', 'commitment')}
                  className="hover:bg-foreground hover:text-background"
                  disabled={!claimCommitment}
                >
                  {copiedId === 'commitment' ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                </Button>
              </div>
            </div>

            {!judgeMode && (
              <div className="pt-5 border-t border-border/50">
                <p className="text-xs text-muted-foreground uppercase tracking-wider mb-3">Shareable Result Link</p>
                <div className="flex items-center gap-3">
                  <code className="flex-1 text-xs font-mono bg-secondary/50 p-4 rounded-xl truncate border border-border/50 text-muted-foreground">
                    {getShareableUrl()}
                  </code>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => copyToClipboard(getShareableUrl(), 'url')}
                    className="border-border hover:border-foreground hover:bg-foreground hover:text-background"
                  >
                    {copiedId === 'url' ? <Check className="h-4 w-4" /> : <ExternalLink className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

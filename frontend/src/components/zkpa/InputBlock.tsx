import React from 'react';
import { FileText, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { SAMPLE_REQUIREMENTS, FRAMEWORK_OPTIONS, type AssessmentResult, type Framework } from '@/types/zkpa';

interface InputBlockProps {
  controlIdentifier: string;
  framework: Framework;
  assessmentResult: AssessmentResult;
  assessmentWindow: string;
  onControlIdentifierChange: (value: string) => void;
  onFrameworkChange: (value: Framework) => void;
  onAssessmentResultChange: (value: AssessmentResult) => void;
  onAssessmentWindowChange: (value: string) => void;
  disabled?: boolean;
  judgeMode?: boolean;
}

export const InputBlock: React.FC<InputBlockProps> = ({
  controlIdentifier,
  framework,
  assessmentResult,
  assessmentWindow,
  onControlIdentifierChange,
  onFrameworkChange,
  onAssessmentResultChange,
  onAssessmentWindowChange,
  disabled,
  judgeMode,
}) => {
  const loadSample = (sampleId: string) => {
    const sample = SAMPLE_REQUIREMENTS.find(s => s.id === sampleId);
    if (sample) {
      onControlIdentifierChange(sample.text);
      onFrameworkChange(sample.framework);
    }
  };

  return (
    <div className="glass-card rounded-2xl p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center">
            <FileText className="h-5 w-5 text-foreground" />
          </div>
          <div>
            <h2 className="text-lg font-semibold tracking-tight">Assessed Control Result</h2>
            <p className="text-xs text-muted-foreground">Select a control that has already been evaluated and generate a cryptographic proof of the assessment outcome.</p>
          </div>
        </div>
        
        {!judgeMode && (
          <div className="flex gap-2">
            {SAMPLE_REQUIREMENTS.map((sample, index) => (
              <Button
                key={sample.id}
                variant="outline"
                size="sm"
                onClick={() => loadSample(sample.id)}
                disabled={disabled}
                className="text-xs border-border/50 hover:border-foreground hover:bg-foreground hover:text-background transition-all duration-300 group"
              >
                <Zap className="h-3 w-3 mr-1.5 group-hover:text-background" />
                {sample.name.split(' ')[0]}
              </Button>
            ))}
          </div>
        )}
      </div>

      <div className="space-y-2">
        <p className="text-xs text-muted-foreground uppercase tracking-wide">Control Identifier</p>
        <Input
          value={controlIdentifier}
          onChange={(e) => onControlIdentifierChange(e.target.value)}
          placeholder="e.g., NIST 800-53 AC-7"
          className="bg-secondary/30 border-border/50 focus:border-foreground/50"
          disabled={disabled}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
        <div className="space-y-2">
          <p className="text-xs text-muted-foreground uppercase tracking-wide">Compliance Framework</p>
          <Select
            value={framework}
            onValueChange={(v) => onFrameworkChange(v as Framework)}
            disabled={disabled}
          >
            <SelectTrigger className="w-full bg-secondary border-border/50 hover:border-foreground/30 transition-colors">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-card border-border z-50">
              {FRAMEWORK_OPTIONS.map((opt) => (
                <SelectItem
                  key={opt.value}
                  value={opt.value}
                  className="hover:bg-secondary focus:bg-secondary"
                >
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <p className="text-xs text-muted-foreground uppercase tracking-wide">Assessment Result</p>
          <Select
            value={assessmentResult}
            onValueChange={(v) => onAssessmentResultChange(v as AssessmentResult)}
            disabled={disabled}
          >
            <SelectTrigger className="w-full bg-secondary border-border/50 hover:border-foreground/30 transition-colors">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-card border-border z-50">
              <SelectItem value="PASS" className="hover:bg-secondary focus:bg-secondary">✅ Pass</SelectItem>
              <SelectItem value="FAIL" className="hover:bg-secondary focus:bg-secondary">❌ Fail</SelectItem>
              <SelectItem value="PARTIAL" className="hover:bg-secondary focus:bg-secondary">⚠️ Partial</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground">Result determined upstream by an assessment engine or auditor.</p>
        </div>
      </div>

      <div className="space-y-2">
        <p className="text-xs text-muted-foreground uppercase tracking-wide">Assessment Time Window</p>
        <Input
          value={assessmentWindow}
          onChange={(e) => onAssessmentWindowChange(e.target.value)}
          placeholder="Jan 1, 2026 – Jan 31, 2026"
          className="bg-secondary/30 border-border/50 focus:border-foreground/50"
          disabled={disabled}
        />
      </div>
    </div>
  );
};

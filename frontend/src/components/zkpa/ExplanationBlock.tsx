import React, { useState } from 'react';
import { MessageSquare, Briefcase, Code, Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface ExplanationBlockProps {
  explanation: string;
  judgeMode?: boolean;
}

type ExplanationMode = 'auditor' | 'engineer';

export const ExplanationBlock: React.FC<ExplanationBlockProps> = ({ 
  explanation, 
  judgeMode 
}) => {
  const [mode, setMode] = useState<ExplanationMode>('auditor');

  const formatExplanation = (text: string, format: ExplanationMode) => {
    if (format === 'engineer') {
      return `[TECHNICAL SUMMARY]\n\n${text}\n\n[IMPLEMENTATION NOTES]\n• ZK-SNARK proof validates predicate without revealing witness data\n• Commitment scheme: Pedersen hash over evidence payload\n• Verification time: O(1) with preprocessed verification key\n• No trusted setup required for this proof system`;
    }
    return text;
  };

  return (
    <div className="glass-card rounded-2xl p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center">
            <MessageSquare className="h-5 w-5 text-foreground" />
          </div>
          <div>
            <h2 className="text-lg font-semibold tracking-tight">Privacy Summary</h2>
            <p className="text-xs text-muted-foreground">What was proven, without the evidence</p>
          </div>
        </div>
        
        {!judgeMode && (
          <div className="flex items-center bg-secondary rounded-xl p-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setMode('auditor')}
              className={cn(
                "h-9 px-4 text-sm rounded-lg transition-all",
                mode === 'auditor' && "bg-foreground text-background"
              )}
            >
              <Briefcase className="h-4 w-4 mr-2" />
              Auditor
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setMode('engineer')}
              className={cn(
                "h-9 px-4 text-sm rounded-lg transition-all",
                mode === 'engineer' && "bg-foreground text-background"
              )}
            >
              <Code className="h-4 w-4 mr-2" />
              Engineer
            </Button>
          </div>
        )}
      </div>

      <div className="p-6 rounded-xl bg-secondary/30 border border-border/50">
        <p className={cn(
          "leading-relaxed whitespace-pre-line",
          mode === 'engineer' ? "font-mono text-sm text-muted-foreground" : "text-base"
        )}>
          {formatExplanation(explanation, mode)}
        </p>
      </div>

      <div className="flex items-center gap-3 pt-2">
        <div className="flex items-center gap-2 px-4 py-2 bg-secondary/50 rounded-full border border-border/50">
          <Lock className="h-4 w-4 text-foreground" />
          <span className="text-sm font-medium">Zero-knowledge verified</span>
        </div>
        <div className="w-2 h-2 rounded-full bg-foreground animate-pulse" />
        <span className="text-xs text-muted-foreground">No sensitive data exposed</span>
      </div>
    </div>
  );
};

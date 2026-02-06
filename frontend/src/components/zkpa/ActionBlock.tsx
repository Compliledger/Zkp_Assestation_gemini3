import React from 'react';
import { Play, RotateCcw, Zap, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ProofTimeline } from './ProofTimeline';
import { cn } from '@/lib/utils';
import type { ProgressStep } from '@/types/zkpa';

interface ActionBlockProps {
  onGenerate: () => void;
  onReset: () => void;
  isLoading: boolean;
  canGenerate: boolean;
  steps: ProgressStep[];
  hasResult: boolean;
  onAutoDemo?: () => void;
  judgeMode?: boolean;
}

export const ActionBlock: React.FC<ActionBlockProps> = ({
  onGenerate,
  onReset,
  isLoading,
  canGenerate,
  steps,
  hasResult,
  onAutoDemo,
  judgeMode,
}) => {
  const showTimeline = isLoading || steps.some(s => s.status !== 'pending');

  return (
    <div className="glass-card rounded-2xl p-8 space-y-8">
      <div className="flex items-center gap-4">
        <Button
          onClick={onGenerate}
          disabled={!canGenerate || isLoading}
          size="lg"
          className={cn(
            "flex-1 h-14 text-base font-semibold tracking-tight transition-all duration-300",
            "bg-foreground text-background hover:bg-foreground/90",
            "disabled:bg-secondary disabled:text-muted-foreground",
            canGenerate && !isLoading && "glow-white"
          )}
        >
          {isLoading ? (
            <>
              <div className="w-5 h-5 border-2 border-background/30 border-t-background rounded-full animate-spin mr-3" />
              Generating Compliance Proof...
            </>
          ) : (
            <>
              <Play className="h-5 w-5 mr-3" fill="currentColor" />
              Generate Compliance Proof
              <ArrowRight className="h-5 w-5 ml-3" />
            </>
          )}
        </Button>
        
        {hasResult && (
          <Button
            onClick={onReset}
            variant="outline"
            size="lg"
            className="h-14 px-6 border-border hover:border-foreground hover:bg-foreground hover:text-background transition-all duration-300"
          >
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset
          </Button>
        )}
        
        {!judgeMode && onAutoDemo && !isLoading && !hasResult && (
          <Button
            onClick={onAutoDemo}
            variant="outline"
            size="lg"
            className="h-14 px-6 border-border hover:border-foreground hover:bg-foreground hover:text-background transition-all duration-300 group"
          >
            <Zap className="h-4 w-4 mr-2 group-hover:text-background" />
            Auto Demo
          </Button>
        )}
      </div>

      {showTimeline && (
        <div className="pt-6 border-t border-border/50">
          <ProofTimeline steps={steps} />
        </div>
      )}
    </div>
  );
};

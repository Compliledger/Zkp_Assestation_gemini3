import React from 'react';
import { Check, Loader2, AlertCircle, Circle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ProgressStep } from '@/types/zkpa';

interface ProofTimelineProps {
  steps: ProgressStep[];
  className?: string;
}

export const ProofTimeline: React.FC<ProofTimelineProps> = ({ steps, className }) => {
  const getStepIcon = (status: ProgressStep['status']) => {
    switch (status) {
      case 'complete':
        return <Check className="h-4 w-4" strokeWidth={3} />;
      case 'active':
        return <Loader2 className="h-4 w-4 animate-spin" />;
      case 'error':
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <Circle className="h-2 w-2" />;
    }
  };

  const getStepStyles = (status: ProgressStep['status']) => {
    switch (status) {
      case 'complete':
        return 'bg-foreground text-background border-foreground';
      case 'active':
        return 'bg-foreground/10 text-foreground border-foreground animate-pulse';
      case 'error':
        return 'bg-destructive/20 text-destructive border-destructive';
      default:
        return 'bg-secondary text-muted-foreground border-border';
    }
  };

  return (
    <div className={cn("flex items-center justify-between gap-2", className)}>
      {steps.map((step, index) => (
        <React.Fragment key={step.id}>
          <div className="flex flex-col items-center gap-3 flex-1">
            <div
              className={cn(
                "w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-500",
                getStepStyles(step.status)
              )}
            >
              {getStepIcon(step.status)}
            </div>
            <span className={cn(
              "text-xs font-medium transition-colors text-center",
              step.status === 'active' ? 'text-foreground' :
              step.status === 'complete' ? 'text-foreground' :
              step.status === 'error' ? 'text-destructive' :
              'text-muted-foreground'
            )}>
              {step.label}
            </span>
          </div>
          
          {index < steps.length - 1 && (
            <div className="flex-shrink-0 w-12 h-[2px] -mt-8 relative overflow-hidden">
              <div className={cn(
                "absolute inset-0 transition-all duration-500",
                steps[index].status === 'complete' ? 'bg-foreground' : 'bg-border'
              )} />
              {steps[index].status === 'active' && (
                <div className="absolute inset-0 bg-gradient-to-r from-foreground via-foreground to-transparent animate-pulse" />
              )}
            </div>
          )}
        </React.Fragment>
      ))}
    </div>
  );
};

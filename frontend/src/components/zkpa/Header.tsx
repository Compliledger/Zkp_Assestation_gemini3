import React from 'react';
import { Shield, Github, Sparkles } from 'lucide-react';
import { Switch } from '@/components/ui/switch';
import { cn } from '@/lib/utils';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface HeaderProps {
  judgeMode: boolean;
  onJudgeModeChange: (enabled: boolean) => void;
}

export const Header: React.FC<HeaderProps> = ({ judgeMode, onJudgeModeChange }) => {
  return (
    <header className="border-b border-border/50 bg-background/80 backdrop-blur-xl sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-6 py-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="w-12 h-12 rounded-xl bg-foreground flex items-center justify-center">
                <Shield className="h-7 w-7 text-background" />
              </div>
              <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-foreground animate-pulse" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tightest text-gradient-shine">
                ZKPA
              </h1>
              <p className="text-xs text-muted-foreground tracking-wide uppercase">
                Zero-Knowledge Proof Attestation
              </p>
            </div>
          </div>

          <div className="flex items-center gap-6">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className={cn(
                    "flex items-center gap-3 px-4 py-2.5 rounded-full border transition-all duration-300",
                    judgeMode 
                      ? "bg-foreground text-background border-foreground" 
                      : "bg-secondary/50 border-border hover:border-foreground/30"
                  )}>
                    <Sparkles className={cn(
                      "h-4 w-4 transition-colors",
                      judgeMode ? "text-background" : "text-muted-foreground"
                    )} />
                    <span className={cn(
                      "text-sm font-medium",
                      judgeMode ? "text-background" : "text-foreground"
                    )}>
                      Judge Mode
                    </span>
                    <Switch
                      checked={judgeMode}
                      onCheckedChange={onJudgeModeChange}
                      className="data-[state=checked]:bg-background"
                    />
                  </div>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="max-w-xs">
                  Enables guided demo flow with simulated assessment inputs and explanatory annotations.
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>

            <a 
              href="https://github.com/Compliledger/Zkp_Assestation_gemini3" 
              target="_blank" 
              rel="noopener noreferrer"
              className="w-10 h-10 rounded-full border border-border flex items-center justify-center text-muted-foreground hover:text-foreground hover:border-foreground/50 transition-all duration-300"
            >
              <Github className="h-5 w-5" />
            </a>
          </div>
        </div>
      </div>
    </header>
  );
};

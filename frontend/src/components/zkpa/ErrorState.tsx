import React from 'react';
import { AlertTriangle, RefreshCw, Wifi, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface ErrorStateProps {
  error: string;
  onRetry: () => void;
  isTimeout?: boolean;
}

export const ErrorState: React.FC<ErrorStateProps> = ({ error, onRetry, isTimeout }) => {
  const isNetworkError = error.includes('fetch') || error.includes('network') || error.includes('unreachable');
  
  return (
    <div className="glass-card rounded-2xl p-10 text-center space-y-6 border-destructive/30">
      <div className={cn(
        "w-20 h-20 mx-auto rounded-2xl flex items-center justify-center",
        isTimeout ? "bg-secondary" : "bg-destructive/10"
      )}>
        {isTimeout ? (
          <Clock className="h-10 w-10 text-muted-foreground" />
        ) : isNetworkError ? (
          <Wifi className="h-10 w-10 text-destructive" />
        ) : (
          <AlertTriangle className="h-10 w-10 text-destructive" />
        )}
      </div>
      
      <div>
        <h3 className="text-xl font-bold tracking-tight mb-2">
          {isTimeout ? 'Still Processing' : isNetworkError ? 'Service Unavailable' : 'Error Occurred'}
        </h3>
        <p className="text-sm text-muted-foreground max-w-md mx-auto">
          {error}
        </p>
      </div>

      <Button 
        onClick={onRetry} 
        size="lg"
        className="h-12 px-8 bg-foreground text-background hover:bg-foreground/90"
      >
        <RefreshCw className="h-4 w-4 mr-2" />
        {isTimeout ? 'Continue Polling' : 'Retry'}
      </Button>
    </div>
  );
};

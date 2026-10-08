"use client";

import { Loader2, Brain, Film, Search, CheckCircle2 } from "lucide-react";
import { useEffect, useState } from "react";

interface ProcessingStatusProps {
  message: string;
  step?: string;
  showProgress?: boolean;
}

const processingSteps = [
  { id: 1, name: "Analyzing script", icon: Brain },
  { id: 2, name: "Finding clip moments", icon: Film },
  { id: 3, name: "Searching clips", icon: Search },
  { id: 4, name: "Optimizing results", icon: CheckCircle2 },
];

export function ProcessingStatus({ message, step, showProgress = true }: ProcessingStatusProps) {
  const [elapsed, setElapsed] = useState(0);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  // Time elapsed tracker
  useEffect(() => {
    const startTime = Date.now();
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // Determine current step based on message or step prop
  useEffect(() => {
    const msg = (step || message).toLowerCase();
    
    if (msg.includes('analyzing script')) {
      setCurrentStepIndex(0);
    } else if (msg.includes('finding clip moments')) {
      setCurrentStepIndex(1);
    } else if (msg.includes('searching clips')) {
      setCurrentStepIndex(2);
    } else if (msg.includes('optimizing results')) {
      setCurrentStepIndex(3);
    }
  }, [message, step]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const progress = ((currentStepIndex + 1) / processingSteps.length) * 100;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Loader2 className="h-4 w-4 animate-spin text-white" />
          <span className="text-sm font-medium text-white">
            {message}
          </span>
        </div>
        <div className="px-2 py-0.5 bg-neutral-800 rounded-full">
          <span className="text-xs text-neutral-400">{formatTime(elapsed)}</span>
        </div>
      </div>

      {showProgress && (
        <>
          <div className="h-1.5 bg-neutral-800 rounded-full overflow-hidden">
            <div 
              className="h-full bg-white transition-all duration-300 ease-out rounded-full"
              style={{ width: `${progress}%` }}
            />
          </div>
          
          <div className="grid grid-cols-4 gap-2">
            {processingSteps.map((stepItem, index) => {
              const Icon = stepItem.icon;
              const isActive = index === currentStepIndex;
              const isCompleted = index < currentStepIndex;
              
              return (
                <div
                  key={stepItem.id}
                  className={`flex flex-col items-center gap-1 p-2 rounded-lg transition-all ${
                    isActive 
                      ? 'bg-neutral-800 border border-neutral-700' 
                      : isCompleted 
                      ? 'bg-green-500/10 border border-green-500/20'
                      : 'bg-neutral-900 border border-neutral-800'
                  }`}
                >
                  <Icon className={`h-4 w-4 ${
                    isActive 
                      ? 'text-white animate-pulse' 
                      : isCompleted
                      ? 'text-green-400'
                      : 'text-neutral-600'
                  }`} />
                  <span className={`text-xs ${
                    isActive 
                      ? 'text-white font-medium' 
                      : isCompleted
                      ? 'text-green-400'
                      : 'text-neutral-500'
                  }`}>
                    {stepItem.name}
                  </span>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
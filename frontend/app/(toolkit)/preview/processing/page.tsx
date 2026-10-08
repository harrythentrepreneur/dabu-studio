"use client";

import { useState, useRef, useEffect } from "react";
import { ProcessingStatus } from "@/components/processing-status";
import { Button } from "@/components/ui/button";
import { Play, Pause, RotateCcw, Settings2, Activity } from "lucide-react";

export default function ProcessingPreviewPage() {
  const [currentStep, setCurrentStep] = useState(3);
  const [progress, setProgress] = useState(25);
  const [isRunning, setIsRunning] = useState(false);
  const [hasVoiceover, setHasVoiceover] = useState(false);
  const [isQuickCreate, setIsQuickCreate] = useState(true);
  const [processingStartTime] = useState(new Date());
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Simulate processing
  const startSimulation = () => {
    if (isRunning) return;

    setIsRunning(true);
    const totalSteps = isQuickCreate ? (hasVoiceover ? 14 : 12) : (hasVoiceover ? 10 : 8);

    let step = currentStep;
    intervalRef.current = setInterval(() => {
      step++;
      const newProgress = (step / totalSteps) * 100;
      setCurrentStep(step);
      setProgress(newProgress);

      if (step >= totalSteps) {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
        setIsRunning(false);
      }
    }, 2000);
  };

  const pause = () => {
    setIsRunning(false);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  const reset = () => {
    setCurrentStep(1);
    setProgress(0);
    setIsRunning(false);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  const getStatusMessage = () => {
    const messages = [
      "Initializing processing pipeline...",
      "Analyzing voiceover audio...",
      "Loading video files...",
      "Merging video segments...",
      "Uploading to Gemini AI...",
      "AI analyzing content...",
      "Validating duration targets...",
      "Extracting video segments...",
      "Exporting final outputs...",
      "Adding voiceover track...",
      "Cleaning up temporary files...",
      "Initializing CapCut project...",
      "Auto-transcribing audio...",
      "Applying caption style...",
      "Packaging project files..."
    ];
    return messages[currentStep - 1] || "Processing...";
  };

  return (
    <div className="min-h-screen">
      {/* Processing Status Component - Exactly as it appears in the app */}
      <ProcessingStatus
        currentStep={currentStep}
        progress={progress}
        statusMessage={getStatusMessage()}
        onCancel={() => {
          pause();
          console.log("Cancel clicked");
        }}
        hasVoiceover={hasVoiceover}
        processingStartTime={processingStartTime}
        totalSteps={isQuickCreate ? 14 : undefined}
        isQuickCreate={isQuickCreate}
      />
    </div>
  );
}
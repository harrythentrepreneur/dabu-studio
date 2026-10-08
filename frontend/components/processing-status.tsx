"use client";

import { useState, useEffect } from "react";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { VideoCacheIndicator } from "@/components/VideoCacheIndicator";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useStore } from "@/lib/store";
import {
  Loader2,
  CheckCircle2,
  Upload,
  Cpu,
  FileVideo,
  Package,
  X,
  FolderOpen,
  CheckCircle,
  Database,
  Mic,
  Music,
  Captions,
  Sparkles,
  Zap,
  FileText,
  Clock,
  Activity,
  ChevronRight,
  XCircle,
  RefreshCw
} from "lucide-react";

interface ProcessingStatusProps {
  currentStep?: number;
  progress?: number;
  statusMessage?: string;
  onCancel?: () => void;
  hasVoiceover?: boolean;
  processingStartTime?: Date | number | null;
  totalSteps?: number;
  isQuickCreate?: boolean;
}

const stepsWithoutVoiceover = [
  { id: 1, name: "Preparing files", icon: FolderOpen },
  { id: 2, name: "Uploading to cloud", icon: Upload },
  { id: 3, name: "Merging videos", icon: FileVideo },
  { id: 4, name: "Analyzing with AI", icon: Cpu },
  { id: 5, name: "Matching script to video", icon: Sparkles },
  { id: 6, name: "Extracting segments", icon: FileVideo },
  { id: 7, name: "Creating final video", icon: Package },
  { id: 8, name: "Finalizing", icon: CheckCircle },
];

const stepsWithVoiceover = [
  { id: 1, name: "Analyzing voiceover", icon: Mic },
  { id: 2, name: "Preparing files", icon: FolderOpen },
  { id: 3, name: "Uploading to cloud", icon: Upload },
  { id: 4, name: "Merging videos", icon: FileVideo },
  { id: 5, name: "Analyzing with AI", icon: Cpu },
  { id: 6, name: "Matching script to video", icon: Sparkles },
  { id: 7, name: "Extracting segments", icon: FileVideo },
  { id: 8, name: "Creating final video", icon: Package },
  { id: 9, name: "Adding voiceover", icon: Music },
  { id: 10, name: "Finalizing", icon: CheckCircle },
];

const quickCreateStepsWithVoiceover = [
  { id: 1, name: "Analyzing voiceover", icon: Mic },
  { id: 2, name: "Loading inputs", icon: FolderOpen },
  { id: 3, name: "Merging videos", icon: FileVideo },
  { id: 4, name: "Uploading to AI", icon: Upload },
  { id: 5, name: "AI Analysis", icon: Cpu },
  { id: 6, name: "Validating duration", icon: CheckCircle },
  { id: 7, name: "Extracting segments", icon: FileVideo },
  { id: 8, name: "Exporting outputs", icon: Package },
  { id: 9, name: "Adding voiceover", icon: Music },
  { id: 10, name: "Cleanup", icon: Database },
  { id: 11, name: "Initializing CapCut", icon: Sparkles },
  { id: 12, name: "Auto-Transcribing", icon: Captions },
  { id: 13, name: "Applying Caption Style", icon: Zap },
  { id: 14, name: "Packaging Project", icon: FileText },
];

const quickCreateStepsWithoutVoiceover = [
  { id: 1, name: "Loading inputs", icon: FolderOpen },
  { id: 2, name: "Merging videos", icon: FileVideo },
  { id: 3, name: "Uploading to AI", icon: Upload },
  { id: 4, name: "AI Analysis", icon: Cpu },
  { id: 5, name: "Validating duration", icon: CheckCircle },
  { id: 6, name: "Extracting segments", icon: FileVideo },
  { id: 7, name: "Exporting outputs", icon: Package },
  { id: 8, name: "Cleanup", icon: Database },
  { id: 9, name: "Initializing CapCut", icon: Sparkles },
  { id: 10, name: "Auto-Transcribing", icon: Captions },
  { id: 11, name: "Applying Caption Style", icon: Zap },
  { id: 12, name: "Packaging Project", icon: FileText },
];

export function ProcessingStatus({
  currentStep = 1,
  progress = 0,
  statusMessage = "Processing...",
  onCancel = () => { },
  hasVoiceover = false,
  processingStartTime,
  totalSteps,
  isQuickCreate = false
}: ProcessingStatusProps) {

  let steps;
  if (isQuickCreate || totalSteps === 14) {
    steps = hasVoiceover ? quickCreateStepsWithVoiceover : quickCreateStepsWithoutVoiceover;
  } else if (totalSteps) {
    steps = hasVoiceover ? stepsWithVoiceover : stepsWithoutVoiceover;
  } else {
    // Default to basic steps if no totalSteps provided
    steps = hasVoiceover ? stepsWithVoiceover : stepsWithoutVoiceover;
  }

  const [elapsedTime, setElapsedTime] = useState(0);
  const { archiveCurrentVideo, navigateToVideo } = useStore();

  useEffect(() => {
    const timer = setInterval(() => {
      if (processingStartTime) {
        const startTime = processingStartTime instanceof Date
          ? processingStartTime.getTime()
          : processingStartTime;
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        setElapsedTime(elapsed);
      } else {
        setElapsedTime(prev => prev + 1);
      }
    }, 1000);

    return () => clearInterval(timer);
  }, [processingStartTime]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const estimatedTime = Math.max(180 - elapsedTime, 0); // 3 minutes estimate

  return (
    <div className="min-h-screen">
      {/* Header - Fixed like Quick Create */}
      <div className="sticky top-0 bg-neutral-950 z-10 px-6 py-6">
        <div className="mb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-xl font-semibold text-white">Processing Video</h1>
                  {/* Status Pills */}
                  <div className="flex items-center gap-1">
                    <div className="flex items-center gap-1 px-2 py-0.5 bg-neutral-900 rounded-full">
                      <Activity className="h-3 w-3 text-purple-400 animate-pulse" />
                      <span className="text-[10px] text-purple-400">Processing</span>
                    </div>
                    <div className="flex items-center gap-1 px-2 py-0.5 bg-neutral-900 rounded-full">
                      <Zap className="h-3 w-3 text-neutral-600" />
                      <span className="text-[10px] text-neutral-500">AI Analysis</span>
                    </div>
                  </div>
                </div>
                <p className="text-xs text-neutral-500 mt-0.5">AI is analyzing and creating your TikTok ad • Step {currentStep} of {steps.length}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {/* Compact action buttons */}
              <div className="flex items-center">
                <TooltipProvider>
                  <Tooltip delayDuration={200}>
                    <TooltipTrigger asChild>
                      <Button
                        onClick={onCancel}
                        size="sm"
                        variant="ghost"
                        className="h-6 px-2 text-[10px] hover:bg-neutral-900 text-neutral-500"
                      >
                        <Sparkles className="h-3 w-3" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="bg-neutral-900 border-neutral-800">
                      <p className="text-xs">Create another video</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>

                <TooltipProvider>
                  <Tooltip delayDuration={200}>
                    <TooltipTrigger asChild>
                      <Button
                        onClick={() => {
                          archiveCurrentVideo();
                          navigateToVideo(-1);
                          onCancel();
                        }}
                        size="sm"
                        variant="ghost"
                        className="h-6 px-2 text-[10px] hover:bg-neutral-900 text-neutral-500"
                      >
                        <XCircle className="h-3 w-3" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="bg-neutral-900 border-neutral-800">
                      <p className="text-xs">Cancel & delete</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>

              <div className="w-px h-4 bg-neutral-800 ml-2 mr-3" />
              <VideoCacheIndicator />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="px-6 pb-6">
        <div className="space-y-4">
          {/* Progress Bar - Full Width */}
          <div className="bg-neutral-950 rounded-lg border border-neutral-900 p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-4">
                <span className="text-sm font-medium text-white">Progress</span>
                <span className="text-xs text-neutral-500">{formatTime(elapsedTime)} elapsed</span>
              </div>
              <span className="text-xs text-neutral-500">{Math.round(progress)}%</span>
            </div>
            <Progress value={progress} className="h-1 bg-neutral-900" />
          </div>

          {/* Current Status - Full Width */}
          <div className="bg-neutral-950 rounded-lg border border-neutral-900 p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-neutral-900 rounded-lg">
                <Zap className="h-4 w-4 text-purple-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-white">Current Operation</p>
                <p className="text-xs text-neutral-500">{statusMessage}</p>
              </div>
            </div>
          </div>

          {/* Steps List - Full Width */}
          <div className="bg-neutral-950 rounded-lg border border-neutral-900 p-4">
            <div className="space-y-2">
              {steps.map((step, index) => {
                const StepIcon = step.icon;
                const isActive = step.id === currentStep;
                const isComplete = step.id < currentStep;
                const isUpcoming = step.id > currentStep;

                return (
                  <div
                    key={step.id}
                    className={`flex items-center gap-3 p-2 rounded-lg transition-all ${isActive
                      ? 'bg-purple-500/5'
                      : isComplete
                        ? 'opacity-50'
                        : 'opacity-30'
                      }`}
                  >
                    <div className={`p-1.5 rounded-full ${isActive
                      ? 'bg-purple-500/10'
                      : isComplete
                        ? 'bg-green-500/10'
                        : 'bg-neutral-900'
                      }`}>
                      {isComplete ? (
                        <CheckCircle2 className="h-3.5 w-3.5 text-green-400" />
                      ) : isActive ? (
                        <Loader2 className="h-3.5 w-3.5 text-purple-400 animate-spin" />
                      ) : (
                        <StepIcon className="h-3.5 w-3.5 text-neutral-600" />
                      )}
                    </div>
                    <span className={`text-xs font-medium flex-1 ${isActive
                      ? 'text-white'
                      : isComplete
                        ? 'text-neutral-500 line-through'
                        : 'text-neutral-600'
                      }`}>
                      {step.name}
                    </span>
                    {isActive && (
                      <ChevronRight className="h-3 w-3 text-purple-400 animate-pulse" />
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-start gap-3 pt-2">
            <Button
              size="sm"
              onClick={onCancel}
              className="bg-white hover:bg-neutral-200 text-black font-medium"
            >
              <Sparkles className="h-3.5 w-3.5 mr-1.5" />
              Create Another Video
            </Button>
            <Button
              size="sm"
              onClick={onCancel}
              variant="outline"
              className="border-neutral-800 hover:bg-neutral-900 text-neutral-300"
            >
              <X className="h-3.5 w-3.5 mr-1.5" />
              Cancel Processing
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
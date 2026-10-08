"use client";

import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Sparkles,
  Film,
  Mic,
  ChevronRight,
  X,
  Scissors,
  Captions,
  Brain,
  Package,
  Clock,
  Info,
  Zap,
  Upload
} from "lucide-react";
import { useStore } from "@/lib/store";
import { ProcessingStatus } from "../../../components/processing-status";
import { ResultsDisplay } from "../../../components/results-display";
import { VideoCacheIndicator } from "../../../components/VideoCacheIndicator";
import { uploadHandler } from "@/lib/upload-handler";
import { Progress } from "@/components/ui/progress";

interface ProcessingResult {
  videoUrl?: string;
  scriptUrl?: string;
  timestampsUrl?: string;
  mergedFullUrl?: string;
  captionedVideoUrl?: string;
  projectBundleUrl?: string;
  segments?: any[];
  error?: string;
  processingMode?: string;
  capcutSuccess?: boolean;
}

export default function ExpressBuilderPage() {
  const [script, setScript] = useState("");
  const [videos, setVideos] = useState<File[]>([]);
  const [voiceover, setVoiceover] = useState<File | null>(null);
  const [processingState, setProcessingState] = useState<"idle" | "uploading" | "processing" | "complete" | "error">("idle");
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  const [result, setResult] = useState<ProcessingResult | null>(null);
  const [processingStartTime, setProcessingStartTime] = useState<Date | null>(null);
  const [isNewVideo, setIsNewVideo] = useState(true);
  const [targetDuration, setTargetDuration] = useState("30");
  const [processingMode, setProcessingMode] = useState<"express_builder" | "quick_create">("express_builder");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  
  const videoInputRef = useRef<HTMLInputElement>(null);
  const voiceoverInputRef = useRef<HTMLInputElement>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const { currentVideoIndex, getCurrentVideo, addVideoToCache } = useStore();
  const currentVideo = getCurrentVideo();

  const handlePaste = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    e.preventDefault();
    const pastedText = e.clipboardData.getData('text');

    // Split by newlines and add double spacing
    const formattedText = pastedText
      .split('\n')
      .filter(line => line.trim() !== '') // Remove empty lines
      .join('\n\n'); // Join with double newlines

    // Insert at cursor position
    const textarea = e.currentTarget;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const currentValue = textarea.value;

    const newValue =
      currentValue.substring(0, start) +
      formattedText +
      currentValue.substring(end);

    setScript(newValue);

    // Set cursor position after inserted text
    setTimeout(() => {
      textarea.selectionStart = textarea.selectionEnd = start + formattedText.length;
    }, 0);
  };

  const handleVideoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setVideos(files);
  };

  const handleVoiceoverUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    setVoiceover(file);
  };

  const removeVideo = (index: number) => {
    setVideos(videos.filter((_, i) => i !== index));
  };

  const removeVoiceover = () => {
    setVoiceover(null);
    if (voiceoverInputRef.current) voiceoverInputRef.current.value = "";
  };

  const handleProcess = async () => {
    console.log("🚀 [PROCESS START] Starting processing...");
    console.log(`[PROCESS] Script length: ${script.length}, Videos: ${videos.length}`);

    if (!script || videos.length === 0) {
      alert("Please provide a script and at least one video");
      return;
    }

    setProcessingState("uploading");
    setCurrentStep(1);
    setProgress(0);
    setStatusMessage("Uploading files to cloud storage...");
    setProcessingStartTime(new Date());
    setResult(null);

    try {
      // Upload all videos to DO Spaces
      const videoUrls: string[] = [];
      let totalUploadProgress = 0;
      
      for (let i = 0; i < videos.length; i++) {
        const video = videos[i];
        setStatusMessage(`Uploading video ${i + 1}/${videos.length}: ${video.name}`);
        
        const result = await uploadHandler.uploadFile(video, {
          onProgress: (progress) => {
            // Calculate overall progress
            const videoProgress = (i * 100 + progress) / videos.length;
            setUploadProgress(Math.round(videoProgress));
          },
          onStatusChange: (status) => {
            console.log(`[UPLOAD] Video ${i + 1}: ${status}`);
          }
        });

        if (!result.success || !result.publicUrl) {
          throw new Error(`Failed to upload video ${i + 1}: ${result.error}`);
        }
        
        videoUrls.push(result.publicUrl);
        console.log(`✅ Uploaded video ${i + 1}: ${result.publicUrl}`);
      }

      // Upload voiceover if provided
      let voiceoverUrl: string | undefined;
      if (voiceover) {
        setStatusMessage(`Uploading voiceover: ${voiceover.name}`);
        
        const result = await uploadHandler.uploadFile(voiceover, {
          onProgress: (progress) => {
            setUploadProgress(progress);
          },
          onStatusChange: (status) => {
            console.log(`[UPLOAD] Voiceover: ${status}`);
          }
        });

        if (!result.success || !result.publicUrl) {
          throw new Error(`Failed to upload voiceover: ${result.error}`);
        }
        
        voiceoverUrl = result.publicUrl;
        console.log(`✅ Uploaded voiceover: ${voiceoverUrl}`);
      }

      // All files uploaded, now submit to RunPod
      setProcessingState("processing");
      setStatusMessage("Submitting job to processing queue...");
      setProgress(10);

      const response = await fetch('/api/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          script,
          videoUrls,
          voiceoverUrl,
          duration: parseInt(targetDuration),
          processingMode,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to submit processing job');
      }

      const { jobId, requestId } = await response.json();
      setCurrentJobId(jobId);
      console.log(`✅ Job submitted: ${jobId}`);

      // Start polling for status
      setStatusMessage("Processing your video...");
      pollJobStatus(jobId);

    } catch (error) {
      console.error("❌ [ERROR]", error);
      setProcessingState("error");
      setResult({ 
        error: error instanceof Error ? error.message : "Processing failed" 
      });
    }
  };

  const pollJobStatus = async (jobId: string) => {
    // Clear any existing polling
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }

    const poll = async () => {
      try {
        const response = await fetch(`/api/status/${jobId}`);
        
        if (!response.ok) {
          throw new Error('Failed to fetch job status');
        }

        const status = await response.json();
        console.log(`[POLL] Job ${jobId} status:`, status.status);

        // Update progress based on status
        if (status.status === 'IN_QUEUE') {
          setProgress(20);
          setStatusMessage('Job queued for processing...');
        } else if (status.status === 'IN_PROGRESS') {
          setProgress(50);
          setStatusMessage('Processing your video...');
        } else if (status.status === 'COMPLETED') {
          setProgress(100);
          setStatusMessage('Processing complete!');
          setProcessingState('complete');
          
          // Set the result
          setResult({
            videoUrl: status.result?.videoUrl,
            scriptUrl: status.result?.scriptUrl,
            timestampsUrl: status.result?.timestampsUrl,
            captionedVideoUrl: status.result?.captionedVideoUrl,
            projectBundleUrl: status.result?.projectBundleUrl,
            segments: status.result?.segments,
            processingMode: status.result?.processingMode,
            capcutSuccess: status.result?.capcutSuccess,
          });

          // Stop polling
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
        } else if (status.status === 'FAILED' || status.status === 'TIMED_OUT') {
          setProcessingState('error');
          setResult({
            error: status.error || 'Processing failed',
          });

          // Stop polling
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
        }

        // Update current step based on execution time
        if (status.executionTime) {
          const seconds = Math.floor(status.executionTime / 1000);
          if (seconds < 30) setCurrentStep(2);
          else if (seconds < 60) setCurrentStep(3);
          else if (seconds < 90) setCurrentStep(4);
          else setCurrentStep(5);
        }

      } catch (error) {
        console.error('[POLL] Error:', error);
        // Continue polling even on error (network issues, etc)
      }
    };

    // Initial poll
    await poll();

    // Set up interval polling (every 2 seconds)
    if (processingState === 'processing') {
      pollIntervalRef.current = setInterval(poll, 2000);
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
      uploadHandler.cancelUpload();
    };
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 dark:from-slate-950 dark:via-slate-900 dark:to-blue-950">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl shadow-lg">
              <Zap className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Express Builder
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Create professional TikTok ads in minutes with AI-powered video compilation
              </p>
            </div>
          </div>

          {/* Mode Selector */}
          <div className="flex gap-2 p-1 bg-gray-100 dark:bg-gray-800 rounded-lg w-fit">
            <Button
              variant={processingMode === "express_builder" ? "default" : "ghost"}
              size="sm"
              onClick={() => setProcessingMode("express_builder")}
              className="gap-2"
            >
              <Scissors className="h-4 w-4" />
              Express Builder
            </Button>
            <Button
              variant={processingMode === "quick_create" ? "default" : "ghost"}
              size="sm"
              onClick={() => setProcessingMode("quick_create")}
              className="gap-2"
            >
              <Captions className="h-4 w-4" />
              Quick Create
              <span className="text-xs bg-yellow-500/20 text-yellow-600 dark:text-yellow-400 px-1.5 py-0.5 rounded">
                +Captions
              </span>
            </Button>
          </div>
        </div>

        {processingState === "idle" || processingState === "uploading" ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column - Script Input */}
            <div className="space-y-6">
              <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold flex items-center gap-2">
                    <Brain className="h-5 w-5 text-blue-500" />
                    Script
                  </h2>
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <Info className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Paste your script here. Each line will be matched to video segments.</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
                <Textarea
                  placeholder="Paste your advertising script here...

Each line will be matched to a video segment.
Leave empty lines for natural pauses."
                  value={script}
                  onChange={(e) => setScript(e.target.value)}
                  onPaste={handlePaste}
                  className="min-h-[400px] font-mono text-sm"
                />
                <div className="mt-4 flex items-center justify-between">
                  <span className="text-sm text-gray-500">
                    {script.split('\n').filter(line => line.trim()).length} lines
                  </span>
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-gray-400" />
                    <input
                      type="number"
                      value={targetDuration}
                      onChange={(e) => setTargetDuration(e.target.value)}
                      className="w-16 px-2 py-1 text-sm border rounded"
                      min="15"
                      max="60"
                    />
                    <span className="text-sm text-gray-500">seconds</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column - Media Upload */}
            <div className="space-y-6">
              {/* Video Upload */}
              <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold flex items-center gap-2">
                    <Film className="h-5 w-5 text-green-500" />
                    Video Files
                  </h2>
                  <span className="text-sm text-gray-500">{videos.length} selected</span>
                </div>
                
                <input
                  ref={videoInputRef}
                  type="file"
                  multiple
                  accept="video/*"
                  onChange={handleVideoUpload}
                  className="hidden"
                />
                
                {videos.length === 0 ? (
                  <button
                    onClick={() => videoInputRef.current?.click()}
                    className="w-full h-32 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg hover:border-blue-500 dark:hover:border-blue-400 transition-colors flex flex-col items-center justify-center gap-2 cursor-pointer"
                  >
                    <Upload className="h-8 w-8 text-gray-400" />
                    <span className="text-gray-500">Click to upload videos</span>
                  </button>
                ) : (
                  <div className="space-y-2">
                    {videos.map((video, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                        <div className="flex items-center gap-3">
                          <Film className="h-4 w-4 text-gray-400" />
                          <span className="text-sm truncate max-w-[300px]">{video.name}</span>
                          <span className="text-xs text-gray-500">
                            {(video.size / 1024 / 1024).toFixed(1)} MB
                          </span>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => removeVideo(index)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => videoInputRef.current?.click()}
                      className="w-full mt-2"
                    >
                      Add More Videos
                    </Button>
                  </div>
                )}
              </div>

              {/* Voiceover Upload */}
              <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold flex items-center gap-2">
                    <Mic className="h-5 w-5 text-purple-500" />
                    Voiceover
                    <span className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 px-2 py-1 rounded">
                      Optional
                    </span>
                  </h2>
                </div>
                
                <input
                  ref={voiceoverInputRef}
                  type="file"
                  accept="audio/*"
                  onChange={handleVoiceoverUpload}
                  className="hidden"
                />
                
                {!voiceover ? (
                  <button
                    onClick={() => voiceoverInputRef.current?.click()}
                    className="w-full h-24 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg hover:border-purple-500 dark:hover:border-purple-400 transition-colors flex flex-col items-center justify-center gap-2 cursor-pointer"
                  >
                    <Mic className="h-6 w-6 text-gray-400" />
                    <span className="text-gray-500 text-sm">Add voiceover for perfect sync</span>
                  </button>
                ) : (
                  <div className="flex items-center justify-between p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Mic className="h-4 w-4 text-purple-500" />
                      <span className="text-sm">{voiceover.name}</span>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={removeVoiceover}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                )}
              </div>

              {/* Upload Progress */}
              {processingState === "uploading" && (
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Uploading files...</span>
                    <span className="text-sm text-gray-600">{uploadProgress}%</span>
                  </div>
                  <Progress value={uploadProgress} className="h-2" />
                </div>
              )}

              {/* Process Button */}
              <Button
                onClick={handleProcess}
                disabled={!script || videos.length === 0 || processingState !== "idle"}
                className="w-full h-14 text-lg gap-3"
                size="lg"
              >
                <Sparkles className="h-5 w-5" />
                {processingMode === "quick_create" ? "Create with Captions" : "Build Video"}
                <ChevronRight className="h-5 w-5" />
              </Button>
            </div>
          </div>
        ) : processingState === "processing" ? (
          <ProcessingStatus
            currentStep={currentStep}
            progress={progress}
            statusMessage={statusMessage}
            onCancel={() => {
              setProcessingState("idle");
              setResult(null);
              setCurrentStep(0);
              setProgress(0);
              setCurrentJobId(null);
            }}
            hasVoiceover={voiceover !== null}
            processingStartTime={processingStartTime}
            totalSteps={processingMode === "quick_create" ? 14 : 10}
            isQuickCreate={processingMode === "quick_create"}
          />
        ) : (
          <ResultsDisplay
            results={result || undefined}
            processingState={processingState as "complete" | "error"}
            onReset={() => {
              setProcessingState("idle");
              setResult(null);
              setCurrentStep(0);
              setProgress(0);
              setCurrentJobId(null);
            }}
          />
        )}
      </div>
    </div>
  );
}
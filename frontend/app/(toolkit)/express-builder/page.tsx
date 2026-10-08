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

          // Add to cache
          setTimeout(() => {
            addVideoToCache({
              id: Date.now().toString(),
              videoUrl: status.result?.videoUrl,
              scriptUrl: status.result?.scriptUrl,
              timestampsUrl: status.result?.timestampsUrl,
              captionedVideoUrl: status.result?.captionedVideoUrl,
              projectBundleUrl: status.result?.projectBundleUrl,
              createdAt: Date.now(),
              status: 'complete' as const,
            });
          }, 100);
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

  const handleReset = () => {
    setScript("");
    setVideos([]);
    setVoiceover(null);
    setProcessingState("idle");
    setCurrentStep(0);
    setProgress(0);
    setStatusMessage("");
    setResult(null);
    setProcessingStartTime(null);
    setIsNewVideo(true);
    setCurrentJobId(null);

    if (videoInputRef.current) videoInputRef.current.value = "";
    if (voiceoverInputRef.current) voiceoverInputRef.current.value = "";
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  // Smart duration detection
  useEffect(() => {
    if (!script.trim()) {
      setTargetDuration("30");
      return;
    }

    const words = script.trim().split(/\s+/);
    const wordCount = words.length;
    const wordsPerSecond = 140 / 60;
    const baseDuration = wordCount / wordsPerSecond;
    const paddedDuration = baseDuration * 1.15;
    const finalDuration = Math.round(paddedDuration);

    setTargetDuration(finalDuration.toString());
  }, [script]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
      uploadHandler.cancelUpload();
    };
  }, []);

  useEffect(() => {
    if (currentVideo?.videoUrl) {
      const isTestVideo = !currentVideo.id || currentVideo.id === "test";
      if (!isTestVideo && processingState !== "processing") {
        setIsNewVideo(false);
        setProcessingState("complete");
        setResult(currentVideo);
      }
    }
  }, [currentVideoIndex, currentVideo, processingState]);

  return (
    <div className="min-h-screen">
      {((processingState === "idle" || processingState === "uploading") && isNewVideo) && (
        <>
          {/* Header */}
          <div className="sticky top-0 bg-neutral-950 z-10 px-6 py-6">
            <div className="mb-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div>
                    <div className="flex items-center gap-3">
                      <h1 className="text-xl font-semibold text-white">Express Builder</h1>
                      {/* Feature Pills */}
                      <div className="flex items-center gap-1">
                        <div className="flex items-center gap-1 px-2 py-0.5 bg-neutral-900 rounded-full">
                          <Zap className="h-3 w-3 text-neutral-600" />
                          <span className="text-[10px] text-neutral-500">3-5 min</span>
                        </div>
                        <div className="flex items-center gap-1 px-2 py-0.5 bg-neutral-900 rounded-full">
                          <Brain className="h-3 w-3 text-neutral-600" />
                          <span className="text-[10px] text-neutral-500">Gemini AI</span>
                        </div>
                        <div className="flex items-center gap-1 px-2 py-0.5 bg-neutral-900 rounded-full">
                          <Sparkles className="h-3 w-3 text-neutral-600" />
                          <span className="text-[10px] text-neutral-500">Perfect Sync</span>
                        </div>
                      </div>
                    </div>
                    <p className="text-xs text-neutral-500 mt-0.5">Script-to-video alignment with automatic scene matching & voiceover sync</p>
                  </div>
                </div>
                <VideoCacheIndicator />
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="px-6 pb-6">
            <div className="grid lg:grid-cols-2 gap-6">
              {/* Left Half - Script */}
              <div className="space-y-4">
                <div className="lg:sticky lg:top-[110px]">
                  <div className="bg-neutral-950 rounded-lg border border-neutral-900 p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-medium text-white">Script</span>
                        {script && (
                          <div className="flex items-center gap-1 px-2 py-0.5 bg-green-500/10 rounded-full">
                            <Clock className="h-3 w-3 text-green-400" />
                            <span className="text-[10px] text-green-400 font-medium">~{targetDuration}s</span>
                          </div>
                        )}
                      </div>
                      <TooltipProvider>
                        <Tooltip delayDuration={200}>
                          <TooltipTrigger asChild>
                            <button className="text-neutral-700 hover:text-neutral-500 transition-colors">
                              <Info className="h-3 w-3" />
                            </button>
                          </TooltipTrigger>
                          <TooltipContent className="max-w-xs bg-neutral-900 border-neutral-800">
                            <p className="text-xs leading-relaxed">
                              <span className="font-semibold text-white">Pro Tips</span><br />
                              <span className="text-neutral-400">
                                • Break script into clear, emotional moments<br />
                                • Use action words that match visual content<br />
                                • Keep sentences short and punchy<br />
                                • Hook viewers in first 3 seconds
                              </span>
                            </p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>

                    <Textarea
                      placeholder="Enter your TikTok ad script..."
                      value={script}
                      onChange={(e) => setScript(e.target.value)}
                      onPaste={handlePaste}
                      className="min-h-[300px] resize-none bg-neutral-900 border-neutral-800 text-sm placeholder:text-neutral-600"
                    />
                  </div>

                  {/* Processing Mode Toggle */}
                  <div className="mt-4 p-4 bg-neutral-900 rounded-lg border border-neutral-800">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-xs text-neutral-400">Processing Mode:</span>
                    </div>
                    <div className="flex bg-neutral-800 rounded-lg p-1">
                      <button
                        onClick={() => setProcessingMode("express_builder")}
                        className={`flex-1 px-3 py-2 text-xs rounded-md transition-all ${processingMode === "express_builder"
                          ? "bg-neutral-700 text-white"
                          : "text-neutral-400 hover:text-neutral-300"
                          }`}
                      >
                        <div className="flex items-center gap-2 justify-center">
                          <Package className="w-3 h-3" />
                          Express Builder Only
                        </div>
                      </button>
                      <button
                        onClick={() => setProcessingMode("quick_create")}
                        className={`flex-1 px-3 py-2 text-xs rounded-md transition-all ${processingMode === "quick_create"
                          ? "bg-neutral-700 text-white"
                          : "text-neutral-400 hover:text-neutral-300"
                          }`}
                      >
                        <div className="flex items-center gap-2 justify-center">
                          <Captions className="w-3 h-3" />
                          Quick Create + Captions
                        </div>
                      </button>
                    </div>
                    {processingMode === "quick_create" && (
                      <div className="mt-3 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                        <div className="flex items-center gap-2 text-xs text-blue-400">
                          <Captions className="w-3 h-3" />
                          <span>Will automatically add captions using Intelligent CapCut after video processing</span>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Process Button */}
                  <div className="flex justify-center mt-4">
                    <Button
                      size="default"
                      onClick={handleProcess}
                      disabled={!script || videos.length === 0 || processingState !== "idle"}
                      className="px-6 h-10 bg-white hover:bg-neutral-200 text-black font-medium disabled:opacity-50"
                    >
                      Generate Video
                      <ChevronRight className="ml-2 h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>

              {/* Right Half - Videos & Voiceover */}
              <div className="space-y-4 min-h-screen">
                {/* Videos */}
                <div className="bg-neutral-950 rounded-lg border border-neutral-900 p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-white">Videos</span>
                      {videos.length > 0 && (
                        <span className="text-xs text-green-400">
                          {videos.length} selected
                        </span>
                      )}
                    </div>
                    <TooltipProvider>
                      <Tooltip delayDuration={200}>
                        <TooltipTrigger asChild>
                          <button className="text-neutral-700 hover:text-neutral-500 transition-colors">
                            <Info className="h-3 w-3" />
                          </button>
                        </TooltipTrigger>
                        <TooltipContent className="max-w-xs bg-neutral-900 border-neutral-800">
                          <p className="text-xs leading-relaxed">
                            <span className="font-semibold text-white">Video Tips</span><br />
                            <span className="text-neutral-400">
                              • More videos = better scene matching<br />
                              • Mix different angles and energy levels<br />
                              • Include both wide and close-up shots<br />
                              • Upload 2x your target duration for flexibility
                            </span>
                          </p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>

                  {videos.length === 0 ? (
                    <div
                      onClick={() => videoInputRef.current?.click()}
                      className="relative group cursor-pointer"
                    >
                      <div className="p-6 border-2 border-dashed border-neutral-800 rounded-lg hover:border-neutral-700 transition-all">
                        <div className="text-center">
                          <Film className="w-6 h-6 text-neutral-600 mx-auto mb-2" />
                          <p className="text-xs text-neutral-400">Click to upload</p>
                          <p className="text-xs text-neutral-600 mt-1">MP4, MOV, WEBM</p>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="max-h-[200px] overflow-y-auto space-y-2 pr-1">
                        {videos.map((video, index) => (
                          <div key={index} className="flex items-center justify-between p-2 bg-neutral-900 rounded-lg">
                            <div className="flex items-center gap-2 flex-1 min-w-0">
                              <Film className="w-4 h-4 text-neutral-500 flex-shrink-0" />
                              <div className="flex-1 min-w-0">
                                <p className="text-xs text-white truncate">{video.name}</p>
                                <p className="text-xs text-neutral-500">{formatFileSize(video.size)}</p>
                              </div>
                            </div>
                            <button
                              onClick={() => removeVideo(index)}
                              className="p-1 hover:bg-neutral-800 rounded transition-colors"
                            >
                              <X className="w-3 h-3 text-neutral-500" />
                            </button>
                          </div>
                        ))}
                      </div>
                      <button
                        onClick={() => videoInputRef.current?.click()}
                        className="w-full p-2 border border-dashed border-neutral-800 rounded-lg hover:border-neutral-700 transition-all"
                      >
                        <p className="text-xs text-neutral-500">Add more videos</p>
                      </button>
                    </div>
                  )}

                  <input
                    ref={videoInputRef}
                    type="file"
                    multiple
                    accept="video/*"
                    onChange={handleVideoUpload}
                    className="hidden"
                  />
                </div>

                {/* Voiceover */}
                <div className="bg-neutral-950 rounded-lg border border-neutral-900 p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-white">Voiceover</span>
                      <span className="text-xs text-neutral-500">Optional</span>
                    </div>
                    <TooltipProvider>
                      <Tooltip delayDuration={200}>
                        <TooltipTrigger asChild>
                          <button className="text-neutral-700 hover:text-neutral-500 transition-colors">
                            <Info className="h-3 w-3" />
                          </button>
                        </TooltipTrigger>
                        <TooltipContent className="max-w-xs bg-neutral-900 border-neutral-800">
                          <p className="text-xs leading-relaxed">
                            <span className="font-semibold text-white">Voiceover Benefits</span><br />
                            <span className="text-neutral-400">
                              • AI syncs video cuts to your voice timing<br />
                              • Perfect for testimonials and narratives<br />
                              • Eliminates manual timing adjustments<br />
                              • Works best with clear, paced delivery
                            </span>
                          </p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>

                  {!voiceover ? (
                    <div
                      onClick={() => voiceoverInputRef.current?.click()}
                      className="relative group cursor-pointer"
                    >
                      <div className="p-6 border-2 border-dashed border-neutral-800 rounded-lg hover:border-neutral-700 transition-all">
                        <div className="text-center">
                          <Mic className="w-6 h-6 text-neutral-600 mx-auto mb-2" />
                          <p className="text-xs text-neutral-400">Add audio</p>
                          <p className="text-xs text-neutral-600 mt-1">MP3, WAV, M4A</p>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="p-2 bg-neutral-900 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                          <Mic className="w-4 h-4 text-neutral-500 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <p className="text-xs text-white truncate">{voiceover.name}</p>
                            <p className="text-xs text-neutral-500">{formatFileSize(voiceover.size)}</p>
                          </div>
                        </div>
                        <button
                          onClick={removeVoiceover}
                          className="p-1 hover:bg-neutral-800 rounded transition-colors"
                        >
                          <X className="w-3 h-3 text-neutral-500" />
                        </button>
                      </div>
                    </div>
                  )}

                  <input
                    ref={voiceoverInputRef}
                    type="file"
                    accept="audio/*"
                    onChange={handleVoiceoverUpload}
                    className="hidden"
                  />
                </div>

                {/* Upload Progress */}
                {processingState === "uploading" && (
                  <div className="bg-neutral-950 rounded-lg border border-neutral-900 p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-white">Uploading files...</span>
                      <span className="text-sm text-neutral-500">{uploadProgress}%</span>
                    </div>
                    <Progress value={uploadProgress} className="h-2" />
                    <p className="text-xs text-neutral-500 mt-2">{statusMessage}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}

      {/* Processing Status */}
      {processingState === "processing" && (
        <div className="p-6">
          <ProcessingStatus
            currentStep={currentStep}
            progress={progress}
            statusMessage={statusMessage}
            onCancel={handleReset}
            hasVoiceover={voiceover !== null}
            processingStartTime={processingStartTime}
            totalSteps={processingMode === "quick_create" ? 14 : 10}
            isQuickCreate={processingMode === "quick_create"}
          />
        </div>
      )}

      {/* Results */}
      {(processingState === "complete" || processingState === "error") && result && (
        <div className="p-6">
          <ResultsDisplay
            results={result}
            processingState={processingState}
            onReset={handleReset}
          />
        </div>
      )}
    </div>
  );
}
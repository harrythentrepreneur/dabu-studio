"use client";

import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Sparkles,
  Upload,
  FileText,
  Film,
  Mic,
  ChevronRight,
  X,
  Scissors,
  Captions,
  Brain,
  Package,
  Clock,
  Wand2,
  Zap,
  Info
} from "lucide-react";
import { useStore } from "@/lib/store";
import { CaptionStyleSelector } from "./components/caption-style-selector";
import { ProcessingStatus } from "../../../components/processing-status";
import { ResultsDisplay } from "../../../components/results-display";
import { VideoCacheIndicator } from "../../../components/VideoCacheIndicator";
import { API_ENDPOINTS, ensureAbsoluteUrl } from "@/lib/api-config";

interface ProcessingResult {
  videoUrl?: string;
  scriptUrl?: string;
  timestampsUrl?: string;
  mergedFullUrl?: string;
  captionedVideoUrl?: string;
  projectBundleUrl?: string;
  segments?: any[];
  error?: string;
}

export default function QuickCreatePage() {
  const [script, setScript] = useState("");
  const [videos, setVideos] = useState<File[]>([]);
  const [voiceover, setVoiceover] = useState<File | null>(null);
  const [captionStyle, setCaptionStyle] = useState("");
  const [processingState, setProcessingState] = useState<"idle" | "processing" | "complete" | "error">("idle");
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  const [result, setResult] = useState<ProcessingResult | null>(null);
  const [processingStartTime, setProcessingStartTime] = useState<Date | null>(null);
  const [isNewVideo, setIsNewVideo] = useState(true);
  const [targetDuration, setTargetDuration] = useState("35");
  const eventSourceRef = useRef<EventSource | null>(null);

  const videoInputRef = useRef<HTMLInputElement>(null);
  const voiceoverInputRef = useRef<HTMLInputElement>(null);

  const { currentVideoIndex, getCurrentVideo, addVideoToCache, updateVideoInCache } = useStore();
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
    if (!script || videos.length === 0 || !captionStyle) return;

    setProcessingState("processing");
    setCurrentStep(1);
    setProgress(0);
    setStatusMessage("Initializing...");
    setProcessingStartTime(new Date());

    const formData = new FormData();
    formData.append("script", script);
    formData.append("target_duration", targetDuration);
    formData.append("use_mock", "false");
    formData.append("apply_captions", "true");
    formData.append("caption_template", captionStyle);

    videos.forEach(video => {
      formData.append("videos", video);
    });

    if (voiceover) {
      formData.append("voiceover", voiceover);
    }

    // Generate request ID
    const requestId = `request_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    formData.append("request_id", requestId);

    // Create SSE connection
    const eventSource = new EventSource(API_ENDPOINTS.statusStream(requestId));
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleStatusUpdate(data);
      } catch (error) {
        console.error("Error parsing SSE data:", error);
      }
    };

    eventSource.onerror = (error) => {
      console.error("SSE error:", error);
      eventSource.close();
      setProcessingState("error");
      setResult({ error: "Connection lost during processing" });
    };

    // Send processing request
    try {
      const response = await fetch(API_ENDPOINTS.process, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error("Processing error:", error);
      setProcessingState("error");
      setResult({ error: "Failed to start processing" });
      eventSource.close();
    }
  };

  const handleStatusUpdate = (data: any) => {
    setCurrentStep(data.step);
    setProgress(data.progress);
    setStatusMessage(data.message);

    if (data.success && data.result) {
      // Extract URLs from download_urls object
      const urls = data.result.download_urls || {};

      // Use the imported ensureAbsoluteUrl function from api-config

      const resultData = {
        videoUrl: ensureAbsoluteUrl(urls.video),
        scriptUrl: ensureAbsoluteUrl(urls.script),
        timestampsUrl: ensureAbsoluteUrl(urls.timestamps),
        captionedVideoUrl: ensureAbsoluteUrl(urls.captioned_video),
        projectBundleUrl: ensureAbsoluteUrl(urls.bundle),
      };

      // Set result and state FIRST
      setResult(resultData);
      setProcessingState("complete");

      // Close SSE connection
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      // Add to store AFTER setting state to avoid race condition
      setTimeout(() => {
        addVideoToCache({
          id: Date.now().toString(),
          ...resultData,
          createdAt: Date.now(),
          status: 'complete' as const,
        });
      }, 100);
    } else if (data.error) {
      setProcessingState("error");
      setResult({ error: data.error });

      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    }
  };

  const handleReset = () => {
    setScript("");
    setVideos([]);
    setVoiceover(null);
    setCaptionStyle("");
    setProcessingState("idle");
    setCurrentStep(0);
    setProgress(0);
    setStatusMessage("");
    setResult(null);
    setProcessingStartTime(null);
    setIsNewVideo(true);

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

  // Smart duration detection based on script length
  useEffect(() => {
    if (!script.trim()) {
      setTargetDuration("30");
      return;
    }

    const words = script.trim().split(/\s+/);
    const wordCount = words.length;

    // Calculate based on natural speaking rate
    // Using slower, more natural rate: 140 WPM (2.33 words per second)
    const wordsPerSecond = 140 / 60;
    const baseDuration = wordCount / wordsPerSecond;

    // Add padding for natural pauses and pacing
    const paddedDuration = baseDuration * 1.15;

    // Round to nearest whole second
    const finalDuration = Math.round(paddedDuration);

    setTargetDuration(finalDuration.toString());
  }, [script]);


  useEffect(() => {
    // Don't reset state if we're currently processing
    if (processingState === "processing") {
      return;
    }

    if (currentVideo?.videoUrl) {
      const isTestVideo = !currentVideo.id || currentVideo.id === "test";

      if (!isTestVideo) {
        setIsNewVideo(false);
        setProcessingState("complete");
        setResult(currentVideo);
      } else {
        setIsNewVideo(true);
        setProcessingState("idle");
        setResult(null);
      }
    } else {
      // Only reset to idle if we're not in the middle of processing or just completed
      if (processingState !== "complete") {
        setIsNewVideo(true);
        setProcessingState("idle");
        setResult(null);
      }
    }
  }, [currentVideoIndex, currentVideo, processingState]);

  return (
    <div className="min-h-screen">
      {(processingState === "idle" && isNewVideo) && (
        <>
          {/* Header - Fixed */}
          <div className="sticky top-0 bg-neutral-950 z-10 px-6 py-6">
            <div className="mb-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div>
                    <div className="flex items-center gap-3">
                      <h1 className="text-xl font-semibold text-white">Quick Create</h1>
                      {/* Feature Pills - cleanly to the right of title */}
                      <div className="flex items-center gap-1">
                        <div className="flex items-center gap-1 px-2 py-0.5 bg-neutral-900 rounded-full">
                          <Scissors className="h-3 w-3 text-neutral-600" />
                          <span className="text-[10px] text-neutral-500">Auto-Edit</span>
                        </div>
                        <div className="flex items-center gap-1 px-2 py-0.5 bg-neutral-900 rounded-full">
                          <Captions className="h-3 w-3 text-neutral-600" />
                          <span className="text-[10px] text-neutral-500">Auto-Transcribe</span>
                        </div>
                        <div className="flex items-center gap-1 px-2 py-0.5 bg-neutral-900 rounded-full">
                          <Brain className="h-3 w-3 text-neutral-600" />
                          <span className="text-[10px] text-neutral-500">Gemini AI</span>
                        </div>
                        <div className="flex items-center gap-1 px-2 py-0.5 bg-neutral-900 rounded-full">
                          <Package className="h-3 w-3 text-neutral-600" />
                          <span className="text-[10px] text-neutral-500">CapCut</span>
                        </div>
                      </div>
                    </div>
                    <p className="text-xs text-neutral-500 mt-0.5">Complete TikTok video ads with captions & CapCut project files</p>
                  </div>
                </div>
                <VideoCacheIndicator />
              </div>
            </div>
          </div>

          {/* Main Content - Two Column Layout */}
          <div className="px-6 pb-6">
            <div className="grid lg:grid-cols-2 gap-6">
              {/* Left Half - Script (Fixed Position) */}
              <div className="space-y-4">
                <div className="lg:sticky lg:top-[110px]">
                  <div className="bg-neutral-950 rounded-lg border border-neutral-900 p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-medium text-white">Script</span>
                        {/* Smart Duration Badge */}
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
                      onPaste={handlePaste}
                      onChange={(e) => {
                        const text = e.target.value;
                        const lastChar = text[text.length - 1];
                        const prevChar = text[text.length - 2];

                        // Only auto-format when user types ". " (period + space) and it's not already formatted
                        if (lastChar === ' ' && prevChar === '.' && !text.endsWith('.\n\n ')) {
                          const formattedText = text.slice(0, -2) + '.\n\n';
                          setScript(formattedText);
                        } else {
                          setScript(text);
                        }
                      }}
                      className="min-h-[300px] resize-none bg-neutral-900 border-neutral-800 text-sm placeholder:text-neutral-600"
                    />
                  </div>

                  {/* Quick Stats */}
                  {(videos.length > 0 || voiceover || captionStyle) && (
                    <div className="flex items-center justify-center gap-6 py-2 mt-3">
                      {videos.length > 0 && (
                        <div className="flex items-center gap-1 text-xs text-neutral-500">
                          <Film className="h-3 w-3" />
                          <span>{videos.length} video{videos.length > 1 ? 's' : ''}</span>
                        </div>
                      )}
                      {voiceover && (
                        <div className="flex items-center gap-1 text-xs text-neutral-500">
                          <Mic className="h-3 w-3" />
                          <span>Voiceover ready</span>
                        </div>
                      )}
                      {captionStyle && (
                        <div className="flex items-center gap-1 text-xs text-neutral-500">
                          <Captions className="h-3 w-3" />
                          <span>Style {captionStyle}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Process Button */}
                  <div className="flex justify-center mt-4">
                    <Button
                      size="default"
                      onClick={handleProcess}
                      disabled={!script || videos.length === 0 || !captionStyle}
                      className="px-6 h-10 bg-white hover:bg-neutral-200 text-black font-medium disabled:opacity-50"
                    >
                      Generate Video
                      <ChevronRight className="ml-2 h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>

              {/* Right Half - Videos, Audio, Captions (Scrollable) */}
              <div className="space-y-4">
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

                {/* Caption Style */}
                <div className="bg-neutral-950 rounded-lg border border-neutral-900 p-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-medium text-white">Caption Style</span>
                    <TooltipProvider>
                      <Tooltip delayDuration={200}>
                        <TooltipTrigger asChild>
                          <button className="text-neutral-700 hover:text-neutral-500 transition-colors">
                            <Info className="h-3 w-3" />
                          </button>
                        </TooltipTrigger>
                        <TooltipContent className="max-w-xs bg-neutral-900 border-neutral-800">
                          <p className="text-xs leading-relaxed">
                            <span className="font-semibold text-white">Auto Captions</span><br />
                            <span className="text-neutral-400">
                              • Captions overlay your script on the video<br />
                              • Synced word-by-word with timing<br />
                              • Increases viewer retention by 40%<br />
                              • Essential for sound-off viewing
                            </span>
                          </p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>
                  <CaptionStyleSelector
                    selected={captionStyle}
                    onChange={setCaptionStyle}
                  />
                </div>
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
            totalSteps={14}
            isQuickCreate={true}
          />
        </div>
      )}

      {/* Results */}
      {(processingState === "complete" || processingState === "error") && result && (
        <ResultsDisplay
          results={result}
          processingState={processingState}
          onReset={handleReset}
        />
      )}
    </div>
  );
}
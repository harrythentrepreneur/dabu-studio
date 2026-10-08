"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { VideoCacheIndicator } from "@/components/VideoCacheIndicator";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Download,
  Play,
  FileText,
  Clock,
  CheckCircle2,
  XCircle,
  RefreshCw,
  FileJson,
  Video,
  Loader2,
  Sparkles,
  ChevronRight,
  Package,
  AlertCircle,
  Copy,
  Check
} from "lucide-react";
import { useStore } from "@/lib/store";
import { ensureAbsoluteUrl } from "@/lib/api-config";

interface ResultsDisplayProps {
  results?: {
    videoUrl?: string;
    scriptUrl?: string;
    timestampsUrl?: string;
    mergedFullUrl?: string;
    captionedVideoUrl?: string;
    projectBundleUrl?: string;
    segments?: any[];
    error?: string;
  };
  processingState?: "complete" | "error";
  onReset?: () => void;
}

export function ResultsDisplay({ results, processingState = "complete", onReset = () => { } }: ResultsDisplayProps = {}) {
  const result = results || {};
  const isSuccess = processingState === "complete" && !result.error;
  const [scriptContent, setScriptContent] = useState<string>("");
  const [timestampsData, setTimestampsData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [selectedSegment, setSelectedSegment] = useState<number | null>(null);

  const { archiveCurrentVideo, navigateToVideo } = useStore();

  // Use the imported ensureAbsoluteUrl function from api-config

  useEffect(() => {
    setIsLoading(true);

    const loadData = async () => {
      try {
        const promises = [];

        if (isSuccess && result.scriptUrl) {
          const scriptUrl = ensureAbsoluteUrl(result.scriptUrl);
          if (scriptUrl) {
            promises.push(
              fetch(scriptUrl)
                .then(res => res.text())
                .then(text => setScriptContent(text))
            );
          }
        }

        if (isSuccess && result.timestampsUrl) {
          const timestampsUrl = ensureAbsoluteUrl(result.timestampsUrl);
          if (timestampsUrl) {
            promises.push(
              fetch(timestampsUrl)
                .then(res => res.json())
                .then(data => setTimestampsData(data))
            );
          }
        }

        await Promise.all(promises);
      } catch (err) {
        console.error('Failed to load data:', err);
      } finally {
        setTimeout(() => setIsLoading(false), 500);
      }
    };

    if (isSuccess) {
      loadData();
    } else {
      setIsLoading(false);
    }
  }, [isSuccess, result.scriptUrl, result.timestampsUrl]);

  const handleDownload = (url: string | undefined, filename: string) => {
    const absoluteUrl = ensureAbsoluteUrl(url);
    if (!absoluteUrl) return;

    // Check if it's a CDN URL (DO Spaces) - these should open in new tab
    if (absoluteUrl.includes('digitaloceanspaces.com') || 
        absoluteUrl.includes('cdn.digitaloceanspaces.com')) {
      // Open CDN URLs in new tab for direct download
      window.open(absoluteUrl, '_blank');
      return;
    }

    // Local download through backend
    const a = document.createElement('a');
    a.href = absoluteUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const copyScript = () => {
    if (scriptContent) {
      navigator.clipboard.writeText(scriptContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const formatTime = (seconds: number | string) => {
    // Convert to number if it's a string
    const numSeconds = typeof seconds === 'string' ? parseFloat(seconds) : seconds;
    // Handle invalid numbers
    if (isNaN(numSeconds)) return '0.0s';
    return `${numSeconds.toFixed(1)}s`;
  };

  // Error state
  if (!isSuccess) {
    return (
      <div className="min-h-screen">
        {/* Header - Fixed like other pages */}
        <div className="sticky top-0 bg-neutral-950 z-10 px-6 py-6">
          <div className="mb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div>
                  <div className="flex items-center gap-3">
                    <h1 className="text-xl font-semibold text-white">Processing Failed</h1>
                    {/* Status Pills */}
                    <div className="flex items-center gap-1">
                      <div className="flex items-center gap-1 px-2 py-0.5 bg-neutral-900 rounded-full">
                        <XCircle className="h-3 w-3 text-red-400" />
                        <span className="text-[10px] text-red-400">Error</span>
                      </div>
                    </div>
                  </div>
                  <p className="text-xs text-neutral-500 mt-0.5">Something went wrong during processing</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {/* Compact action buttons */}
                <div className="flex items-center">
                  <Button
                    onClick={onReset}
                    size="sm"
                    variant="ghost"
                    className="h-6 px-2 text-[10px] hover:bg-neutral-900 text-neutral-500"
                  >
                    <RefreshCw className="h-3 w-3" />
                  </Button>

                  <TooltipProvider>
                    <Tooltip delayDuration={200}>
                      <TooltipTrigger asChild>
                        <Button
                          onClick={() => {
                            archiveCurrentVideo();
                            navigateToVideo(-1);
                          }}
                          size="sm"
                          variant="ghost"
                          className="h-6 px-2 text-[10px] hover:bg-neutral-900 text-neutral-500"
                        >
                          <XCircle className="h-3 w-3" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent side="bottom" className="bg-neutral-900 border-neutral-800">
                        <p className="text-xs">Delete from cache</p>
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
          <div className="max-w-2xl">
            <div className="bg-neutral-950 rounded-lg border border-neutral-900 p-6">
              <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="h-4 w-4 text-red-400 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm text-red-400 font-medium mb-1">Error Details</p>
                    <p className="text-xs text-neutral-400">
                      {result.error || "Failed to start processing"}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-center gap-2 mt-4">
              <Button
                onClick={onReset}
                size="sm"
                variant="ghost"
                className="h-8 px-3 text-xs hover:bg-neutral-900 text-neutral-400"
              >
                <RefreshCw className="h-3 w-3 mr-1.5" />
                Try Again
              </Button>

              <Button
                onClick={() => window.location.href = 'mailto:support@dabu.ai'}
                size="sm"
                variant="ghost"
                className="h-8 px-3 text-xs hover:bg-neutral-900 text-neutral-400"
              >
                Contact Support
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Loading state
  if (isLoading && isSuccess) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6">
        <div className="text-center">
          <Loader2 className="h-8 w-8 text-purple-400 animate-spin mx-auto mb-4" />
          <p className="text-sm text-neutral-500">Loading your video...</p>
        </div>
      </div>
    );
  }

  // Success state
  return (
    <div className="min-h-screen">
      {/* Header - Fixed */}
      <div className="sticky top-0 bg-neutral-950 z-10 px-6 py-6">
        <div className="mb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-xl font-semibold text-white">TikTok Ad Ready</h1>
                  {/* Status Pills */}
                  <div className="flex items-center gap-1">
                    <div className="flex items-center gap-1 px-2 py-0.5 bg-neutral-900 rounded-full">
                      <CheckCircle2 className="h-3 w-3 text-green-400" />
                      <span className="text-[10px] text-green-400">Processed</span>
                    </div>
                    <div className="flex items-center gap-1 px-2 py-0.5 bg-neutral-900 rounded-full">
                      <FileText className="h-3 w-3 text-neutral-600" />
                      <span className="text-[10px] text-neutral-500">{timestampsData?.script_segments?.length || 0} cuts</span>
                    </div>
                    <div className="flex items-center gap-1 px-2 py-0.5 bg-neutral-900 rounded-full">
                      <Clock className="h-3 w-3 text-neutral-600" />
                      <span className="text-[10px] text-neutral-500">{timestampsData?.total_duration ? formatTime(timestampsData.total_duration) : '0s'} analysed</span>
                    </div>
                  </div>
                </div>
                <p className="text-xs text-neutral-500 mt-0.5">AI-matched segments with{result.captionedVideoUrl ? ' captions and' : ''} voiceover ready for TikTok</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {/* Compact action buttons */}
              <div className="flex items-center">
                <TooltipProvider>
                  <Tooltip delayDuration={200}>
                    <TooltipTrigger asChild>
                      <Button
                        onClick={onReset}
                        size="sm"
                        variant="ghost"
                        className="h-6 px-2 text-[10px] hover:bg-neutral-900 text-neutral-500"
                      >
                        <Sparkles className="h-3 w-3" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="bg-neutral-900 border-neutral-800">
                      <p className="text-xs">Process another simultaneously</p>
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
                        }}
                        size="sm"
                        variant="ghost"
                        className="h-6 px-2 text-[10px] hover:bg-neutral-900 text-neutral-500"
                      >
                        <XCircle className="h-3 w-3" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="bg-neutral-900 border-neutral-800">
                      <p className="text-xs">Delete from cache</p>
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

      {/* Main Content - Two Column Layout */}
      <div className="px-6 pb-6">
        <div className="lg:flex lg:gap-6">
          {/* Left Half - Video (Fixed Position) */}
          <div className="hidden lg:block lg:w-[320px] lg:flex-shrink-0">
            <div className="bg-neutral-950 rounded-lg border border-neutral-900 p-5 lg:sticky lg:top-[110px]">
              <div className="mb-3">
                <h3 className="text-sm font-medium text-white mb-1">Your Video</h3>
                <p className="text-xs text-neutral-500">Portrait mode (9:16)</p>
              </div>

              {/* Video Player */}
              <div className="aspect-[9/16] bg-black rounded-lg overflow-hidden mb-4">
                {(result.captionedVideoUrl || result.videoUrl) ? (
                  <video
                    controls
                    className="w-full h-full object-contain"
                    src={ensureAbsoluteUrl(result.captionedVideoUrl || result.videoUrl)}
                  >
                    Your browser does not support the video tag.
                  </video>
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <Video className="h-12 w-12 text-neutral-600" />
                  </div>
                )}
              </div>

              {/* Download buttons */}
              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={() => handleDownload(result.captionedVideoUrl || result.videoUrl, 'tiktok_video.mp4')}
                  className="flex-1 bg-white hover:bg-neutral-200 text-black font-medium"
                >
                  <Video className="h-3.5 w-3.5 mr-1.5" />
                  Download Video
                </Button>

                {result.projectBundleUrl && (
                  <Button
                    size="sm"
                    onClick={() => handleDownload(result.projectBundleUrl, 'capcut_project.zip')}
                    variant="outline"
                    className="border-neutral-800 hover:bg-neutral-900 text-neutral-400"
                  >
                    <Package className="h-3.5 w-3.5 mr-1.5" />
                    CapCut
                  </Button>
                )}
              </div>
            </div>
          </div>

          {/* Mobile Video Section */}
          <div className="lg:hidden mb-4">
            <div className="bg-neutral-950 rounded-lg border border-neutral-900 p-5">
              <div className="mb-3">
                <h3 className="text-sm font-medium text-white mb-1">Your Video</h3>
                <p className="text-xs text-neutral-500">Portrait mode (9:16)</p>
              </div>

              {/* Video Player */}
              <div className="aspect-[9/16] bg-black rounded-lg overflow-hidden mb-4">
                {(result.captionedVideoUrl || result.videoUrl) ? (
                  <video
                    controls
                    className="w-full h-full object-contain"
                    src={ensureAbsoluteUrl(result.captionedVideoUrl || result.videoUrl)}
                  >
                    Your browser does not support the video tag.
                  </video>
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <Video className="h-12 w-12 text-neutral-600" />
                  </div>
                )}
              </div>

              {/* Download buttons */}
              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={() => handleDownload(result.captionedVideoUrl || result.videoUrl, 'tiktok_video.mp4')}
                  className="flex-1 bg-white hover:bg-neutral-200 text-black font-medium"
                >
                  <Video className="h-3.5 w-3.5 mr-1.5" />
                  Download Video
                </Button>

                {result.projectBundleUrl && (
                  <Button
                    size="sm"
                    onClick={() => handleDownload(result.projectBundleUrl, 'capcut_project.zip')}
                    variant="outline"
                    className="border-neutral-800 hover:bg-neutral-900 text-neutral-400"
                  >
                    <Package className="h-3.5 w-3.5 mr-1.5" />
                    CapCut
                  </Button>
                )}
              </div>
            </div>
          </div>

          {/* Right Half - Timeline & Script (Scrollable) */}
          <div className="flex-1">
            <div className="space-y-4">
              {/* Segments Timeline */}
              <div className="bg-neutral-950 rounded-lg border border-neutral-900 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-sm font-medium text-white mb-1">Scene Breakdown</h3>
                    <p className="text-xs text-neutral-500">AI-matched segments</p>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleDownload(result.timestampsUrl, 'timestamps.json')}
                    className="text-neutral-500 hover:text-white"
                  >
                    <Download className="h-3.5 w-3.5" />
                  </Button>
                </div>

                <div className="space-y-2 max-h-[400px] overflow-y-auto scrollbar-thin pr-1">
                  {timestampsData?.script_segments && timestampsData.script_segments.length > 0 ? (
                    timestampsData.script_segments.map((segment: any, index: number) => (
                      <div
                        key={index}
                        onClick={() => setSelectedSegment(index)}
                        className={`p-3 rounded-lg border transition-all cursor-pointer ${selectedSegment === index
                            ? 'bg-purple-500/5 border-purple-500/20'
                            : 'bg-neutral-900 border-neutral-800 hover:border-neutral-700'
                          }`}
                      >
                        {/* Top Row - Clean and minimal */}
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2.5">
                            <span className="text-xs font-medium text-white">
                              {String(index + 1).padStart(2, '0')}
                            </span>

                            {/* Simple confidence bar */}
                            {segment.confidence && (
                              <div className="flex items-center gap-1.5">
                                <div className="h-0.5 w-8 bg-neutral-800 rounded-full overflow-hidden">
                                  <div
                                    className={`h-full rounded-full ${segment.confidence >= 0.9
                                        ? 'bg-green-500/60'
                                        : segment.confidence >= 0.7
                                          ? 'bg-yellow-500/60'
                                          : 'bg-orange-500/60'
                                      }`}
                                    style={{ width: `${segment.confidence * 100}%` }}
                                  />
                                </div>
                                <span className="text-[9px] text-neutral-600">
                                  {Math.round(segment.confidence * 100)}%
                                </span>
                              </div>
                            )}
                          </div>

                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3 text-neutral-600" />
                            <span className="text-xs text-neutral-500">
                              {segment.duration_seconds ? `${segment.duration_seconds.toFixed(1)}s` : '0s'}
                            </span>
                          </div>
                        </div>

                        {/* Script Text */}
                        <p className="text-xs text-neutral-300 mb-1.5">
                          {segment.segment_text}
                        </p>

                        {/* Visual Description - Very subtle */}
                        {segment.visual_description && (
                          <p className="text-[10px] text-neutral-600 leading-relaxed">
                            {segment.visual_description}
                          </p>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8">
                      <p className="text-xs text-neutral-500">No scene data available</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Script Section */}
              <div className="bg-neutral-950 rounded-lg border border-neutral-900 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-sm font-medium text-white mb-1">Script</h3>
                    <p className="text-xs text-neutral-500">Narration content</p>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={copyScript}
                    className="text-neutral-500 hover:text-white"
                  >
                    {copied ? (
                      <Check className="h-3.5 w-3.5" />
                    ) : (
                      <Copy className="h-3.5 w-3.5" />
                    )}
                  </Button>
                </div>

                <div className="bg-neutral-900 rounded-lg p-4 max-h-[200px] overflow-y-auto scrollbar-thin">
                  <p className="text-sm text-neutral-300 leading-relaxed whitespace-pre-wrap">
                    {scriptContent || "Loading script..."}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
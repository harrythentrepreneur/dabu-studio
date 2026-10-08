"use client";

import { Card, CardContent } from "@/components/ui/card";
import { useStore, VideoResult } from "@/lib/store";
import { Button } from "@/components/ui/button";
import { Play, Upload, FileText, Volume2 } from "lucide-react";
import { VideoUploadSection } from "./video-upload-section";
import { ScriptInputSection } from "./script-input-section";
import { VoiceoverUploadSection } from "./voiceover-upload-section";
import { ProcessingStatus } from "./processing-status";
import { ResultsDisplay } from "./results-display";
import { StandardSection } from "./shared/StandardSection";
import { useState, useEffect, useRef } from "react";
import API_ENDPOINTS from "@/lib/api-config";

interface StatusUpdate {
  step: number;
  step_name: string;
  progress: number;
  message: string;
  error?: string;
  success?: boolean;
  result?: any;
  timestamp: string;
}

export function MainSection() {
  const {
    processingStatus,
    setProcessingStatus,
    addVideoToCache,
    updateVideoInCache,
    getCurrentVideo,
    currentVideoIndex,
    videoCache
  } = useStore();

  // Local state for form handling
  const [videos, setVideos] = useState<File[]>([]);
  const [script, setScript] = useState("");
  const [voiceover, setVoiceover] = useState<File | null>(null);
  const [isNewVideo, setIsNewVideo] = useState(true);
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  const [currentEventSource, setCurrentEventSource] = useState<EventSource | null>(null);
  const [currentVideoId, setCurrentVideoId] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Get current video from cache
  const currentVideo = getCurrentVideo();

  const handleProcess = async () => {
    if (!script || videos.length === 0) {
      return;
    }

    // Create a placeholder video entry
    const videoId = `video-${Date.now()}`;
    setCurrentVideoId(videoId);
    const startTime = Date.now();

    const placeholderVideo: VideoResult = {
      id: videoId,
      createdAt: Date.now(),
      archived: false,
      status: 'processing' as const,
      currentStep: 0,
      progress: 0,
      statusMessage: 'Initializing...',
      processingStartTime: startTime,
    };

    // Add to cache immediately when processing starts
    addVideoToCache(placeholderVideo);
    setIsNewVideo(false);

    setProcessingStatus("processing");
    setCurrentStep(0);
    setProgress(0);
    setStatusMessage("Initializing...");

    const formData = new FormData();
    formData.append("script", script);
    formData.append("target_duration", "30");
    formData.append("use_mock", "false");

    videos.forEach(video => {
      formData.append("videos", video);
    });

    if (voiceover) {
      formData.append("voiceover", voiceover);
    }

    try {
      // Get a request ID from the backend
      const requestIdResponse = await fetch(`${API_ENDPOINTS.process.replace('/process', '/generate-request-id')}`);
      const requestIdData = await requestIdResponse.json();
      const requestId = requestIdData.request_id;

      formData.append("request_id", requestId);

      // Set up SSE connection with reconnection logic
      const connectSSE = () => {
        const eventSource = new EventSource(API_ENDPOINTS.statusStream(requestId));
        eventSourceRef.current = eventSource;
        setCurrentEventSource(eventSource);

        let reconnectAttempts = 0;
        const maxReconnectAttempts = 5;

        eventSource.onmessage = (event) => {
          try {
            const statusUpdate: StatusUpdate = JSON.parse(event.data);

            // Handle completion
            if (statusUpdate.success && statusUpdate.result) {
              const urls = statusUpdate.result.download_urls;
              const ensureAbsoluteUrl = (url: string) => {
                if (!url) return url;
                if (url.startsWith('http')) return url;
                return `${API_ENDPOINTS.process.replace('/api/process', '')}${url}`;
              };

              const updatedData = {
                videoUrl: ensureAbsoluteUrl(urls?.video),
                scriptUrl: ensureAbsoluteUrl(urls?.script),
                timestampsUrl: ensureAbsoluteUrl(urls?.timestamps),
                mergedFullUrl: ensureAbsoluteUrl(urls?.merged_full),
                segments: statusUpdate.result.metadata?.segments,
                status: 'complete' as const,
                progress: 100,
                statusMessage: 'Processing complete!'
              };

              if (updateVideoInCache) {
                updateVideoInCache(videoId, updatedData);
              }
              setProcessingStatus("completed");
              setProgress(100);
              setStatusMessage("Processing complete!");
              eventSource.close();
              eventSourceRef.current = null;
              setCurrentEventSource(null);
            }

            // Handle errors
            if (statusUpdate.error) {
              if (updateVideoInCache) {
                updateVideoInCache(videoId, {
                  error: statusUpdate.error,
                  status: 'error' as const
                });
              }
              setProcessingStatus("idle");
              eventSource.close();
              eventSourceRef.current = null;
              setCurrentEventSource(null);
            }

            // Handle regular status updates
            if (statusUpdate.step > 0) {
              setCurrentStep(statusUpdate.step);
              setProgress(statusUpdate.progress);
              setStatusMessage(statusUpdate.message);

              if (updateVideoInCache) {
                updateVideoInCache(videoId, {
                  currentStep: statusUpdate.step,
                  progress: statusUpdate.progress,
                  statusMessage: statusUpdate.message
                });
              }
            }
          } catch (err) {
            console.error("Error parsing SSE data:", err);
          }
        };

        eventSource.onerror = (error) => {
          console.error("SSE connection error:", error);
          eventSource.close();

          // Try to reconnect if under the limit
          if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            console.log(`Attempting to reconnect SSE (${reconnectAttempts}/${maxReconnectAttempts})...`);
            setTimeout(() => {
              connectSSE();
            }, 2000 * reconnectAttempts); // Exponential backoff
          } else {
            // Max reconnect attempts reached, poll for final status
            console.log("Max SSE reconnect attempts reached, polling for final status...");
            pollForStatus(requestId, videoId);
          }
        };
      };

      // Polling fallback function
      const pollForStatus = async (reqId: string, vidId: string) => {
        const pollInterval = setInterval(async () => {
          try {
            const response = await fetch(`${API_ENDPOINTS.process.replace('/process', '/status')}/${reqId}`);
            const data = await response.json();

            if (data.status === 'completed' && data.download_urls) {
              clearInterval(pollInterval);
              const urls = data.download_urls;
              const ensureAbsoluteUrl = (url: string) => {
                if (!url) return url;
                if (url.startsWith('http')) return url;
                return `${API_ENDPOINTS.process.replace('/api/process', '')}${url}`;
              };

              const updatedData = {
                videoUrl: ensureAbsoluteUrl(urls?.video),
                scriptUrl: ensureAbsoluteUrl(urls?.script),
                timestampsUrl: ensureAbsoluteUrl(urls?.timestamps),
                mergedFullUrl: ensureAbsoluteUrl(urls?.merged_full),
                segments: data.metadata?.segments,
                status: 'complete' as const,
                progress: 100,
                statusMessage: 'Processing complete!'
              };

              if (updateVideoInCache) {
                updateVideoInCache(vidId, updatedData);
              }
              setProcessingStatus("completed");
              setProgress(100);
              setStatusMessage("Processing complete!");
            } else if (data.status === 'error') {
              clearInterval(pollInterval);
              if (updateVideoInCache) {
                updateVideoInCache(vidId, {
                  error: data.error || 'Processing failed',
                  status: 'error' as const
                });
              }
              setProcessingStatus("idle");
            }
          } catch (err) {
            console.error("Polling error:", err);
          }
        }, 3000); // Poll every 3 seconds

        // Clean up after 5 minutes
        setTimeout(() => {
          clearInterval(pollInterval);
        }, 300000);
      };

      // Connect SSE before starting processing
      connectSSE();

      // Start the processing request
      const processResponse = await fetch(API_ENDPOINTS.process, {
        method: "POST",
        body: formData,
      });

      // If the response is immediate (not relying on SSE), handle it
      if (processResponse.ok) {
        const data = await processResponse.json();
        if (data.success && data.download_urls && !eventSourceRef.current) {
          // SSE might have disconnected, use the direct response
          const urls = data.download_urls;
          const ensureAbsoluteUrl = (url: string) => {
            if (!url) return url;
            if (url.startsWith('http')) return url;
            return `${API_ENDPOINTS.process.replace('/api/process', '')}${url}`;
          };

          const updatedData = {
            videoUrl: ensureAbsoluteUrl(urls?.video),
            scriptUrl: ensureAbsoluteUrl(urls?.script),
            timestampsUrl: ensureAbsoluteUrl(urls?.timestamps),
            mergedFullUrl: ensureAbsoluteUrl(urls?.merged_full),
            segments: data.metadata?.segments_count,
            status: 'complete' as const,
            progress: 100,
            statusMessage: 'Processing complete!'
          };

          if (updateVideoInCache) {
            updateVideoInCache(videoId, updatedData);
          }
          setProcessingStatus("completed");
          setProgress(100);
          setStatusMessage("Processing complete!");
        }
      }

    } catch (error) {
      console.error("Processing error:", error);
      if (currentEventSource) {
        currentEventSource.close();
        setCurrentEventSource(null);
      }
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      setProcessingStatus("idle");
    }
  };

  const handleCreateNew = () => {
    setIsNewVideo(true);
    setVideos([]);
    setScript("");
    setVoiceover(null);
    setProcessingStatus("idle");
  };

  // Clean up SSE on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (currentEventSource) {
        currentEventSource.close();
      }
    };
  }, [currentEventSource]);

  // Watch for video navigation
  useEffect(() => {
    if (currentVideo && !isNewVideo) {
      // Video from cache is being viewed
      if (currentVideo.status === 'complete' || currentVideo.videoUrl) {
        setProcessingStatus("completed");
      } else if (currentVideo.status === 'processing') {
        setProcessingStatus("processing");
        setCurrentStep(currentVideo.currentStep || 0);
        setProgress(currentVideo.progress || 0);
        setStatusMessage(currentVideo.statusMessage || "Processing...");
      }
    }
  }, [currentVideoIndex, currentVideo, isNewVideo, setProcessingStatus]);

  const canProcess = videos.length >= 1 && script.length > 50;

  // Create items for the processing overview card
  const processingItems = [
    {
      id: "videos",
      label: "Video Files",
      value: videos.length,
      percentage: videos.length > 0 ? Math.min(videos.length * 20, 100) : 0
    },
    {
      id: "script",
      label: "Script Length",
      value: `${script.split(" ").filter(w => w.length > 0).length} words`,
      percentage: script.length > 0 ? Math.min((script.length / 500) * 100, 100) : 0
    },
    {
      id: "voiceover",
      label: "Voiceover",
      value: voiceover ? "Uploaded" : "None",
      percentage: voiceover ? 100 : 0
    }
  ];

  return (
    <div className="space-y-6">
      {/* Processing Overview Card */}
      <Card>
        <CardContent className="p-0 w-full">
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-4">
                <div className="text-lg font-semibold flex items-center gap-1.5 opacity-90">
                  <div className="w-5 h-5 bg-white rounded flex items-center justify-center">
                    <span className="text-xs font-bold text-black">V</span>
                  </div>
                  Video Ad Automation
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Button
                  onClick={handleProcess}
                  disabled={!canProcess || processingStatus === "processing"}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <Play className="w-4 h-4 mr-2" />
                  {processingStatus === "processing" ? "Processing..." : "Start Processing"}
                </Button>
              </div>
            </div>

            {/* Processing Status */}
            {processingStatus !== "idle" && (
              <div className="mb-4">
                <ProcessingStatus
                  currentStep={1}
                  progress={0}
                  statusMessage="Processing..."
                  isQuickCreate={false}
                />
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Only show upload sections for new videos */}
      {isNewVideo && (
        <>
          {/* Upload Sections */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Video Upload */}
            <VideoUploadSection
              videos={videos}
              setVideos={setVideos}
            />

            {/* Script Input */}
            <ScriptInputSection
              script={script}
              setScript={setScript}
            />
          </div>

          {/* Optional Voiceover Section */}
          <VoiceoverUploadSection
            voiceover={voiceover}
            setVoiceover={setVoiceover}
          />

          {/* Processing Overview */}
          <StandardSection
            title="Processing Overview"
            items={processingItems}
            countLabel="Status"
            maxDisplay={6}
          />
        </>
      )}

      {/* Results Display */}
      {processingStatus === "completed" && !isNewVideo && currentVideo && (
        <ResultsDisplay
          results={currentVideo}
          processingState="complete"
          onReset={handleCreateNew}
        />
      )}

      {/* Show upload sections only for new videos */}
      {isNewVideo && processingStatus === "idle" && (
        <div className="text-center py-8">
          <p className="text-neutral-400 mb-4">Start by uploading videos and adding your script above</p>
        </div>
      )}
    </div>
  );
}
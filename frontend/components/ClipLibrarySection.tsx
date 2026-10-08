"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Sparkles, Download, RefreshCw, FileText, Video, Share2 } from "lucide-react";
import { ScriptInputSection } from "./clip-studio/ScriptInputSection";
import { ResultsDisplay } from "./clip-studio/ResultsDisplay";
import { ProcessingStatus } from "./clip-studio/ProcessingStatus";
import { useState } from "react";
import { analyzeScriptWithGemini } from "@/lib/clip-studio/gemini-service";
import { searchClipsWithKlipy } from "@/lib/clip-studio/klipy-service";
import { findBestClipsForMoment } from "@/lib/clip-studio/simple-clip-search";
import { ClipMoment } from "@/lib/clip-studio/types";
import { toast } from "@/hooks/use-toast";

export function ClipLibrarySection() {
  const [script, setScript] = useState("");
  const [clipMoments, setClipMoments] = useState<ClipMoment[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState("");
  const [downloadedClips, setDownloadedClips] = useState<Set<string>>(new Set());
  const [abortController, setAbortController] = useState<AbortController | null>(null);

  const handleAnalyze = async () => {
    // Validation
    const trimmedScript = script.trim();
    
    if (!trimmedScript || trimmedScript.length < 50) {
      toast({
        title: "Script too short",
        description: "Please enter at least 50 characters",
        variant: "destructive"
      });
      return;
    }

    if (trimmedScript.length > 5000) {
      toast({
        title: "Script too long", 
        description: `Script is ${trimmedScript.length} characters. Maximum is 5000.`,
        variant: "destructive"
      });
      return;
    }

    setIsProcessing(true);
    setClipMoments([]);
    setDownloadedClips(new Set());
    
    // Create abort controller for potential cancellation
    const controller = new AbortController();
    setAbortController(controller);
    
    try {
      // Step 1: Analyze script with Gemini AI
      setProcessingStep("Analyzing script");
      console.log('Starting Gemini analysis for script:', trimmedScript.substring(0, 100) + '...');
      
      // Add a small delay to show the first step
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const moments = await analyzeScriptWithGemini(trimmedScript);
      
      if (!moments || moments.length === 0) {
        toast({
          title: "No moments found",
          description: "Could not identify clip opportunities. Try adding more descriptive language.",
          variant: "destructive"
        });
        return;
      }

      console.log(`Gemini analysis complete: ${moments.length} moments found`);

      // Step 2: Finding clip moments
      setProcessingStep("Finding clip moments");
      await new Promise(resolve => setTimeout(resolve, 800));

      // Step 3: Searching for clips
      setProcessingStep("Searching clips");
      console.log('Using simple search strategy for optimal clip discovery');
      
      // Process each moment with simple search
      const momentsWithClips = await Promise.all(
        moments.map(async (moment, index) => {
          try {
            const bestClips = await findBestClipsForMoment(moment);
            return {
              ...moment,
              clips: bestClips
            };
          } catch (error) {
            console.warn(`Simple search failed for moment ${moment.id}, falling back to basic search:`, error);
            // Fallback to basic search if advanced fails
            const fallbackMoments = await searchClipsWithKlipy([moment]);
            return fallbackMoments[0] || { ...moment, clips: [] };
          }
        })
      );
      
      // Step 4: Optimizing results
      setProcessingStep("Optimizing results");
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Count how many moments have clips
      const momentsWithResults = momentsWithClips.filter(m => m.clips && m.clips.length > 0);
      
      if (momentsWithResults.length === 0) {
        toast({
          title: "No clips found",
          description: "Could not find matching clips. Try refreshing or modifying your script.",
          variant: "destructive"
        });
        setClipMoments(momentsWithClips); // Still show moments even if no clips
      } else {
        setClipMoments(momentsWithClips);
        toast({
          title: "Analysis complete",
          description: `Found ${momentsWithResults.length} moments with clips (${momentsWithClips.length} total moments)`
        });
      }
    } catch (error) {
      console.error("Error analyzing script:", error);
      toast({
        title: "Analysis failed",
        description: error instanceof Error ? error.message : "An unexpected error occurred. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsProcessing(false);
      setProcessingStep("");
    }
  };

  const handleDownloadClip = async (clipUrl: string, clipId: string) => {
    try {
      // Track download
      setDownloadedClips(prev => new Set(prev).add(clipId));
      
      // Fetch the clip as a blob
      const response = await fetch(clipUrl);
      const blob = await response.blob();
      
      // Create a blob URL
      const blobUrl = URL.createObjectURL(blob);
      
      // Create a download link
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = `clip-${clipId}.mp4`;
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      
      // Clean up
      document.body.removeChild(link);
      URL.revokeObjectURL(blobUrl);
      
      toast({
        title: "Clip downloaded",
        description: "Clip has been downloaded to your device"
      });
    } catch (error) {
      console.error('Error downloading clip:', error);
      toast({
        title: "Download failed",
        description: "Failed to download the clip. Please try again.",
        variant: "destructive"
      });
    }
  };

  const handleRefreshClips = async (momentId: string) => {
    const moment = clipMoments.find(m => m.id === momentId);
    if (!moment) {
      console.error(`Moment ${momentId} not found`);
      return;
    }

    setIsProcessing(true);
    
    try {
      // Show specific processing message
      const shortExcerpt = moment.scriptExcerpt.length > 30 
        ? moment.scriptExcerpt.substring(0, 30) + "..." 
        : moment.scriptExcerpt;
      setProcessingStep(`Refreshing clips for "${shortExcerpt}"...`);
      
      // Search with refresh flag
      const refreshedMoments = await searchClipsWithKlipy([moment], true);
      
      if (refreshedMoments && refreshedMoments.length > 0) {
        const refreshedMoment = refreshedMoments[0];
        
        // Update only this specific moment
        setClipMoments(prev => prev.map(m => 
          m.id === momentId ? refreshedMoment : m
        ));
        
        // Show success message with count
        const clipCount = refreshedMoment.clips?.length || 0;
        toast({
          title: "Clips refreshed",
          description: clipCount > 0 
            ? `Found ${clipCount} new clip suggestions` 
            : "No new clips found. Try different search terms."
        });
      }
    } catch (error) {
      console.error("Error refreshing clips:", error);
      toast({
        title: "Refresh failed",
        description: "Could not refresh clips. Please check your connection and try again.",
        variant: "destructive"
      });
    } finally {
      setIsProcessing(false);
      setProcessingStep("");
    }
  };

  const canAnalyze = script.length >= 50 && !isProcessing;

  return (
    <div className="pt-6 space-y-3">
      {/* Hero Card - Express Builder Style */}
      <Card>
        <CardContent className="py-8">
          <div className="text-center space-y-4">
            <h1 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100">
              Transform Your Script with AI-Powered Clip Suggestions
            </h1>
            <p className="text-neutral-600 dark:text-neutral-400 max-w-xl mx-auto">
              AI analyzes your content and matches perfect video clips to enhance your storytelling
            </p>

            {/* Feature Pills - Express Builder Style */}
            <div className="flex flex-wrap gap-2 justify-center pt-2">
              <div className="flex items-center gap-1.5 px-3 py-1.5 bg-neutral-100 dark:bg-neutral-800 rounded-full">
                <FileText className="h-3.5 w-3.5 text-neutral-600 dark:text-neutral-400" />
                <span className="text-xs font-medium text-neutral-700 dark:text-neutral-300">Script Analysis</span>
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1.5 bg-neutral-100 dark:bg-neutral-800 rounded-full">
                <Video className="h-3.5 w-3.5 text-neutral-600 dark:text-neutral-400" />
                <span className="text-xs font-medium text-neutral-700 dark:text-neutral-300">Video Clip Library</span>
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1.5 bg-neutral-100 dark:bg-neutral-800 rounded-full">
                <Share2 className="h-3.5 w-3.5 text-neutral-600 dark:text-neutral-400" />
                <span className="text-xs font-medium text-neutral-700 dark:text-neutral-300">Instant Export</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Script Input Section */}
      <ScriptInputSection
        script={script}
        setScript={setScript}
        onAnalyze={handleAnalyze}
        isProcessing={isProcessing}
        characterCount={script.length}
      />

      {/* Process Button - Express Builder Style */}
      {!isProcessing && script.length > 0 && (
        <div className="flex justify-center py-4">
          <Button
            size="lg"
            onClick={handleAnalyze}
            disabled={!canAnalyze}
            className="px-8 py-4 text-base font-semibold bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
          >
            <Sparkles className="mr-2 h-5 w-5" />
            Analyze Script for Clips
          </Button>
        </div>
      )}

      {/* Processing Status */}
      {isProcessing && (
        <Card>
          <CardContent className="py-6">
            <ProcessingStatus message={processingStep} step={processingStep} />
          </CardContent>
        </Card>
      )}

      {/* Results Display */}
      {clipMoments.length > 0 && (
        <>
          {/* Results Header */}
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
              Clip Suggestions
            </h2>
            {downloadedClips.size > 0 && (
              <div className="flex items-center gap-2 text-sm text-neutral-500 dark:text-neutral-400">
                <Download className="w-4 h-4" />
                <span>{downloadedClips.size} clips downloaded</span>
              </div>
            )}
          </div>
          
          <ResultsDisplay
            script={script}
            clipMoments={clipMoments}
            onDownloadClip={handleDownloadClip}
            onRefreshClips={handleRefreshClips}
            downloadedClips={downloadedClips}
          />
        </>
      )}
    </div>
  );
}
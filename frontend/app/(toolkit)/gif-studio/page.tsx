"use client";

import { useState } from "react";
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
  ChevronRight,
  Image,
  Download,
  RefreshCw,
  Info,
  Clock,
  Zap,
  Brain,
  Share2
} from "lucide-react";
import { analyzeScriptWithGemini } from "@/lib/gif-studio/gemini-service";
import { searchGifsWithKlipy } from "@/lib/gif-studio/klipy-service";
import { findBestGifsForMoment } from "@/lib/gif-studio/simple-gif-search";
import { GifMoment } from "@/lib/gif-studio/types";
import { toast } from "@/hooks/use-toast";
import { ProcessingStatus } from "@/components/gif-studio/ProcessingStatus";

export default function GifStudioPage() {
  const [script, setScript] = useState("");
  const [gifMoments, setGifMoments] = useState<GifMoment[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState("");
  const [downloadedGifs, setDownloadedGifs] = useState<Set<string>>(new Set());
  const [hoveredMomentId, setHoveredMomentId] = useState<string | null>(null);

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

  const handleAnalyze = async () => {
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
    setGifMoments([]);
    setDownloadedGifs(new Set());
    
    try {
      setProcessingStep("Analyzing script");
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const moments = await analyzeScriptWithGemini(trimmedScript);
      
      if (!moments || moments.length === 0) {
        toast({
          title: "No moments found",
          description: "Could not identify GIF opportunities. Try adding more descriptive language.",
          variant: "destructive"
        });
        return;
      }

      setProcessingStep("Finding GIF moments");
      await new Promise(resolve => setTimeout(resolve, 800));
      
      setProcessingStep("Searching GIFs");
      
      const momentsWithGifs = await Promise.all(
        moments.map(async (moment) => {
          try {
            const bestGifs = await findBestGifsForMoment(moment);
            return {
              ...moment,
              gifs: bestGifs
            };
          } catch (error) {
            console.warn(`Search failed for moment ${moment.id}:`, error);
            const fallbackMoments = await searchGifsWithKlipy([moment]);
            return fallbackMoments[0] || { ...moment, gifs: [] };
          }
        })
      );
      
      setProcessingStep("Optimizing results");
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const momentsWithResults = momentsWithGifs.filter(m => m.gifs && m.gifs.length > 0);
      
      if (momentsWithResults.length === 0) {
        toast({
          title: "No GIFs found",
          description: "Could not find matching GIFs. Try refreshing or modifying your script.",
          variant: "destructive"
        });
        setGifMoments(momentsWithGifs);
      } else {
        setGifMoments(momentsWithGifs);
        toast({
          title: "Analysis complete",
          description: `Found ${momentsWithResults.length} moments with GIFs`
        });
      }
    } catch (error) {
      console.error("Error analyzing script:", error);
      toast({
        title: "Analysis failed",
        description: error instanceof Error ? error.message : "An unexpected error occurred.",
        variant: "destructive"
      });
    } finally {
      setIsProcessing(false);
      setProcessingStep("");
    }
  };

  const handleDownloadGif = async (gifUrl: string, gifId: string) => {
    try {
      setDownloadedGifs(prev => new Set(prev).add(gifId));
      
      const response = await fetch(gifUrl);
      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = `gif-${gifId}.gif`;
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      
      document.body.removeChild(link);
      URL.revokeObjectURL(blobUrl);
      
      toast({
        title: "GIF downloaded",
        description: "GIF has been downloaded to your device"
      });
    } catch (error) {
      console.error('Error downloading GIF:', error);
      toast({
        title: "Download failed",
        description: "Failed to download the GIF.",
        variant: "destructive"
      });
    }
  };

  const handleRefreshGifs = async (momentId: string) => {
    const moment = gifMoments.find(m => m.id === momentId);
    if (!moment) return;

    setIsProcessing(true);
    
    try {
      const shortExcerpt = moment.scriptExcerpt.length > 30 
        ? moment.scriptExcerpt.substring(0, 30) + "..." 
        : moment.scriptExcerpt;
      setProcessingStep(`Refreshing GIFs for "${shortExcerpt}"...`);
      
      const refreshedMoments = await searchGifsWithKlipy([moment], true);
      
      if (refreshedMoments && refreshedMoments.length > 0) {
        const refreshedMoment = refreshedMoments[0];
        
        setGifMoments(prev => prev.map(m => 
          m.id === momentId ? refreshedMoment : m
        ));
        
        const gifCount = refreshedMoment.gifs?.length || 0;
        toast({
          title: "GIFs refreshed",
          description: gifCount > 0 
            ? `Found ${gifCount} new GIF suggestions` 
            : "No new GIFs found. Try different search terms."
        });
      }
    } catch (error) {
      console.error("Error refreshing GIFs:", error);
      toast({
        title: "Refresh failed",
        description: "Could not refresh GIFs.",
        variant: "destructive"
      });
    } finally {
      setIsProcessing(false);
      setProcessingStep("");
    }
  };

  const getHighlightedScript = () => {
    if (!hoveredMomentId || !script) return script;
    
    const moment = gifMoments.find(m => m.id === hoveredMomentId);
    if (!moment) return script;
    
    const excerpt = moment.scriptExcerpt;
    const index = script.toLowerCase().indexOf(excerpt.toLowerCase());
    
    if (index === -1) return script;
    
    return (
      <>
        {script.substring(0, index)}
        <span className="bg-yellow-400/30 text-white font-medium">
          {script.substring(index, index + excerpt.length)}
        </span>
        {script.substring(index + excerpt.length)}
      </>
    );
  };

  return (
    <div className="min-h-screen">
      {/* Header - Fixed */}
      <div className="sticky top-0 bg-neutral-950 z-10 px-6 py-6">
        <div className="mb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-xl font-semibold text-white">GIF Studio</h1>
                  {/* Feature Pills */}
                  <div className="flex items-center gap-1">
                    <div className="flex items-center gap-1 px-2 py-0.5 bg-neutral-900 rounded-full">
                      <Brain className="h-3 w-3 text-neutral-600" />
                      <span className="text-[10px] text-neutral-500">AI Analysis</span>
                    </div>
                    <div className="flex items-center gap-1 px-2 py-0.5 bg-neutral-900 rounded-full">
                      <Image className="h-3 w-3 text-neutral-600" />
                      <span className="text-[10px] text-neutral-500">GIF Library</span>
                    </div>
                    <div className="flex items-center gap-1 px-2 py-0.5 bg-neutral-900 rounded-full">
                      <Zap className="h-3 w-3 text-neutral-600" />
                      <span className="text-[10px] text-neutral-500">Instant Match</span>
                    </div>
                  </div>
                </div>
                <p className="text-xs text-neutral-500 mt-0.5">AI-powered GIF suggestions to enhance your storytelling</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="px-6 pb-6">
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Left Half - Script */}
          <div className="space-y-4">
            <div className="lg:sticky lg:top-[110px]">
              <div className="space-y-4">
                <div className="bg-neutral-950 rounded-lg border border-neutral-900 p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium text-white">Script</span>
                      {script && (
                        <div className="flex items-center gap-1 px-2 py-0.5 bg-green-500/10 rounded-full">
                          <Clock className="h-3 w-3 text-green-400" />
                          <span className="text-[10px] text-green-400 font-medium">{script.length} chars</span>
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
                            <span className="font-semibold text-white">GIF Tips</span><br/>
                            <span className="text-neutral-400">
                              • Use emotional and action words<br/>
                              • Describe visual moments clearly<br/>
                              • Include reactions and expressions<br/>
                              • Minimum 50 characters required
                            </span>
                          </p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>
                  
                  {hoveredMomentId && gifMoments.length > 0 ? (
                    <div className="min-h-[300px] p-3 bg-neutral-900 border border-neutral-800 rounded-md text-sm whitespace-pre-wrap">
                      {getHighlightedScript()}
                    </div>
                  ) : (
                    <Textarea
                      placeholder="Enter your script or content to find matching GIFs..."
                      value={script}
                      onChange={(e) => setScript(e.target.value)}
                      onPaste={handlePaste}
                      className="min-h-[300px] resize-none bg-neutral-900 border-neutral-800 text-sm placeholder:text-neutral-600"
                    />
                  )}
                </div>

                {/* Process Button */}
                <div className="flex justify-center pt-2">
                  <Button
                    size="default"
                    onClick={handleAnalyze}
                    disabled={script.length < 50 || isProcessing}
                    className="px-6 h-10 bg-white hover:bg-neutral-200 text-black font-medium disabled:opacity-50"
                  >
                    Find GIFs
                    <ChevronRight className="ml-2 h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          </div>

          {/* Right Half - Results */}
          <div className="space-y-4 min-h-screen">
            {/* Processing Status */}
            {isProcessing && (
              <div className="bg-neutral-950 rounded-lg border border-neutral-900 p-6">
                <ProcessingStatus message={processingStep} step={processingStep} />
              </div>
            )}

            {/* Results */}
            {!isProcessing && gifMoments.length > 0 && (
              <div className="space-y-4">
                {downloadedGifs.size > 0 && (
                  <div className="flex items-center justify-end">
                    <span className="text-xs text-neutral-500">
                      {downloadedGifs.size} downloaded
                    </span>
                  </div>
                )}

                {gifMoments.map((moment) => (
                  <div 
                    key={moment.id} 
                    className="bg-neutral-950 rounded-lg border border-neutral-900 p-4 transition-all hover:border-neutral-700"
                    onMouseEnter={() => setHoveredMomentId(moment.id)}
                    onMouseLeave={() => setHoveredMomentId(null)}
                  >
                    <div className="space-y-3">
                      {/* Moment Header */}
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="text-sm text-white leading-relaxed mb-2">{moment.scriptExcerpt}</p>
                          {moment.searchQueries && moment.searchQueries.length > 0 && (
                            <div>
                              <p className="text-[10px] text-neutral-500 mb-1">Search terms:</p>
                              <div className="flex flex-wrap gap-1">
                                {moment.searchQueries.slice(0, 4).map((query, idx) => (
                                  <span key={idx} className="px-1.5 py-0.5 bg-neutral-900 rounded text-[10px] text-neutral-400">
                                    {query}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                        <button
                          onClick={() => handleRefreshGifs(moment.id)}
                          className="p-1.5 hover:bg-neutral-800 rounded transition-colors"
                          disabled={isProcessing}
                        >
                          <RefreshCw className="w-3.5 h-3.5 text-neutral-500" />
                        </button>
                      </div>

                      {/* GIFs Grid */}
                      {moment.gifs && moment.gifs.length > 0 ? (
                        <div className="grid grid-cols-3 gap-1.5">
                          {moment.gifs.slice(0, 6).map((gif) => (
                            <div key={gif.id} className="relative group aspect-square">
                              <img
                                src={gif.previewUrl || gif.url}
                                alt={`GIF for ${moment.category}`}
                                className="w-full h-full object-cover rounded-lg bg-neutral-900"
                                loading="lazy"
                              />
                              <button
                                onClick={() => handleDownloadGif(gif.downloadUrl || gif.url, gif.id)}
                                className="absolute top-1 right-1 p-1 bg-black/70 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                              >
                                <Download className="w-3 h-3 text-white" />
                              </button>
                              {downloadedGifs.has(gif.id) && (
                                <div className="absolute bottom-1 left-1 px-1.5 py-0.5 bg-green-500/90 rounded text-[10px] text-white">
                                  Downloaded
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-4">
                          <p className="text-xs text-neutral-500">No GIFs found for this moment</p>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Empty State */}
            {!isProcessing && gifMoments.length === 0 && (
              <div className="bg-neutral-950 rounded-lg border border-neutral-900 p-12">
                <div className="text-center">
                  <Image className="w-8 h-8 text-neutral-600 mx-auto mb-3" />
                  <p className="text-sm text-white mb-1">No GIFs yet</p>
                  <p className="text-xs text-neutral-500">Enter your script and click "Find GIFs" to get started</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
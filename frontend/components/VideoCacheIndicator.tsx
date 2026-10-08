"use client";

import { useStore } from "@/lib/store";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
  TooltipProvider,
} from "@/components/ui/tooltip";

export function VideoCacheIndicator() {
  const { 
    getNonArchivedVideos,
    currentVideoIndex,
    navigateToPreviousVideo,
    navigateToNextVideo,
    videoCache
  } = useStore();

  const nonArchivedVideos = getNonArchivedVideos();
  const currentVideo = videoCache[currentVideoIndex];
  const isCurrentArchived = currentVideo?.archived || false;
  
  // Find position in non-archived videos
  const nonArchivedIndex = nonArchivedVideos.findIndex(
    v => v.id === currentVideo?.id
  );
  
  // Allow navigation when there's at least 1 video
  // For cycling: if only 1 video, both arrows go to that same video
  // For multiple videos: normal prev/next behavior
  const hasVideos = nonArchivedVideos.length > 0;
  const canGoPrevious = hasVideos; // Can always go "previous" if there are videos (cycles)
  const canGoNext = hasVideos; // Can always go "next" if there are videos (cycles)

  return (
    <div className="flex items-center gap-2 text-base text-neutral-200">
      {/* Green dot indicator */}
      <div className="flex items-center gap-1">
        <div className="flex justify-center">
          <span className="relative flex h-3 w-3">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex h-3 w-3 rounded-full bg-green-500"></span>
          </span>
        </div>

        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger>
              <span className="text-sm text-neutral-200 ml-1 font-medium">
                {nonArchivedVideos.length}
              </span>
            </TooltipTrigger>
            <TooltipContent>
              <p>Videos in cache</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      {/* Navigation arrows - always visible */}
      <div className="flex items-center ml-2">
        <Button
          variant="outline"
          size="icon"
          onClick={navigateToPreviousVideo}
          disabled={!canGoPrevious}
          className="rounded-r-none h-7 w-7 hover:bg-neutral-800 disabled:opacity-30 disabled:cursor-not-allowed"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="icon"
          onClick={navigateToNextVideo}
          disabled={!canGoNext}
          className="rounded-l-none -ml-px h-7 w-7 hover:bg-neutral-800 disabled:opacity-30 disabled:cursor-not-allowed"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
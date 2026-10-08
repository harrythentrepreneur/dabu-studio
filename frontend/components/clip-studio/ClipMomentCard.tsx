"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Download, RefreshCw, CheckCircle, Play } from "lucide-react";
import { ClipMoment } from "@/lib/clip-studio/types";
import { useState } from "react";

interface ClipMomentCardProps {
  moment: ClipMoment;
  onDownloadClip: (clipUrl: string, clipId: string) => void;
  onRefreshClips: (momentId: string) => void;
  onHover: (momentId: string | null) => void;
  downloadedClips: Set<string>;
}

const categoryColors: Record<string, string> = {
  Hook: "bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400 border-blue-200 dark:border-blue-500/30",
  Wow: "bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-400 border-purple-200 dark:border-purple-500/30",
  Emotion: "bg-pink-100 text-pink-700 dark:bg-pink-500/20 dark:text-pink-400 border-pink-200 dark:border-pink-500/30",
  Transition: "bg-orange-100 text-orange-700 dark:bg-orange-500/20 dark:text-orange-400 border-orange-200 dark:border-orange-500/30",
  Problem: "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400 border-red-200 dark:border-red-500/30",
  Solution: "bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400 border-green-200 dark:border-green-500/30",
  "Social Proof": "bg-cyan-100 text-cyan-700 dark:bg-cyan-500/20 dark:text-cyan-400 border-cyan-200 dark:border-cyan-500/30",
  CTA: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400 border-emerald-200 dark:border-emerald-500/30",
  Humor: "bg-yellow-100 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-400 border-yellow-200 dark:border-yellow-500/30"
};

export function ClipMomentCard({
  moment,
  onDownloadClip,
  onRefreshClips,
  onHover,
  downloadedClips
}: ClipMomentCardProps) {
  const [loadingClips, setLoadingClips] = useState<Set<string>>(new Set());
  const [hoveredClip, setHoveredClip] = useState<string | null>(null);
  const [playingClip, setPlayingClip] = useState<string | null>(null);

  const handleClipLoad = (clipId: string) => {
    setLoadingClips(prev => {
      const newSet = new Set(prev);
      newSet.delete(clipId);
      return newSet;
    });
  };

  const handleClipError = (clipId: string) => {
    setLoadingClips(prev => {
      const newSet = new Set(prev);
      newSet.delete(clipId);
      return newSet;
    });
  };

  const handleVideoClick = (clipId: string) => {
    setPlayingClip(playingClip === clipId ? null : clipId);
  };

  return (
    <div
      className="bg-neutral-950 rounded-lg border border-neutral-900 p-4 transition-all hover:border-neutral-700"
      onMouseEnter={() => onHover(moment.id)}
      onMouseLeave={() => onHover(null)}
    >
      <div className="space-y-3">
        {/* Header */}
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
            onClick={() => onRefreshClips(moment.id)}
            className="p-1.5 hover:bg-neutral-800 rounded transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5 text-neutral-500" />
          </button>
        </div>

        {/* Clip Grid - 3x2 layout for 6 clips */}
        <div className="grid grid-cols-3 gap-1.5">
          {moment.clips.slice(0, 6).map((clip) => (
            <div
              key={clip.id}
              className="relative group aspect-square"
              onMouseEnter={() => setHoveredClip(clip.id)}
              onMouseLeave={() => setHoveredClip(null)}
            >
              {loadingClips.has(clip.id) && (
                <div className="absolute inset-0 flex items-center justify-center bg-neutral-900 rounded-lg">
                  <div className="w-6 h-6 border-2 border-neutral-600 border-t-neutral-400 rounded-full animate-spin" />
                </div>
              )}
              
              {/* Video element for clips */}
              <video
                src={clip.previewUrl}
                poster={clip.formats?.gif || undefined}
                className="w-full h-full object-cover rounded-lg bg-neutral-900"
                onLoadedData={() => handleClipLoad(clip.id)}
                onError={() => handleClipError(clip.id)}
                muted
                loop
                playsInline
                autoPlay={playingClip === clip.id}
                onClick={() => handleVideoClick(clip.id)}
              />
              
              {/* Play button overlay */}
              <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center">
                <Play className="w-6 h-6 text-white" />
              </div>
              
              {/* Download button */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDownloadClip(clip.downloadUrl || clip.url, clip.id);
                }}
                className="absolute top-1 right-1 p-1 bg-black/70 rounded opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <Download className="w-3 h-3 text-white" />
              </button>
              
              {/* Duration badge - removed as duration is not in Clip type */}
              
              {/* Downloaded indicator */}
              {downloadedClips.has(clip.id) && (
                <div className="absolute bottom-1 left-1 px-1.5 py-0.5 bg-green-500/90 rounded text-[10px] text-white">
                  Downloaded
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
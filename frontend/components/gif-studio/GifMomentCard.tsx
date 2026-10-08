"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Download, RefreshCw, CheckCircle } from "lucide-react";
import { GifMoment } from "@/lib/gif-studio/types";
import { useState } from "react";

interface GifMomentCardProps {
  moment: GifMoment;
  onDownloadGif: (gifUrl: string, gifId: string) => void;
  onRefreshGifs: (momentId: string) => void;
  onHover: (momentId: string | null) => void;
  downloadedGifs: Set<string>;
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

export function GifMomentCard({
  moment,
  onDownloadGif,
  onRefreshGifs,
  onHover,
  downloadedGifs
}: GifMomentCardProps) {
  const [loadingGifs, setLoadingGifs] = useState<Set<string>>(new Set());
  const [hoveredGif, setHoveredGif] = useState<string | null>(null);

  const handleGifLoad = (gifId: string) => {
    setLoadingGifs(prev => {
      const newSet = new Set(prev);
      newSet.delete(gifId);
      return newSet;
    });
  };

  const handleGifError = (gifId: string) => {
    setLoadingGifs(prev => {
      const newSet = new Set(prev);
      newSet.delete(gifId);
      return newSet;
    });
  };

  return (
    <Card
      className="border-neutral-200 dark:border-neutral-800 hover:shadow-lg transition-shadow"
      onMouseEnter={() => onHover(moment.id)}
      onMouseLeave={() => onHover(null)}
    >
      <CardContent className="p-6 space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-2 flex-1">
          <div className="flex items-center gap-2">
            <Badge 
              variant="outline" 
              className={categoryColors[moment.category] || "bg-neutral-500/20 text-neutral-400"}
            >
              {moment.category}
            </Badge>
          </div>
          <p className="text-xs text-neutral-400 italic">"{moment.scriptExcerpt}"</p>
          <p className="text-xs text-neutral-500">{moment.context}</p>
        </div>
        <Button
          onClick={() => onRefreshGifs(moment.id)}
          size="sm"
          variant="ghost"
          className="h-8 w-8 p-0"
        >
          <RefreshCw className="w-4 h-4" />
        </Button>
      </div>

      {/* GIF Grid - Responsive layout for up to 6 GIFs */}
      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2">
        {moment.gifs.map((gif) => (
          <div
            key={gif.id}
            className="relative group cursor-pointer"
            onMouseEnter={() => setHoveredGif(gif.id)}
            onMouseLeave={() => setHoveredGif(null)}
          >
            <div className="aspect-square rounded overflow-hidden bg-neutral-900 relative">
              {loadingGifs.has(gif.id) && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-6 h-6 border-2 border-neutral-600 border-t-neutral-400 rounded-full animate-spin" />
                </div>
              )}
              <img
                src={gif.previewUrl}
                alt={`GIF option ${gif.id}`}
                className="w-full h-full object-cover transition-transform duration-200 group-hover:scale-110"
                onLoad={() => handleGifLoad(gif.id)}
                onError={() => handleGifError(gif.id)}
                loading="lazy"
              />
              
              {/* Download overlay */}
              {hoveredGif === gif.id && (
                <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
                  {downloadedGifs.has(gif.id) ? (
                    <CheckCircle className="w-6 h-6 text-green-400" />
                  ) : (
                    <Button
                      onClick={() => onDownloadGif(gif.downloadUrl || gif.url, gif.id)}
                      size="sm"
                      variant="ghost"
                      className="h-8 w-8 p-0 bg-white/10 hover:bg-white/20"
                    >
                      <Download className="w-4 h-4 text-white" />
                    </Button>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      </CardContent>
    </Card>
  );
}
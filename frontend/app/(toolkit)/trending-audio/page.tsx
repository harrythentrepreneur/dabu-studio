"use client";

import { useState, useEffect, useRef } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { API_URL } from "@/lib/api-config";
import {
  Play,
  Pause,
  Search,
  TrendingUp,
  ChevronUp,
  ChevronDown,
  Download,
  Music,
  RefreshCw,
  Minus,
  ExternalLink
} from "lucide-react";

interface TrendingAudio {
  rank: number;
  position_change: string;
  artist: string;
  title: string;
  full_title: string;
  country: string;
  cover_url: string | null;
  preview_url: string | null;
  apple_music_url: string | null;
  youtube_search_url?: string | null;
}

export default function TrendingAudioPage() {
  const [audioData, setAudioData] = useState<TrendingAudio[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [playingId, setPlayingId] = useState<number | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>("");
  const [refreshing, setRefreshing] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    fetchTrendingAudio();
  }, []);

  const fetchTrendingAudio = async () => {
    try {
      setLoading(true);
      // Use the new Next.js API route instead of old backend
      const response = await fetch('/api/music-library');
      const result = await response.json();

      if (result.success && result.data) {
        setAudioData(result.data);
        if (result.timestamp) {
          const date = new Date(result.timestamp);
          const timeAgo = getTimeAgo(date);
          setLastUpdated(timeAgo);
        } else if (result.date) {
          // Fallback to date field if timestamp not available
          const date = new Date(result.date);
          const timeAgo = getTimeAgo(date);
          setLastUpdated(timeAgo);
        }
      }
    } catch (error) {
      console.error('Error fetching trending audio:', error);
      // Use fallback data if API fails
      setAudioData([]);
    } finally {
      setLoading(false);
    }
  };

  const refreshData = async () => {
    setRefreshing(true);
    try {
      // Since we're scraping fresh data each time, just refetch
      await fetchTrendingAudio();
    } catch (error) {
      console.error('Error refreshing data:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const getTimeAgo = (date: Date) => {
    const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000);

    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
    return `${Math.floor(seconds / 86400)} days ago`;
  };

  const handlePlayPause = async (audio: TrendingAudio) => {
    // If no preview URL but has YouTube URL, open YouTube in new tab
    if (!audio.preview_url && audio.youtube_search_url) {
      window.open(audio.youtube_search_url, '_blank');
      return;
    }

    if (!audio.preview_url) return;

    if (playingId === audio.rank) {
      // Pause current audio
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      setPlayingId(null);
    } else {
      // Stop any playing audio
      if (audioRef.current) {
        audioRef.current.pause();
      }

      // Play new audio
      audioRef.current = new Audio(audio.preview_url!);
      audioRef.current.play().catch(err => {
        console.error('Error playing audio:', err);
        setPlayingId(null);
      });

      audioRef.current.onended = () => {
        setPlayingId(null);
      };

      setPlayingId(audio.rank);
    }
  };

  const getTrendIcon = (change: string) => {
    if (change === "NEW") {
      return (
        <span className="text-[10px] font-medium text-purple-400 bg-purple-500/10 px-1.5 py-0.5 rounded">
          NEW
        </span>
      );
    } else if (change === "=") {
      return (
        <span className="text-[11px] text-neutral-600">—</span>
      );
    } else if (change.startsWith("+")) {
      return (
        <div className="flex items-center gap-0.5 text-emerald-500">
          <ChevronUp className="w-3 h-3" />
          <span className="text-[11px] font-medium">{change}</span>
        </div>
      );
    } else if (change.startsWith("-")) {
      return (
        <div className="flex items-center gap-0.5 text-red-500">
          <ChevronDown className="w-3 h-3" />
          <span className="text-[11px] font-medium">{change}</span>
        </div>
      );
    }
    return <span className="text-[11px] text-neutral-600">—</span>;
  };

  const filteredData = audioData.filter(audio =>
    audio.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    audio.artist.toLowerCase().includes(searchTerm.toLowerCase()) ||
    audio.full_title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleDownload = async (audio: TrendingAudio) => {
    // Always search on YouTube for download, regardless of preview availability
    const searchQuery = encodeURIComponent(`${audio.artist} ${audio.title}`);
    window.open(`https://www.youtube.com/results?search_query=${searchQuery}`, '_blank');
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header - Sticky */}
      <div className="sticky top-0 bg-neutral-950 z-10 px-6 py-6 border-b border-neutral-900">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-xl font-semibold text-white">Trending Audio</h1>
            <p className="text-xs text-neutral-500 mt-0.5">Top 100 TikTok sounds right now</p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="ghost"
              className="h-8 px-3 text-xs hover:bg-neutral-900"
              onClick={refreshData}
              disabled={refreshing}
            >
              <RefreshCw className={`w-3 h-3 mr-1.5 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <span className="text-xs text-neutral-500">
              Updated {lastUpdated || 'recently'}
            </span>
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-3.5 h-3.5 text-neutral-500" />
          <Input
            placeholder="Search tracks..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="h-9 pl-9 text-sm bg-neutral-950 border-neutral-800 text-white placeholder:text-neutral-500 focus:border-neutral-700"
          />
        </div>
      </div>

      {/* Main Content - Scrollable */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="bg-neutral-950 rounded-lg border border-neutral-900">
          <div>
            {/* Header Row */}
            <div className="flex items-center px-4 py-2.5 text-[10px] font-medium text-neutral-600 uppercase tracking-wider border-b border-neutral-900">
              <div className="w-8 text-center">#</div>
              <div className="flex-1 pl-3">Track</div>
              <div className="w-20 text-center">Change</div>
              <div className="w-20 text-center">Actions</div>
            </div>

            {/* Data Rows */}
            {loading ? (
              <>
                {Array.from({ length: 10 }).map((_, i) => (
                  <div key={i} className="px-6 py-4">
                    <Skeleton className="h-16 w-full bg-neutral-900" />
                  </div>
                ))}
              </>
            ) : filteredData.length === 0 ? (
              <div className="px-6 py-12 text-center text-neutral-500">
                No tracks found {searchTerm && `for "${searchTerm}"`}
              </div>
            ) : (
              filteredData.map((audio) => (
                <div
                  key={audio.rank}
                  className="flex items-center px-4 py-2 hover:bg-neutral-900/50 transition-colors group border-b border-neutral-900/50"
                >
                  {/* Rank */}
                  <div className="w-8 text-center">
                    <span className="text-xs font-medium text-neutral-500">
                      {audio.rank}
                    </span>
                  </div>

                  {/* Track Info with Cover */}
                  <div className="flex-1 flex items-center gap-2.5 pl-3">
                    {/* Cover Image */}
                    <div className="w-10 h-10 bg-neutral-900 rounded-md overflow-hidden flex-shrink-0">
                      {audio.cover_url ? (
                        <img
                          src={audio.cover_url}
                          alt={audio.title}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = 'none';
                          }}
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <Music className="w-4 h-4 text-neutral-700" />
                        </div>
                      )}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-white truncate">
                        {audio.title}
                      </div>
                      <div className="text-xs text-neutral-500 truncate">
                        {audio.artist}
                      </div>
                    </div>
                  </div>

                  {/* Position Change */}
                  <div className="w-20 flex justify-center">
                    {getTrendIcon(audio.position_change)}
                  </div>

                  {/* Actions */}
                  <div className="w-20 flex items-center justify-center gap-1">
                    <Button
                      size="sm"
                      variant="ghost"
                      className="w-7 h-7 p-0 hover:bg-neutral-800 rounded transition-colors"
                      onClick={() => handlePlayPause(audio)}
                      disabled={!audio.preview_url && !audio.youtube_search_url}
                      title={
                        audio.preview_url
                          ? "Play preview"
                          : audio.youtube_search_url
                            ? "Search on YouTube"
                            : "No preview available"
                      }
                    >
                      {audio.preview_url ? (
                        playingId === audio.rank ? (
                          <Pause className="w-3.5 h-3.5 text-neutral-400" />
                        ) : (
                          <Play className="w-3.5 h-3.5 text-neutral-400" />
                        )
                      ) : audio.youtube_search_url ? (
                        <ExternalLink className="w-3.5 h-3.5 text-red-400" />
                      ) : (
                        <Play className="w-3.5 h-3.5 text-neutral-600" />
                      )}
                    </Button>

                    <Button
                      size="sm"
                      variant="ghost"
                      className="w-7 h-7 p-0 hover:bg-neutral-800 rounded transition-colors"
                      onClick={() => handleDownload(audio)}
                      title="Download"
                    >
                      <Download className="w-3.5 h-3.5 text-neutral-400" />
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
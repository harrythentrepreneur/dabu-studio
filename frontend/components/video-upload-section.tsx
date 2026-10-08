"use client";

import { useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";
import { Upload, Video, X, FileVideo, AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface VideoUploadSectionProps {
  videos: File[];
  setVideos: (videos: File[]) => void;
}

export function VideoUploadSection({ videos, setVideos }: VideoUploadSectionProps) {
  const totalSize = videos.reduce((acc, file) => acc + file.size, 0) / (1024 * 1024); // MB
  const totalDuration = videos.length * 30; // Estimate 30s per video

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files).filter(file => 
      file.type.startsWith("video/")
    );
    setVideos([...videos, ...files]);
  }, [videos, setVideos]);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      setVideos([...videos, ...files]);
    }
  };

  const removeVideo = (index: number) => {
    setVideos(videos.filter((_, i) => i !== index));
  };

  const formatFileSize = (bytes: number) => {
    const mb = bytes / (1024 * 1024);
    return mb > 1 ? `${mb.toFixed(1)} MB` : `${(bytes / 1024).toFixed(0)} KB`;
  };

  return (
    <Card className="border border-neutral-800">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="p-1.5 bg-blue-500/10 rounded">
              <Video className="h-4 w-4 text-blue-500" />
            </div>
            <div>
              <CardTitle className="text-base font-medium">Video Files</CardTitle>
              <CardDescription className="text-xs">Upload 5-15 videos (recommended)</CardDescription>
            </div>
          </div>
          <div className="text-right">
            <p className="text-xs font-medium">{videos.length} files</p>
            <p className="text-xs text-muted-foreground">{totalSize.toFixed(1)} MB</p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Drop Zone */}
        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          className="relative"
        >
          <input
            type="file"
            multiple
            accept="video/*"
            onChange={handleFileInput}
            className="hidden"
            id="video-upload"
          />
          <label
            htmlFor="video-upload"
            className="flex flex-col items-center justify-center w-full h-28 border border-dashed border-neutral-700 rounded-lg cursor-pointer bg-neutral-950 hover:bg-neutral-900 hover:border-neutral-600 transition-colors"
          >
            <div className="flex flex-col items-center justify-center">
              <Upload className="w-6 h-6 mb-2 text-muted-foreground" />
              <p className="mb-1 text-xs text-muted-foreground">
                <span className="font-medium">Click to upload</span> or drag and drop
              </p>
              <p className="text-xs text-muted-foreground/70">
                MP4, MOV, AVI (max 500MB each)
              </p>
            </div>
          </label>
        </div>

        {/* File List */}
        {videos.length > 0 && (
          <ScrollArea className="h-[180px] w-full rounded-md border border-neutral-800 bg-neutral-950 p-2">
            <div className="space-y-1.5">
              {videos.map((video, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-2 rounded bg-neutral-900 group hover:bg-neutral-800 transition-colors"
                >
                  <div className="flex items-center space-x-2">
                    <FileVideo className="h-3.5 w-3.5 text-blue-500" />
                    <div>
                      <p className="text-xs font-medium truncate max-w-[180px]">
                        {video.name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {formatFileSize(video.size)}
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeVideo(index)}
                    className="opacity-0 group-hover:opacity-100 transition-opacity h-6 w-6 p-0"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </div>
              ))}
            </div>
          </ScrollArea>
        )}

        {/* Status Info */}
        {videos.length > 0 && (
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">Estimated processing time</span>
              <span className="font-medium">~{Math.ceil(totalDuration / 60)} minutes</span>
            </div>
            
            {videos.length < 5 && (
              <Alert className="border-yellow-500/20 bg-yellow-500/10">
                <AlertCircle className="h-3.5 w-3.5 text-yellow-500" />
                <AlertDescription className="text-xs text-yellow-400">
                  Upload at least 5 videos for best results
                </AlertDescription>
              </Alert>
            )}
          </div>
        )}

        {/* Info Box */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-2.5 space-y-1">
          <p className="text-xs font-medium text-foreground">
            Video Requirements
          </p>
          <ul className="text-xs text-muted-foreground space-y-0.5">
            <li>• 9:16 aspect ratio (vertical) preferred</li>
            <li>• High quality source videos recommended</li>
            <li>• Total duration should exceed target by 2x</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
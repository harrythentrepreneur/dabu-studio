"use client";

import { useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Mic, Upload, X } from "lucide-react";

interface VoiceoverUploadSectionProps {
  voiceover: File | null;
  setVoiceover: (file: File | null) => void;
}

export function VoiceoverUploadSection({ voiceover, setVoiceover }: VoiceoverUploadSectionProps) {
  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      const validTypes = ['audio/mp3', 'audio/mpeg', 'audio/wav', 'audio/m4a', 'audio/aac', 'audio/ogg'];
      const validExtensions = ['.mp3', '.wav', '.m4a', '.aac', '.ogg'];
      const fileExtension = file.name.substring(file.name.lastIndexOf('.'));
      
      if (!validTypes.includes(file.type) && !validExtensions.includes(fileExtension.toLowerCase())) {
        alert('Please upload a valid audio file (MP3, WAV, M4A, AAC, or OGG)');
        return;
      }
      
      // Validate file size (max 100MB)
      if (file.size > 100 * 1024 * 1024) {
        alert('Voiceover file must be less than 100MB');
        return;
      }
      
      setVoiceover(file);
    }
  }, [setVoiceover]);

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      // Same validation as handleFileSelect
      const validTypes = ['audio/mp3', 'audio/mpeg', 'audio/wav', 'audio/m4a', 'audio/aac', 'audio/ogg'];
      const validExtensions = ['.mp3', '.wav', '.m4a', '.aac', '.ogg'];
      const fileExtension = file.name.substring(file.name.lastIndexOf('.'));
      
      if (!validTypes.includes(file.type) && !validExtensions.includes(fileExtension.toLowerCase())) {
        alert('Please upload a valid audio file (MP3, WAV, M4A, AAC, or OGG)');
        return;
      }
      
      if (file.size > 100 * 1024 * 1024) {
        alert('Voiceover file must be less than 100MB');
        return;
      }
      
      setVoiceover(file);
    }
  }, [setVoiceover]);

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  }, []);

  const handleRemove = useCallback(() => {
    setVoiceover(null);
  }, [setVoiceover]);

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <Card className="border border-neutral-800">
      <CardHeader className="pb-3">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 bg-orange-500/10 rounded">
            <Mic className="h-4 w-4 text-orange-500" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <CardTitle className="text-base font-medium">Voiceover</CardTitle>
              <span className="px-1.5 py-0.5 bg-neutral-800 text-neutral-400 text-[10px] rounded-full font-normal">
                Optional
              </span>
            </div>
            <CardDescription className="text-xs">Upload voiceover (e.g. ElevenLabs) for perfect sync</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {!voiceover ? (
          <div
            className="relative"
            onDrop={handleDrop}
            onDragOver={handleDragOver}
          >
            <input
              type="file"
              accept="audio/*,.mp3,.wav,.m4a,.aac,.ogg"
              onChange={handleFileSelect}
              className="hidden"
              id="voiceover-upload"
            />
            <label
              htmlFor="voiceover-upload"
              className="flex flex-col items-center justify-center w-full h-28 border border-dashed border-neutral-700 rounded-lg cursor-pointer bg-neutral-950 hover:bg-neutral-900 hover:border-neutral-600 transition-colors"
            >
              <Upload className="h-6 w-6 text-muted-foreground mb-2" />
              <p className="text-xs text-muted-foreground">
                Drop voiceover here or click to browse
              </p>
              <p className="text-xs text-muted-foreground/70 mt-1">
                MP3, WAV, M4A, AAC, OGG (max 100MB)
              </p>
            </label>
          </div>
        ) : (
          <div className="bg-orange-500/10 rounded-lg p-3 border border-orange-500/20">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-1.5 bg-orange-500/20 rounded">
                  <Mic className="h-3.5 w-3.5 text-orange-500" />
                </div>
                <div>
                  <p className="font-medium text-xs">{voiceover.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {formatFileSize(voiceover.size)}
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRemove}
                className="h-6 w-6 p-0"
              >
                <X className="h-3 w-3" />
              </Button>
            </div>
          </div>
        )}
        
        <div className="mt-3 p-2.5 bg-neutral-900 border border-neutral-800 rounded-lg">
          <p className="text-xs text-muted-foreground">
            <span className="font-medium text-yellow-500">Voiceover Mode:</span> When provided, video segments will be 
            extracted with exact durations matching your voiceover for perfect sync.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
"use client";

import { Card, CardContent } from "@/components/ui/card";
import { ClipMomentCard } from "./ClipMomentCard";
import { ScriptColumn } from "./ScriptColumn";
import { ClipMoment } from "@/lib/clip-studio/types";
import { useState } from "react";

interface ResultsDisplayProps {
  script: string;
  clipMoments: ClipMoment[];
  onDownloadClip: (clipUrl: string, clipId: string) => void;
  onRefreshClips: (momentId: string) => void;
  downloadedClips: Set<string>;
}

export function ResultsDisplay({
  script,
  clipMoments,
  onDownloadClip,
  onRefreshClips,
  downloadedClips
}: ResultsDisplayProps) {
  const [highlightedMoment, setHighlightedMoment] = useState<string | null>(null);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* Script Column - Left Side */}
      <div className="lg:sticky lg:top-4 lg:h-fit">
        <Card className="border border-neutral-800">
          <CardContent className="p-6">
            <h3 className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-4">
              Your Script with Highlights
            </h3>
            <div className="rounded-md border border-neutral-800 bg-neutral-950 p-4">
              <ScriptColumn
                script={script}
                clipMoments={clipMoments}
                highlightedMoment={highlightedMoment}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Clip Column - Right Side */}
      <div className="space-y-4">
        {clipMoments.length === 0 ? (
          <Card className="border-neutral-200 dark:border-neutral-800">
            <CardContent className="p-6">
              <div className="text-center py-8 text-neutral-500">
                No clip moments identified. Try analyzing your script.
              </div>
            </CardContent>
          </Card>
        ) : (
          clipMoments.map((moment) => (
            <ClipMomentCard
              key={moment.id}
              moment={moment}
              onDownloadClip={onDownloadClip}
              onRefreshClips={onRefreshClips}
              onHover={setHighlightedMoment}
              downloadedClips={downloadedClips}
            />
          ))
        )}
      </div>
    </div>
  );
}
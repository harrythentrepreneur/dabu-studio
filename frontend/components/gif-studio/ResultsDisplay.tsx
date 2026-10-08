"use client";

import { Card, CardContent } from "@/components/ui/card";
import { GifMomentCard } from "./GifMomentCard";
import { ScriptColumn } from "./ScriptColumn";
import { GifMoment } from "@/lib/gif-studio/types";
import { useState } from "react";

interface ResultsDisplayProps {
  script: string;
  gifMoments: GifMoment[];
  onDownloadGif: (gifUrl: string, gifId: string) => void;
  onRefreshGifs: (momentId: string) => void;
  downloadedGifs: Set<string>;
}

export function ResultsDisplay({
  script,
  gifMoments,
  onDownloadGif,
  onRefreshGifs,
  downloadedGifs
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
                gifMoments={gifMoments}
                highlightedMoment={highlightedMoment}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* GIF Column - Right Side */}
      <div className="space-y-4">
        {gifMoments.length === 0 ? (
          <Card className="border-neutral-200 dark:border-neutral-800">
            <CardContent className="p-6">
              <div className="text-center py-8 text-neutral-500">
                No GIF moments identified. Try analyzing your script.
              </div>
            </CardContent>
          </Card>
        ) : (
          gifMoments.map((moment) => (
            <GifMomentCard
              key={moment.id}
              moment={moment}
              onDownloadGif={onDownloadGif}
              onRefreshGifs={onRefreshGifs}
              onHover={setHighlightedMoment}
              downloadedGifs={downloadedGifs}
            />
          ))
        )}
      </div>
    </div>
  );
}
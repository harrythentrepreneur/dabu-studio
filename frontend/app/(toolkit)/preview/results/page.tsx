"use client";

import { useState } from "react";
import { ResultsDisplay } from "@/components/results-display";
import { Button } from "@/components/ui/button";
import { CheckCircle2, XCircle, Package, Captions, Settings2 } from "lucide-react";

export default function ResultsPreviewPage() {
  const [processingState, setProcessingState] = useState<"complete" | "error">("complete");
  const [includeCapCut, setIncludeCapCut] = useState(true);
  const [includeCaptions, setIncludeCaptions] = useState(true);
  
  // Sample successful result
  const successResult = {
    videoUrl: "/api/download/test/video.mp4",
    scriptUrl: "/api/download/test/script.txt",
    timestampsUrl: "/api/download/test/timestamps.json",
    captionedVideoUrl: includeCaptions ? "/api/download/test/captioned.mp4" : undefined,
    projectBundleUrl: includeCapCut ? "/api/download/test/capcut.zip" : undefined,
    segments: [
      { text: "This is the first segment", start_time: 0, end_time: 5 },
      { text: "Second segment here", start_time: 5, end_time: 10 },
      { text: "Third and final segment", start_time: 10, end_time: 15 }
    ]
  };
  
  // Sample error result
  const errorResult = {
    error: "Failed to process video: Gemini API returned an error - The uploaded video file is too large or corrupted. Please try with a different video."
  };

  return (
    <div className="min-h-screen">
      {/* Results Display Component - Exactly as it appears in the app */}
      <ResultsDisplay
        results={processingState === "complete" ? successResult : errorResult}
        processingState={processingState}
        onReset={() => console.log("Reset clicked")}
      />
    </div>
  );
}
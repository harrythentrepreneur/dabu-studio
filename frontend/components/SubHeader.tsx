"use client";

import { Button } from "@/components/ui/button";
import { useStore } from "@/lib/store";
import { RotateCcw, Upload } from "lucide-react";
import { VideoCacheIndicator } from "./VideoCacheIndicator";

export function SubHeader() {
  const { processingStatus, resetStore } = useStore();

  return (
    <div>
      <div className="flex gap-2 mb-3 justify-between">
        <div className="flex items-center gap-2">
          <h1 className="text-lg font-semibold text-neutral-100">
            Video Ad Automation
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <VideoCacheIndicator />
          <Button
            variant="outline"
            size="sm"
            onClick={resetStore}
            disabled={processingStatus === "processing"}
            className="bg-transparent hover:bg-neutral-800 border-neutral-700 text-neutral-300 hover:text-neutral-100"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Reset
          </Button>
          {processingStatus === "idle" && (
            <div className="text-sm text-neutral-400 flex items-center gap-2">
              <Upload className="w-4 h-4" />
              Ready to process
            </div>
          )}
          {processingStatus === "processing" && (
            <div className="text-sm text-blue-400 flex items-center gap-2">
              <div className="animate-spin w-4 h-4 border-2 border-blue-400/20 border-t-blue-400 rounded-full" />
              Processing...
            </div>
          )}
          {processingStatus === "completed" && (
            <div className="text-sm text-green-400 flex items-center gap-2">
              <div className="w-4 h-4 bg-green-400 rounded-full flex items-center justify-center">
                <div className="w-2 h-2 bg-green-800 rounded-full" />
              </div>
              Complete
            </div>
          )}
          {processingStatus === "error" && (
            <div className="text-sm text-red-400 flex items-center gap-2">
              <div className="w-4 h-4 bg-red-400 rounded-full flex items-center justify-center">
                <div className="w-2 h-2 bg-red-800 rounded-full" />
              </div>
              Error
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
"use client";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useStore } from "@/lib/store";
import { Plus } from "lucide-react";
import { VideoCacheIndicator } from "./VideoCacheIndicator";

export function SubHeader({ onCreateAnother }: { onCreateAnother?: () => void }) {
  const { navigateToVideo } = useStore();
  
  const handleCreateAnother = () => {
    if (onCreateAnother) {
      onCreateAnother();
    } else {
      // Navigate to main page (index -1)
      navigateToVideo(-1);
    }
  };

  return (
    <div>
      <div className="flex gap-2 mb-3 justify-between">
        <div className="flex items-center gap-2">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={handleCreateAnother}
                  className="gap-2 border-neutral-700 hover:bg-neutral-800"
                >
                  <Plus className="h-4 w-4" />
                  Create Another
                </Button>
              </TooltipTrigger>
              <TooltipContent side="right">
                <p className="text-xs">Start another while this processes. Switch between requests using the navigation arrows.</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
        
        <div className="flex items-center gap-2">
          <VideoCacheIndicator />
        </div>
      </div>
    </div>
  );
}
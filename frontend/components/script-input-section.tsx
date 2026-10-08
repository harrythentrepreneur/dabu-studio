"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { AlertCircle, FileText, Sparkles } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface ScriptInputSectionProps {
  script: string;
  setScript: (script: string) => void;
}

export function ScriptInputSection({ script, setScript }: ScriptInputSectionProps) {
  const wordCount = script.split(" ").filter(word => word.length > 0).length;
  const estimatedDuration = Math.round((wordCount / 2.5)); // ~2.5 words per second
  const durationProgress = Math.min((estimatedDuration / 45) * 100, 100);
  
  const getDurationColor = () => {
    if (estimatedDuration < 15) return "text-yellow-600";
    if (estimatedDuration > 45) return "text-red-600";
    return "text-green-600";
  };

  return (
    <Card className="border border-neutral-800">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="p-1.5 bg-purple-500/10 rounded">
              <FileText className="h-4 w-4 text-purple-500" />
            </div>
            <div>
              <CardTitle className="text-base font-medium">Script Content</CardTitle>
              <CardDescription className="text-xs">Enter your TikTok ad script (15-45 seconds works best)</CardDescription>
            </div>
          </div>
          <div className="text-right">
            <p className="text-xs font-medium">{wordCount} words</p>
            <p className={`text-xs ${getDurationColor()}`}>~{estimatedDuration}s</p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-2">
          <Label htmlFor="script" className="text-xs">Ad Script</Label>
          <Textarea
            id="script"
            placeholder={`Enter your TikTok ad script here...

Example:
"I accidentally discovered something incredible...
This simple morning routine changed everything.
In just 30 days, my productivity doubled.
Here's exactly how I did it..."`}
            className="min-h-[200px] resize-none text-sm bg-neutral-950 border-neutral-800 placeholder:text-neutral-500 focus:placeholder:text-neutral-600"
            value={script}
            onChange={(e) => setScript(e.target.value)}
          />
        </div>

        {/* Duration Progress Bar */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">Duration estimate</span>
            <span className={getDurationColor()}>{estimatedDuration}s / 15-45s</span>
          </div>
          <Progress value={durationProgress} className="h-1.5" />
        </div>

        {/* Warnings */}
        {estimatedDuration < 15 && script.length > 0 && (
          <Alert className="border-yellow-500/20 bg-yellow-500/10">
            <AlertCircle className="h-3.5 w-3.5 text-yellow-500" />
            <AlertDescription className="text-xs text-yellow-400">
              Script is too short. Add more content for a 15-second minimum.
            </AlertDescription>
          </Alert>
        )}
        
        {estimatedDuration > 45 && (
          <Alert className="border-red-500/20 bg-red-500/10">
            <AlertCircle className="h-3.5 w-3.5 text-red-500" />
            <AlertDescription className="text-xs text-red-400">
              Script is too long. Consider shortening to stay under 45 seconds.
            </AlertDescription>
          </Alert>
        )}

        {/* Tips */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-2.5 space-y-1">
          <div className="flex items-center space-x-1.5 text-xs font-medium text-foreground">
            <Sparkles className="h-3.5 w-3.5 text-purple-500" />
            <span>Pro Tips</span>
          </div>
          <ul className="text-xs text-muted-foreground space-y-0.5 ml-5">
            <li>• Break script into clear, emotional moments</li>
            <li>• Use action words that match visual content</li>
            <li>• Keep sentences short and punchy</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
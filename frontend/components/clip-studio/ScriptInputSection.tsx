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
  onAnalyze: () => void;
  isProcessing: boolean;
  characterCount: number;
}

export function ScriptInputSection({
  script,
  setScript,
  onAnalyze,
  isProcessing,
  characterCount
}: ScriptInputSectionProps) {
  const wordCount = script.split(" ").filter(word => word.length > 0).length;
  const maxCharacters = 5000;
  const minCharacters = 50;
  const characterProgress = Math.min((characterCount / 1000) * 100, 100); // Progress to 1000 chars as optimal
  
  const getCharacterColor = () => {
    if (characterCount < minCharacters) return "text-yellow-600";
    if (characterCount > maxCharacters) return "text-red-600";
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
              <CardDescription className="text-xs">Enter your advertising script for clip analysis</CardDescription>
            </div>
          </div>
          <div className="text-right">
            <p className="text-xs font-medium">{wordCount} words</p>
            <p className={`text-xs ${getCharacterColor()}`}>{characterCount} chars</p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-2">
          <Label htmlFor="script" className="text-xs">Ad Script</Label>
          <Textarea
            id="script"
            placeholder={`Enter your advertising script here...

Example:
"Stop scrolling! This will blow your mind...
Our revolutionary product increased sales by 300% overnight.
Thousands of customers are already experiencing incredible results.
Don't miss out on this game-changing opportunity.
Click now to transform your business!"`}
            className="min-h-[200px] resize-none text-sm bg-neutral-950 border-neutral-800 placeholder:text-neutral-500 focus:placeholder:text-neutral-600"
            value={script}
            onChange={(e) => setScript(e.target.value)}
            disabled={isProcessing}
          />
        </div>

        {/* Character Progress Bar */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">Script length</span>
            <span className={getCharacterColor()}>{characterCount} / {maxCharacters}</span>
          </div>
          <Progress value={characterProgress} className="h-1.5" />
        </div>

        {/* Warnings */}
        {characterCount < minCharacters && script.length > 0 && (
          <Alert className="border-yellow-500/20 bg-yellow-500/10">
            <AlertCircle className="h-3.5 w-3.5 text-yellow-500" />
            <AlertDescription className="text-xs text-yellow-400">
              Script is too short. Add {minCharacters - characterCount} more characters.
            </AlertDescription>
          </Alert>
        )}
        
        {characterCount > maxCharacters && (
          <Alert className="border-red-500/20 bg-red-500/10">
            <AlertCircle className="h-3.5 w-3.5 text-red-500" />
            <AlertDescription className="text-xs text-red-400">
              Script is too long. Please shorten by {characterCount - maxCharacters} characters.
            </AlertDescription>
          </Alert>
        )}

        {/* Ready indicator */}
        {characterCount >= minCharacters && characterCount <= maxCharacters && script.length > 0 && (
          <Alert className="border-green-500/20 bg-green-500/10">
            <Sparkles className="h-3.5 w-3.5 text-green-500" />
            <AlertDescription className="text-xs text-green-400">
              Script ready for clip analysis! AI will identify 4-8 key moments.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}
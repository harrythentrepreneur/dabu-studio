"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Loader2, CheckCircle2, ArrowRight, Beaker } from "lucide-react";

export default function PreviewIndexPage() {
  return (
    <div className="min-h-screen bg-black">
      {/* Header */}
      <div className="sticky top-0 bg-neutral-950 border-b border-neutral-900 z-50">
        <div className="px-6 py-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-purple-500/10 rounded-lg">
              <Beaker className="h-5 w-5 text-purple-400" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-white">Component Preview</h1>
              <p className="text-xs text-neutral-500 mt-0.5">Test and preview UI components in isolation</p>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        <div className="max-w-4xl mx-auto">
          <div className="grid md:grid-cols-2 gap-4">
            {/* Processing Status Preview */}
            <Link href="/preview/processing">
              <div className="bg-neutral-950 rounded-lg border border-neutral-900 p-6 hover:border-neutral-800 transition-all cursor-pointer group">
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-purple-500/10 rounded-lg group-hover:bg-purple-500/15 transition-colors">
                    <Loader2 className="h-6 w-6 text-purple-400" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-sm font-medium text-white mb-1">Processing Status</h3>
                    <p className="text-xs text-neutral-500 mb-3">
                      Preview the video processing status component with different states and configurations
                    </p>
                    <div className="flex items-center gap-4 text-xs">
                      <div className="flex items-center gap-1">
                        <div className="w-1.5 h-1.5 bg-green-400 rounded-full"></div>
                        <span className="text-neutral-600">Interactive</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <div className="w-1.5 h-1.5 bg-blue-400 rounded-full"></div>
                        <span className="text-neutral-600">Animated</span>
                      </div>
                    </div>
                  </div>
                  <ArrowRight className="h-4 w-4 text-neutral-600 group-hover:text-neutral-400 transition-colors" />
                </div>
              </div>
            </Link>

            {/* Results Display Preview */}
            <Link href="/preview/results">
              <div className="bg-neutral-950 rounded-lg border border-neutral-900 p-6 hover:border-neutral-800 transition-all cursor-pointer group">
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-green-500/10 rounded-lg group-hover:bg-green-500/15 transition-colors">
                    <CheckCircle2 className="h-6 w-6 text-green-400" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-sm font-medium text-white mb-1">Results Display</h3>
                    <p className="text-xs text-neutral-500 mb-3">
                      Preview the results display component with success and error states
                    </p>
                    <div className="flex items-center gap-4 text-xs">
                      <div className="flex items-center gap-1">
                        <div className="w-1.5 h-1.5 bg-green-400 rounded-full"></div>
                        <span className="text-neutral-600">Success State</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <div className="w-1.5 h-1.5 bg-red-400 rounded-full"></div>
                        <span className="text-neutral-600">Error State</span>
                      </div>
                    </div>
                  </div>
                  <ArrowRight className="h-4 w-4 text-neutral-600 group-hover:text-neutral-400 transition-colors" />
                </div>
              </div>
            </Link>
          </div>

          {/* Info Box */}
          <div className="mt-8 bg-neutral-950 rounded-lg border border-neutral-900 p-6">
            <h3 className="text-sm font-medium text-white mb-2">How to Use</h3>
            <div className="space-y-2 text-xs text-neutral-400">
              <p>• Click on a component card above to preview it in isolation</p>
              <p>• Use the control panel in each preview to test different states and configurations</p>
              <p>• Changes made to the component files will be reflected here automatically</p>
              <p>• These are the same components used in Quick Create and Express Builder</p>
            </div>
          </div>

          {/* Quick Links */}
          <div className="mt-6 flex items-center justify-center gap-4">
            <Link href="/quick-create">
              <Button variant="outline" size="sm" className="text-xs">
                Quick Create Page
                <ArrowRight className="h-3 w-3 ml-1" />
              </Button>
            </Link>
            <Link href="/express-builder">
              <Button variant="outline" size="sm" className="text-xs">
                Express Builder Page
                <ArrowRight className="h-3 w-3 ml-1" />
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
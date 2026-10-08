"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

export function VideoSkeletonLoader() {
  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header Skeleton */}
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center p-2 rounded-full mb-3">
          <Skeleton className="h-6 w-6 rounded-full" />
        </div>
        <Skeleton className="h-8 w-64 mx-auto mb-2" />
        <Skeleton className="h-4 w-96 mx-auto" />
      </div>

      {/* Main Results Grid Skeleton */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Left: Video Player Skeleton */}
        <Card className="border border-neutral-800">
          <CardHeader>
            <Skeleton className="h-5 w-32 mb-2" />
            <Skeleton className="h-4 w-48" />
          </CardHeader>
          <CardContent>
            <Skeleton className="aspect-[9/16] w-full rounded-lg" />
            <div className="mt-4 space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          </CardContent>
        </Card>

        {/* Right: Details Skeleton */}
        <div className="space-y-4">
          {/* Script Card Skeleton */}
          <Card className="border border-neutral-800">
            <CardHeader>
              <div className="flex items-center justify-between">
                <Skeleton className="h-5 w-24" />
                <Skeleton className="h-8 w-8 rounded" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            </CardContent>
          </Card>

          {/* Segments Card Skeleton */}
          <Card className="border border-neutral-800">
            <CardHeader>
              <div className="flex items-center justify-between">
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-6 w-16 rounded-full" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="p-3 rounded-lg border border-neutral-800">
                    <div className="flex items-start justify-between mb-2">
                      <Skeleton className="h-4 w-20" />
                      <Skeleton className="h-4 w-24" />
                    </div>
                    <Skeleton className="h-3 w-full mb-1" />
                    <Skeleton className="h-3 w-4/5" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export function ProcessingSkeletonLoader() {
  return (
    <div className="max-w-2xl mx-auto">
      <Card className="border border-neutral-800">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <Skeleton className="h-5 w-40 mb-2" />
              <Skeleton className="h-3 w-64" />
            </div>
            <Skeleton className="h-8 w-8 rounded" />
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Progress Bar Skeleton */}
          <div className="space-y-1.5">
            <div className="flex justify-between">
              <Skeleton className="h-3 w-24" />
              <Skeleton className="h-3 w-8" />
            </div>
            <Skeleton className="h-2 w-full rounded-full" />
          </div>

          {/* Steps Skeleton */}
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex items-center space-x-2 p-2.5 rounded-lg bg-neutral-900 border border-neutral-800">
                <Skeleton className="h-8 w-8 rounded-full" />
                <div className="flex-1">
                  <Skeleton className="h-3 w-32 mb-1" />
                  {i === 2 && <Skeleton className="h-2 w-48" />}
                </div>
                {i < 2 && <Skeleton className="h-5 w-16 rounded-full" />}
              </div>
            ))}
          </div>

          {/* Time and Cancel Button Skeleton */}
          <div className="flex items-center justify-between pt-2 border-t border-neutral-800">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-8 w-20 rounded" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export function UploadSectionSkeletonLoader() {
  return (
    <Card className="border border-neutral-800">
      <CardHeader>
        <Skeleton className="h-5 w-32 mb-2" />
        <Skeleton className="h-3 w-48" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-32 w-full rounded-lg border-2 border-dashed" />
        <div className="mt-4 space-y-2">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-2 w-full" />
        </div>
      </CardContent>
    </Card>
  );
}
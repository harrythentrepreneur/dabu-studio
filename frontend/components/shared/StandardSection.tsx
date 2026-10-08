"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { AlertCircle, Info, RefreshCcw } from "lucide-react";
import { ReactNode } from "react";

const Skeleton = () => {
  // Generate widths following a natural data distribution
  const widths = Array.from({ length: 6 }, (_, i) => {
    if (i === 0) {
      return 100;
    } else if (i === 1) {
      return 60 + Math.random() * 20;
    } else {
      const factor = 1 - (i - 2) / 4;
      return 10 + factor * 30;
    }
  });

  const labelWidths = Array.from({ length: 6 }, (_, i) => {
    return i < 3 ? 75 + Math.random() * 50 : 40 + Math.random() * 40;
  });

  const valueWidths = Array.from(
    { length: 6 },
    () => 20 + Math.random() * 30
  );

  return (
    <>
      <div className="flex flex-row gap-2 justify-between pr-1 text-xs text-neutral-400">
        <div className="h-4 bg-neutral-800 rounded animate-pulse w-16"></div>
        <div className="h-4 bg-neutral-800 rounded animate-pulse w-12"></div>
      </div>
      {Array.from({ length: 6 }).map((_, index) => (
        <div key={index} className="relative h-6 flex items-center">
          <div
            className="absolute inset-0 bg-neutral-800 py-2 rounded-md animate-pulse"
            style={{ width: `${widths[index]}%` }}
          />
          <div className="z-5 mx-2 flex justify-between items-center text-sm w-full">
            <div className="flex items-center gap-1">
              <div
                className="h-4 bg-neutral-800 rounded animate-pulse"
                style={{ width: `${labelWidths[index]}px` }}
              />
            </div>
            <div className="text-sm flex gap-2">
              <div
                className="h-4 bg-neutral-800 rounded animate-pulse"
                style={{ width: `${valueWidths[index]}px` }}
              />
            </div>
          </div>
        </div>
      ))}
    </>
  );
};

type StandardSectionItem = {
  id: string;
  label: ReactNode;
  value: string | number;
  percentage?: number;
  link?: string;
};

export function StandardSection({
  title,
  items,
  countLabel = "Count",
  isLoading = false,
  isFetching = false,
  error = null,
  onRetry,
  maxDisplay = 6,
}: {
  title: string;
  items?: StandardSectionItem[];
  countLabel?: string;
  isLoading?: boolean;
  isFetching?: boolean;
  error?: string | null;
  onRetry?: () => void;
  maxDisplay?: number;
}) {
  const ratio = items?.[0]?.percentage ? 100 / items[0].percentage : 1;

  return (
    <Card>
      <CardContent className="p-4 relative">
        {isFetching && (
          <div className="absolute inset-0 bg-black/20 flex items-center justify-center rounded-md">
            <div className="animate-spin w-5 h-5 border-2 border-white/20 border-t-white rounded-full" />
          </div>
        )}
        
        <div className="flex flex-col gap-2 max-h-[344px] overflow-y-auto">
          {isLoading ? (
            <Skeleton />
          ) : error ? (
            <div className="py-6 flex-1 flex flex-col items-center justify-center gap-3 transition-all">
              <AlertCircle className="text-amber-400 w-8 h-8" />
              <div className="text-center">
                <div className="text-neutral-100 font-medium mb-1">
                  Failed to load data
                </div>
                <div className="text-sm text-neutral-400 max-w-md mx-auto mb-3">
                  {error}
                </div>
              </div>
              {onRetry && (
                <Button
                  variant="outline"
                  size="sm"
                  className="bg-transparent hover:bg-neutral-800 border-neutral-700 text-neutral-300 hover:text-neutral-100"
                  onClick={onRetry}
                >
                  <RefreshCcw className="w-3 h-3" /> Try Again
                </Button>
              )}
            </div>
          ) : (
            <div className="flex flex-col gap-2 overflow-x-hidden">
              <div className="flex flex-row gap-2 justify-between pr-1 text-xs text-neutral-400">
                <div>{title}</div>
                <div>{countLabel}</div>
              </div>
              {items?.length ? (
                items
                  .slice(0, maxDisplay)
                  .map((item) => (
                    <div
                      key={item.id}
                      className="relative h-6 flex items-center cursor-pointer hover:bg-neutral-850 group"
                    >
                      {item.percentage && (
                        <div
                          className="absolute inset-0 bg-blue-500/25 py-2 rounded-md"
                          style={{ width: `${item.percentage * ratio}%` }}
                        />
                      )}
                      <div className="z-10 mx-2 flex justify-between items-center text-xs w-full">
                        <div className="flex items-center gap-1">
                          {item.label}
                          {item.link && (
                            <a href={item.link} target="_blank" onClick={(e) => e.stopPropagation()}>
                              <Info className="ml-0.5 w-3.5 h-3.5 text-neutral-300 hover:text-neutral-100" />
                            </a>
                          )}
                        </div>
                        <div className="text-xs flex gap-2">
                          {item.percentage && (
                            <div className="hidden group-hover:block text-neutral-400">
                              {Math.round(item.percentage * 10) / 10}%
                            </div>
                          )}
                          <div>{item.value}</div>
                        </div>
                      </div>
                    </div>
                  ))
              ) : (
                <div className="text-neutral-300 w-full text-center mt-6 flex flex-row gap-2 items-center justify-center">
                  <Info className="w-5 h-5" />
                  No Data
                </div>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
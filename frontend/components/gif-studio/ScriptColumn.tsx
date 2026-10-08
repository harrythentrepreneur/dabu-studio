"use client";

import { GifMoment } from "@/lib/gif-studio/types";
import { useEffect, useRef, useMemo, ReactElement } from "react";

interface ScriptColumnProps {
  script: string;
  gifMoments: GifMoment[];
  highlightedMoment: string | null;
}

export function ScriptColumn({ script, gifMoments, highlightedMoment }: ScriptColumnProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Fix positions by finding the actual text in the script
  const fixedMoments = useMemo(() => {
    return gifMoments.map(moment => {
      // Use the excerpt as primary search text
      let searchText = moment.scriptExcerpt || "";
      
      // Clean up the search text - remove ellipsis and trim
      searchText = searchText.replace(/\.\.\.$/g, '').trim();
      
      // If search text is too short, skip
      if (searchText.length < 5) {
        return moment;
      }
      
      // Try to find this text in the script
      let startPos = -1;
      let endPos = -1;
      
      // First try exact match (case insensitive)
      const lowerScript = script.toLowerCase();
      const lowerSearch = searchText.toLowerCase();
      startPos = lowerScript.indexOf(lowerSearch);
      
      if (startPos >= 0) {
        endPos = startPos + searchText.length;
      } else {
        // Try to find key words from the excerpt
        const words = searchText.split(' ').filter(w => w.length > 3);
        if (words.length > 2) {
          // Try to find at least 2 consecutive words
          for (let i = 0; i < words.length - 1; i++) {
            const phrase = words.slice(i, i + 2).join(' ').toLowerCase();
            startPos = lowerScript.indexOf(phrase);
            if (startPos >= 0) {
              // Found a match, extend to reasonable boundaries
              endPos = startPos + phrase.length;
              // Try to extend to sentence end
              for (let j = endPos; j < Math.min(script.length, startPos + 60); j++) {
                if (script[j] === '.' || script[j] === '!' || script[j] === '?') {
                  endPos = j + 1;
                  break;
                }
              }
              break;
            }
          }
        }
        
        // Last resort: try to match just the first significant word
        if (startPos < 0 && words.length > 0) {
          const firstWord = words[0].toLowerCase();
          if (firstWord.length > 4) {
            startPos = lowerScript.indexOf(firstWord);
            if (startPos >= 0) {
              endPos = Math.min(startPos + 40, script.length);
            }
          }
        }
      }
      
      // If we found a valid position, update it
      if (startPos >= 0 && endPos > startPos) {
        return {
          ...moment,
          scriptPosition: {
            start: startPos,
            end: endPos
          }
        };
      }
      
      // Otherwise return the original moment (will be skipped in rendering)
      return moment;
    });
  }, [gifMoments, script]);

  // Sort moments by position for proper rendering
  const sortedMoments = [...fixedMoments].sort((a, b) => {
    const aStart = a.scriptPosition?.start || 0;
    const bStart = b.scriptPosition?.start || 0;
    return aStart - bStart;
  });

  // Remove auto-scroll to prevent page jumping on hover
  // Users can manually scroll to see highlights

  // Create highlighted script with proper text flow
  const renderHighlightedScript = () => {
    // Build a map of character positions to highlight info
    const highlightMap = new Map<number, { momentId: string; category: string; excerpt: string }>();
    
    sortedMoments.forEach((moment) => {
      const start = moment.scriptPosition?.start || 0;
      const end = moment.scriptPosition?.end || script.length;
      
      // Skip invalid ranges
      if (start < 0 || end > script.length || start >= end) {
        return;
      }
      
      // Mark each character position in this range
      for (let i = start; i < end && i < script.length; i++) {
        if (!highlightMap.has(i)) {
          highlightMap.set(i, {
            momentId: moment.id,
            category: moment.category,
            excerpt: moment.scriptExcerpt
          });
        }
      }
    });

    // Build the output
    const elements: ReactElement[] = [];
    let currentText = '';
    let currentHighlight: { momentId: string; category: string; excerpt: string } | null = null;
    let spanKey = 0;

    for (let i = 0; i <= script.length; i++) {
      const char = i < script.length ? script[i] : '';
      const highlight = highlightMap.get(i) || null;
      
      // Check if highlight state changed
      const highlightChanged = (
        (!currentHighlight && highlight) ||
        (currentHighlight && !highlight) ||
        (currentHighlight && highlight && currentHighlight.momentId !== highlight.momentId)
      );
      
      if (highlightChanged || i === script.length) {
        // Output accumulated text
        if (currentText) {
          if (currentHighlight) {
            // Output highlighted text
            const isActive = highlightedMoment === currentHighlight.momentId;
            elements.push(
              <mark
                key={`highlight-${spanKey++}`}
                data-moment-id={currentHighlight.momentId}
                className={`
                  transition-all duration-200 rounded-sm
                  ${isActive 
                    ? 'bg-yellow-300/50 dark:bg-yellow-400/30 outline outline-2 outline-yellow-400/30' 
                    : 'bg-yellow-100 dark:bg-yellow-400/15 hover:bg-yellow-200 dark:hover:bg-yellow-400/25'
                  }
                `}
                style={{ 
                  textDecoration: 'none',
                  color: 'inherit',
                  padding: '2px 0',
                  display: 'inline'
                }}
                title={`${currentHighlight.category}: ${currentHighlight.excerpt}`}
              >
                {currentText}
              </mark>
            );
          } else {
            // Output normal text
            elements.push(
              <span key={`text-${spanKey++}`}>
                {currentText}
              </span>
            );
          }
          currentText = '';
        }
        
        // Update current highlight state
        currentHighlight = highlight;
      }
      
      // Add current character to buffer
      if (i < script.length) {
        currentText += char;
      }
    }

    return elements;
  };

  return (
    <div ref={containerRef}>
      <pre className="text-xs whitespace-pre-wrap font-mono text-muted-foreground leading-relaxed">
        {renderHighlightedScript()}
      </pre>
    </div>
  );
}
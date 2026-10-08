import { ClipMoment } from './types';
import { API_URL } from '@/lib/api-config';

// Backend API configuration
const BACKEND_API_URL = API_URL;

interface GeminiAnalysisResponse {
  success: boolean;
  moments: Array<{
    id: string;
    category: string;
    excerpt: string;
    scriptPosition: {
      start: number;
      end: number;
    };
    searchQueries: string[];
    reasoning: string;
    actualText: string;
    timestamp: string;
  }>;
  metadata: {
    script_length: number;
    moments_found: number;
    max_moments_requested: number;
    analysis_timestamp: string;
    analyzer_version: string;
  };
}

export async function analyzeScriptWithGemini(script: string): Promise<ClipMoment[]> {
  try {
    console.log('Analyzing script with Gemini API for clips...');

    // Try to call backend Gemini API first (reuse gif-studio endpoint for script analysis)
    const response = await fetch(`${BACKEND_API_URL}/api/gif-studio/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        script: script.trim(),
        maxMoments: 8
      })
    });

    if (response.ok) {
      const data: GeminiAnalysisResponse = await response.json();

      if (data.success && data.moments) {
        console.log(`Successfully analyzed script: ${data.moments.length} moments found`);

        // Transform response to ClipMoment format
        return data.moments.map(moment => ({
          id: moment.id,
          category: moment.category as ClipMoment['category'],
          scriptExcerpt: moment.excerpt,
          scriptPosition: moment.scriptPosition,
          searchQuery: moment.searchQueries[0] || 'reaction clip',
          searchQueries: moment.searchQueries,
          context: moment.reasoning,
          clipStyle: determineClipStyleFromCategory(moment.category),
          importance: determineImportanceFromPosition(moment.scriptPosition.start, script.length),
          clips: []
        }));
      }
    }

    // If backend fails or returns invalid data, fall back to client-side analysis
    throw new Error('Backend analysis failed or returned invalid data');

  } catch (error) {
    console.error('Error with backend Gemini analysis:', error);
    console.log('Falling back to client-side analysis...');
    return await performFallbackAnalysis(script);
  }
}

// Helper functions for transforming backend response
function determineClipStyleFromCategory(category: string): ClipMoment['clipStyle'] {
  const styleMap: Record<string, ClipMoment['clipStyle']> = {
    'Hook': 'reaction',
    'Problem': 'reaction',
    'Solution': 'illustration',
    'Wow': 'illustration',
    'Social Proof': 'meme',
    'CTA': 'animated-text',
    'Emotion': 'reaction',
    'Humor': 'meme',
    'Transition': 'aesthetic'
  };
  return styleMap[category] || 'reaction';
}

function determineImportanceFromPosition(position: number, scriptLength: number): ClipMoment['importance'] {
  const relativePosition = position / scriptLength;
  if (relativePosition < 0.2 || relativePosition > 0.8) {
    return 'high'; // Beginning or end
  }
  if (relativePosition < 0.4 || relativePosition > 0.6) {
    return 'medium'; // Early/late middle
  }
  return 'low'; // Middle
}

// Fallback client-side analysis (simplified version)
async function performFallbackAnalysis(script: string): Promise<ClipMoment[]> {
  console.log('Using fallback client-side analysis');

  // Small delay for UX smoothness
  await new Promise(resolve => setTimeout(resolve, 800));

  const scriptLength = script.length;
  const fallbackMoments: ClipMoment[] = [];

  // Create basic moments based on script structure
  const segmentSize = Math.floor(scriptLength / 5);

  const basicMoments = [
    {
      position: 0,
      category: 'Hook' as const,
      searchQuery: 'attention grabbing wow',
      importance: 'high' as const
    },
    {
      position: segmentSize,
      category: 'Problem' as const,
      searchQuery: 'frustrated issue problem',
      importance: 'medium' as const
    },
    {
      position: segmentSize * 2,
      category: 'Solution' as const,
      searchQuery: 'solution success happy',
      importance: 'high' as const
    },
    {
      position: segmentSize * 3,
      category: 'Wow' as const,
      searchQuery: 'amazing results mind blown',
      importance: 'medium' as const
    },
    {
      position: Math.max(0, scriptLength - 100),
      category: 'CTA' as const,
      searchQuery: 'click here call to action',
      importance: 'high' as const
    }
  ];

  basicMoments.forEach((moment, index) => {
    const startPos = Math.min(moment.position, scriptLength - 30);
    const endPos = Math.min(startPos + 60, scriptLength);
    const excerpt = script.substring(startPos, endPos).trim();

    if (excerpt.length > 10) {
      fallbackMoments.push({
        id: `fallback-${index}`,
        category: moment.category,
        scriptExcerpt: excerpt,
        scriptPosition: { start: startPos, end: endPos },
        searchQuery: moment.searchQuery,
        searchQueries: [moment.searchQuery],
        context: `Fallback moment for ${moment.category}`,
        clipStyle: determineClipStyleFromCategory(moment.category),
        importance: moment.importance,
        clips: []
      });
    }
  });

  console.log(`Fallback analysis created ${fallbackMoments.length} moments`);
  return fallbackMoments;
}
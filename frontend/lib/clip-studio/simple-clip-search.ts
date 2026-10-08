import { ClipMoment, Clip } from './types';

/**
 * Simple, effective clip search optimized for actual clip discovery
 * Focuses on what makes clips work: reactions, emotions, and visual moments
 */

const KLIPY_API_KEY = process.env.NEXT_PUBLIC_KLIPY_API_KEY || '';
const KLIPY_BASE_URL = 'https://api.klipy.com/api/v1';

export async function findBestClipsForMoment(moment: ClipMoment): Promise<Clip[]> {
  console.log(`🎯 Simple search for: ${moment.category} - "${moment.scriptExcerpt}"`);
  
  // Generate 3-4 targeted search queries that work well for clips
  const searchQueries = generateClipOptimizedQueries(moment);
  console.log(`Generated queries: ${searchQueries.join(', ')}`);
  
  // Search with each query and combine results
  const allClips: Clip[] = [];
  const seenIds = new Set<string>();
  
  for (const query of searchQueries) {
    try {
      const clips = await searchKlipyWithQuery(query);
      
      // Add unique clips
      clips.forEach(clip => {
        if (!seenIds.has(clip.id)) {
          allClips.push(clip);
          seenIds.add(clip.id);
        }
      });
      
      // Stop early if we have enough good options
      if (allClips.length >= 15) break;
      
    } catch (error) {
      console.warn(`Query "${query}" failed:`, error);
    }
  }
  
  // Return top 6 clips
  const topClips = allClips.slice(0, 6);
  console.log(`✨ Selected ${topClips.length} clips from ${allClips.length} candidates`);
  
  return topClips;
}

function generateClipOptimizedQueries(moment: ClipMoment): string[] {
  const queries: string[] = [];
  
  // Start with Gemini's best query
  if (moment.searchQueries && moment.searchQueries.length > 0) {
    queries.push(moment.searchQueries[0]);
  } else {
    queries.push(moment.searchQuery);
  }
  
  // Add emotion-based query (clips are great for emotions)
  const emotionQuery = getEmotionQuery(moment.scriptExcerpt, moment.category);
  if (emotionQuery && !queries.includes(emotionQuery)) {
    queries.push(emotionQuery);
  }
  
  // Add reaction-based query (very popular clip category)
  const reactionQuery = getReactionQuery(moment.scriptExcerpt, moment.category);
  if (reactionQuery && !queries.includes(reactionQuery)) {
    queries.push(reactionQuery);
  }
  
  // Add category-specific query optimized for clips
  const categoryQuery = getCategoryClipQuery(moment.category);
  if (categoryQuery && !queries.includes(categoryQuery)) {
    queries.push(categoryQuery);
  }
  
  return queries.slice(0, 3); // Keep it simple - 3 queries max
}

function getEmotionQuery(text: string, category: string): string {
  const textLower = text.toLowerCase();
  
  // Common emotional patterns in advertising scripts
  if (textLower.includes('amazing') || textLower.includes('incredible') || textLower.includes('wow')) {
    return 'amazed wow reaction';
  }
  if (textLower.includes('frustrated') || textLower.includes('annoying') || textLower.includes('difficult')) {
    return 'frustrated annoyed';
  }
  if (textLower.includes('happy') || textLower.includes('excited') || textLower.includes('love')) {
    return 'happy excited celebration';
  }
  if (textLower.includes('solved') || textLower.includes('finally') || textLower.includes('easy')) {
    return 'relief finally solved';
  }
  if (textLower.includes('surprised') || textLower.includes('shocking') || textLower.includes('unexpected')) {
    return 'surprised shocked reaction';
  }
  
  // Category-based emotions
  const categoryEmotions: Record<string, string> = {
    'Hook': 'wow surprised reaction',
    'Problem': 'frustrated annoyed upset',
    'Solution': 'happy relief excited',
    'Wow': 'amazed mind blown',
    'Social Proof': 'thumbs up approval',
    'CTA': 'excited lets go',
    'Emotion': 'emotional heartfelt',
    'Humor': 'laughing funny',
    'Transition': 'thinking contemplating'
  };
  
  return categoryEmotions[category] || 'happy reaction';
}

function getReactionQuery(text: string, category: string): string {
  const textLower = text.toLowerCase();
  
  // Look for action words that translate to good reaction clips
  if (textLower.includes('click') || textLower.includes('tap')) {
    return 'pointing finger click';
  }
  if (textLower.includes('get') || textLower.includes('start') || textLower.includes('now')) {
    return 'lets go action';
  }
  if (textLower.includes('look') || textLower.includes('see') || textLower.includes('check')) {
    return 'looking checking';
  }
  if (textLower.includes('work') || textLower.includes('done') || textLower.includes('success')) {
    return 'success celebration';
  }
  
  // Category-based reactions  
  const categoryReactions: Record<string, string> = {
    'Hook': 'stop wait attention',
    'Problem': 'facepalm headache stress',
    'Solution': 'lightbulb eureka moment',
    'Wow': 'jaw drop mind blown',
    'Social Proof': 'clapping applause approval',
    'CTA': 'pointing tap click here',
    'Emotion': 'crying laughing emotional',
    'Humor': 'lol laughing crying',
    'Transition': 'next arrow forward'
  };
  
  return categoryReactions[category] || 'reaction face';
}

function getCategoryClipQuery(category: string): string {
  // Simple, proven clip search terms for each category
  const categoryQueries: Record<string, string> = {
    'Hook': 'attention grabbing wow',
    'Problem': 'problem struggle annoyed',
    'Solution': 'solution fixed success',
    'Wow': 'amazing incredible spectacular',
    'Social Proof': 'approval five stars thumbs up',
    'CTA': 'call to action click now',
    'Emotion': 'emotional reaction feeling',
    'Humor': 'funny comedy laughing',
    'Transition': 'next step forward'
  };
  
  return categoryQueries[category] || 'reaction';
}

async function searchKlipyWithQuery(query: string): Promise<Clip[]> {
  try {
    const params = new URLSearchParams({
      q: query.trim(),
      page: '1',
      per_page: '8', // Get 8 per query
      customer_id: 'clip-studio-simple',
      locale: 'en_US',
      content_filter: 'medium'
    });

    const response = await fetch(`${KLIPY_BASE_URL}/${KLIPY_API_KEY}/clips/search?${params}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    });

    if (!response.ok) {
      console.warn(`Klipy API returned ${response.status} for query: ${query}`);
      return [];
    }

    const responseData = await response.json();
    
    // Check if the request was successful
    if (!responseData.result) {
      console.warn(`Klipy API returned unsuccessful result for query: ${query}`);
      return [];
    }
    
    // Extract clips array from the correct structure
    const clipsArray = responseData.data?.data || [];

    if (clipsArray.length === 0) {
      console.log(`No clips found for query: ${query}`);
      return [];
    }

    return clipsArray.slice(0, 8).map((clip: any, i: number) => {
      // Extract clip URLs from the API structure
      const mp4Url = clip.file?.mp4;
      const gifUrl = clip.file?.gif;
      const webpUrl = clip.file?.webp;
      
      // Use MP4 as main URL, fallback to GIF then WebP
      const mainUrl = mp4Url || gifUrl || webpUrl || clip.url;
      
      return {
        id: clip.slug || `clip-${Date.now()}-${i}`,
        url: mainUrl,
        previewUrl: mp4Url || gifUrl || webpUrl,
        downloadUrl: mp4Url || mainUrl,
        title: clip.title || '',
        slug: clip.slug || '',
        dimensions: {
          width: clip.file_meta?.mp4?.width || clip.file_meta?.gif?.width || 300,
          height: clip.file_meta?.mp4?.height || clip.file_meta?.gif?.height || 300
        },
        fileSize: 0, // File size not provided in this API
        tags: clip.tags || [],
        formats: {
          mp4: mp4Url,
          gif: gifUrl,
          webp: webpUrl
        },
        source: 'klipy' as const
      };
    });
    
  } catch (error) {
    console.error(`Search error for query "${query}":`, error);
    return [];
  }
}
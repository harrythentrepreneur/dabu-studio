import { GifMoment, Gif } from './types';

/**
 * Simple, effective GIF search optimized for actual GIF discovery
 * Focuses on what makes GIFs work: reactions, emotions, and visual moments
 */

const KLIPY_API_KEY = process.env.NEXT_PUBLIC_KLIPY_API_KEY || '';
const KLIPY_BASE_URL = 'https://api.klipy.com/api/v1';

export async function findBestGifsForMoment(moment: GifMoment): Promise<Gif[]> {
  console.log(`🎯 Simple search for: ${moment.category} - "${moment.scriptExcerpt}"`);
  
  // Generate 3-4 targeted search queries that work well for GIFs
  const searchQueries = generateGifOptimizedQueries(moment);
  console.log(`Generated queries: ${searchQueries.join(', ')}`);
  
  // Search with each query and combine results
  const allGifs: Gif[] = [];
  const seenIds = new Set<string>();
  
  for (const query of searchQueries) {
    try {
      const gifs = await searchKlipyWithQuery(query);
      
      // Add unique GIFs
      gifs.forEach(gif => {
        if (!seenIds.has(gif.id)) {
          allGifs.push(gif);
          seenIds.add(gif.id);
        }
      });
      
      // Stop early if we have enough good options
      if (allGifs.length >= 15) break;
      
    } catch (error) {
      console.warn(`Query "${query}" failed:`, error);
    }
  }
  
  // Return top 6 GIFs
  const topGifs = allGifs.slice(0, 6);
  console.log(`✨ Selected ${topGifs.length} GIFs from ${allGifs.length} candidates`);
  
  return topGifs;
}

function generateGifOptimizedQueries(moment: GifMoment): string[] {
  const queries: string[] = [];
  
  // Start with Gemini's best query
  if (moment.searchQueries && moment.searchQueries.length > 0) {
    queries.push(moment.searchQueries[0]);
  } else {
    queries.push(moment.searchQuery);
  }
  
  // Add emotion-based query (GIFs are great for emotions)
  const emotionQuery = getEmotionQuery(moment.scriptExcerpt, moment.category);
  if (emotionQuery && !queries.includes(emotionQuery)) {
    queries.push(emotionQuery);
  }
  
  // Add reaction-based query (very popular GIF category)
  const reactionQuery = getReactionQuery(moment.scriptExcerpt, moment.category);
  if (reactionQuery && !queries.includes(reactionQuery)) {
    queries.push(reactionQuery);
  }
  
  // Add category-specific query optimized for GIFs
  const categoryQuery = getCategoryGifQuery(moment.category);
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
  
  // Look for action words that translate to good reaction GIFs
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

function getCategoryGifQuery(category: string): string {
  // Simple, proven GIF search terms for each category
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

async function searchKlipyWithQuery(query: string): Promise<Gif[]> {
  try {
    const params = new URLSearchParams({
      q: query.trim(),
      page: '1',
      per_page: '8', // Get 8 per query
      customer_id: 'gif-studio-simple',
      locale: 'en_US',
      content_filter: 'medium',
      sort: 'relevant'
    });

    const response = await fetch(`${KLIPY_BASE_URL}/${KLIPY_API_KEY}/gifs/search?${params}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    });

    if (!response.ok) {
      console.warn(`Klipy API returned ${response.status} for query: ${query}`);
      return [];
    }

    const responseData = await response.json();
    let gifsArray: any[] = [];
    
    // Handle the nested response structure
    if (responseData.data?.data && Array.isArray(responseData.data.data)) {
      gifsArray = responseData.data.data;
    } else if (Array.isArray(responseData.data)) {
      gifsArray = responseData.data;
    } else {
      console.warn(`Unexpected response structure for query: ${query}`);
      return [];
    }

    if (gifsArray.length === 0) {
      console.log(`No GIFs found for query: ${query}`);
      return [];
    }

    return gifsArray.slice(0, 8).map((gif: any, i: number) => ({
      id: gif.id?.toString() || `gif-${Date.now()}-${i}`,
      url: gif.file?.hd?.gif?.url || gif.HD?.gif || gif.file?.md?.gif?.url || gif.MD?.gif || '',
      previewUrl: gif.file?.md?.gif?.url || gif.MD?.gif || gif.file?.sm?.gif?.url || gif.SM?.gif || '',
      downloadUrl: gif.file?.hd?.gif?.url || gif.HD?.gif || gif.file?.md?.gif?.url || gif.MD?.gif || '',
      dimensions: {
        width: gif.file?.hd?.gif?.width || gif.HD?.width || 300,
        height: gif.file?.hd?.gif?.height || gif.HD?.height || 300
      },
      fileSize: gif.file?.hd?.gif?.size || gif.HD?.size || 0,
      source: 'klipy' as const
    }));
    
  } catch (error) {
    console.error(`Search error for query "${query}":`, error);
    return [];
  }
}
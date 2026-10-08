import { ClipMoment, Clip, KlipyClipResponse } from './types';

const KLIPY_API_KEY = process.env.NEXT_PUBLIC_KLIPY_API_KEY || '';
const KLIPY_BASE_URL = 'https://api.klipy.com/api/v1';
const KLIPY_CUSTOMER_ID = 'clip-studio-user'; // Unique identifier for this application

export async function searchClipsWithKlipy(
  moments: ClipMoment[], 
  refresh: boolean = false
): Promise<ClipMoment[]> {
  if (!moments || moments.length === 0) {
    return [];
  }

  try {
    // Process each moment in parallel with proper error handling
    const momentsWithClips = await Promise.all(
      moments.map(async (moment) => {
        try {
          const clips = await searchClipsForMoment(moment, refresh);
          return {
            ...moment,
            clips: clips || []
          };
        } catch (error) {
          console.error(`Failed to search clips for moment ${moment.id}:`, error);
          // Return moment with empty clips array on error
          return {
            ...moment,
            clips: []
          };
        }
      })
    );

    return momentsWithClips;
  } catch (error) {
    console.error('Critical error in searchClipsWithKlipy:', error);
    // Return original moments with empty clip arrays as fallback
    return moments.map(moment => ({ ...moment, clips: [] }));
  }
}

async function searchClipsForMoment(moment: ClipMoment, refresh: boolean): Promise<Clip[]> {
  try {
    // Use multiple search queries from Gemini API if available
    let searchQuery = moment.searchQuery;
    
    if (refresh && moment.searchQueries && moment.searchQueries.length > 1) {
      // Use different search queries when refreshing
      const randomIndex = Math.floor(Math.random() * moment.searchQueries.length);
      searchQuery = moment.searchQueries[randomIndex];
    } else if (refresh) {
      // Fallback to alternative search terms based on category
      searchQuery = getAlternativeSearchQuery(moment.category, moment.searchQuery);
    }
    
    // Clean up the search query for better results
    searchQuery = optimizeSearchQuery(searchQuery);

    // Build URL with optimized parameters for Klipy Clips API
    const params = new URLSearchParams({
      q: searchQuery,
      page: refresh ? '2' : '1', // Get different results when refreshing
      per_page: '15', // Get more options to choose from
      customer_id: KLIPY_CUSTOMER_ID,
      locale: 'en_US',
      content_filter: 'medium'
    });

    const response = await fetch(`${KLIPY_BASE_URL}/${KLIPY_API_KEY}/clips/search?${params}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Klipy Clips API error: ${response.status}`);
    }

    const responseData: KlipyClipResponse = await response.json();
    
    // Check if the request was successful
    if (!responseData.result) {
      console.log('Klipy API returned unsuccessful result for query:', searchQuery);
      return [];
    }
    
    // Extract clips array from the correct structure
    const clipsArray = responseData.data?.data || [];
    
    // If no clips found, return empty array
    if (clipsArray.length === 0) {
      console.log('No clips found for query:', searchQuery);
      return [];
    }
    
    // Transform clips according to the actual API structure
    const transformedClips: Clip[] = [];
    const maxClips = 8; // Show more options for user to choose from
    
    // Process all available clips
    for (let i = 0; i < Math.min(maxClips, clipsArray.length); i++) {
      const clip = clipsArray[i];
      
      // Extract clip URLs from the API structure
      const mp4Url = clip.file?.mp4;
      const gifUrl = clip.file?.gif;
      const webpUrl = clip.file?.webp;
      
      // Use MP4 as main URL, fallback to GIF then WebP
      const mainUrl = mp4Url || gifUrl || webpUrl || clip.url;
      if (!mainUrl) {
        console.warn(`Skipping clip ${clip.slug} - no valid URL found`);
        continue;
      }
      
      // Use MP4 for preview if available, otherwise GIF
      const previewUrl = mp4Url || gifUrl || webpUrl;
      
      // Use the best available format for download
      const downloadUrl = mp4Url || mainUrl;
      
      transformedClips.push({
        id: clip.slug || `clip-${Date.now()}-${i}`,
        url: mainUrl,
        previewUrl: previewUrl,
        downloadUrl: downloadUrl,
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
      });
    }
    
    // Return top results (Klipy already sorts by relevance)
    return transformedClips.slice(0, 6);
  } catch (error) {
    console.error('Error fetching clips from Klipy:', error);
    
    // Return fallback trending clips if search fails
    return getFallbackClips(moment.category);
  }
}

// Optimize search query for better clip results
function optimizeSearchQuery(query: string): string {
  // Remove extra spaces and clean up
  let optimized = query.trim().replace(/\s+/g, ' ');
  
  // Limit to most important keywords (Klipy works better with focused queries)
  const words = optimized.split(' ');
  if (words.length > 4) {
    // Keep the most important words (usually first few)
    optimized = words.slice(0, 4).join(' ');
  }
  
  // Remove common stop words that don't help with clip search
  const stopWords = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'];
  const filteredWords = optimized.split(' ').filter(word => 
    !stopWords.includes(word.toLowerCase())
  );
  
  return filteredWords.join(' ');
}

// Get alternative search queries for refresh
function getAlternativeSearchQuery(category: string, originalQuery: string): string {
  const alternatives: Record<string, string[]> = {
    'Hook': [
      'omg wow shocked surprise',
      'mind blown amazing unbelievable',
      'attention alert breaking news',
      'stop look dramatic reaction'
    ],
    'Problem': [
      'frustrated angry annoyed mad',
      'confused thinking puzzled what',
      'tired exhausted sleepy done',
      'stressed anxiety overwhelmed help'
    ],
    'Solution': [
      'yes success winner victory',
      'problem solved fixed done',
      'happy relief finally phew',
      'thumbs up good great perfect'
    ],
    'Wow': [
      'money rich dollars cash',
      'explosion boom mind blown',
      'rocket moon launch space',
      'fire hot viral trending'
    ],
    'Social Proof': [
      'five stars rating review',
      'crowd people group happy',
      'applause clapping cheering celebration',
      'verified trust authentic real'
    ],
    'CTA': [
      'click tap press button',
      'buy now shopping cart',
      'swipe up arrow pointing',
      'download get app install'
    ],
    'Emotion': [
      'love hearts romance cute',
      'happy joy smile laugh',
      'excited party celebration fun',
      'awesome cool amazing great'
    ],
    'Transition': [
      'next arrow forward continue',
      'loading wait progress dots',
      'transition change transform morph',
      'meanwhile switch flip turn'
    ],
    'Humor': [
      'lol funny hilarious comedy',
      'meme joke laugh humor',
      'silly goofy weird crazy',
      'sarcastic ironic witty clever'
    ]
  };
  
  const categoryAlternatives = alternatives[category] || [originalQuery];
  // Pick a random alternative
  return categoryAlternatives[Math.floor(Math.random() * categoryAlternatives.length)];
}

async function getFallbackClips(category: string): Promise<Clip[]> {
  try {
    // Use category-specific trending search as fallback
    const fallbackQueries: Record<string, string> = {
      'Hook': 'wow amazing reaction',
      'Problem': 'frustrated confused',
      'Solution': 'success celebration',
      'Wow': 'mind blown awesome',
      'Social Proof': 'thumbs up applause',
      'CTA': 'click here button',
      'Emotion': 'happy excited',
      'Transition': 'arrow next',
      'Humor': 'funny lol'
    };
    
    const fallbackQuery = fallbackQueries[category] || 'reaction clip';
    
    const params = new URLSearchParams({
      q: fallbackQuery,
      page: '1',
      per_page: '10',
      customer_id: KLIPY_CUSTOMER_ID,
      locale: 'en_US',
      content_filter: 'medium'
    });

    const response = await fetch(`${KLIPY_BASE_URL}/${KLIPY_API_KEY}/clips/search?${params}`);
    
    if (!response.ok) {
      return [];
    }

    const responseData: KlipyClipResponse = await response.json();
    
    // Check if the request was successful
    if (!responseData.result) {
      return [];
    }
    
    // Extract clips array from the correct structure
    const clipsArray = responseData.data?.data || [];
    
    // If no clips found, return empty array
    if (clipsArray.length === 0) {
      return [];
    }
    
    // Transform with validation
    const transformedClips: Clip[] = [];
    
    for (let i = 0; i < Math.min(6, clipsArray.length); i++) {
      const clip = clipsArray[i];
      
      // Extract clip URLs from the API structure
      const mp4Url = clip.file?.mp4;
      const gifUrl = clip.file?.gif;
      const webpUrl = clip.file?.webp;
      
      // Use MP4 as main URL, fallback to GIF then WebP
      const mainUrl = mp4Url || gifUrl || webpUrl || clip.url;
      if (!mainUrl) {
        continue;
      }
      
      transformedClips.push({
        id: clip.slug || `clip-fallback-${Date.now()}-${i}`,
        url: mainUrl,
        previewUrl: mp4Url || gifUrl || webpUrl,
        downloadUrl: mp4Url || mainUrl,
        title: clip.title || '',
        slug: clip.slug || '',
        dimensions: {
          width: clip.file_meta?.mp4?.width || clip.file_meta?.gif?.width || 300,
          height: clip.file_meta?.mp4?.height || clip.file_meta?.gif?.height || 300
        },
        fileSize: 0,
        tags: clip.tags || [],
        formats: {
          mp4: mp4Url,
          gif: gifUrl,
          webp: webpUrl
        },
        source: 'klipy' as const
      });
    }
    
    return transformedClips;
  } catch (error) {
    console.error('Error fetching fallback clips:', error);
    return [];
  }
}

export async function getTrendingClips(): Promise<Clip[]> {
  try {
    const params = new URLSearchParams({
      per_page: '20',
      customer_id: KLIPY_CUSTOMER_ID,
      locale: 'en_US',
      content_filter: 'medium'
    });

    const response = await fetch(`${KLIPY_BASE_URL}/${KLIPY_API_KEY}/clips/trending?${params}`);
    
    if (!response.ok) {
      throw new Error(`Klipy Trending Clips API error: ${response.status}`);
    }

    const responseData: KlipyClipResponse = await response.json();
    
    // Check if the request was successful
    if (!responseData.result) {
      return [];
    }
    
    // Extract clips array from the correct structure
    const clipsArray = responseData.data?.data || [];
    
    // Transform trending clips
    const transformedClips: Clip[] = [];
    
    for (let i = 0; i < Math.min(10, clipsArray.length); i++) {
      const clip = clipsArray[i];
      
      // Extract clip URLs from the API structure
      const mp4Url = clip.file?.mp4;
      const gifUrl = clip.file?.gif;
      const webpUrl = clip.file?.webp;
      
      const mainUrl = mp4Url || gifUrl || webpUrl || clip.url;
      if (!mainUrl) {
        continue;
      }
      
      transformedClips.push({
        id: clip.slug || `trending-clip-${Date.now()}-${i}`,
        url: mainUrl,
        previewUrl: mp4Url || gifUrl || webpUrl,
        downloadUrl: mp4Url || mainUrl,
        title: clip.title || '',
        slug: clip.slug || '',
        dimensions: {
          width: clip.file_meta?.mp4?.width || clip.file_meta?.gif?.width || 300,
          height: clip.file_meta?.mp4?.height || clip.file_meta?.gif?.height || 300
        },
        fileSize: 0,
        tags: clip.tags || [],
        formats: {
          mp4: mp4Url,
          gif: gifUrl,
          webp: webpUrl
        },
        source: 'klipy' as const
      });
    }
    
    return transformedClips;
  } catch (error) {
    console.error('Error fetching trending clips:', error);
    return [];
  }
}
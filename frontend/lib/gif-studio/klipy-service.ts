import { GifMoment, Gif, KlipyGifResponse } from './types';

const KLIPY_API_KEY = process.env.NEXT_PUBLIC_KLIPY_API_KEY || '';
const KLIPY_BASE_URL = 'https://api.klipy.com/api/v1';
const KLIPY_CUSTOMER_ID = 'gif-studio-user'; // Unique identifier for this application

export async function searchGifsWithKlipy(
  moments: GifMoment[], 
  refresh: boolean = false
): Promise<GifMoment[]> {
  if (!moments || moments.length === 0) {
    return [];
  }

  try {
    // Process each moment in parallel with proper error handling
    const momentsWithGifs = await Promise.all(
      moments.map(async (moment) => {
        try {
          const gifs = await searchGifsForMoment(moment, refresh);
          return {
            ...moment,
            gifs: gifs || []
          };
        } catch (error) {
          console.error(`Failed to search GIFs for moment ${moment.id}:`, error);
          // Return moment with empty GIFs array on error
          return {
            ...moment,
            gifs: []
          };
        }
      })
    );

    return momentsWithGifs;
  } catch (error) {
    console.error('Critical error in searchGifsWithKlipy:', error);
    // Return original moments with empty GIF arrays as fallback
    return moments.map(moment => ({ ...moment, gifs: [] }));
  }
}

async function searchGifsForMoment(moment: GifMoment, refresh: boolean): Promise<Gif[]> {
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

    // Build URL with optimized parameters for Klipy API
    const params = new URLSearchParams({
      q: searchQuery,
      page: refresh ? '2' : '1', // Get different results when refreshing
      per_page: '15', // Get more options to choose from
      customer_id: KLIPY_CUSTOMER_ID,
      locale: 'en_US',
      content_filter: 'medium',
      // Add additional parameters for better results
      sort: 'relevant' // Sort by relevance
    });

    const response = await fetch(`${KLIPY_BASE_URL}/${KLIPY_API_KEY}/gifs/search?${params}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Klipy API error: ${response.status}`);
    }

    const responseData = await response.json();
    
    // Handle nested data structure from Klipy API
    // The API returns { result: true, data: { data: [...] } }
    let gifsArray: any[] = [];
    
    if (responseData.data && responseData.data.data && Array.isArray(responseData.data.data)) {
      gifsArray = responseData.data.data;
    } else if (Array.isArray(responseData.data)) {
      gifsArray = responseData.data;
    } else if (responseData.results && Array.isArray(responseData.results)) {
      gifsArray = responseData.results;
    }
    
    // If no GIFs found, return empty array
    if (!gifsArray || gifsArray.length === 0) {
      console.log('No GIFs found for query:', moment.searchQuery);
      return [];
    }
    
    // Transform and select best GIFs from results
    const transformedGifs: Gif[] = [];
    const maxGifs = 8; // Show more options for user to choose from
    
    // Process all available GIFs
    for (let i = 0; i < Math.min(maxGifs, gifsArray.length); i++) {
      const gif = gifsArray[i];
      
      // Extract GIF URLs from the nested file structure
      const hdGif = gif.file?.hd?.gif?.url || gif.HD?.gif;
      const mdGif = gif.file?.md?.gif?.url || gif.MD?.gif;
      const smGif = gif.file?.sm?.gif?.url || gif.SM?.gif;
      const xsGif = gif.file?.xs?.gif?.url || gif.XS?.gif;
      
      // Skip if no valid URL found
      const mainUrl = hdGif || mdGif || smGif || xsGif;
      if (!mainUrl) {
        console.warn(`Skipping GIF ${gif.id} - no valid URL found`);
        continue;
      }
      
      // Prefer medium size for preview (better performance)
      const previewUrl = mdGif || smGif || xsGif || hdGif || mainUrl;
      
      // Use HD for download when available
      const downloadUrl = hdGif || mdGif || mainUrl;
      
      transformedGifs.push({
        id: gif.id?.toString() || `gif-${Date.now()}-${i}`,
        url: mainUrl,
        previewUrl: previewUrl,
        downloadUrl: downloadUrl,
        dimensions: {
          width: gif.file?.hd?.gif?.width || gif.file?.md?.gif?.width || gif.HD?.width || gif.MD?.width || 300,
          height: gif.file?.hd?.gif?.height || gif.file?.md?.gif?.height || gif.HD?.height || gif.MD?.height || 300
        },
        fileSize: gif.file?.hd?.gif?.size || gif.file?.md?.gif?.size || gif.HD?.size || gif.MD?.size || 0,
        source: 'klipy' as const
      });
    }
    
    // Return top results (Klipy already sorts by relevance)
    return transformedGifs.slice(0, 6);
  } catch (error) {
    console.error('Error fetching GIFs from Klipy:', error);
    
    // Return fallback trending GIFs if search fails
    return getFallbackGifs(moment.category);
  }
}

// Optimize search query for better GIF results
function optimizeSearchQuery(query: string): string {
  // Remove extra spaces and clean up
  let optimized = query.trim().replace(/\s+/g, ' ');
  
  // Limit to most important keywords (Klipy works better with focused queries)
  const words = optimized.split(' ');
  if (words.length > 4) {
    // Keep the most important words (usually first few)
    optimized = words.slice(0, 4).join(' ');
  }
  
  // Remove common stop words that don't help with GIF search
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

async function getFallbackGifs(category: string): Promise<Gif[]> {
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
    
    const fallbackQuery = fallbackQueries[category] || 'reaction gif';
    
    const params = new URLSearchParams({
      q: fallbackQuery,
      page: '1',
      per_page: '10',
      customer_id: KLIPY_CUSTOMER_ID,
      locale: 'en_US',
      content_filter: 'medium',
      sort: 'trending' // Get trending GIFs as fallback
    });

    const response = await fetch(`${KLIPY_BASE_URL}/${KLIPY_API_KEY}/gifs/search?${params}`);
    
    if (!response.ok) {
      return [];
    }

    const responseData = await response.json();
    
    // Handle nested data structure from Klipy API
    // The API returns { result: true, data: { data: [...] } }
    let gifsArray: any[] = [];
    
    if (responseData.data && responseData.data.data && Array.isArray(responseData.data.data)) {
      gifsArray = responseData.data.data;
    } else if (Array.isArray(responseData.data)) {
      gifsArray = responseData.data;
    } else if (responseData.results && Array.isArray(responseData.results)) {
      gifsArray = responseData.results;
    }
    
    // If no GIFs found, return empty array
    if (!gifsArray || gifsArray.length === 0) {
      return [];
    }
    
    // Transform with validation
    const transformedGifs: Gif[] = [];
    
    for (let i = 0; i < Math.min(6, gifsArray.length); i++) {
      const gif = gifsArray[i];
      
      // Extract GIF URLs from the nested file structure
      const hdGif = gif.file?.hd?.gif?.url || gif.HD?.gif;
      const mdGif = gif.file?.md?.gif?.url || gif.MD?.gif;
      const smGif = gif.file?.sm?.gif?.url || gif.SM?.gif;
      const xsGif = gif.file?.xs?.gif?.url || gif.XS?.gif;
      
      // Skip if no valid URL found
      const mainUrl = hdGif || mdGif || smGif || xsGif;
      if (!mainUrl) {
        continue;
      }
      
      transformedGifs.push({
        id: gif.id?.toString() || `gif-fallback-${Date.now()}-${i}`,
        url: mainUrl,
        previewUrl: smGif || xsGif || mdGif || hdGif || mainUrl,
        downloadUrl: hdGif || mdGif || smGif || mainUrl,
        dimensions: {
          width: gif.file?.hd?.gif?.width || gif.file?.md?.gif?.width || gif.HD?.width || gif.MD?.width || 300,
          height: gif.file?.hd?.gif?.height || gif.file?.md?.gif?.height || gif.HD?.height || gif.MD?.height || 300
        },
        fileSize: gif.file?.hd?.gif?.size || gif.file?.md?.gif?.size || gif.HD?.size || gif.MD?.size || 0,
        source: 'klipy' as const
      });
    }
    
    return transformedGifs;
  } catch (error) {
    console.error('Error fetching fallback GIFs:', error);
    return [];
  }
}
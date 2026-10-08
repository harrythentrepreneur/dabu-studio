export interface GifMoment {
  id: string;
  category: 'Hook' | 'Wow' | 'Emotion' | 'Transition' | 'Problem' | 'Solution' | 'Social Proof' | 'CTA' | 'Humor';
  scriptExcerpt: string;
  scriptPosition: {
    start: number;
    end: number;
  };
  searchQuery: string;
  searchQueries?: string[]; // Multiple search queries from Gemini API
  context: string;
  gifStyle: 'reaction' | 'illustration' | 'text-overlay' | 'meme' | 'aesthetic' | 'animated-text';
  importance: 'high' | 'medium' | 'low';
  gifs: Gif[];
}

export interface Gif {
  id: string;
  url: string;
  previewUrl: string;
  downloadUrl: string;
  dimensions: {
    width: number;
    height: number;
  };
  fileSize: number;
  source: 'klipy' | 'giphy' | 'tenor' | 'other';
}

export interface GeminiResponse {
  gif_moments: Array<{
    category: string;
    script_excerpt: string;
    search_query: string;
    context: string;
    gif_style: string;
    position: number;
    importance: string;
  }>;
}

export interface KlipyGifResponse {
  data: Array<{
    id: string;
    title?: string;
    HD: {
      gif?: string;
      webp?: string;
      width: number;
      height: number;
      size?: number;
    };
    MD: {
      gif?: string;
      webp?: string;
      width: number;
      height: number;
      size?: number;
    };
    SM: {
      gif?: string;
      webp?: string;
      width: number;
      height: number;
      size?: number;
    };
    XS: {
      gif?: string;
      webp?: string;
      width: number;
      height: number;
      size?: number;
    };
  }>;
  meta: {
    msg: string;
    status: number;
    response_id: string;
  };
  pagination?: {
    total_count: number;
    count: number;
    offset: number;
  };
}
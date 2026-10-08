export interface ClipMoment {
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
  clipStyle: 'reaction' | 'illustration' | 'text-overlay' | 'meme' | 'aesthetic' | 'animated-text';
  importance: 'high' | 'medium' | 'low';
  clips: Clip[];
}

export interface Clip {
  id: string;
  url: string;
  previewUrl: string;
  downloadUrl: string;
  title?: string;
  slug?: string;
  dimensions: {
    width: number;
    height: number;
  };
  fileSize: number;
  tags?: string[];
  formats: {
    mp4?: string;
    gif?: string;
    webp?: string;
  };
  source: 'klipy' | 'other';
}

export interface GeminiResponse {
  clip_moments: Array<{
    category: string;
    script_excerpt: string;
    search_query: string;
    context: string;
    clip_style: string;
    position: number;
    importance: string;
  }>;
}

export interface KlipyClipResponse {
  result: boolean;
  data: {
    data: Array<{
      url: string;
      title: string;
      slug: string;
      blur_preview?: string;
      file: {
        mp4: string;
        gif: string;
        webp: string;
      };
      file_meta: {
        mp4: {
          width: number;
          height: number;
        };
        gif: {
          width: number;
          height: number;
        };
        webp: {
          width: number;
          height: number;
        };
      };
      tags: string[];
      type: string;
    }>;
    current_page: number;
    per_page: number;
    has_next: boolean;
  };
}
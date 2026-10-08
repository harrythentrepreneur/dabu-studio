import { NextRequest, NextResponse } from 'next/server';
import { GoogleGenerativeAI } from '@google/generative-ai';

// Initialize Gemini AI
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY!);

interface GifMoment {
  id: string;
  scriptSegment: string;
  category: 'reaction' | 'emotion' | 'action' | 'object' | 'text' | 'transition';
  searchQuery: string;
  alternativeQueries: string[];
  timing: {
    suggestedDuration: number;
    placement: 'overlay' | 'cutaway' | 'split-screen';
  };
  mood: string;
  intensity: 'low' | 'medium' | 'high';
}

interface GifAnalysisResponse {
  moments: GifMoment[];
  summary: {
    totalMoments: number;
    dominantCategory: string;
    overallMood: string;
    suggestedStyle: string;
  };
}

export async function POST(request: NextRequest) {
  try {
    // Check if Gemini API key is configured
    if (!process.env.GEMINI_API_KEY) {
      return NextResponse.json(
        { 
          error: 'Gemini API key not configured', 
          details: 'Please add GEMINI_API_KEY to your .env.local file' 
        },
        { status: 500 }
      );
    }

    const { script, maxMoments = 8 } = await request.json();

    if (!script) {
      return NextResponse.json(
        { error: 'Script is required' },
        { status: 400 }
      );
    }

    // Validate maxMoments
    const validMaxMoments = Math.min(Math.max(4, maxMoments), 12);

    // Analyze script with Gemini
    const analysis = await analyzeScriptWithGemini(script, validMaxMoments);

    return NextResponse.json(analysis);
  } catch (error) {
    console.error('Error analyzing script:', error);
    
    // Provide more detailed error information
    let errorMessage = 'Failed to analyze script';
    let errorDetails = 'Unknown error';
    
    if (error instanceof Error) {
      errorDetails = error.message;
      
      // Check for common Gemini API errors
      if (error.message.includes('API key not valid')) {
        errorMessage = 'Invalid Gemini API key';
        errorDetails = 'Please check your GEMINI_API_KEY in .env.local';
      } else if (error.message.includes('model')) {
        errorMessage = 'Invalid model specified';
        errorDetails = 'The requested Gemini model may not be available';
      }
    }
    
    return NextResponse.json(
      { error: errorMessage, details: errorDetails },
      { status: 500 }
    );
  }
}

async function analyzeScriptWithGemini(
  script: string,
  maxMoments: number
): Promise<GifAnalysisResponse> {
  const model = genAI.getGenerativeModel({ 
    model: 'gemini-2.5-flash',
    generationConfig: {
      temperature: 0.1,
      topK: 40,
      topP: 0.8,
      maxOutputTokens: 8192,
      responseMimeType: 'application/json',
    },
  });

  const prompt = `You are an expert at identifying optimal GIF moments in advertising scripts for TikTok videos.

Analyze this script and identify exactly ${maxMoments} moments that would benefit from GIF overlays or cutaways.

Script:
"${script}"

For each moment, provide:
1. The exact script segment (1-2 lines)
2. Category: reaction, emotion, action, object, text, or transition
3. A specific search query for finding the perfect GIF
4. 2-3 alternative search queries
5. Timing suggestions (duration in seconds, placement type)
6. Mood descriptor
7. Intensity level (low/medium/high)

Prioritize:
- Emotional peaks and reactions
- Visual metaphors that enhance the message
- Trending meme potential
- Smooth transitions between scenes
- Text emphasis moments

Return a JSON object with this structure:
{
  "moments": [
    {
      "id": "moment_1",
      "scriptSegment": "exact text from script",
      "category": "reaction",
      "searchQuery": "shocked face gif",
      "alternativeQueries": ["surprised reaction", "mind blown", "omg face"],
      "timing": {
        "suggestedDuration": 2,
        "placement": "overlay"
      },
      "mood": "surprised",
      "intensity": "high"
    }
  ],
  "summary": {
    "totalMoments": ${maxMoments},
    "dominantCategory": "most common category",
    "overallMood": "general mood of all moments",
    "suggestedStyle": "recommended visual style"
  }
}`;

  try {
    const result = await model.generateContent(prompt);
    const response = result.response;
    const text = response.text();
    
    // Parse JSON response
    const analysis = JSON.parse(text);
    
    // Validate and ensure we have the expected structure
    if (!analysis.moments || !Array.isArray(analysis.moments)) {
      throw new Error('Invalid response structure from Gemini');
    }

    // Ensure we have exactly the requested number of moments
    analysis.moments = analysis.moments.slice(0, maxMoments);
    
    // Add IDs if missing
    analysis.moments = analysis.moments.map((moment: any, index: number) => ({
      ...moment,
      id: moment.id || `moment_${index + 1}`,
    }));

    return analysis as GifAnalysisResponse;
  } catch (error: any) {
    console.error('Gemini API error:', error);
    
    // Re-throw the error with more context
    if (error?.message?.includes('API key')) {
      throw new Error('Gemini API key is invalid or not configured properly');
    }
    if (error?.message?.includes('model')) {
      throw new Error('The specified Gemini model (gemini-2.5-flash) is not available or accessible');
    }
    
    throw error; // Re-throw original error if not a known issue
  }
}

// Simple GIF search endpoint (uses Giphy or Tenor API)
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const query = searchParams.get('q');
    const limit = parseInt(searchParams.get('limit') || '10');

    if (!query) {
      return NextResponse.json(
        { error: 'Search query is required' },
        { status: 400 }
      );
    }

    // For now, return mock data (replace with actual Giphy/Tenor API call)
    // You would need to add GIPHY_API_KEY to your environment variables
    const mockGifs = Array.from({ length: limit }, (_, i) => ({
      id: `gif_${i + 1}`,
      title: `${query} GIF ${i + 1}`,
      url: `https://media.giphy.com/media/placeholder${i + 1}/giphy.gif`,
      thumbnail: `https://media.giphy.com/media/placeholder${i + 1}/giphy-preview.gif`,
      width: 480,
      height: 270,
    }));

    return NextResponse.json({
      query,
      results: mockGifs,
      total: mockGifs.length,
    });
  } catch (error) {
    console.error('Error searching GIFs:', error);
    return NextResponse.json(
      { error: 'Failed to search GIFs' },
      { status: 500 }
    );
  }
}
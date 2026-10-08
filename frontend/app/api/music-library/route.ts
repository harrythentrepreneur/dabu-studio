import { NextRequest, NextResponse } from 'next/server';

interface TrendingAudio {
  rank: number;
  position_change: string;
  artist: string;
  title: string;
  full_title: string;
  country: string;
  cover_url: string | null;
  preview_url: string | null;
  apple_music_url: string | null;
  youtube_search_url?: string | null;
}

// Static trending audio data - update this JSON file as needed
const TRENDING_AUDIO_DATA: TrendingAudio[] = [
  {
    rank: 1,
    position_change: '=',
    artist: 'sped up 8282',
    title: 'Cupid – Twin Ver. (FIFTY FIFTY) – Sped Up Version',
    full_title: 'sped up 8282 - Cupid – Twin Ver. (FIFTY FIFTY) – Sped Up Version',
    country: 'US',
    cover_url: 'https://is1-ssl.mzstatic.com/image/thumb/Music116/v4/e1/bc/28/e1bc2835-a85a-c42b-e57a-c8e4d936e7ed/5054197783050.jpg/600x600bb.jpg',
    preview_url: 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview116/v4/1d/fb/f8/1dfbf832-0a5c-850c-ccb9-c77edc10a448/mzaf_18345398077076379739.plus.aac.p.m4a',
    apple_music_url: 'https://music.apple.com/us/album/cupid-twin-ver-feat-sabrina-carpenter/1702580851?i=1702580852&uo=4',
    youtube_search_url: 'https://www.youtube.com/results?search_query=sped+up+8282+Cupid'
  },
  {
    rank: 2,
    position_change: 'NEW',
    artist: 'Ohboyprince',
    title: 'Bounce When She Walk',
    full_title: 'Ohboyprince - Bounce When She Walk',
    country: 'US',
    cover_url: 'https://is1-ssl.mzstatic.com/image/thumb/Music126/v4/e7/4c/da/e74cda50-0180-a513-d852-f9bb20a50d7e/197545157372_cover.jpg/600x600bb.jpg',
    preview_url: 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview122/v4/00/dc/b2/00dcb292-7167-ca5f-9f06-932cb7802f88/mzaf_48026013819792142.plus.aac.p.m4a',
    apple_music_url: 'https://music.apple.com/us/album/bounce-when-she-walk-feat-mykfresh-gwallagangspec/1683611009?i=1683611010&uo=4',
    youtube_search_url: 'https://www.youtube.com/results?search_query=Ohboyprince+Bounce+When+She+Walk'
  },
  {
    rank: 3,
    position_change: '=',
    artist: 'yvel',
    title: 'lovers rock',
    full_title: 'yvel - lovers rock',
    country: 'US',
    cover_url: 'https://is1-ssl.mzstatic.com/image/thumb/Music124/v4/85/d9/05/85d9053a-565b-723d-0823-c0c2a0dbff87/mzi.ifrkjjuc.jpg/600x600bb.jpg',
    preview_url: 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview115/v4/55/26/c7/5526c72b-fbcd-bd2c-a6fe-1b1986a3fc88/mzaf_7203491429243665356.plus.aac.p.m4a',
    apple_music_url: 'https://music.apple.com/us/album/lovers-rock/193532145?i=193533249&uo=4',
    youtube_search_url: 'https://www.youtube.com/results?search_query=yvel+lovers+rock'
  },
  {
    rank: 4,
    position_change: '=',
    artist: 'Pink Paul',
    title: 'Pretty Girls Walk Up',
    full_title: 'Pink Paul - Pretty Girls Walk Up',
    country: 'US',
    cover_url: 'https://is1-ssl.mzstatic.com/image/thumb/Music118/v4/19/c2/33/19c2338e-f80e-f98e-c762-478e0e62354d/4050538311983.jpg/600x600bb.jpg',
    preview_url: 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview116/v4/f1/b3/3e/f1b33e04-4593-d4e0-ae19-6459f3cf7cff/mzaf_14055095197568979735.plus.aac.p.m4a',
    apple_music_url: 'https://music.apple.com/us/album/pretty-girl-2017-remaster/1438560772?i=1438560971&uo=4',
    youtube_search_url: 'https://www.youtube.com/results?search_query=Pink+Paul+Pretty+Girls+Walk+Up'
  },
  {
    rank: 5,
    position_change: '+1',
    artist: 'Rich The Kid',
    title: 'New Freezer',
    full_title: 'Rich The Kid - New Freezer',
    country: 'US',
    cover_url: null,
    preview_url: null,
    apple_music_url: null,
    youtube_search_url: 'https://www.youtube.com/results?search_query=Rich+The+Kid+New+Freezer'
  },
  {
    rank: 6,
    position_change: '+2',
    artist: 'Drake',
    title: 'Rich Flex',
    full_title: 'Drake - Rich Flex',
    country: 'US',
    cover_url: 'https://is1-ssl.mzstatic.com/image/thumb/Music112/v4/8c/e3/85/8ce385f5-3faa-4a01-7b85-ec48e1df2e7a/196589588196.jpg/600x600bb.jpg',
    preview_url: null,
    apple_music_url: 'https://music.apple.com/us/album/rich-flex/1640841971?i=1640841972',
    youtube_search_url: 'https://www.youtube.com/results?search_query=Drake+Rich+Flex'
  },
  {
    rank: 7,
    position_change: '-1',
    artist: 'SZA',
    title: 'Kill Bill',
    full_title: 'SZA - Kill Bill',
    country: 'US',
    cover_url: 'https://is1-ssl.mzstatic.com/image/thumb/Music112/v4/8c/e3/85/8ce385f5-3faa-4a01-7b85-ec48e1df2e7a/196589588196.jpg/600x600bb.jpg',
    preview_url: null,
    apple_music_url: 'https://music.apple.com/us/album/kill-bill/1640841971?i=1640841973',
    youtube_search_url: 'https://www.youtube.com/results?search_query=SZA+Kill+Bill'
  },
  {
    rank: 8,
    position_change: 'NEW',
    artist: 'Ice Spice',
    title: 'In Ha Mood',
    full_title: 'Ice Spice - In Ha Mood',
    country: 'US',
    cover_url: 'https://is1-ssl.mzstatic.com/image/thumb/Music112/v4/8c/e3/85/8ce385f5-3faa-4a01-7b85-ec48e1df2e7a/196589588196.jpg/600x600bb.jpg',
    preview_url: null,
    apple_music_url: 'https://music.apple.com/us/album/in-ha-mood/1640841971?i=1640841974',
    youtube_search_url: 'https://www.youtube.com/results?search_query=Ice+Spice+In+Ha+Mood'
  },
  {
    rank: 9,
    position_change: '=',
    artist: 'Metro Boomin',
    title: 'Creepin',
    full_title: 'Metro Boomin - Creepin',
    country: 'US',
    cover_url: 'https://is1-ssl.mzstatic.com/image/thumb/Music112/v4/8c/e3/85/8ce385f5-3faa-4a01-7b85-ec48e1df2e7a/196589588196.jpg/600x600bb.jpg',
    preview_url: null,
    apple_music_url: 'https://music.apple.com/us/album/creepin/1640841971?i=1640841975',
    youtube_search_url: 'https://www.youtube.com/results?search_query=Metro+Boomin+Creepin'
  },
  {
    rank: 10,
    position_change: '-2',
    artist: 'The Weeknd',
    title: 'Die For You',
    full_title: 'The Weeknd - Die For You',
    country: 'US',
    cover_url: 'https://is1-ssl.mzstatic.com/image/thumb/Music112/v4/8c/e3/85/8ce385f5-3faa-4a01-7b85-ec48e1df2e7a/196589588196.jpg/600x600bb.jpg',
    preview_url: null,
    apple_music_url: 'https://music.apple.com/us/album/die-for-you/1640841971?i=1640841976',
    youtube_search_url: 'https://www.youtube.com/results?search_query=The+Weeknd+Die+For+You'
  }
];

export async function GET() {
  try {
    return NextResponse.json({
      success: true,
      data: TRENDING_AUDIO_DATA,
      timestamp: new Date().toISOString(),
      source: 'static_json',
      total: TRENDING_AUDIO_DATA.length
    });
  } catch (error) {
    console.error('Error in GET /api/music-library:', error);

    return NextResponse.json({
      success: false,
      error: 'Failed to load trending audio data',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 });
  }
}

// POST endpoint for search
export async function POST(request: NextRequest) {
  try {
    const { query } = await request.json();

    // Filter songs if query provided
    let filteredSongs = TRENDING_AUDIO_DATA;
    if (query) {
      const searchLower = query.toLowerCase();
      filteredSongs = TRENDING_AUDIO_DATA.filter((song: any) =>
        song.artist.toLowerCase().includes(searchLower) ||
        song.title.toLowerCase().includes(searchLower) ||
        song.full_title.toLowerCase().includes(searchLower)
      );
    }

    return NextResponse.json({
      success: true,
      data: filteredSongs,
      query: query || '',
      total: filteredSongs.length
    });
  } catch (error) {
    console.error('Error searching trending audio:', error);
    return NextResponse.json(
      {
        success: false,
        error: 'Failed to search trending audio',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}
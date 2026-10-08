"use client";

import { ResultsDisplay } from "@/components/results-display";
import { API_URL } from "@/lib/api-config";

// Mock data for testing the results display
const mockResults = {
  videoUrl: `${API_URL}/api/download/test/video`,
  scriptUrl: `${API_URL}/api/download/test/script`,
  timestampsUrl: `${API_URL}/api/download/test/timestamps`,
  mergedFullUrl: `${API_URL}/api/download/test/merged_full`,
  segments: [] as any[]
};

// Mock timestamps data that will be "fetched"
const mockTimestampsData = {
  total_duration: 120,
  target_duration: 37.96,
  script_segments: [
    {
      segment_number: 1,
      segment_text: "I've been in therapy for three years.",
      start_timestamp: "00:00:21.238",
      end_timestamp: "00:00:23.556",
      duration_seconds: 2.32,
      confidence: 0.9,
      visual_description: "A stable, clear shot of the emotional graph on the laptop screen, setting a baseline before the story begins."
    },
    {
      segment_number: 2,
      segment_text: "Know what my therapist couldn't show me?",
      start_timestamp: "00:00:02.018",
      end_timestamp: "00:00:04.418",
      duration_seconds: 2.4,
      confidence: 0.9,
      visual_description: "A close-up of a hand moving over the laptop's trackpad, suggesting a search for answers or information."
    },
    {
      segment_number: 3,
      segment_text: "Proof I was actually getting better.",
      start_timestamp: "00:00:25.838",
      end_timestamp: "00:00:28.598",
      duration_seconds: 2.76,
      confidence: 0.9,
      visual_description: "A full, clear view of the colorful emotional graph, presented as the 'proof' mentioned in the voiceover."
    },
    {
      segment_number: 4,
      segment_text: "Uploaded five years of WhatsApp to this AI.",
      start_timestamp: "00:03:08.000",
      end_timestamp: "00:03:11.360",
      duration_seconds: 3.36,
      confidence: 0.95,
      visual_description: "The screen shows the user interface for uploading conversations, directly matching the voiceover's action."
    },
    {
      segment_number: 5,
      segment_text: "It mapped my entire emotional evolution.",
      start_timestamp: "00:06:05.000",
      end_timestamp: "00:06:08.520",
      duration_seconds: 3.52,
      confidence: 0.95,
      visual_description: "A wide shot of the emotional graph showing multiple data points and trends over time."
    },
    {
      segment_number: 6,
      segment_text: "Depression peaked January 2023.",
      start_timestamp: "00:04:12.000",
      end_timestamp: "00:04:14.880",
      duration_seconds: 2.88,
      confidence: 0.92,
      visual_description: "Focusing on a specific peak in the graph, highlighting the January 2023 data point."
    },
    {
      segment_number: 7,
      segment_text: "Anxiety dropped 47% after changing jobs.",
      start_timestamp: "00:05:15.000",
      end_timestamp: "00:05:18.240",
      duration_seconds: 3.24,
      confidence: 0.93,
      visual_description: "Graph showing a downward trend in anxiety metrics after a marked job change event."
    },
    {
      segment_number: 8,
      segment_text: "Happiness increased when I started journaling.",
      start_timestamp: "00:07:20.000",
      end_timestamp: "00:07:23.520",
      duration_seconds: 3.52,
      confidence: 0.91,
      visual_description: "Upward trend in happiness metrics correlated with journaling habit markers."
    },
    {
      segment_number: 9,
      segment_text: "The AI found patterns I never noticed.",
      start_timestamp: "00:08:45.000",
      end_timestamp: "00:08:48.160",
      duration_seconds: 3.16,
      confidence: 0.94,
      visual_description: "Complex pattern visualizations and correlations highlighted on the dashboard."
    },
    {
      segment_number: 10,
      segment_text: "My emotional triggers were right there.",
      start_timestamp: "00:09:30.000",
      end_timestamp: "00:09:32.800",
      duration_seconds: 2.8,
      confidence: 0.92,
      visual_description: "Close-up of trigger analysis section showing specific emotional catalysts."
    },
    {
      segment_number: 11,
      segment_text: "Three years of therapy in one dashboard.",
      start_timestamp: "00:10:15.000",
      end_timestamp: "00:10:18.400",
      duration_seconds: 3.4,
      confidence: 0.95,
      visual_description: "Full dashboard view showing comprehensive emotional analysis and insights."
    },
    {
      segment_number: 12,
      segment_text: "Now I know exactly what makes me tick.",
      start_timestamp: "00:11:00.000",
      end_timestamp: "00:11:03.200",
      duration_seconds: 3.2,
      confidence: 0.93,
      visual_description: "Personal insights section highlighting key behavioral patterns and motivations."
    },
    {
      segment_number: 13,
      segment_text: "Try it yourself - link in bio.",
      start_timestamp: "00:11:45.000",
      end_timestamp: "00:11:47.600",
      duration_seconds: 2.6,
      confidence: 0.96,
      visual_description: "Call-to-action screen with the app interface and signup prompt."
    },
    {
      segment_number: 14,
      segment_text: "Your mental health journey, visualized.",
      start_timestamp: "00:12:30.000",
      end_timestamp: "00:12:33.360",
      duration_seconds: 3.36,
      confidence: 0.94,
      visual_description: "Final shot of the complete emotional journey visualization, ending on an inspiring note."
    }
  ]
};

// Mock script content
const mockScriptContent = `I've been in therapy for three years.
Know what my therapist couldn't show me?
Proof I was actually getting better.
Uploaded five years of WhatsApp to this AI.
It mapped my entire emotional evolution.
Depression peaked January 2023.
Anxiety dropped 47% after changing jobs.
Happiness increased when I started journaling.
The AI found patterns I never noticed.
My emotional triggers were right there.
Three years of therapy in one dashboard.
Now I know exactly what makes me tick.
Try it yourself - link in bio.
Your mental health journey, visualized.`;

export default function TestResultsPage() {
  // Mock the fetch responses
  if (typeof window !== 'undefined') {
    // Override fetch for test URLs
    const originalFetch = window.fetch;
    window.fetch = async (url: RequestInfo | URL, ...args: any[]) => {
      const urlString = url.toString();

      if (urlString.includes('/api/download/test/timestamps')) {
        return new Response(JSON.stringify(mockTimestampsData), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        });
      }

      if (urlString.includes('/api/download/test/script')) {
        return new Response(mockScriptContent, {
          status: 200,
          headers: { 'Content-Type': 'text/plain' }
        });
      }

      // For video URL, return a placeholder video URL
      if (urlString.includes('/api/download/test/video')) {
        // You can replace this with an actual test video URL if you have one
        return new Response('', { status: 200 });
      }

      return originalFetch(url, ...args);
    };
  }

  const handleReset = () => {
    console.log("Reset clicked - in real app this would reset the form");
    // Reload the page to simulate reset
    window.location.reload();
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-bold mb-2">Test Results Page</h1>
        <p className="text-muted-foreground">
          This is a test page to preview the results display design.
          Changes to ResultsDisplay component will be reflected here.
        </p>
        <div className="mt-4 space-x-4">
          <button
            onClick={() => window.location.href = '/test-results?state=success'}
            className="px-4 py-2 bg-green-500/20 text-green-500 rounded hover:bg-green-500/30"
          >
            Show Success State
          </button>
          <button
            onClick={() => window.location.href = '/test-results?state=error'}
            className="px-4 py-2 bg-red-500/20 text-red-500 rounded hover:bg-red-500/30"
          >
            Show Error State
          </button>
        </div>
      </div>

      {/* Render the actual ResultsDisplay component */}
      <ResultsDisplay
        results={
          typeof window !== 'undefined' &&
            new URLSearchParams(window.location.search).get('state') === 'error'
            ? { error: "This is a sample error message. Processing failed due to invalid video format or network issues." }
            : mockResults
        }
        processingState={
          typeof window !== 'undefined' &&
            new URLSearchParams(window.location.search).get('state') === 'error'
            ? "error"
            : "complete"
        }
        onReset={handleReset}
      />
    </div>
  );
}
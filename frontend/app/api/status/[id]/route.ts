import { NextRequest, NextResponse } from 'next/server';

const RUNPOD_API_URL = 'https://api.runpod.ai/v2';
const RUNPOD_ENDPOINT_ID = process.env.RUNPOD_ENDPOINT_ID;
const RUNPOD_API_KEY = process.env.RUNPOD_API_KEY;

interface RunPodStatus {
  id: string;
  status: 'IN_QUEUE' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'CANCELLED' | 'TIMED_OUT';
  output?: {
    videoUrl?: string;
    scriptUrl?: string;
    timestampsUrl?: string;
    captionedVideoUrl?: string;
    projectBundleUrl?: string;
    segments?: any[];
    error?: string;
    processingMode?: string;
    capcutSuccess?: boolean;
  };
  error?: string;
  executionTime?: number;
  retries?: number;
}

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id: jobId } = params;

    if (!jobId) {
      return NextResponse.json(
        { error: 'Job ID is required' },
        { status: 400 }
      );
    }

    // Fetch job status from RunPod
    const runpodResponse = await fetch(
      `${RUNPOD_API_URL}/${RUNPOD_ENDPOINT_ID}/status/${jobId}`,
      {
        headers: {
          'Authorization': `Bearer ${RUNPOD_API_KEY}`,
        },
      }
    );

    if (!runpodResponse.ok) {
      const errorData = await runpodResponse.text();
      console.error('RunPod status API error:', errorData);
      return NextResponse.json(
        { error: 'Failed to fetch job status', details: errorData },
        { status: runpodResponse.status }
      );
    }

    const statusData: RunPodStatus = await runpodResponse.json();

    // Map RunPod status to our format
    const response = {
      jobId,
      status: statusData.status,
      progress: getProgressFromStatus(statusData.status),
      executionTime: statusData.executionTime,
      retries: statusData.retries,
      timestamp: new Date().toISOString(),
    };

    // If completed, include output
    if (statusData.status === 'COMPLETED' && statusData.output) {
      return NextResponse.json({
        ...response,
        result: {
          videoUrl: statusData.output.videoUrl,
          scriptUrl: statusData.output.scriptUrl,
          timestampsUrl: statusData.output.timestampsUrl,
          captionedVideoUrl: statusData.output.captionedVideoUrl,
          projectBundleUrl: statusData.output.projectBundleUrl,
          segments: statusData.output.segments,
          processingMode: statusData.output.processingMode,
          capcutSuccess: statusData.output.capcutSuccess,
        },
      });
    }

    // If failed, include error
    if (statusData.status === 'FAILED' || statusData.status === 'TIMED_OUT') {
      return NextResponse.json({
        ...response,
        error: statusData.error || statusData.output?.error || 'Processing failed',
      });
    }

    // Return status for ongoing jobs
    return NextResponse.json(response);

  } catch (error) {
    console.error('Error fetching job status:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

// Helper function to estimate progress based on status
function getProgressFromStatus(status: string): number {
  switch (status) {
    case 'IN_QUEUE':
      return 5;
    case 'IN_PROGRESS':
      return 50;
    case 'COMPLETED':
      return 100;
    case 'FAILED':
    case 'CANCELLED':
    case 'TIMED_OUT':
      return 0;
    default:
      return 0;
  }
}
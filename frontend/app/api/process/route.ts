import { NextRequest, NextResponse } from 'next/server';
import crypto from 'crypto';

const RUNPOD_API_URL = 'https://api.runpod.ai/v2';
const RUNPOD_ENDPOINT_ID = process.env.RUNPOD_ENDPOINT_ID;
const RUNPOD_API_KEY = process.env.RUNPOD_API_KEY;

interface ProcessRequest {
  requestId?: string;
  script: string;
  videoUrls: string[];
  voiceoverUrl?: string;
  duration?: number;
  processingMode?: 'express_builder' | 'quick_create';
  webhookUrl?: string;
}

export async function POST(request: NextRequest) {
  try {
    const body: ProcessRequest = await request.json();

    // Validate required fields
    if (!body.script || !body.videoUrls || body.videoUrls.length === 0) {
      return NextResponse.json(
        { error: 'Missing required fields: script and videoUrls' },
        { status: 400 }
      );
    }

    // Generate request ID if not provided
    const requestId = body.requestId || `req_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`;

    // Prepare RunPod payload
    const runpodPayload = {
      input: {
        type: 'process_video',
        request_id: requestId,
        task_type: body.processingMode || 'express_builder',
        script: body.script,
        videos: body.videoUrls,
        voiceover: body.voiceoverUrl || null,
        duration: body.duration || 30,
        timestamp: new Date().toISOString(),
      },
      // RunPod webhooks require a publicly reachable URL. Only include if set.
      webhook: (body.webhookUrl || process.env.WEBHOOK_URL) || undefined,
      // Enable streamed logs if supported on the endpoint (harmless if ignored).
      stream: true,
    } as const;

    // Call RunPod API
    const runpodResponse = await fetch(
      `${RUNPOD_API_URL}/${RUNPOD_ENDPOINT_ID}/run`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${RUNPOD_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(runpodPayload),
      }
    );

    if (!runpodResponse.ok) {
      const errorData = await runpodResponse.text();
      console.error('RunPod API error:', errorData);
      return NextResponse.json(
        { error: 'Failed to submit job to RunPod', details: errorData },
        { status: runpodResponse.status }
      );
    }

    const runpodData = await runpodResponse.json();

    // Return job information
    return NextResponse.json({
      success: true,
      requestId,
      jobId: runpodData.id,
      status: runpodData.status || 'IN_QUEUE',
      message: 'Job submitted successfully',
      statusUrl: `/api/status/${runpodData.id}`,
    });

  } catch (error) {
    console.error('Error processing request:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

// Health check endpoint
export async function GET(request: NextRequest) {
  try {
    // Check RunPod endpoint health
    const runpodResponse = await fetch(
      `${RUNPOD_API_URL}/${RUNPOD_ENDPOINT_ID}/health`,
      {
        headers: {
          'Authorization': `Bearer ${RUNPOD_API_KEY}`,
        },
      }
    );

    const isHealthy = runpodResponse.ok;
    const runpodStatus = isHealthy ? await runpodResponse.json() : { error: 'RunPod endpoint unreachable' };

    return NextResponse.json({
      status: isHealthy ? 'healthy' : 'unhealthy',
      timestamp: new Date().toISOString(),
      runpod: runpodStatus,
      environment: {
        hasRunpodKey: !!RUNPOD_API_KEY,
        hasEndpointId: !!RUNPOD_ENDPOINT_ID,
        hasDoSpacesKey: !!process.env.DO_SPACES_KEY,
      },
    });
  } catch (error) {
    return NextResponse.json(
      {
        status: 'error',
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}
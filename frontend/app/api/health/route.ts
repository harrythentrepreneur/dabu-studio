import { NextResponse } from 'next/server';

// Ensure this route is always evaluated at runtime, not during build
export const dynamic = 'force-dynamic';

export async function GET() {
    return NextResponse.json({ status: 'ok' });
}

// Optional: support HEAD requests commonly used by uptime checks
export async function HEAD() {
    return new Response(null, { status: 200 });
}

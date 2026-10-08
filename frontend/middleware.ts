import { NextResponse } from 'next/server';

// For demo purposes we bypass all authentication checks. Any route is accessible
// without a Clerk session.  Re-enable the original Clerk middleware once auth is needed.

export function middleware() {
  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!.*\\..*|_next).*)', '/', '/(api|trpc)(.*)'],
};
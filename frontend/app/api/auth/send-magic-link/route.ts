import { NextResponse } from 'next/server';
import { clerkClient } from '@clerk/nextjs/server';
import { Resend } from 'resend';

export async function POST(request: Request) {
  try {
    const { email } = await request.json();

    if (!email) {
      return NextResponse.json({ error: 'Email is required' }, { status: 400 });
    }

    // 1️⃣ Fetch or create user in Clerk
    let userId: string;

    try {
      const existing = await clerkClient.users.getUserList({ emailAddress: [email] });
      if (existing.totalCount > 0) {
        userId = existing.data[0].id;
      } else {
        const newUser = await clerkClient.users.createUser({ emailAddress: [email] });
        userId = newUser.id;
      }
    } catch (err) {
      console.error('[Magic-Link] Clerk user fetch/create failed:', err);
      return NextResponse.json({ error: 'Unable to create user' }, { status: 500 });
    }

    // 2️⃣ Create sign-in token (valid 30 min)
    const tokenResp = await clerkClient.signInTokens.createSignInToken({
      userId,
      expiresInSeconds: 1800,
    });

    const magicLinkUrl = `${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'}/sign-in-token?token=${tokenResp.token}`;

    // 3️⃣ Send e-mail via Resend if configured
    const apiKey = process.env.RESEND_API_KEY;
    if (apiKey) {
      try {
        const resend = new Resend(apiKey);
        await resend.emails.send({
          from: process.env.RESEND_FROM || 'Dabu <no-reply@dabu.ai>',
          to: [email],
          subject: 'Your magic sign-in link',
          html: `<p>Hello,</p><p>Click <a href="${magicLinkUrl}">this secure link</a> to access your account. It expires in 30 minutes.</p><p>If you didn’t request this, please ignore.</p><p>— The Dabu Team</p>`,
        });
      } catch (mailErr) {
        console.error('[Magic-Link] Failed to send email:', mailErr);
        // Do not fail request if email sending fails – frontend can display link in dev
      }
    }

    return NextResponse.json({
      success: true,
      // For non-production we return the link so testers can click directly
      magicLinkUrl: process.env.NODE_ENV !== 'production' ? magicLinkUrl : undefined,
    });

  } catch (error) {
    console.error('[Magic-Link] Unexpected error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
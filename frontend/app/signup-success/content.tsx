'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { useSignUp } from '@clerk/nextjs';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle, Loader2, Mail } from 'lucide-react';
import Link from 'next/link';
import { Alert, AlertDescription } from '@/components/ui/alert';

export default function SignupSuccessContent() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('session_id');
  const emailParam = searchParams.get('email');
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [customerEmail, setCustomerEmail] = useState<string>(emailParam || '');
  const [magicLinkSent, setMagicLinkSent] = useState(false);
  const { signUp } = useSignUp();

  const sendMagicLink = async (email: string) => {
    try {
      // Since the user was created by the webhook, we need to use signIn for magic link
      const response = await fetch('/api/auth/send-magic-link', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      if (response.ok) {
        setMagicLinkSent(true);
        setStatus('success');
      } else {
        setStatus('success'); // Still show success but without magic link
      }
    } catch (error) {
      console.error('Error sending magic link:', error);
      setStatus('success'); // Still show success but without magic link
    }
  };

  useEffect(() => {
    if (!sessionId) {
      setStatus('error');
      return;
    }

    // Verify payment and account creation
    const verifyPayment = async () => {
      try {
        const response = await fetch('/api/stripe/verify-session', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sessionId }),
        });

        const data = await response.json();
        
        if (data.success) {
          setCustomerEmail(data.email || customerEmail);
          // At this point, the Stripe webhook should have created the Clerk user
          // Now we need to send a magic link for the user to sign in
          await sendMagicLink(data.email || customerEmail);
        } else {
          setStatus('error');
        }
      } catch (error) {
        console.error('Error verifying payment:', error);
        setStatus('error');
      }
    };

    // Delay to allow webhook processing
    setTimeout(verifyPayment, 2000);
  }, [sessionId]);

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4" />
            <CardTitle>Setting up your account...</CardTitle>
            <CardDescription>
              Processing your payment and creating your account. This may take a few moments.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle className="text-red-500">Setup Failed</CardTitle>
            <CardDescription>
              There was an issue setting up your account. Please contact support.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <Link href="/">
              <Button variant="outline">Return Home</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          {magicLinkSent ? (
            <Mail className="h-12 w-12 text-blue-500 mx-auto mb-4" />
          ) : (
            <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
          )}
          <CardTitle>Welcome to Dabu!</CardTitle>
          <CardDescription>
            Your subscription is active and your account is ready!
            {customerEmail && (
              <span className="block mt-2 font-medium text-foreground">
                Account: {customerEmail}
              </span>
            )}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {magicLinkSent ? (
            <Alert>
              <Mail className="h-4 w-4" />
              <AlertDescription>
                We've sent a magic sign-in link to your email. Click the link to access your dashboard.
              </AlertDescription>
            </Alert>
          ) : (
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertDescription>
                Your account is ready! Use the magic link sign-in to access your dashboard.
              </AlertDescription>
            </Alert>
          )}
          
          <div className="text-center space-y-2">
            <p className="text-sm text-muted-foreground">
              Start creating AI-powered TikTok video ads with perfect script-to-video timing.
            </p>
          </div>
          
          <div className="flex gap-2">
            <Link href="/sign-in" className="flex-1">
              <Button className="w-full">
                {magicLinkSent ? 'Get New Magic Link' : 'Sign In with Magic Link'}
              </Button>
            </Link>
            <Link href="/" className="flex-1">
              <Button variant="outline" className="w-full">Home</Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
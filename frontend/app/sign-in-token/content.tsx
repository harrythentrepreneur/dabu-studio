'use client';

import { useEffect, useState } from 'react';
import { useClerk } from '@clerk/nextjs';
import { useSearchParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';
import Link from 'next/link';

export default function SignInTokenContent() {
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [error, setError] = useState('');
  
  const clerk = useClerk();
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  useEffect(() => {
    const handleSignInToken = async () => {
      if (!token) {
        setError('No sign-in token provided');
        setStatus('error');
        return;
      }

      try {
        // Use Clerk's signIn.create with ticket strategy
        const signInAttempt = await clerk.client?.signIn.create({
          strategy: 'ticket',
          ticket: token,
        });

        if (signInAttempt?.status === 'complete') {
          await clerk.setActive({ session: signInAttempt.createdSessionId });
          setStatus('success');
          router.push('/express-builder');
        } else {
          setError('Failed to complete sign-in. Please try again.');
          setStatus('error');
        }

      } catch (err: any) {
        console.error('Sign-in token error:', err);
        
        if (err.errors?.[0]?.code === 'token_expired') {
          setError('This sign-in link has expired. Please request a new one.');
        } else if (err.errors?.[0]?.code === 'token_used') {
          setError('This sign-in link has already been used. Please request a new one.');
        } else {
          setError('Failed to sign in. Please try again or contact support.');
        }
        
        setStatus('error');
      }
    };

    // Small delay to ensure hook is ready
    if (clerk.loaded) {
      handleSignInToken();
    }
  }, [token, clerk, router]);

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4" />
            <CardTitle>Signing You In</CardTitle>
            <CardDescription>
              Please wait while we authenticate your sign-in link...
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  if (status === 'success') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
            <CardTitle>Welcome Back!</CardTitle>
            <CardDescription>
              You're being redirected to your dashboard...
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-sm text-muted-foreground mb-4">
              If you're not redirected automatically, click below.
            </p>
            <Link href="/express-builder">
              <Button className="w-full">Go to Dashboard</Button>
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
          <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <CardTitle>Sign-In Failed</CardTitle>
          <CardDescription>
            We couldn't sign you in with this link.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert variant="destructive">
            <XCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
          
          <div className="flex gap-2">
            <Link href="/sign-in" className="flex-1">
              <Button className="w-full">
                Get New Magic Link
              </Button>
            </Link>
            <Link href="/" className="flex-1">
              <Button variant="outline" className="w-full">
                Home
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
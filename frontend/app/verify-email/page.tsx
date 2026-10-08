// Full rewrite of Verify Email page
'use client';
import { useEffect, useState } from 'react';
import { useClerk, useSignIn, useSignUp } from '@clerk/nextjs';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';

export default function VerifyEmailPage() {
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [error, setError] = useState<string>('');

  const clerk = useClerk();
  const { handleEmailLinkVerification } = clerk;
  const { signIn, createdSessionId: signInSessionId, status: signInStatus, setActive: setSignInActive } = useSignIn();
  const { signUp, createdSessionId: signUpSessionId, status: signUpStatus, setActive: setSignUpActive } = useSignUp();
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const verify = async () => {
      try {
        await handleEmailLinkVerification({
          redirectUrl: window.location.href,
          redirectUrlComplete: '/express-builder',
        });

        if (signInStatus === 'complete' && signInSessionId) {
          await setSignInActive({ session: signInSessionId });
          setStatus('success');
          router.push('/express-builder');
          return;
        }
        if (signUpStatus === 'complete' && signUpSessionId) {
          await setSignUpActive({ session: signUpSessionId });
          setStatus('success');
          router.push('/express-builder');
          return;
        }
        setError('Unable to sign in. Please try again.');
        setStatus('error');
      } catch (err: any) {
        console.error('Email verification error:', err);
        if (err.errors?.[0]?.code === 'verification_link_expired') {
          setError('This magic link has expired. Please request a new one.');
        } else if (err.errors?.[0]?.code === 'verification_link_used') {
          setError('This magic link has already been used. Please request a new one.');
        } else {
          setError('Failed to verify email. Please try again or contact support.');
        }
        setStatus('error');
      }
    };
    verify();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [handleEmailLinkVerification, signInStatus, signInSessionId, signUpStatus, signUpSessionId]);

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4" />
            <CardTitle>Verifying Your Email</CardTitle>
            <CardDescription>Please wait while we verify your magic link...</CardDescription>
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
            <CardTitle>Login Successful!</CardTitle>
            <CardDescription>Redirecting to your workspace...</CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <CardTitle>Verification Failed</CardTitle>
          <CardDescription>We couldn't verify your email address.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert variant="destructive">
            <XCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
          <div className="flex gap-2">
            <Link href="/sign-in" className="flex-1"><Button variant="outline" className="w-full">Try Again</Button></Link>
            <Link href="/" className="flex-1"><Button variant="outline" className="w-full">Home</Button></Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
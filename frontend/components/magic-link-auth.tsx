'use client';

import { useState } from 'react';
import { useSignIn, useSignUp, useClerk } from '@clerk/nextjs';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Mail, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { isClerkAPIResponseError } from '@clerk/nextjs/errors';

export default function MagicLinkAuth() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const [error, setError] = useState('');
  const [isExistingUser, setIsExistingUser] = useState<boolean | null>(null);

  const { signIn, setActive } = useSignIn();
  const { signUp } = useSignUp();
  const clerk = useClerk();

  const validateEmail = (email: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleMagicLinkFlow = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email.trim()) {
      setError('Email is required');
      return;
    }
    
    if (!validateEmail(email)) {
      setError('Please enter a valid email address');
      return;
    }
    
    setError('');
    setLoading(true);

    try {
      // First try to sign up (for new users)
      if (signUp) {
        const signUpResponse = await signUp.create({
          emailAddress: email,
        });

        // Start the magic link flow for sign-up
        await signUp.prepareEmailAddressVerification({
          strategy: 'email_link',
          redirectUrl: `${window.location.origin}/verify-email`,
        });

        setIsExistingUser(false);
        setEmailSent(true);
        setLoading(false);
      }
    } catch (err) {
      console.error('Sign-up error:', err);
      
      // If user already exists, try sign-in
      if (isClerkAPIResponseError(err) && err.errors[0]?.code === 'form_identifier_exists') {
        try {
          if (signIn) {
            const signInResponse = await signIn.create({
              identifier: email,
            });

            // Start the magic link flow for sign-in
            const firstFactor = signInResponse.supportedFirstFactors?.[0];
            if (firstFactor && 'emailAddressId' in firstFactor) {
              await signIn.prepareFirstFactor({
                strategy: 'email_link',
                emailAddressId: firstFactor.emailAddressId,
                redirectUrl: `${window.location.origin}/verify-email`,
              });
            }

            setIsExistingUser(true);
            setEmailSent(true);
            setLoading(false);
          }
        } catch (signInErr) {
          console.error('Sign-in error:', signInErr);
          setError('Failed to send magic link. Please try again.');
          setLoading(false);
        }
      } else {
        setError('Failed to send magic link. Please try again.');
        setLoading(false);
      }
    }
  };

  const handleResendEmail = async () => {
    setLoading(true);
    try {
      if (isExistingUser && signIn) {
        const firstFactor = signIn.supportedFirstFactors?.[0];
        if (firstFactor && 'emailAddressId' in firstFactor) {
          await signIn.prepareFirstFactor({
            strategy: 'email_link',
            emailAddressId: firstFactor.emailAddressId,
            redirectUrl: `${window.location.origin}/verify-email`,
          });
        }
      } else if (!isExistingUser && signUp) {
        await signUp.prepareEmailAddressVerification({
          strategy: 'email_link',
          redirectUrl: `${window.location.origin}/verify-email`,
        });
      }
    } catch (err) {
      console.error('Resend error:', err);
      setError('Failed to resend email. Please try again.');
    }
    setLoading(false);
  };

  if (emailSent) {
    return (
      <Card className="w-full max-w-md mx-auto">
        <CardHeader className="text-center">
          <div className="mx-auto w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-4">
            <Mail className="h-6 w-6 text-green-600" />
          </div>
          <CardTitle>Check Your Email</CardTitle>
          <CardDescription>
            We've sent a magic link to <strong>{email}</strong>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert>
            <CheckCircle className="h-4 w-4" />
            <AlertDescription>
              {isExistingUser 
                ? "Click the link in your email to sign in to your account."
                : "Click the link in your email to complete your account setup."
              }
            </AlertDescription>
          </Alert>
          
          <div className="text-center text-sm text-muted-foreground">
            <p>Didn't receive the email? Check your spam folder or</p>
            <Button
              variant="link"
              onClick={handleResendEmail}
              disabled={loading}
              className="p-0 h-auto text-primary"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                  Sending...
                </>
              ) : (
                'resend the magic link'
              )}
            </Button>
          </div>

          <Button
            variant="outline"
            onClick={() => {
              setEmailSent(false);
              setEmail('');
              setIsExistingUser(null);
            }}
            className="w-full"
          >
            Use Different Email
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="text-center">
        <CardTitle>Welcome to Dabu</CardTitle>
        <CardDescription>
          Enter your email to sign in or create an account
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleMagicLinkFlow} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email Address</Label>
            <Input
              id="email"
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Button 
            type="submit" 
            className="w-full" 
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Sending Magic Link...
              </>
            ) : (
              <>
                <Mail className="mr-2 h-4 w-4" />
                Continue with Magic Link
              </>
            )}
          </Button>
        </form>

        <div className="mt-4 text-center text-xs text-muted-foreground">
          <p>
            By continuing, you agree to our{' '}
            <a href="/terms" className="underline hover:text-foreground">
              Terms of Service
            </a>{' '}
            and{' '}
            <a href="/privacy" className="underline hover:text-foreground">
              Privacy Policy
            </a>
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
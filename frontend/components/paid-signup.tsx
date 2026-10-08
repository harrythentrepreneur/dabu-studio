'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Check, Loader2 } from 'lucide-react';
import { loadStripe } from '@stripe/stripe-js';

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!);

const plan = {
  name: 'Pro',
  price: '$29',
  period: '/month',
  description: 'Start creating AI-powered video ads',
  features: [
    'Unlimited video generations',
    'Premium AI processing with Gemini 2.5 Pro',
    'Perfect script-to-video timing',
    'Voiceover synchronization',
    'CapCut automation integration',
    'Priority support',
    'Advanced export options'
  ],
  planType: 'monthly',
};

export default function PaidSignup() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [emailError, setEmailError] = useState('');

  const validateEmail = (email: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email.trim()) {
      setEmailError('Email is required');
      return;
    }
    
    if (!validateEmail(email)) {
      setEmailError('Please enter a valid email address');
      return;
    }
    
    setEmailError('');
    setLoading(true);

    try {
      const response = await fetch('/api/stripe/signup-checkout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          plan: plan.planType,
          email: email.trim(),
          successUrl: `${window.location.origin}/signup-success?session_id={CHECKOUT_SESSION_ID}&email=${encodeURIComponent(email.trim())}`,
          cancelUrl: `${window.location.origin}/?canceled=true`,
        }),
      });

      const { sessionId, url } = await response.json();

      if (url) {
        // Redirect to Stripe hosted checkout
        window.location.href = url;
      } else {
        // Fallback to programmatic redirect
        const stripe = await stripePromise;
        if (stripe && sessionId) {
          const { error } = await stripe.redirectToCheckout({ sessionId });
          if (error) {
            console.error('Stripe error:', error);
            setLoading(false);
          }
        }
      }
    } catch (error) {
      console.error('Error creating checkout session:', error);
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <Card className="relative border-primary">
        <Badge className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-primary">
          Start Your Journey
        </Badge>
        
        <CardHeader className="text-center pt-6">
          <CardTitle className="text-2xl font-semibold">{plan.name}</CardTitle>
          <CardDescription>{plan.description}</CardDescription>
          <div className="mt-4">
            <span className="text-4xl font-extrabold text-foreground">
              {plan.price}
            </span>
            <span className="text-base font-medium text-muted-foreground">
              {plan.period}
            </span>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-6">
          <ul className="space-y-3">
            {plan.features.map((feature) => (
              <li key={feature} className="flex items-start">
                <Check className="flex-shrink-0 h-5 w-5 text-green-500 mr-2 mt-0.5" />
                <span className="text-sm text-muted-foreground">{feature}</span>
              </li>
            ))}
          </ul>
          
          <form onSubmit={handleSignup} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email Address</Label>
              <Input
                id="email"
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={emailError ? 'border-red-500' : ''}
                disabled={loading}
                required
              />
              {emailError && (
                <p className="text-sm text-red-500">{emailError}</p>
              )}
            </div>
            
            <Button 
              type="submit" 
              className="w-full" 
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                'Subscribe & Create Account'
              )}
            </Button>
          </form>
          
          <div className="text-center">
            <p className="text-xs text-muted-foreground">
              By subscribing, you agree to our terms of service and privacy policy.
              Your account will be created after payment confirmation.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
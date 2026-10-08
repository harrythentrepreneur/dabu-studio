'use client';

import { useState } from 'react';
import { useAuth } from '@clerk/nextjs';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Check } from 'lucide-react';
import { loadStripe } from '@stripe/stripe-js';

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!);

const plans = [
  {
    name: 'Monthly',
    price: '$29',
    period: '/month',
    description: 'Perfect for trying out',
    features: [
      'Unlimited video generations',
      'Premium AI processing with Gemini 2.5 Pro',
      'Perfect script-to-video timing',
      'Voiceover synchronization',
      'Priority support'
    ],
    planType: 'monthly',
    popular: false,
  },
  {
    name: 'Yearly',
    price: '$290',
    period: '/year',
    originalPrice: '$348',
    description: 'Best value - Save $58/year',
    features: [
      'Everything in Monthly',
      'Save $58 per year',
      'Priority feature requests',
      'Advanced export options',
      'CapCut automation integration'
    ],
    planType: 'yearly',
    popular: true,
  },
  {
    name: 'Lifetime',
    price: '$499',
    period: 'one-time',
    description: 'Pay once, use forever',
    features: [
      'Everything in Yearly',
      'Lifetime access',
      'All future updates',
      'VIP support',
      'Early access to new features'
    ],
    planType: 'lifetime',
    popular: false,
  },
];

export default function StripePricing() {
  const { isSignedIn, userId } = useAuth();
  const [loading, setLoading] = useState<string | null>(null);

  const handleSubscribe = async (planType: string) => {
    if (!isSignedIn) {
      window.location.href = '/sign-in';
      return;
    }

    setLoading(planType);

    try {
      const response = await fetch('/api/stripe/signup-checkout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          plan: planType,
          successUrl: `${window.location.origin}/signup-success?session_id={CHECKOUT_SESSION_ID}`,
          cancelUrl: `${window.location.origin}/?canceled=true`,
        }),
      });

      const { sessionId, url } = await response.json();

      if (url) {
        window.location.href = url;
      } else {
        const stripe = await stripePromise;
        if (stripe && sessionId) {
          const { error } = await stripe.redirectToCheckout({ sessionId });
          if (error) {
            console.error('Stripe error:', error);
          }
        }
      }
    } catch (error) {
      console.error('Error creating checkout session:', error);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-3xl font-extrabold text-foreground sm:text-4xl">
            Simple, transparent pricing
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Choose the plan that's right for you
          </p>
        </div>
        
        <div className="mt-12 space-y-4 sm:mt-16 sm:space-y-0 sm:grid sm:grid-cols-1 md:grid-cols-3 sm:gap-6 lg:max-w-4xl lg:mx-auto xl:max-w-none xl:mx-0">
          {plans.map((plan) => (
            <Card key={plan.name} className={`relative ${plan.popular ? 'border-primary' : ''}`}>
              {plan.popular && (
                <Badge className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-primary">
                  Most Popular
                </Badge>
              )}
              
              <CardHeader>
                <CardTitle className="text-2xl font-semibold">{plan.name}</CardTitle>
                <CardDescription>{plan.description}</CardDescription>
                <div className="mt-4">
                  <span className="text-4xl font-extrabold text-foreground">
                    {plan.price}
                  </span>
                  {plan.period && (
                    <span className="text-base font-medium text-muted-foreground">
                      {plan.period}
                    </span>
                  )}
                  {plan.originalPrice && (
                    <div className="mt-1">
                      <span className="text-sm text-muted-foreground line-through">
                        {plan.originalPrice}
                      </span>
                    </div>
                  )}
                </div>
              </CardHeader>
              
              <CardContent>
                <ul className="space-y-3">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start">
                      <Check className="flex-shrink-0 h-5 w-5 text-green-500 mr-2 mt-0.5" />
                      <span className="text-sm text-muted-foreground">{feature}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
              
              <CardFooter>
                <Button
                  className="w-full"
                  onClick={() => handleSubscribe(plan.planType)}
                  disabled={loading === plan.planType}
                  variant={plan.popular ? 'default' : 'outline'}
                >
                  {loading === plan.planType ? 'Loading...' : 'Get Started'}
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
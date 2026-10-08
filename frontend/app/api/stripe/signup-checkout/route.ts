import { NextResponse } from 'next/server';
import Stripe from 'stripe';

// Force dynamic execution to prevent build-time errors
export const dynamic = 'force-dynamic';

// Lazy initialize Stripe to prevent build-time execution
let stripe: Stripe | null = null;

function getStripe(): Stripe {
  if (!stripe) {
    stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
      apiVersion: '2025-07-30.basil',
    });
  }
  return stripe;
}

export async function POST(request: Request) {
  try {
    const { plan = 'monthly', email, successUrl, cancelUrl } = await request.json();

    // Initialize Stripe only when the route is actually called
    const stripeInstance = getStripe();

    // Define pricing based on plan
    const pricing = {
      monthly: {
        amount: 2900, // $29.00
        interval: 'month' as const,
        name: 'Dabu Pro Monthly',
        description: 'TikTok video ad automation - Monthly subscription'
      },
      yearly: {
        amount: 29000, // $290.00 (save $58/year)
        interval: 'year' as const,
        name: 'Dabu Pro Yearly',
        description: 'TikTok video ad automation - Yearly subscription'
      },
      lifetime: {
        amount: 49900, // $499.00
        interval: null,
        name: 'Dabu Pro Lifetime',
        description: 'TikTok video ad automation - One-time payment'
      }
    };

    const selectedPlan = pricing[plan as keyof typeof pricing] || pricing.monthly;

    const sessionConfig: any = {
      payment_method_types: ['card'],
      billing_address_collection: 'required',
      customer_email: email || undefined,
      line_items: [
        {
          price_data: {
            currency: 'usd',
            product_data: {
              name: selectedPlan.name,
              description: selectedPlan.description,
            },
            unit_amount: selectedPlan.amount,
            ...(selectedPlan.interval && {
              recurring: {
                interval: selectedPlan.interval,
              },
            }),
          },
          quantity: 1,
        },
      ],
      mode: selectedPlan.interval ? 'subscription' : 'payment',
      success_url: successUrl || `${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3001'}/signup-success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: cancelUrl || `${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3001'}/?canceled=true`,
      metadata: {
        signup_flow: 'true',
        email: email || '',
        plan: plan || 'monthly',
      },
      allow_promotion_codes: true,
      consent_collection: {
        terms_of_service: 'required',
      },
    };

    // Only add customer_creation for payment mode
    if (!selectedPlan.interval) {
      sessionConfig.customer_creation = 'always';
    }

    const session = await stripeInstance.checkout.sessions.create(sessionConfig);

    return NextResponse.json({ sessionId: session.id, url: session.url });
  } catch (error) {
    console.error('Error creating signup checkout session:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
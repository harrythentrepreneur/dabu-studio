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
    const { sessionId } = await request.json();

    if (!sessionId) {
      return NextResponse.json(
        { success: false, error: 'Session ID required' },
        { status: 400 }
      );
    }

    const stripeInstance = getStripe();

    // Retrieve the session
    const session = await stripeInstance.checkout.sessions.retrieve(sessionId);

    if (session.payment_status === 'paid') {
      // Get customer details
      const customer = await stripeInstance.customers.retrieve(session.customer as string);
      const customerData = customer as Stripe.Customer;

      return NextResponse.json({
        success: true,
        email: customerData.email,
        name: customerData.name,
        customerId: customerData.id,
      });
    } else {
      return NextResponse.json({
        success: false,
        error: 'Payment not completed',
      });
    }
  } catch (error) {
    console.error('Error verifying session:', error);
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}
import { NextResponse } from 'next/server';
import { headers } from 'next/headers';
import Stripe from 'stripe';
import { clerkClient } from '@clerk/nextjs/server';

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

const endpointSecret = process.env.STRIPE_WEBHOOK_SECRET!;

export async function POST(request: Request) {
  const body = await request.text();
  const signature = (await headers()).get('stripe-signature');

  if (!signature) {
    return NextResponse.json(
      { error: 'No signature found' },
      { status: 400 }
    );
  }

  const stripeInstance = getStripe();

  let event: Stripe.Event;

  try {
    event = stripeInstance.webhooks.constructEvent(body, signature, endpointSecret);
  } catch (err) {
    console.error('Webhook signature verification failed:', err);
    return NextResponse.json(
      { error: 'Invalid signature' },
      { status: 400 }
    );
  }

  try {
    switch (event.type) {
      case 'checkout.session.completed': {
        const session = event.data.object as Stripe.Checkout.Session;
        const userId = session.metadata?.userId;
        const isSignupFlow = session.metadata?.signup_flow === 'true';

        if (isSignupFlow) {
          try {
            const customer = await stripeInstance.customers.retrieve(session.customer as string);
            const customerData = customer as Stripe.Customer;

            if (customerData.email) {
              console.log(`Creating Clerk user for email: ${customerData.email}`);

              const clerk = await clerkClient();
              const clerkUser = await clerk.users.createUser({
                emailAddress: [customerData.email],
                firstName: customerData.name?.split(' ')[0] || '',
                lastName: customerData.name?.split(' ').slice(1).join(' ') || '',
                skipPasswordRequirement: true,
                skipPasswordChecks: true,
              });

              await stripeInstance.customers.update(session.customer as string, {
                metadata: {
                  clerk_user_id: clerkUser.id,
                },
              });

              console.log(`Clerk user created: ${clerkUser.id} for email: ${customerData.email}`);
            }
          } catch (error) {
            console.error('Error creating Clerk user:', error);
          }
        } else if (userId) {
          console.log(`Payment successful for existing user: ${userId}`);
        }
        break;
      }

      case 'customer.subscription.created':
      case 'customer.subscription.updated': {
        const subscription = event.data.object as Stripe.Subscription;
        console.log(`Subscription ${event.type}:`, subscription.id);
        break;
      }

      case 'customer.subscription.deleted': {
        const subscription = event.data.object as Stripe.Subscription;
        console.log(`Subscription deleted:`, subscription.id);
        break;
      }

      default:
        console.log(`Unhandled event type: ${event.type}`);
    }

    return NextResponse.json({ received: true });
  } catch (error) {
    console.error('Error handling webhook:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
'use client';

import { Button } from "@/components/ui/button";
import PaidSignup from "@/components/paid-signup";
import UserButton from "@/components/user-button";
import Link from "next/link";
import { useAuth } from '@clerk/nextjs';

export default function Home() {
  const { isSignedIn } = useAuth();
  return (
    <div className="min-h-screen bg-background">
      <nav className="border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link href="/" className="text-2xl font-bold text-foreground">
                Dabu
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/dashboard">
                <Button variant="ghost">Dashboard</Button>
              </Link>
              <UserButton />
            </div>
          </div>
        </div>
      </nav>

      <main>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center">
            <h1 className="text-4xl font-extrabold text-foreground sm:text-6xl">
              AI Video Ad Creator
            </h1>
            <p className="mt-6 text-xl text-muted-foreground max-w-3xl mx-auto">
              Transform your scripts into perfectly synced TikTok ads in seconds. 
              AI-powered video editing that matches your script to the perfect moments 
              with frame-perfect timing.
            </p>
            <div className="mt-10 flex justify-center space-x-4">
              {isSignedIn ? (
                <Link href="/express-builder">
                  <Button size="lg" className="px-8 py-3 text-lg">
                    Go to Dashboard
                  </Button>
                </Link>
              ) : (
                <>
                  <a href="#signup">
                    <Button size="lg" className="px-8 py-3 text-lg">
                      Get Started
                    </Button>
                  </a>
                  <Link href="/sign-in">
                    <Button variant="outline" size="lg" className="px-8 py-3 text-lg">
                      Sign In
                    </Button>
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>

        {!isSignedIn && (
          <section id="signup" className="py-16">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="text-center mb-12">
                <h2 className="text-3xl font-extrabold text-foreground sm:text-4xl">
                  Start Creating Today
                </h2>
                <p className="mt-4 text-lg text-muted-foreground">
                  Subscribe and get instant access to AI-powered video creation
                </p>
              </div>
              <div className="flex justify-center">
                <PaidSignup />
              </div>
              <div className="mt-8 text-center">
                <p className="text-sm text-muted-foreground">
                  Already have an account?{" "}
                  <Link href="/sign-in" className="text-primary hover:underline">
                    Sign in here
                  </Link>
                </p>
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
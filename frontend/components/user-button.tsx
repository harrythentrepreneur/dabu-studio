'use client';

import { UserButton as ClerkUserButton, SignInButton, useAuth } from '@clerk/nextjs';
import { Button } from '@/components/ui/button';

export default function UserButton() {
  const { isSignedIn } = useAuth();

  if (isSignedIn) {
    return <ClerkUserButton afterSignOutUrl="/" />;
  }

  return (
    <SignInButton mode="redirect">
      <Button variant="outline" size="sm">
        Sign In
      </Button>
    </SignInButton>
  );
}
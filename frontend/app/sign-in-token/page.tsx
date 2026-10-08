import { Suspense } from 'react';

export const dynamic = 'force-dynamic';
import SignInTokenContent from './content';
import { Loader2 } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';

function LoadingFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4" />
          <CardTitle>Loading</CardTitle>
          <CardDescription>
            Please wait while we load the page...
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}

export default function SignInTokenPage() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <SignInTokenContent />
    </Suspense>
  );
}
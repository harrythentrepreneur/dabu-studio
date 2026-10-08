import { Suspense } from 'react';
import SignupSuccessContent from './content';

export const dynamic = 'force-dynamic';

export default function SignupSuccessPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <SignupSuccessContent />
    </Suspense>
  );
}
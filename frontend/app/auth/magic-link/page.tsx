'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import { Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

export default function MagicLinkVerifyPage() {
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [error, setError] = useState('');
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const token = searchParams.get('token');
    
    if (!token) {
      setStatus('error');
      setError('Invalid or missing magic link token.');
      return;
    }

    const verifyToken = async () => {
      try {
        await api.auth.verifyMagicLink(token);
        setStatus('success');
        // Redirect to dashboard after short delay
        setTimeout(() => {
          router.push('/dashboard');
        }, 1500);
      } catch (err: any) {
        setStatus('error');
        const msg = err.response?.data?.detail || 'Failed to verify magic link. It may have expired.';
        setError(msg);
      }
    };

    verifyToken();
  }, [searchParams, router]);

  return (
    <div className="min-h-screen flex items-center justify-center p-8 bg-background">
      <div className="w-full max-w-sm space-y-6 text-center">
        {status === 'loading' && (
          <>
            <div className="w-16 h-16 mx-auto rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center">
              <Loader2 className="w-8 h-8 text-primary animate-spin" />
            </div>
            <div>
              <h2 className="text-2xl font-semibold text-foreground">Verifying your magic link</h2>
              <p className="mt-2 text-muted-foreground">
                Please wait while we sign you in...
              </p>
            </div>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="w-16 h-16 mx-auto rounded-full bg-green-500/10 border border-green-500/20 flex items-center justify-center">
              <CheckCircle2 className="w-8 h-8 text-green-500" />
            </div>
            <div>
              <h2 className="text-2xl font-semibold text-foreground">Welcome back!</h2>
              <p className="mt-2 text-muted-foreground">
                You've been signed in successfully. Redirecting to dashboard...
              </p>
            </div>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="w-16 h-16 mx-auto rounded-full bg-destructive/10 border border-destructive/20 flex items-center justify-center">
              <XCircle className="w-8 h-8 text-destructive" />
            </div>
            <div>
              <h2 className="text-2xl font-semibold text-foreground">Link invalid</h2>
              <p className="mt-2 text-muted-foreground">
                {error}
              </p>
            </div>
            <Button asChild className="mt-4">
              <Link href="/login">
                Back to login
              </Link>
            </Button>
          </>
        )}
      </div>
    </div>
  );
}

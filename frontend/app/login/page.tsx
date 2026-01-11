'use client';

import { Suspense, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2, CheckCircle2, Zap, Shield, ArrowRight, Mail, KeyRound } from 'lucide-react';
import Link from 'next/link';

const features = [
  { icon: CheckCircle2, text: '50M+ annotations processed' },
  { icon: Zap, text: '10x faster than manual labeling' },
  { icon: Shield, text: 'Enterprise-grade security' },
];

type AuthMode = 'password' | 'magic-link';

function LoginContent() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [authMode, setAuthMode] = useState<AuthMode>('password');
  const [magicLinkSent, setMagicLinkSent] = useState(false);
  const { login } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      await login(email, password);
      // Redirect to original destination or dashboard
      const redirect = searchParams.get('redirect') || '/dashboard';
      router.push(redirect);
    } catch (err: any) {
      console.error('Login error:', err);
      let msg = 'Invalid credentials or server error.';
      if (err.response?.data?.detail) {
        msg = err.response.data.detail;
      } else if (err.message) {
        msg = err.message;
      }
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleMagicLinkRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      await api.auth.requestMagicLink(email);
      setMagicLinkSent(true);
    } catch (err: any) {
      console.error('Magic link error:', err);
      let msg = 'Failed to send magic link.';
      if (err.response?.data?.detail) {
        msg = err.response.data.detail;
      }
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  if (magicLinkSent) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8 bg-background">
        <div className="w-full max-w-sm space-y-6 text-center">
          <div className="w-16 h-16 mx-auto rounded-full bg-green-500/10 border border-green-500/20 flex items-center justify-center">
            <Mail className="w-8 h-8 text-green-500" />
          </div>
          <div>
            <h2 className="text-2xl font-semibold text-foreground">Check your email</h2>
            <p className="mt-2 text-muted-foreground">
              We sent a magic link to <strong>{email}</strong>. Click the link in the email to sign in.
            </p>
          </div>
          <p className="text-sm text-muted-foreground">
            Didn't receive the email?{' '}
            <button 
              onClick={() => setMagicLinkSent(false)} 
              className="text-primary hover:underline"
            >
              Try again
            </button>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex">
      {/* Left Panel - Branding */}
      <div className="hidden lg:flex lg:w-1/2 relative bg-gradient-to-br from-violet-950 via-[#0c0a1a] to-[#0a0e1a] overflow-hidden">
        {/* Grid pattern overlay */}
        <div 
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          }}
        />
        
        {/* Gradient orb */}
        <div className="absolute -top-40 -left-40 w-80 h-80 bg-violet-500/30 rounded-full blur-[120px]" />
        <div className="absolute -bottom-40 -right-40 w-80 h-80 bg-purple-500/20 rounded-full blur-[120px]" />
        
        <div className="relative z-10 flex flex-col justify-between p-12 w-full">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg shadow-violet-500/30">
              <span className="text-white font-bold text-lg">C</span>
            </div>
            <div>
              <span className="font-semibold text-white">CaliperAI</span>
              <span className="text-violet-400 text-sm ml-2">AutoAnn</span>
            </div>
          </div>
          
          {/* Main content */}
          <div className="space-y-8">
            <div>
              <h1 className="text-4xl font-bold text-white leading-tight">
                Enterprise Auto-Annotation
                <br />
                <span className="text-gradient bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">
                  at Scale
                </span>
              </h1>
              <p className="mt-4 text-lg text-zinc-400 max-w-md">
                Run production-grade 2D and 3D annotation pipelines. 
                Upload your data, select a model, and download results.
              </p>
            </div>
            
            {/* Features */}
            <div className="space-y-4">
              {features.map((feature, i) => (
                <div key={i} className="flex items-center gap-3 text-zinc-300">
                  <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-violet-500/10 border border-violet-500/20 flex items-center justify-center">
                    <feature.icon className="w-4 h-4 text-violet-400" />
                  </div>
                  <span className="text-sm">{feature.text}</span>
                </div>
              ))}
            </div>
          </div>
          
          {/* Footer */}
          <p className="text-sm text-zinc-600">
            © 2026 Caliper AI Inc. All rights reserved.
          </p>
        </div>
      </div>
      
      {/* Right Panel - Login Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-background">
        <div className="w-full max-w-sm space-y-8">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center justify-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
              <span className="text-white font-bold text-lg">C</span>
            </div>
            <span className="font-semibold text-lg">CaliperAI AutoAnn</span>
          </div>
          
          {/* Header */}
          <div>
            <h2 className="text-2xl font-semibold text-foreground">Welcome back</h2>
            <p className="mt-2 text-muted-foreground">
              Sign in to your account to continue
            </p>
          </div>

          {/* Auth mode tabs */}
          <div className="flex rounded-lg bg-secondary p-1">
            <button
              type="button"
              onClick={() => setAuthMode('password')}
              className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 text-sm font-medium rounded-md transition-colors ${
                authMode === 'password'
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <KeyRound className="w-4 h-4" />
              Password
            </button>
            <button
              type="button"
              onClick={() => setAuthMode('magic-link')}
              className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 text-sm font-medium rounded-md transition-colors ${
                authMode === 'magic-link'
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <Mail className="w-4 h-4" />
              Magic Link
            </button>
          </div>
          
          {/* Password Login Form */}
          {authMode === 'password' && (
            <form onSubmit={handlePasswordLogin} className="space-y-5">
              <div className="space-y-2">
                <label htmlFor="email" className="text-sm font-medium text-foreground">
                  Email address
                </label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                />
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label htmlFor="password" className="text-sm font-medium text-foreground">
                    Password
                  </label>
                  <Link href="/forgot-password" className="text-xs text-primary hover:text-primary/80 transition-colors">
                    Forgot password?
                  </Link>
                </div>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                />
              </div>

              {error && (
                <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm">
                  {error}
                </div>
              )}

              <Button type="submit" className="w-full h-11" disabled={loading}>
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    Sign in
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </>
                )}
              </Button>
            </form>
          )}

          {/* Magic Link Form */}
          {authMode === 'magic-link' && (
            <form onSubmit={handleMagicLinkRequest} className="space-y-5">
              <div className="space-y-2">
                <label htmlFor="email-magic" className="text-sm font-medium text-foreground">
                  Email address
                </label>
                <Input
                  id="email-magic"
                  type="email"
                  placeholder="you@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                />
                <p className="text-xs text-muted-foreground">
                  We'll send you a secure link to sign in without a password.
                </p>
              </div>

              {error && (
                <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm">
                  {error}
                </div>
              )}

              <Button type="submit" className="w-full h-11" disabled={loading}>
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    Send magic link
                    <Mail className="ml-2 h-4 w-4" />
                  </>
                )}
              </Button>
            </form>
          )}
          
          {/* Demo credentials */}
          <div className="pt-4 border-t border-border">
            <p className="text-xs text-muted-foreground mb-2">Demo credentials:</p>
            <div className="flex gap-2">
              <code className="flex-1 px-3 py-2 rounded-lg bg-secondary text-xs font-mono text-muted-foreground">
                admin@example.com
              </code>
              <code className="px-3 py-2 rounded-lg bg-secondary text-xs font-mono text-muted-foreground">
                password
              </code>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function LoadingFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center p-8 bg-background">
      <div className="text-center space-y-4">
        <Loader2 className="w-8 h-8 text-primary animate-spin mx-auto" />
        <p className="text-muted-foreground">Loading...</p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <LoginContent />
    </Suspense>
  );
}

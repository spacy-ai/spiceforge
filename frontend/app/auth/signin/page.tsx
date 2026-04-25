'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ChevronLeft } from 'lucide-react';
import { useTheme } from 'next-themes';
import { useRouter } from 'next/navigation';

export default function SignIn() {
  const { theme, setTheme } = useTheme();
  const previousTheme = useRef<string | undefined>(undefined);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const router = useRouter();

  useEffect(() => {
    previousTheme.current = theme;
    setTheme('light');

    return () => {
      if (previousTheme.current) {
        setTheme(previousTheme.current);
      } else {
        setTheme('system');
      }
    };
  }, [setTheme, theme]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const res = await fetch('/api/auth/signin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.message || 'Login failed');
      }
      router.push('/circuit?circuitid=3');
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div className="bg-background text-foreground relative flex min-h-screen flex-col items-center justify-center px-6">
      {/* Back Button */}
      <Link
        href="/dashboard"
        className="text-muted-foreground hover:text-foreground absolute top-6 left-6 flex items-center gap-2 transition-colors"
      >
        <ChevronLeft className="h-5 w-5" />
        <span className="text-sm">Back</span>
      </Link>

      <div className="mb-12 text-center">
        <h1 className="text-3xl font-bold">Welcome Back</h1>
        <p className="text-muted-foreground mt-2">Sign in to your account to continue</p>
      </div>

      {/* Sign In Form */}
      <div className="w-full max-w-md">
        <div className="border-border bg-card rounded-lg border p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Email Input */}
            <div className="space-y-2">
              <label htmlFor="email" className="block text-sm font-medium">
                Email
              </label>
              <input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="border-border bg-background w-full rounded-lg border px-4 py-2 transition-colors focus:border-transparent focus:ring-2 focus:ring-orange-600 focus:outline-none"
                required
              />
            </div>

            {/* Password Input */}
            <div className="space-y-2">
              <label htmlFor="password" className="block text-sm font-medium">
                Password
              </label>
              <input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="border-border bg-background w-full rounded-lg border px-4 py-2 transition-colors focus:border-transparent focus:ring-2 focus:ring-orange-600 focus:outline-none"
                required
              />
            </div>

            {/* Forgot Password Link */}
            <div className="flex justify-end">
              <button
                type="button"
                className="text-sm text-orange-600 transition-colors hover:text-orange-700"
              >
                Forgot password?
              </button>
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              className="w-full rounded-lg bg-orange-600 py-2 font-semibold text-white transition-colors hover:bg-orange-700"
            >
              Sign In
            </Button>
          </form>

          {/* Sign Up Link */}
          <div className="border-border mt-6 border-t pt-6 text-center">
            <p className="text-muted-foreground text-sm">
              Don&apos;t have an account?{' '}
              <Link
                href="/auth/signup"
                className="font-medium text-orange-600 transition-colors hover:text-orange-700"
              >
                Sign up
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

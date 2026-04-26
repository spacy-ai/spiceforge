'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { ChevronLeft } from 'lucide-react';
import { toast } from 'sonner';

export default function SignUp() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    if (password !== confirmPassword) {
      toast.error('Passwords do not match', {
        position: 'top-right',
      });
      setLoading(false);
      return;
    }

    try {
      const res = await fetch('/api/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: fullName,
          email,
          password,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.message || 'Signup failed');
      }

      toast.success('Account created successfully', {
        position: 'top-right',
      });

      router.push('/circuit');
    } catch (err: any) {
      toast.error(err.message || 'Something went wrong', {
        position: 'top-right',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="light-surface bg-background text-foreground relative flex min-h-screen flex-col items-center justify-center px-6">
      {/* Back Button */}
      <Link
        href="/dashboard"
        className="text-muted-foreground hover:text-foreground absolute top-6 left-6 flex items-center gap-2 transition-colors"
      >
        <ChevronLeft className="h-5 w-5" />
        <span className="text-sm">Back</span>
      </Link>

      {/* Logo */}
      <div className="mb-12 text-center">
        <h1 className="text-3xl font-bold">Create Account</h1>
        <p className="text-muted-foreground mt-2">Join us to start designing circuits with AI</p>
      </div>

      {/* Sign Up Form */}
      <div className="w-full max-w-md">
        <div className="border-border bg-card rounded-lg border p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Full Name Input */}
            <div className="space-y-2">
              <label htmlFor="name" className="block text-sm font-medium">
                Full Name
              </label>
              <input
                id="name"
                type="text"
                placeholder="John Doe"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                disabled={loading}
                className="border-border bg-background w-full rounded-lg border px-4 py-2 transition-colors focus:border-transparent focus:ring-2 focus:ring-orange-600 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
                required
              />
            </div>

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
                disabled={loading}
                className="border-border bg-background w-full rounded-lg border px-4 py-2 transition-colors focus:border-transparent focus:ring-2 focus:ring-orange-600 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
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
                disabled={loading}
                className="border-border bg-background w-full rounded-lg border px-4 py-2 transition-colors focus:border-transparent focus:ring-2 focus:ring-orange-600 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
                required
              />
            </div>

            {/* Confirm Password Input */}
            <div className="space-y-2">
              <label htmlFor="confirmPassword" className="block text-sm font-medium">
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type="password"
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                disabled={loading}
                className="border-border bg-background w-full rounded-lg border px-4 py-2 transition-colors focus:border-transparent focus:ring-2 focus:ring-orange-600 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
                required
              />
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-orange-600 py-2 font-semibold text-white transition-colors hover:bg-orange-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? 'Creating Account...' : 'Create Account'}
            </Button>
          </form>

          {/* Sign In Link */}
          <div className="border-border mt-6 border-t pt-6 text-center">
            <p className="text-muted-foreground text-sm">
              Already have an account?{' '}
              <Link
                href="/auth/signin"
                className="font-medium text-orange-600 transition-colors hover:text-orange-700"
              >
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

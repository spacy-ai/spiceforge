'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { ChevronLeft } from 'lucide-react'
import { useTheme } from 'next-themes'
import { useRouter } from 'next/navigation'


export default function SignIn() {
  const { theme, setTheme } = useTheme()
  const previousTheme = useRef<string | undefined>(undefined)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const router = useRouter()

  useEffect(() => {
    previousTheme.current = theme
    setTheme('light')

    return () => {
      if (previousTheme.current) {
        setTheme(previousTheme.current)
      } else {
        setTheme('system')
      }
    }
  }, [setTheme, theme])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    try {
      const res = await fetch('/api/auth/signin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.message || 'Login failed')
      }
      router.push('/circuit?circuitid=3')
    } catch (err: any) {
      alert(err.message)
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col items-center justify-center px-6 relative">
      {/* Back Button */}
      <Link href="/dashboard" className="absolute top-6 left-6 flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors">
        <ChevronLeft className="w-5 h-5" />
        <span className="text-sm">Back</span>
      </Link>

      <div className="mb-12 text-center">
        <h1 className="text-3xl font-bold">Welcome Back</h1>
        <p className="text-muted-foreground mt-2">Sign in to your account to continue</p>
      </div>

      {/* Sign In Form */}
      <div className="w-full max-w-md">
        <div className="border border-border rounded-lg p-8 bg-card">
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
                className="w-full px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-orange-600 focus:border-transparent transition-colors"
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
                className="w-full px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-orange-600 focus:border-transparent transition-colors"
                required
              />
            </div>

            {/* Forgot Password Link */}
            <div className="flex justify-end">
              <button type="button" className="text-sm text-orange-600 hover:text-orange-700 transition-colors">
                Forgot password?
              </button>
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              className="w-full bg-orange-600 hover:bg-orange-700 text-white font-semibold py-2 rounded-lg transition-colors"
            >
              Sign In
            </Button>
          </form>

          {/* Sign Up Link */}
          <div className="mt-6 text-center border-t border-border pt-6">
            <p className="text-sm text-muted-foreground">
              Don&apos;t have an account?{' '}
              <Link href="/auth/signup" className="text-orange-600 hover:text-orange-700 font-medium transition-colors">
                Sign up
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

'use client';

import Link from 'next/link';
import { Badge } from '@/components/ui/badge';
import { Sparkles, ChevronDown, Sun, Moon } from 'lucide-react';
import { useTheme } from 'next-themes';
import { Button } from '@/components/ui/button';
import { AnimatedElectronics } from '@/components/animated-electronics';

export default function Home() {
  const { theme, setTheme } = useTheme();

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  return (
    <div className="bg-background text-foreground scroll-smooth">
      {/* Header */}
      <header className="bg-background/80 border-border fixed top-0 right-0 left-0 z-50 flex items-center justify-between border-b px-6 py-4 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2">
            <div className="bg-primary flex h-8 w-8 items-center justify-center rounded-full">
              <Sparkles className="text-primary-foreground h-4 w-4" />
            </div>
            <span className="text-card-foreground text-lg font-semibold">Spacy AI</span>
          </div>
          <Badge variant="secondary" className="text-xs">
            BETA
          </Badge>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            className="text-muted-foreground hover:text-foreground"
          >
            <Sun className="h-5 w-5 scale-100 rotate-0 transition-all dark:scale-0 dark:-rotate-90" />
            <Moon className="absolute h-5 w-5 scale-0 rotate-90 transition-all dark:scale-100 dark:rotate-0" />
            <span className="sr-only">Toggle theme</span>
          </Button>
          <Link
            href="/auth/signin"
            className="rounded-full border border-orange-600 px-4 py-2 text-sm text-orange-600 transition-colors hover:bg-orange-600 hover:text-white"
          >
            Sign In
          </Link>
        </div>
      </header>

      <section
        id="hero-section"
        className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-gradient-to-b from-orange-700 to-orange-600 px-6 pt-20 pb-10"
      >
        <AnimatedElectronics />

        <div className="relative z-10 max-w-4xl text-center">
          {/* Main Heading */}
          <h1 className="mb-8 font-mono text-6xl leading-tight font-bold tracking-tight text-white md:text-7xl">
            DESIGN CIRCUITS
            <br />
            WITH AI POWER
          </h1>

          {/* Tagline */}
          <p className="mx-auto mb-12 max-w-2xl text-lg font-light tracking-wide text-white/90 md:text-xl">
            Harness the power of AI-driven SPICE simulation for next-generation circuit design and
            parametric exploration
          </p>

          {/* CTA Buttons */}
          <div className="mb-12 flex flex-col justify-center gap-4 sm:flex-row">
            <Button
              size="lg"
              className="rounded-full bg-white px-8 font-semibold text-orange-600 hover:bg-gray-100"
            >
              Preview Simulator
            </Button>
            <Link href="/circuit?circuitid=3">
              <Button
                size="lg"
                variant="outline"
                className="rounded-full border-2 border-white bg-transparent px-8 text-white hover:bg-white hover:text-orange-600"
              >
                Launch Project
              </Button>
            </Link>
          </div>

          {/* Scroll Indicator */}
          <div className="animate-bounce">
            <Link href="#about-section">
              <ChevronDown className="mx-auto h-6 w-6 text-white/60" />
            </Link>
          </div>
        </div>
      </section>

      {/* About Section */}
      <section id="about-section" className="bg-background px-6 py-20 md:py-28">
        <div className="mx-auto max-w-3xl">
          <h2 className="mb-6 font-mono text-sm tracking-widest text-orange-600">/ABOUT</h2>

          <div className="text-muted-foreground border-border space-y-6 rounded-lg border p-8 text-lg leading-relaxed md:p-12">
            <p>
              Spacy AI is an intelligent SPICE circuit generator that combines cutting-edge
              artificial intelligence with traditional circuit simulation. Our platform empowers
              engineers, students, and researchers to design, analyze, and optimize circuits with
              unprecedented speed and accuracy.
            </p>

            <p>
              Whether you are prototyping analog circuits, designing power systems, or exploring
              advanced signal processing, Spacy AI provides an intuitive interface backed by
              sophisticated SPICE simulation engines. The AI-powered assistant learns your design
              patterns and offers intelligent suggestions to accelerate your workflow.
            </p>

            <p>
              Built for the modern engineer, Spacy AI bridges the gap between conceptual design and
              rigorous simulation, making complex circuit analysis accessible to everyone from
              students to industry professionals.
            </p>
          </div>

          {/* Features Grid */}
          <div className="mt-16 grid gap-6 md:grid-cols-3">
            <div className="border-border rounded-lg border p-6 transition-colors hover:border-orange-600">
              <div className="mb-4 text-3xl">⚡</div>
              <h3 className="mb-2 text-lg font-semibold">Fast Simulation</h3>
              <p className="text-muted-foreground text-sm">
                First of all understand there is no other ai driven spice simluator. All are busy
                building 5-mins delivery
              </p>
            </div>

            <div className="border-border rounded-lg border p-6 transition-colors hover:border-orange-600">
              <div className="mb-4 text-3xl">🤖</div>
              <h3 className="mb-2 text-lg font-semibold">AI-Powered Design</h3>
              <p className="text-muted-foreground text-sm">
                If you think using ai for circuit design will make you lazy, think again. You use ai
                for making excel sheet right?
              </p>
            </div>

            <div className="border-border rounded-lg border p-6 transition-colors hover:border-orange-600">
              <div className="mb-4 text-3xl">📊</div>
              <h3 className="mb-2 text-lg font-semibold">Rich Analytics</h3>
              <p className="text-muted-foreground text-sm">
                {' '}
                There are analytics inside, dont worry its not paid, but soon before i make it paid
                use it to your best.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-orange-700 px-6 py-16 text-white md:py-24">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="mb-6 text-4xl font-bold md:text-5xl">Ready to Design?</h2>
          <p className="mb-8 text-lg text-orange-100">
            Start simulating circuits with AI-powered intelligence today
          </p>
          <Link
            href="#hero-section"
            className="inline-block rounded-full bg-white px-8 py-3 font-semibold text-orange-600 transition-colors hover:bg-gray-100"
          >
            Get Started
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-background border-border border-t px-6 py-8">
        <div className="text-muted-foreground mx-auto flex max-w-4xl flex-col items-center justify-between text-sm md:flex-row">
          <p>© 2026 Spacy AI. Designed for the future of circuit engineering.</p>
          <div className="mt-4 flex gap-6 md:mt-0">
            <button className="hover:text-foreground transition-colors">Docs</button>
            <button className="hover:text-foreground transition-colors">Support</button>
            <button className="hover:text-foreground transition-colors">GitHub</button>
          </div>
        </div>
      </footer>
    </div>
  );
}

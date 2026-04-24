'use client'

import Link from 'next/link'
import { Badge } from "@/components/ui/badge"
import { Sparkles, ChevronDown, Sun, Moon } from "lucide-react"
import { useTheme } from 'next-themes'
import { Button } from '@/components/ui/button'
import { AnimatedElectronics } from '@/components/animated-electronics'

export default function Home() {
  const { theme, setTheme } = useTheme()

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark')
  }

  return (
    <div className="bg-background text-foreground scroll-smooth">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4 bg-background/80 backdrop-blur-sm border-b border-border">
        <div className="flex items-center gap-2">
           <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary">
            <Sparkles className="h-4 w-4 text-primary-foreground" />
          </div>
          <span className="text-lg font-semibold text-card-foreground">Spacy AI</span>
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
          <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          <span className="sr-only">Toggle theme</span>
        </Button>
          <Link
            href="/auth/signin"
            className="text-sm border border-orange-600 text-orange-600 rounded-full px-4 py-2 hover:bg-orange-600 hover:text-white transition-colors"
          >
            Sign In
          </Link>
        </div>
      </header>


      <section id="hero-section" className="min-h-screen bg-gradient-to-b from-orange-700 to-orange-600 flex flex-col items-center justify-center px-6 pt-20 pb-10 relative overflow-hidden">
        <AnimatedElectronics />

        <div className="max-w-4xl text-center relative z-10">
          

          {/* Main Heading */}
          <h1 className="text-6xl md:text-7xl font-bold text-white mb-8 leading-tight tracking-tight font-mono">
            DESIGN CIRCUITS
            <br />
            WITH AI POWER
          </h1>

          {/* Tagline */}
          <p className="text-lg md:text-xl text-white/90 mb-12 max-w-2xl mx-auto font-light tracking-wide">
            Harness the power of AI-driven SPICE simulation for next-generation circuit design and parametric exploration
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Button
              size="lg"
              className="px-8 bg-white text-orange-600 hover:bg-gray-100 font-semibold rounded-full"
            >
              Preview Simulator
            </Button>
            <Link href="/circuit?circuitid=3">
              <Button
                size="lg"
                variant="outline"
                className="px-8 border-2 border-white text-white bg-transparent hover:bg-white hover:text-orange-600 rounded-full"
              >
                Launch Project
              </Button>
            </Link>
          </div>

          {/* Scroll Indicator */}
          <div className="animate-bounce">
            <Link href="#about-section">
            <ChevronDown  className="w-6 h-6 text-white/60 mx-auto" />
            </Link>
          </div>
        </div>
      </section>

      {/* About Section */}
      <section id="about-section" className="bg-background px-6 py-20 md:py-28" >
        <div className="max-w-3xl mx-auto">
          <h2 className="text-sm font-mono text-orange-600 mb-6 tracking-widest">/ABOUT</h2>

          <div className="space-y-6 text-lg leading-relaxed text-muted-foreground border border-border rounded-lg p-8 md:p-12">
            <p>
              Spacy AI is an intelligent SPICE circuit generator that combines cutting-edge artificial intelligence with traditional circuit simulation. Our platform empowers engineers, students, and researchers to design, analyze, and optimize circuits with unprecedented speed and accuracy.
            </p>

            <p>
              Whether you are prototyping analog circuits, designing power systems, or exploring advanced signal processing, Spacy AI provides an intuitive interface backed by sophisticated SPICE simulation engines. The AI-powered assistant learns your design patterns and offers intelligent suggestions to accelerate your workflow.
            </p>

            <p>
              Built for the modern engineer, Spacy AI bridges the gap between conceptual design and rigorous simulation, making complex circuit analysis accessible to everyone from students to industry professionals.
            </p>
          </div>

          {/* Features Grid */}
          <div className="grid md:grid-cols-3 gap-6 mt-16">
            <div className="border border-border rounded-lg p-6 hover:border-orange-600 transition-colors">
              <div className="text-3xl mb-4">⚡</div>
              <h3 className="font-semibold text-lg mb-2">Fast Simulation</h3>
              <p className="text-sm text-muted-foreground">First of all understand there is no other ai driven spice simluator. All are busy building 5-mins delivery</p>
            </div>

            <div className="border border-border rounded-lg p-6 hover:border-orange-600 transition-colors">
              <div className="text-3xl mb-4">🤖</div>
              <h3 className="font-semibold text-lg mb-2">AI-Powered Design</h3>
              <p className="text-sm text-muted-foreground">If you think using ai for circuit design will make you lazy, think again. You use ai for making excel sheet right?</p>
            </div>

            <div className="border border-border rounded-lg p-6 hover:border-orange-600 transition-colors">
              <div className="text-3xl mb-4">📊</div>
              <h3 className="font-semibold text-lg mb-2">Rich Analytics</h3>
              <p className="text-sm text-muted-foreground"> There are analytics inside, dont worry its not paid, but soon before i make it paid use it to your best.</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-orange-700 text-white px-6 py-16 md:py-24">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">Ready to Design?</h2>
          <p className="text-lg text-orange-100 mb-8">
            Start simulating circuits with AI-powered intelligence today
          </p>
          <Link
            href="#hero-section"
            className="inline-block px-8 py-3 bg-white text-orange-600 font-semibold rounded-full hover:bg-gray-100 transition-colors"
          >
            Get Started
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-background border-t border-border px-6 py-8">
        <div className="max-w-4xl mx-auto flex flex-col md:flex-row items-center justify-between text-sm text-muted-foreground">
          <p>© 2026 Spacy AI. Designed for the future of circuit engineering.</p>
          <div className="flex gap-6 mt-4 md:mt-0">
            <button className="hover:text-foreground transition-colors">Docs</button>
            <button className="hover:text-foreground transition-colors">Support</button>
            <button className="hover:text-foreground transition-colors">GitHub</button>
          </div>
        </div>
      </footer>
    </div>
  )
}

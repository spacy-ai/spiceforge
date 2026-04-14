"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Textarea } from "@/components/ui/textarea"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { 
  Sparkles, 
  Pencil, 
  Settings, 
  ChevronDown, 
  ChevronUp,
  Paperclip,
  Send,
  Wand2
} from "lucide-react"

const examplePrompts = [
  "Build a modular clamping system (80×40mm) for T-track work...",
  "Create a geneva drive mechanism (80×80×20mm) for intermitt...",
  "Create an assembly fixture (300×200mm) with toggle clamp m...",
  "Build a compression fitting (Ø20×40mm) with olive and nut for...",
]

export function ChatPanel() {
  const [examplesOpen, setExamplesOpen] = useState(true)
  const [message, setMessage] = useState("")

  return (
    <div className="flex h-full flex-col bg-card">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold text-card-foreground">New Design</h2>
          <Sparkles className="h-4 w-4 text-muted-foreground" />
          <Pencil className="h-4 w-4 text-muted-foreground" />
        </div>
      </div>

      {/* Model selector */}
      <div className="border-b border-border px-4 py-2">
        <div className="flex items-center gap-2">
          <Badge className="bg-emerald-600 text-white hover:bg-emerald-700">General</Badge>
          <div className="flex items-center gap-1 text-sm text-muted-foreground">
            <Sparkles className="h-3 w-3" />
            <span className="truncate">Gemini 3 Flash Preview</span>
          </div>
        </div>
      </div>

      {/* Chat content */}
      <ScrollArea className="flex-1 min-h-0">
        <div className="flex flex-col gap-4 p-4">
          {/* AI Welcome Message */}
          <div className="rounded-lg bg-secondary p-4">
            <p className="text-sm text-secondary-foreground">
              Welcome to Spacy AI! I&apos;ll help you create versatile, parametric designs 
              for various applications. Describe your project and I&apos;ll generate 
              well-documented OpenSCAD code that&apos;s adaptable to multiple materials 
              and manufacturing methods.
            </p>
            <div className="mt-3 flex items-center justify-end gap-2 text-sm text-muted-foreground">
              <span>Spacy AI</span>
              <Wand2 className="h-4 w-4" />
            </div>
          </div>

          {/* Examples Section */}
          <Collapsible open={examplesOpen} onOpenChange={setExamplesOpen}>
            <CollapsibleTrigger asChild>
              <button className="flex w-full items-center justify-between rounded-lg border border-border bg-secondary/50 px-4 py-3 text-left transition-colors hover:bg-secondary">
                <div className="flex items-center gap-2">
                  <Settings className="h-4 w-4 text-primary" />
                  <span className="font-medium text-primary">Examples</span>
                </div>
                {examplesOpen ? (
                  <ChevronUp className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-muted-foreground" />
                )}
              </button>
            </CollapsibleTrigger>
            <CollapsibleContent className="mt-2 space-y-2">
              {examplePrompts.map((prompt, index) => (
                <button
                  key={index}
                  className="w-full rounded-lg border border-border bg-secondary/30 px-4 py-3 text-left text-sm text-secondary-foreground transition-colors hover:bg-secondary/50"
                >
                  {prompt}
                </button>
              ))}
            </CollapsibleContent>
          </Collapsible>
        </div>
      </ScrollArea>

      {/* Input area - fixed at bottom */}
      <div className="shrink-0 border-t border-border p-3 sm:p-4">
        <div className="relative">
          <Textarea
            placeholder="Describe the model you want to create... (Paste images with Ctrl+V)"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            className="min-h-[60px] sm:min-h-[80px] resize-none border-primary bg-primary/10 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus-visible:ring-primary"
          />
          <Button
            size="icon"
            variant="ghost"
            className="absolute right-1 top-1 h-8 w-8 text-muted-foreground hover:text-foreground"
          >
            <Paperclip className="h-4 w-4" />
          </Button>
        </div>

        {/* Model selector and send */}
        <div className="mt-2 flex items-center gap-2 sm:mt-3">
          <Select defaultValue="gemini">
            <SelectTrigger className="min-w-0 flex-1 border-border bg-secondary text-secondary-foreground">
              <div className="flex items-center gap-2 truncate">
                <Sparkles className="h-4 w-4 shrink-0 text-primary" />
                <SelectValue placeholder="Select model" />
              </div>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="gemini">Gemini 3 Flash Preview</SelectItem>
              <SelectItem value="gpt4">GPT-4 Turbo</SelectItem>
              <SelectItem value="claude">Claude 3 Opus</SelectItem>
            </SelectContent>
          </Select>
          
          <Button size="icon" className="shrink-0 bg-primary text-primary-foreground hover:bg-primary/90">
            <Send className="h-4 w-4 sm:h-5 sm:w-5" />
          </Button>
        </div>
      </div>
    </div>
  )
}

"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
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

type Message = {
  id: number
  role: "user"
  text: string
}

export function ChatPanel() {
  const [examplesOpen, setExamplesOpen] = useState(true)
  const [message, setMessage] = useState("")
  const [heading, setHeading] = useState("New Design")
  const [isEditingHeading, setIsEditingHeading] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const scrollRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when messages update
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  function sendMessage() {
    const text = message.trim()
    if (!text) return
    setMessages((prev) => [...prev, { id: Date.now(), role: "user", text }])
    setMessage("")
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="flex h-full flex-col bg-card">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        {isEditingHeading ? (
          <textarea
            value={heading}
            onChange={(e) => setHeading(e.target.value)}
            autoFocus
            rows={1}
            onBlur={() => setIsEditingHeading(false)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault()
                setIsEditingHeading(false)
              }
            }}
            className="w-full resize-none overflow-hidden bg-transparent font-semibold text-card-foreground focus:outline-none"
          />
        ) : (
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold text-card-foreground">
              {heading}
            </h2>
            <Button
              size="icon"
              className="shrink-0 bg-primary text-primary-foreground hover:bg-primary/80 sm:h-7 sm:w-7"
              onClick={() => setIsEditingHeading(true)}
            >
              <Pencil className="h-2 w-2 sm:h-5 sm:w-5" />
            </Button>
          </div>
        )}
      </div>

      {/* Scroll area */}
      <ScrollArea className="flex-1 min-h-0" ref={scrollRef}>
        <div className="flex flex-col gap-4 p-4">
          {/* Welcome message */}
          <div className="rounded-lg bg-secondary p-4">
            <p className="text-sm text-secondary-foreground">
              Welcome to Spacy AI! I&apos;ll help you create versatile, parametric
              designs for various applications.
            </p>
            <div className="mt-3 flex items-center justify-end gap-2 text-sm text-muted-foreground">
              <span>Spacy AI</span>
              <Wand2 className="h-4 w-4" />
            </div>
          </div>

          {/* Examples */}
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
                  onClick={() => setMessage(prompt)}
                  className="w-full rounded-lg border border-border bg-secondary/30 px-4 py-3 text-left text-sm text-secondary-foreground transition-colors hover:bg-secondary/50"
                >
                  {prompt}
                </button>
              ))}
            </CollapsibleContent>
          </Collapsible>

          {/* Chat messages */}
          {messages.map((msg) => (
            <div key={msg.id} className="flex justify-end">
              <div className="max-w-[80%] rounded-lg bg-primary px-4 py-2 text-sm text-primary-foreground">
                {msg.text}
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>

      {/* Input area */}
      <div className="shrink-0 border-t border-border p-3 sm:p-4">
        <div className="relative">
          <Textarea
            placeholder="Describe the model you want to create... (Paste images with Ctrl+V)"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
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

          <Button
            size="icon"
            onClick={sendMessage}
            className="shrink-0 bg-primary text-primary-foreground hover:bg-primary/90"
          >
            <Send className="h-4 w-4 sm:h-5 sm:w-5" />
          </Button>
        </div>
      </div>
    </div>
  )
}
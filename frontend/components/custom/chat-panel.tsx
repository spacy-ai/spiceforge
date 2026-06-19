'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Textarea } from '@/components/ui/textarea';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Sparkles,
  Pencil,
  ChevronDown,
  Paperclip,
  Send,
  Wand2,
  Loader2,
  Code2,
  Copy,
  Check,
} from 'lucide-react';

// Base URL of the FastAPI netlist generation service.
// Set NEXT_PUBLIC_NETLIST_API_URL in your .env.local, e.g.
//   NEXT_PUBLIC_NETLIST_API_URL=http://localhost:8000
const API_BASE_URL = process.env.NEXT_PUBLIC_NETLIST_API_URL || 'http://localhost:8000';

// Mirrors GenerateNetlistResponse from the FastAPI router. The backend uses
// this same shape whether the run succeeded, needs clarification, or hit an
// error, so we render it uniformly in the chat rather than branching styles.
type NetlistResult = {
  success: boolean;
  title?: string | null;
  netlist: string;
  summary?: string | null;
  python_code?: string | null;
  error?: string | null;
  blueprint?: Record<string, unknown> | null;
  simulation?: Record<string, unknown> | null;
  clarifications: string[];
};

interface ChatPanelProps {
  onNetlistGenerated: (netlist: string) => void;
}

type Message =
  | { id: number; role: 'user'; text: string }
  | { id: number; role: 'assistant'; kind: 'loading' }
  | { id: number; role: 'assistant'; kind: 'response'; result: NetlistResult };

function CopyButton({ value, label }: { value: string; label: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard not available; fail silently.
    }
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      className="text-muted-foreground hover:text-foreground h-7 w-7"
      onClick={handleCopy}
      aria-label={label}
    >
      {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
    </Button>
  );
}

export function ChatPanel( { onNetlistGenerated }: ChatPanelProps ) {
  const [message, setMessage] = useState('');
  const [heading, setHeading] = useState('New Design');
  const [isEditingHeading, setIsEditingHeading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages update
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  async function sendMessage() {
  const text = message.trim();
  if (!text || isGenerating) return;

  const userMessageId = Date.now();
  const loadingId = userMessageId + 1;

  setMessages((prev) => [
    ...prev,
    { id: userMessageId, role: 'user', text },
    { id: loadingId, role: 'assistant', kind: 'loading' },
  ]);
  setMessage('');
  setIsGenerating(true);

  try {
    const response = await fetch(`${API_BASE_URL}/netlist/generate-netlist`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt: text,
        run_simulation: true,
      }),
    });

    if (!response.ok) throw new Error(`Request failed with status ${response.status}`);

    const data: NetlistResult = await response.json();

    setMessages((prev) =>
      prev.map((m) => (m.id === loadingId ? { id: loadingId, role: 'assistant', kind: 'response', result: data } : m))
    );

    if (data.success && data.netlist) {
      await new Promise(resolve => setTimeout(resolve, 50));
      onNetlistGenerated(data.netlist);
    }
  } catch (err) {
    const fallback: NetlistResult = {
      success: false,
      netlist: '',
      clarifications: [],
      error: err instanceof Error ? err.message : 'Something went wrong.',
    };
    setMessages((prev) =>
      prev.map((m) =>
        m.id === loadingId ? { id: loadingId, role: 'assistant', kind: 'response', result: fallback } : m
      )
    );
  } finally {
    setIsGenerating(false);
  }
}

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="bg-card flex h-full flex-col">
      {/* Header */}
      <div className="border-border flex items-center justify-between border-b px-4 py-3">
        {isEditingHeading ? (
          <textarea
            value={heading}
            onChange={(e) => setHeading(e.target.value)}
            autoFocus
            rows={1}
            onBlur={() => setIsEditingHeading(false)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                setIsEditingHeading(false);
              }
            }}
            className="text-card-foreground w-full resize-none overflow-hidden bg-transparent font-semibold focus:outline-none"
          />
        ) : (
          <div className="flex items-center gap-2">
            <h2 className="text-card-foreground text-lg font-semibold">{heading}</h2>
            <Button
              size="icon"
              className="bg-primary text-primary-foreground hover:bg-primary/80 shrink-0 sm:h-7 sm:w-7"
              onClick={() => setIsEditingHeading(true)}
            >
              <Pencil className="h-2 w-2 sm:h-5 sm:w-5" />
            </Button>
          </div>
        )}
      </div>

      {/* Scroll area */}
      <ScrollArea className="min-h-0 flex-1" ref={scrollRef}>
        <div className="flex flex-col gap-4 p-4">
          {/* Welcome message */}
          <div className="bg-secondary rounded-lg p-4">
            <p className="text-secondary-foreground text-sm">
              Welcome to Spacy AI! I&apos;ll help you create versatile, parametric designs for
              various applications.
            </p>
            <div className="text-muted-foreground mt-3 flex items-center justify-end gap-2 text-sm">
              <span>Spacy AI</span>
              <Wand2 className="h-4 w-4" />
            </div>
          </div>

          {/* Chat messages */}
          {messages.map((msg) => {
            if (msg.role === 'user') {
              return (
                <div key={msg.id} className="flex justify-end">
                  <div className="bg-primary text-primary-foreground max-w-[80%] rounded-lg px-4 py-2 text-sm">
                    {msg.text}
                  </div>
                </div>
              );
            }

            if (msg.kind === 'loading') {
              return (
                <div key={msg.id} className="flex justify-start">
                  <div className="bg-secondary text-secondary-foreground flex items-center gap-2 rounded-lg px-4 py-3 text-sm">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Generating netlist...
                  </div>
                </div>
              );
            }

            // kind === 'response' — covers success, clarification requests, and errors alike
            const { result } = msg;
            const hasSummary = Boolean(result.summary);
            const hasClarifications = result.clarifications.length > 0;
            const hasNetlist = Boolean(result.netlist);
            const fallbackText =
              !hasSummary && !hasClarifications && !hasNetlist
                ? result.error || 'Something went wrong.'
                : null;

            return (
              <div key={msg.id} className="flex justify-start">
                <div className="bg-secondary text-secondary-foreground max-w-[85%] space-y-3 rounded-lg p-4 text-sm">
                  {result.title && <p className="font-semibold">{result.title}</p>}
                  {hasSummary && <p>{result.summary}</p>}

                  {hasClarifications && (
                    <div className="space-y-1.5">
                      {!hasSummary && <p>I need a bit more detail before I can build this:</p>}
                      <ul className="list-disc space-y-1 pl-4">
                        {result.clarifications.map((c, i) => (
                          <li key={i}>{c}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {fallbackText && <p>{fallbackText}</p>}

                  {hasNetlist && (
                    <Collapsible>
                      <div className="flex items-center gap-1">
                        <CollapsibleTrigger asChild>
                          <Button variant="outline" size="sm" className="h-7 gap-1.5 text-xs">
                            <Code2 className="h-3.5 w-3.5" />
                            Netlist
                            <ChevronDown className="h-3.5 w-3.5" />
                          </Button>
                        </CollapsibleTrigger>
                        <CopyButton value={result.netlist} label="Copy netlist" />
                      </div>
                      <CollapsibleContent>
                        <pre className="bg-background/60 border-border mt-2 max-h-72 overflow-auto rounded-md border p-3 text-xs">
                          <code>{result.netlist}</code>
                        </pre>
                      </CollapsibleContent>
                    </Collapsible>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </ScrollArea>

      {/* Input area */}
      <div className="border-border shrink-0 border-t p-3 sm:p-4">
        <div className="relative">
          <Textarea
            placeholder="Describe the model you want to create... "
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isGenerating}
            className="border-primary bg-primary/10 text-foreground placeholder:text-muted-foreground focus-visible:ring-primary min-h-[60px] resize-none pr-10 text-sm sm:min-h-[80px]"
          />
          <Button
            size="icon"
            variant="ghost"
            className="text-muted-foreground hover:text-foreground absolute top-1 right-1 h-8 w-8"
          >
            <Paperclip className="h-4 w-4" />
          </Button>
        </div>

        <div className="mt-2 flex items-center gap-2 sm:mt-3">
          <Select defaultValue="spacy">
            <SelectTrigger className="border-border bg-secondary text-secondary-foreground min-w-0 flex-1">
              <div className="flex items-center gap-2 truncate">
                <Sparkles className="text-primary h-4 w-4 shrink-0" />
                <SelectValue placeholder="Select model" />
              </div>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="spacy">spacy-circuit-ai</SelectItem>
            </SelectContent>
          </Select>

          <Button
            size="icon"
            onClick={sendMessage}
            disabled={isGenerating || !message.trim()}
            className="bg-primary text-primary-foreground hover:bg-primary/90 shrink-0 disabled:opacity-50"
          >
            {isGenerating ? (
              <Loader2 className="h-4 w-4 animate-spin sm:h-5 sm:w-5" />
            ) : (
              <Send className="h-4 w-4 sm:h-5 sm:w-5" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
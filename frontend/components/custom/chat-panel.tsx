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
  Settings,
  ChevronDown,
  ChevronUp,
  Paperclip,
  Send,
  Wand2,
} from 'lucide-react';


type Message = {
  id: number;
  role: 'user';
  text: string;
};

export function ChatPanel() {
  const [examplesOpen, setExamplesOpen] = useState(true);
  const [message, setMessage] = useState('');
  const [heading, setHeading] = useState('New Design');
  const [isEditingHeading, setIsEditingHeading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages update
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  function sendMessage() {
    const text = message.trim();
    if (!text) return;
    setMessages((prev) => [...prev, { id: Date.now(), role: 'user', text }]);
    setMessage('');
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
          {messages.map((msg) => (
            <div key={msg.id} className="flex justify-end">
              <div className="bg-primary text-primary-foreground max-w-[80%] rounded-lg px-4 py-2 text-sm">
                {msg.text}
              </div>
            </div>
          ))}
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
            className="bg-primary text-primary-foreground hover:bg-primary/90 shrink-0"
          >
            <Send className="h-4 w-4 sm:h-5 sm:w-5" />
          </Button>
        </div>
      </div>
    </div>
  );
}

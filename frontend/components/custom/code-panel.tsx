'use client';

import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Copy, Terminal, Play, CheckCircle, AlertCircle } from 'lucide-react';
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '@/components/ui/resizable';
import { useState, useEffect, useRef } from 'react';
import { apiBase } from '@/lib/config';
import type { SimulationResponse } from '@/lib/types/simulation';

interface ConsoleMessage {
  id: string;
  type: 'info' | 'success' | 'error' | 'warning';
  text: string;
  timestamp: Date;
}

export function CodePanel({
  onSimulate,
  initialNetlist = '',
  circuitId,
}: {
  onSimulate?: (
    netlist: string,
    svgContent?: string,
    simulationResponse?: SimulationResponse
  ) => void;
  initialNetlist?: string;
  circuitId?: string;
}) {
  const [netlist, setNetlist] = useState(
    initialNetlist || '.title New Circuit\n\n.control\nop\n.endc\n.end'
  );
  const [copied, setCopied] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const messageCounterRef = useRef(0);
  const [messages, setMessages] = useState<ConsoleMessage[]>([
    { id: '1', type: 'info', text: 'Console ready...', timestamp: new Date() },
  ]);

  useEffect(() => {
    if (initialNetlist) {
      setNetlist(initialNetlist);
      setMessages([
        { id: '1', type: 'info', text: `Loaded circuit ${circuitId}`, timestamp: new Date() },
      ]);
    }
  }, [initialNetlist, circuitId]);

  async function copyTextToClipboard(text: string) {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      addMessage('success', 'Netlist copied to clipboard');
      setTimeout(() => {
        setCopied(false);
      }, 3000);
    } catch (err) {
      addMessage('error', 'Failed to copy netlist');
      console.error('Failed to copy: ', err);
    }
  }

  const addMessage = (type: ConsoleMessage['type'], text: string) => {
    messageCounterRef.current += 1;
    const newMessage: ConsoleMessage = {
      id: `${Date.now()}-${messageCounterRef.current}`,
      type,
      text,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, newMessage]);
  };

  const handleSimulate = async () => {
    setIsSimulating(true);
    addMessage('info', `Simulating circuit ${circuitId || 'unknown'}...`);

    // Validate netlist
    if (!netlist.trim()) {
      addMessage('error', 'Netlist is empty');
      setIsSimulating(false);
      return;
    }

    try {
      const response = await fetch(`${apiBase}/simulate/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          netlist,
          options: {
            include_schematic: true,
          },
        }),
      });

      if (!response.ok) {
        throw new Error(`Simulation request failed with status ${response.status}`);
      }

      const data = await response.json();

      if (data.status === 'error') {
        const errMessage = data?.error?.message || 'Simulation failed';
        const hint = data?.error?.hint ? ` Hint: ${data.error.hint}` : '';
        addMessage('error', `✗ ${errMessage}${hint}`);

        if (data?.stderr) {
          addMessage('warning', `stderr: ${data.stderr}`);
        }
        if (data?.stdout) {
          addMessage('info', `stdout: ${data.stdout}`);
        }
      } else {
        addMessage('success', `✓ Simulation of ${circuitId} completed successfully`);
        addMessage('info', 'Simulation results received from backend');

        if (onSimulate) {
          onSimulate(netlist, data?.schematic?.content, data as SimulationResponse);
        }
      }
    } catch (error) {
      addMessage('error', `✗ Simulation failed for ${circuitId}: Check netlist syntax`);
    } finally {
      setIsSimulating(false);
    }
  };

  const clearConsole = () => {
    setMessages([{ id: '1', type: 'info', text: 'Console cleared', timestamp: new Date() }]);
  };

  const getMessageColor = (type: ConsoleMessage['type']): string => {
    switch (type) {
      case 'success':
        return 'text-emerald-500';
      case 'error':
        return 'text-red-500';
      case 'warning':
        return 'text-yellow-500';
      default:
        return 'text-muted-foreground';
    }
  };

  const getMessageIcon = (type: ConsoleMessage['type']) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="h-3 w-3" />;
      case 'error':
        return <AlertCircle className="h-3 w-3" />;
      default:
        return null;
    }
  };

  return (
    <ResizablePanelGroup direction="vertical" className="h-full">
      <ResizablePanel defaultSize={60} minSize={30}>
        <div className="bg-card relative flex h-full flex-col">
          <div className="border-border flex items-center justify-between border-b px-3 py-2">
            <span className="text-card-foreground text-xs font-semibold tracking-wider uppercase">
              Netlist Editor
            </span>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                className="text-card-foreground hover:bg-secondary gap-2 px-3 py-1.5"
                onClick={() => copyTextToClipboard(netlist)}
              >
                <Copy className="h-4 w-4" />
                {copied ? 'Copied!' : 'Copy'}
              </Button>
            </div>
          </div>

          <textarea
            value={netlist}
            onChange={(e) => setNetlist(e.target.value)}
            className="bg-secondary/40 text-secondary-foreground flex-1 resize-none border-none p-4 font-mono text-sm focus:outline-none"
          />

          <div className="border-border bg-secondary/20 flex items-center justify-between border-t px-3 py-2">
            <span className="text-muted-foreground text-xs">
              {netlist.split('\n').length} lines
            </span>
            <Button
              size="sm"
              className="bg-primary text-primary-foreground hover:bg-primary/90 gap-2"
              onClick={handleSimulate}
              disabled={isSimulating}
            >
              <Play className="h-3.5 w-3.5" />
              {isSimulating ? 'Simulating...' : 'Confirm & Simulate'}
            </Button>
          </div>
        </div>
      </ResizablePanel>

      <ResizableHandle className="bg-border" />

      <ResizablePanel defaultSize={40} minSize={20}>
        <div className="bg-card flex h-full flex-col">
          <div className="border-border flex items-center justify-between border-b px-3 py-2">
            <div className="flex items-center gap-2">
              <Terminal className="text-card-foreground h-4 w-4" />
              <span className="text-card-foreground text-sm font-medium">Console Output</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="text-muted-foreground hover:text-card-foreground h-6 px-2 text-xs"
              onClick={clearConsole}
            >
              Clear
            </Button>
          </div>
          <ScrollArea className="h-full w-full flex-1">
            <div className="space-y-1 p-4 pr-6">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-2 font-mono text-xs ${getMessageColor(msg.type)}`}
                >
                  {getMessageIcon(msg.type) && (
                    <span className="flex-shrink-0">{getMessageIcon(msg.type)}</span>
                  )}
                  <span className="flex-1 break-words">{msg.text}</span>
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>
      </ResizablePanel>
    </ResizablePanelGroup>
  );
}

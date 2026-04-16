"use client"

import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Copy, Terminal } from "lucide-react"
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "@/components/ui/resizable"
import { useState } from "react"

export function CodePanel() {

  const[netlist, setNetlist] = useState("hello world");
  const [copied, setCopied] = useState(false);

  async function copyTextToClipboard(text: string) {
  try {
    await navigator.clipboard.writeText(text);
    setCopied(true);

    setTimeout(() => {
      setCopied(false);
    }, 3000);

  } catch (err) {
    console.error('Failed to copy: ', err);
  }
}

  return (
      <ResizablePanelGroup direction="vertical" className="h-full">
      <ResizablePanel defaultSize={60} minSize={30}>
    <div className="relative h-full bg-card">
      
    <textarea
      value={netlist}
      onChange={(e) => setNetlist(e.target.value)}
      className="w-full h-full resize-none bg-secondary/40 p-4 pr-24 font-mono text-sm text-secondary-foreground focus:outline-none"
    />

      <div className="absolute top-2 right-2">
     <Button
      variant="ghost"
      size="sm"
      className="px-3 py-1.5 gap-2 text-card-foreground hover:bg-secondary"
      onClick={() => copyTextToClipboard(netlist)}
    >
      <Copy className="h-4 w-4" />
      {copied ? "Copied!" : "Copy"}
    </Button>
    </div>

    </div>
  </ResizablePanel>
        
      <ResizableHandle className="bg-border" />
      
      <ResizablePanel defaultSize={40} minSize={20}>
        <div className="flex h-full flex-col bg-card">
          <div className="flex items-center gap-2 border-b border-border px-3 py-2">
            <Terminal className="h-4 w-4 text-card-foreground" />
            <span className="text-sm font-medium text-card-foreground">Console</span>
          </div>
          <ScrollArea className="flex-1">
            <div className="p-4">
              <div className="rounded-lg border border-border bg-secondary/40 p-4">
                <p className="font-mono text-sm text-muted-foreground">Console ready...</p>
                <p className="mt-2 font-mono text-sm text-emerald-500">
                  {">"} Waiting for compilation...
                </p>
              </div>
            </div>
          </ScrollArea>
        </div>
      </ResizablePanel>
    </ResizablePanelGroup>
  )
}

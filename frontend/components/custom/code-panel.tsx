"use client"

import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Copy, Terminal } from "lucide-react"
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "@/components/ui/resizable"

export function CodePanel() {
  return (
    <ResizablePanelGroup direction="vertical" className="h-full">
      <ResizablePanel defaultSize={60} minSize={30}>
        <div className="flex h-full flex-col bg-card">
          <div className="flex items-center justify-end border-b border-border px-3 py-2">
            <Button
              variant="ghost"
              size="sm"
              className="gap-2 text-card-foreground hover:bg-secondary"
            >
              <Copy className="h-4 w-4" />
              Copy
            </Button>
          </div>
          <ScrollArea className="flex-1">
            <div className="p-4">
              <pre className="rounded-lg border border-border bg-secondary/40 p-4 font-mono text-sm text-secondary-foreground">
                <code className="text-muted-foreground">
{`// OpenSCAD Code Editor
// Your generated code will appear here

// Example:
module parametric_box(width, height, depth) {
  cube([width, height, depth]);
}

// Call the module
parametric_box(50, 30, 20);`}
                </code>
              </pre>
            </div>
          </ScrollArea>
          <div className="flex items-center justify-center border-t border-border py-8 text-muted-foreground">
            Loading...
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

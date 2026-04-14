"use client"

import { Button } from "@/components/ui/button"
import { Pencil, Download, Box } from "lucide-react"

export function PreviewPanel() {
  return (
    <div className="flex h-full flex-col bg-sidebar">
      <div className="flex items-center justify-end border-b border-sidebar-border px-3 py-2">
        <Button
          variant="ghost"
          size="sm"
          className="gap-2 text-primary hover:bg-sidebar-accent"
        >
          <Pencil className="h-4 w-4" />
          Annotate
        </Button>
      </div>
      
      <div className="flex flex-1 flex-col items-center justify-center">
        <div className="relative flex h-full w-full items-center justify-center">
          {/* Grid background */}
          <div 
            className="absolute inset-0 opacity-10"
            style={{
              backgroundImage: `
                linear-gradient(to right, #475569 1px, transparent 1px),
                linear-gradient(to bottom, #475569 1px, transparent 1px)
              `,
              backgroundSize: '40px 40px'
            }}
          />
          
          {/* 3D Preview placeholder */}
          <div className="relative z-10 flex flex-col items-center gap-4">
            <div className="flex h-24 w-24 items-center justify-center rounded-lg border-2 border-dashed border-muted-foreground/30">
              <Box className="h-12 w-12 text-muted-foreground/50" />
            </div>
            <p className="text-lg text-muted-foreground">Initializing 3D viewer...</p>
          </div>
        </div>
      </div>
      
      <div className="flex items-center justify-end border-t border-sidebar-border px-3 py-2">
        <Button
          variant="outline"
          size="sm"
          className="gap-2 border-sidebar-border text-sidebar-foreground hover:bg-sidebar-accent"
        >
          <Download className="h-4 w-4" />
          Export
        </Button>
      </div>
    </div>
  )
}

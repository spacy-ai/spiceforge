"use client"

import { useState, useRef } from "react"
import { Button } from "@/components/ui/button"
import { CircuitBoard, Pencil, ZoomIn, ZoomOut } from "lucide-react"
import { ExportPopup } from "@/components/custom/exportPopup"
import { AnalysisPanel } from "@/components/custom/analysis-panel"
import type { SimulationResponse } from "@/lib/types/simulation"

interface PreviewPanelProps {
  circuitId?: string
  svgContent?: string
  simulation?: SimulationResponse | null
}

export function PreviewPanel({ circuitId, svgContent, simulation }: PreviewPanelProps) {
  const [zoom, setZoom] = useState(0.75)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [isLoading, setIsLoading] = useState(false)
  const [svgscreen, setScreen] = useState<"circuit" | "analysis">("circuit")
  const svgContainerRef = useRef<HTMLDivElement>(null)
  const svgRef = useRef<HTMLDivElement>(null)

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 0) {
      setIsDragging(true)
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y })
    }
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      })
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault()
    const direction = e.deltaY > 0 ? 0.9 : 1.1
    setZoom((prev) => Math.max(0.5, Math.min(3, prev * direction)))
  }

  const resetView = () => {
    setZoom(1)
    setPan({ x: 0, y: 0 })
  }

  return (
    <div className="flex h-full flex-col bg-transparent">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-2">
        {svgscreen === "circuit" ? (
          <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setZoom((z) => Math.min(3, z + 0.2))}
            className="h-8 w-8 p-0"
          >
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setZoom((z) => Math.max(0.5, z - 0.2))}
            className="h-8 w-8 p-0"
          >
            <ZoomOut className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={resetView}
            className="h-8 w-8 p-0"
          >
            <span className="text-xs font-bold">1:1</span>
          </Button>
          </div>
        ) : (
          <div />
        )}
        <div>
          <Button
           variant="outline"
           size="sm"
           className="border-orange-400/60 bg-orange-400/10 text-orange-900 hover:bg-orange-400/20 dark:text-orange-100"
           onClick={() =>
             setScreen((prev) => (prev === "circuit" ? "analysis" : "circuit"))
           }
          >
          {svgscreen === "circuit" ? (
            <Pencil className="h-2 w-2  " />
          ) : (
            <CircuitBoard className="h-2 w-2  " />
          )}
          <span className="text-xs font-bold">
            {svgscreen === "circuit" ? "Analysis" : "Circuit"}
          </span>
          </Button>
        </div>
      </div>

      {/* SVG Viewer */}
      {svgscreen === "circuit" ? 
      <div
        ref={svgContainerRef}
        className="flex-1 overflow-hidden bg-transparent relative"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
        style={{ cursor: isDragging ? "grabbing" : "grab" }}
        id="svg-container"
      >
        {isLoading ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">Loading circuit {circuitId}...</p>
            </div>
          </div>
        ) : svgContent ? (
          <div
            style={{
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              transformOrigin: "top left",
              transition: isDragging ? "none" : "transform 0.2s ease-out",
              cursor: "inherit",
              width: "max-content",
              height: "max-content",
              minWidth: "100%",
              minHeight: "100%",
              padding: "24px",
            }}
          >
            <div
              ref={svgRef}
              style={{
                display: "block",
                width: "max-content",
                height: "max-content",
                background: "transparent",
              }}
              dangerouslySetInnerHTML={{
                __html: svgContent,
              }}
            />
          </div>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <CircuitBoard className="h-12 w-12 text-muted-foreground/30 mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">No circuit diagram available</p>
              <p className="text-xs text-muted-foreground mt-1">Load a circuit to view SVG</p>
            </div>
          </div>
        )}
      </div> : <AnalysisPanel simulation={simulation} />}

      {/* Footer */}
      <div className="flex items-center justify-between border-t border-border px-4 py-2">
        <span className="text-xs text-muted-foreground">Zoom: {(zoom * 100).toFixed(0)}%</span>
        <div className="flex items-center gap-2">
          <ExportPopup 
          circuitId={circuitId}
          />
        </div>
      </div>
    </div>
  )
}

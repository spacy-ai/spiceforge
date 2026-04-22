"use client"

import { Suspense, useEffect, useState, useRef } from "react"
import { useSearchParams } from "next/navigation"
import { Header } from "@/components/custom/header"
import { CodePanel } from "@/components/custom/code-panel"
import { PreviewPanel } from "@/components/custom/preview-panel"
import { ChatPanel } from "@/components/custom/chat-panel"
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable"
import { apiBase } from "@/lib/config"
import type { SimulationResponse } from "@/lib/types/simulation"
import type { ImperativePanelHandle } from "react-resizable-panels"

interface CircuitData {
  id: number
  name: string
  netlist: string
  svgContent: string
}

function DashboardContent() {
  const searchParams = useSearchParams()
  const [showCode, setShowCode] = useState(true)
  const [showChat, setShowChat] = useState(true)
  const [circuitId, setCircuitId] = useState<string>("1")
  const [circuitData, setCircuitData] = useState<CircuitData | null>(null)
  const [loading, setLoading] = useState(false)
  const [netlist, setNetlist] = useState("")
  const [simulation, setSimulation] = useState<SimulationResponse | null>(null)
  const codePanelRef = useRef<ImperativePanelHandle>(null)
  const chatPanelRef = useRef<ImperativePanelHandle>(null)

  useEffect(() => {
    if (!searchParams) return
    
    const id = searchParams.get("circuitid") || "1"
    
    setCircuitId(id)
    setLoading(true)
    
    const fetchCircuit = async () => {
      try {
        const [circuitResponse, svgResponse] = await Promise.all([
          fetch(`${apiBase}/circuits/${id}`),
          fetch(`${apiBase}/circuits/${id}/svg?renderer=interactive`),
        ])

        if (!circuitResponse.ok || !svgResponse.ok) {
          throw new Error(`Failed to load circuit ${id}`)
        }

        const circuitJson = await circuitResponse.json()
        const svgText = await svgResponse.text()

        const data: CircuitData = {
          id: circuitJson.id,
          name: circuitJson.name ?? `Circuit ${circuitJson.id}`,
          netlist: circuitJson.netlist,
          svgContent: svgText,
        }

        setCircuitData(data)
        setNetlist(data.netlist)
      } catch (error) {
        console.error("Failed to load circuit:", error)
        setCircuitData(null)
        setNetlist("")
      } finally {
        setLoading(false)
      }
    }
    
    fetchCircuit()
  }, [searchParams, apiBase])

  const toggleCode = () => setShowCode((prev) => !prev)
  const toggleChat = () => setShowChat((prev) => !prev)

  useEffect(() => {
    if (!codePanelRef.current) return
    if (showCode) {
      codePanelRef.current.expand()
    } else {
      codePanelRef.current.collapse()
    }
  }, [showCode])

  useEffect(() => {
    if (!chatPanelRef.current) return
    if (showChat) {
      chatPanelRef.current.expand()
    } else {
      chatPanelRef.current.collapse()
    }
  }, [showChat])

  const handleSimulate = (
    updatedNetlist: string,
    updatedSvg?: string,
    simulationResponse?: SimulationResponse,
  ) => {
    setNetlist(updatedNetlist)
    if (simulationResponse) {
      setSimulation(simulationResponse)
    }

    if (circuitData) {
      setCircuitData({
        ...circuitData,
        netlist: updatedNetlist,
        svgContent: updatedSvg ?? circuitData.svgContent,
      })
    }
  }

  return (
    <div className="flex h-screen w-screen flex-col bg-background">
      <Header 
        showCode={showCode}
        showChat={showChat}
        onToggleCode={toggleCode}
        onToggleChat={toggleChat}
      />
      
      <ResizablePanelGroup
        direction="horizontal"
        className="flex-1"
      >
        <ResizablePanel
          id="code-panel"
          order={1}
          defaultSize={25}
          minSize={15}
          maxSize={40}
          collapsible
          collapsedSize={0}
          ref={codePanelRef}
          key={`code-${circuitId}`}
        >
          <CodePanel key={`netlist-${circuitId}`} onSimulate={handleSimulate} initialNetlist={netlist} circuitId={circuitId} />
        </ResizablePanel>

        <ResizableHandle
          withHandle
          className={showCode ? "bg-border hover:bg-primary/50 transition-colors" : "bg-border opacity-0 pointer-events-none"}
        />

        <ResizablePanel
          id="preview-panel"
          order={2}
          defaultSize={50}
          minSize={30}
          key={`preview-${circuitId}`}
        >
          <PreviewPanel
            key={`svg-${circuitId}`}
            circuitId={circuitId}
            svgContent={circuitData?.svgContent}
            simulation={simulation}
          />
        </ResizablePanel>

        <ResizableHandle
          withHandle
          className={showChat ? "bg-border hover:bg-primary/50 transition-colors" : "bg-border opacity-0 pointer-events-none"}
        />

        <ResizablePanel
          id="chat-panel"
          order={3}
          defaultSize={25}
          minSize={20}
          maxSize={40}
          collapsible
          collapsedSize={0}
          ref={chatPanelRef}
        >
          <ChatPanel />
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  )
}

export default function SpacyAIPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen w-screen items-center justify-center bg-background text-sm text-muted-foreground">
          Loading dashboard...
        </div>
      }
    >
      <DashboardContent />
    </Suspense>
  )
}

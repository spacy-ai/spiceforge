"use client"

import { useState } from "react"
import { Header } from "@/components/custom/header"
import { CodePanel } from "@/components/custom/code-panel"
import { PreviewPanel } from "@/components/custom/preview-panel"
import { ChatPanel } from "@/components/custom/chat-panel"
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable"

export default function SpacyAIPage() {
  const [showCode, setShowCode] = useState(true)
  const [showChat, setShowChat] = useState(true)

  const toggleCode = () => setShowCode(!showCode)
  const toggleChat = () => setShowChat(!showChat)
  const getPreviewSize = () => {
    if (!showCode && !showChat) return 100
    if (!showCode || !showChat) return 70
    return 50
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
        {showCode && (
          <>
            <ResizablePanel 
              defaultSize={25} 
              minSize={15}
              maxSize={40}
            >
              <CodePanel />
            </ResizablePanel>
            
            <ResizableHandle withHandle className="bg-border hover:bg-primary/50 transition-colors" />
          </>
        )}
        
        <ResizablePanel 
          defaultSize={getPreviewSize()} 
          minSize={30}
        >
          <PreviewPanel />
        </ResizablePanel>
        
        {showChat && (
          <>
            <ResizableHandle withHandle className="bg-border hover:bg-primary/50 transition-colors" />
            
            <ResizablePanel 
              defaultSize={25} 
              minSize={20}
              maxSize={40}
            >
              <ChatPanel />
            </ResizablePanel>
          </>
        )}
      </ResizablePanelGroup>
    </div>
  )
}

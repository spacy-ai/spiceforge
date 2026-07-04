// app/circuit/page.tsx (or wherever DashboardContent is located)

'use client';

import { Suspense, useEffect, useState, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Header } from '@/components/custom/header';
import { CodePanel } from '@/components/custom/code-panel';
import { PreviewPanel } from '@/components/custom/preview-panel';
import { ChatPanel } from '@/components/custom/chat-panel';
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '@/components/ui/resizable';
import { apiBase } from '@/lib/config';
import type { SimulationResponse } from '@/lib/types/simulation';
import type { ImperativePanelHandle } from 'react-resizable-panels';
import { toast } from 'sonner';

interface CircuitData {
  id: number;
  name: string;
  netlist: string;
}

function DashboardContent() {
  const searchParams = useSearchParams();
  const [showCode, setShowCode] = useState(true);
  const [showChat, setShowChat] = useState(true);
  const [circuitId, setCircuitId] = useState<string | null>(null);
  const [circuitData, setCircuitData] = useState<CircuitData | null>(null);
  const [loading, setLoading] = useState(false);
  const [netlist, setNetlist] = useState('');
  const [simulation, setSimulation] = useState<SimulationResponse | null>(null);
  const [svgExportUrl, setSvgExportUrl] = useState<string | null>(null);
  const [previewKey, setPreviewKey] = useState(0);
  const router = useRouter();
  const codePanelRef = useRef<ImperativePanelHandle>(null);
  const chatPanelRef = useRef<ImperativePanelHandle>(null);


  useEffect(() => {
    if (!searchParams) return;


    const resolveCircuit = async () => {
      const idParam = searchParams.get('circuitid');
      if (!idParam) {
        setCircuitId(null);
        setCircuitData(null);
        setNetlist('.title New Circuit\n\n.control\nop\n.endc\n.end');
        setSvgExportUrl(null);
        return;
      }

      const id = idParam;
      setCircuitId(id);
      setLoading(true);

      try {
        const circuitResponse = await fetch(`${apiBase}/circuits/${id}`);

        if (!circuitResponse.ok) {
          throw new Error(`Failed to load circuit ${id}`);
        }

        const circuitJson = await circuitResponse.json();

        const data: CircuitData = {
          id: circuitJson.id,
          name: circuitJson.name ?? `Circuit ${circuitJson.id}`,
          netlist: circuitJson.netlist,
        };

        setCircuitData(data);
        setNetlist(data.netlist);
        
        // Update the heading in ChatPanel (optional - ChatPanel loads it itself)
        // The ChatPanel already loads the name from the database, so no need to pass it
        
        // Generate SVG export for this circuit
        await generateSvgExport(id, data.netlist);
        
      } catch (error) {
        console.error('Failed to load circuit:', error);
        setCircuitData(null);
        setNetlist('');
        setSvgExportUrl(null);
        toast.error('Failed to load circuit', { position: 'top-right' });
      } finally {
        setLoading(false);
      }
    };

    resolveCircuit();
  }, [searchParams, apiBase, router]);

  const generateSvgExport = async (id: string, netlistContent: string) => {
    try {
      const response = await fetch(`${apiBase}/export/svg`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          circuit_id: parseInt(id),
          netlist: netlistContent,
          format: 'interactive',
          highlight_color: '#ffeb3b',
          highlight_opacity: 0.8,
          hover_stroke_width: 2,
        }),
      });

      if (!response.ok) throw new Error(`Failed to generate SVG export: ${response.status}`);

      const data = await response.json();
      
      if (data.status === 'success' && data.export_id) {
        await new Promise(resolve => setTimeout(resolve, 200));
        setSvgExportUrl(`${apiBase}/export/svg/${data.export_id}`);
        setPreviewKey(prev => prev + 1);
      } else {
        throw new Error('Export failed - invalid response');
      }
    } catch (error) {
      console.error('Failed to generate SVG export:', error);
      setSvgExportUrl(null);
      toast.error('Failed to render circuit diagram', { position: 'top-right' });
    }
  };

  const toggleCode = () => setShowCode((prev) => !prev);
  const toggleChat = () => setShowChat((prev) => !prev);

  useEffect(() => {
    if (!codePanelRef.current) return;
    if (showCode) {
      codePanelRef.current.expand();
    } else {
      codePanelRef.current.collapse();
    }
  }, [showCode]);

  useEffect(() => {
    if (!chatPanelRef.current) return;
    if (showChat) {
      chatPanelRef.current.expand();
    } else {
      chatPanelRef.current.collapse();
    }
  }, [showChat]);

  const saveCircuit = async (updatedNetlist: string) => {
    try {
      if (!circuitId) {
        const createRes = await fetch('/api/circuits', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            name: 'Untitled Project',
            netlist: updatedNetlist,
          }),
        });

        if (!createRes.ok) {
          console.error('Failed to create circuit', createRes.status);
          return;
        }

        const created = (await createRes.json()) as { id: number };
        setCircuitId(String(created.id));
        router.replace(`/circuit?circuitid=${created.id}`);
        toast.success('New project created', { position: 'top-right' });
        return;
      }

      const res = await fetch(`/api/circuits/${circuitId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ netlist: updatedNetlist }),
      });

      if (!res.ok) {
        console.error('Failed to save circuit', res.status);
      }
    } catch (error) {
      console.error('Failed to save circuit', error);
    }
  };

   // In your DashboardContent, update the runSimulation function:

const runSimulation = async (netlistToSimulate: string) => {
  try {
    setNetlist(netlistToSimulate);
    
    let currentCircuitId = circuitId;
    
    if (!currentCircuitId) {
      const createRes = await fetch('/api/circuits', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: 'Untitled Project',
          netlist: netlistToSimulate,
        }),
      });

      if (!createRes.ok) throw new Error('Failed to create circuit');

      const created = (await createRes.json()) as { id: number };
      currentCircuitId = String(created.id);
      setCircuitId(currentCircuitId);
      router.replace(`/circuit?circuitid=${currentCircuitId}`);
      await new Promise(resolve => setTimeout(resolve, 100));
    } else {
      await saveCircuit(netlistToSimulate);
    }

    const response = await fetch(`${apiBase}/simulate/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        netlist: netlistToSimulate,
        options: { include_schematic: true },
      }),
    });

    if (!response.ok) throw new Error(`Simulation failed`);

    const data = await response.json();
    setSimulation(data);

    if (currentCircuitId) {
      await generateSvgExport(currentCircuitId, netlistToSimulate);
    }

    return data;
  } catch (err) {
    console.error(err);
    throw err;
  }
};

  const onNetlistGenerated = async (
    generatedNetlist: string
  ) => {
    setNetlist(generatedNetlist);

    await runSimulation(generatedNetlist);
  };

  const onCircuitCreated = (newCircuitId: number) => {
    setCircuitId(String(newCircuitId));
    router.replace(`/circuit?circuitid=${newCircuitId}`);
  };

  return (
    <div className="bg-background flex h-screen w-screen flex-col">
      <Header
        showCode={showCode}
        showChat={showChat}
        onToggleCode={toggleCode}
        onToggleChat={toggleChat}
        currentCircuitId={circuitId}
      />

      <ResizablePanelGroup direction="horizontal" className="flex-1">
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
          <CodePanel
            key={`netlist-${circuitId}`}
            onSimulate={runSimulation}
            netlist={netlist}
            onNetlistChange={setNetlist}
            circuitId={circuitId}
          />
        </ResizablePanel>

        <ResizableHandle
          withHandle
          className={
            showCode
              ? 'bg-border hover:bg-primary/50 transition-colors'
              : 'bg-border pointer-events-none opacity-0'
          }
        />

        <ResizablePanel
          id="preview-panel"
          order={2}
          defaultSize={50}
          minSize={30}
          key={`preview-${circuitId}`}
        >
          <PreviewPanel
            key={`preview-${circuitId}-${previewKey}`}
            circuitId={circuitId}
            svgExportUrl={svgExportUrl}
            simulation={simulation}
            onRefreshExport={async () => {
              if (circuitId && netlist) {
                await generateSvgExport(circuitId, netlist);
              }
            }}
          />
        </ResizablePanel>

        <ResizableHandle
          withHandle
          className={
            showChat
              ? 'bg-border hover:bg-primary/50 transition-colors'
              : 'bg-border pointer-events-none opacity-0'
          }
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

          <ChatPanel
            onNetlistGenerated={onNetlistGenerated}
            onCircuitCreated={onCircuitCreated}
            circuitId={circuitId}  
          />

        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}

export default function SpacyAIPage() {
  return (
    <Suspense
      fallback={
        <div className="bg-background text-muted-foreground flex h-screen w-screen items-center justify-center text-sm">
          Loading dashboard...
        </div>
      }
    >
      <DashboardContent />
    </Suspense>
  );
}
'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import {
  CircuitBoard,
  Pencil,
  ZoomIn,
  ZoomOut,
  RefreshCw,
} from 'lucide-react';
import { ExportPopup } from '@/components/custom/exportPopup';
import { AnalysisPanel } from '@/components/custom/analysis-panel';
import type { SimulationResponse } from '@/lib/types/simulation';

interface PreviewPanelProps {
  circuitId?: string;
  svgExportUrl?: string | null;
  simulation?: SimulationResponse | null;
  onRefreshExport?: () => Promise<void>;
}

export function PreviewPanel({
  circuitId,
  svgExportUrl,
  simulation,
  onRefreshExport,
}: PreviewPanelProps) {
  const [zoom, setZoom] = useState(0.75);
  const [pan, setPan] = useState({ x: 0, y: 0 });

  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const [isLoading, setIsLoading] = useState(false);
  const [svgContent, setSvgContent] = useState<string | null>(null);

  const [svgscreen, setScreen] = useState<'circuit' | 'analysis'>(
    'circuit'
  );

  const svgContainerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<HTMLDivElement>(null);

  // Load SVG from export URL
  useEffect(() => {
    const loadSvg = async () => {
      if (!svgExportUrl) {
        setSvgContent(null);
        return;
      }

      setIsLoading(true);

      try {
        const response = await fetch(svgExportUrl);

        if (!response.ok) {
          throw new Error(`Failed to load SVG: ${response.status}`);
        }

        const svgText = await response.text();
        setSvgContent(svgText);
      } catch (error) {
        console.error('Failed to load SVG:', error);
        setSvgContent(null);
      } finally {
        setIsLoading(false);
      }
    };

    loadSvg();
  }, [svgExportUrl]);

  // Center the SVG when it loads or when zoom changes
  useEffect(() => {
    if (!svgContent || !svgRef.current || !svgContainerRef.current) return;

    // Small delay to ensure DOM is fully rendered
    const timer = setTimeout(() => {
      const container = svgContainerRef.current;
      const svgElement = svgRef.current;

      if (container && svgElement) {
        const containerRect = container.getBoundingClientRect();
        const svgRect = svgElement.getBoundingClientRect();
        
        // Calculate center position
        const centerX = (containerRect.width - svgRect.width * zoom) / 2;
        const centerY = (containerRect.height - svgRect.height * zoom) / 2;
        
        setPan({
          x: Math.max(centerX, 0),
          y: Math.max(centerY, 0),
        });
      }
    }, 100);

    return () => clearTimeout(timer);
  }, [svgContent, zoom]);

  // Also center when window resizes
  useEffect(() => {
    const handleResize = () => {
      if (!svgContent || !svgRef.current || !svgContainerRef.current) return;
      
      const container = svgContainerRef.current;
      const svgElement = svgRef.current;
      
      if (container && svgElement) {
        const containerRect = container.getBoundingClientRect();
        const svgRect = svgElement.getBoundingClientRect();
        
        const centerX = (containerRect.width - svgRect.width * zoom) / 2;
        const centerY = (containerRect.height - svgRect.height * zoom) / 2;
        
        setPan({
          x: Math.max(centerX, 0),
          y: Math.max(centerY, 0),
        });
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [svgContent, zoom]);

  const handleRefresh = async () => {
    if (!onRefreshExport) return;

    setIsLoading(true);

    try {
      await onRefreshExport();
    } finally {
      setIsLoading(false);
    }
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return;

    setIsDragging(true);

    setDragStart({
      x: e.clientX - pan.x,
      y: e.clientY - pan.y,
    });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;

    setPan({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();

    const direction = e.deltaY > 0 ? 0.9 : 1.1;

    setZoom((prev) =>
      Math.max(0.5, Math.min(3, prev * direction))
    );
  };

  const resetView = () => {
    setZoom(0.75);
    // Reset will trigger the centering useEffect
  };

  return (
    <div className="flex h-full flex-col bg-transparent">
      {/* Header */}
      <div className="border-border flex items-center justify-between border-b px-4 py-2">
        {svgscreen === 'circuit' ? (
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() =>
                setZoom((z) => Math.min(3, z + 0.2))
              }
              className="h-8 w-8 p-0"
            >
              <ZoomIn className="h-4 w-4" />
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={() =>
                setZoom((z) => Math.max(0.5, z - 0.2))
              }
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

            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefresh}
              className="h-8 w-8 p-0"
            >
              <RefreshCw
                className={`h-4 w-4 ${
                  isLoading ? 'animate-spin' : ''
                }`}
              />
            </Button>
          </div>
        ) : (
          <div />
        )}

        <Button
          variant="outline"
          size="sm"
          className="border-orange-400/60 bg-orange-400/10 text-orange-900 hover:bg-orange-400/20 dark:text-orange-100"
          onClick={() =>
            setScreen((prev) =>
              prev === 'circuit' ? 'analysis' : 'circuit'
            )
          }
        >
          {svgscreen === 'circuit' ? (
            <Pencil className="h-2 w-2" />
          ) : (
            <CircuitBoard className="h-2 w-2" />
          )}

          <span className="text-xs font-bold">
            {svgscreen === 'circuit'
              ? 'Analysis'
              : 'Circuit'}
          </span>
        </Button>
      </div>

      {/* Circuit Viewer */}
      {svgscreen === 'circuit' ? (
        <div
          ref={svgContainerRef}
          id="svg-container"
          className="relative flex-1 overflow-hidden bg-transparent"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onWheel={handleWheel}
          style={{
            cursor: isDragging ? 'grabbing' : 'grab',
          }}
        >
          {isLoading ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="border-primary mx-auto mb-2 h-8 w-8 animate-spin rounded-full border-2 border-t-transparent" />
                <p className="text-muted-foreground text-sm">
                  Loading circuit {circuitId}...
                </p>
              </div>
            </div>
          ) : svgContent ? (
            <div
              style={{
                transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                transformOrigin: 'top left',
                transition: isDragging
                  ? 'none'
                  : 'transform 0.2s ease-out',
                width: 'max-content',
                height: 'max-content',
                minWidth: '100%',
                minHeight: '100%',
                padding: '24px',
              }}
            >
              <div
                ref={svgRef}
                style={{
                  display: 'block',
                  width: 'max-content',
                  height: 'max-content',
                  background: 'transparent',
                }}
                dangerouslySetInnerHTML={{
                  __html: svgContent,
                }}
              />
            </div>
          ) : (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <CircuitBoard className="text-muted-foreground/30 mx-auto mb-2 h-12 w-12" />

                <p className="text-muted-foreground text-sm">
                  No circuit diagram available
                </p>

                <p className="text-muted-foreground mt-1 text-xs">
                  Generate/export a circuit first
                </p>
              </div>
            </div>
          )}
        </div>
      ) : (
        <AnalysisPanel simulation={simulation} />
      )}

      {/* Footer */}
      <div className="border-border flex items-center justify-between border-t px-4 py-2">
        <span className="text-muted-foreground text-xs">
          Zoom: {(zoom * 100).toFixed(0)}%
        </span>

        <ExportPopup circuitId={circuitId} />
      </div>
    </div>
  );
}
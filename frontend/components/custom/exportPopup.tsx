'use client';

import { Download } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogClose,
} from '@/components/ui/dialog';
import { useState } from 'react';
import { apiBase } from '@/lib/config';

interface exportPopupProps {
  circuitId?: string;
}

export function ExportPopup({ circuitId }: exportPopupProps) {
  const [target, setTarget] = useState<'image' | 'kicad' | 'report'>('image');

  const handleExport = async () => {
    if (!circuitId) return;
    if (target === 'image') {
      const url = `${apiBase}/circuits/${encodeURIComponent(circuitId)}/png/download`;
      window.location.href = url;
      return;
    }
    if (target === 'kicad') {
      const circuitIdNumber = Number(circuitId);
      if (Number.isNaN(circuitIdNumber)) return;
      const response = await fetch(`${apiBase}/export/kicad`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          circuit_id: circuitIdNumber,
        }),
      });
      if (!response.ok) {
        console.error('Failed to export KiCad', response.status);
        return;
      }
      const data = await response.json();
      if (data?.download_url) {
        window.location.href = data.download_url;
      }
    }
  };
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="border-sidebar-border text-sidebar-foreground hover:bg-sidebar-accent gap-2"
        >
          <Download className="h-4 w-4" />
          Export
        </Button>
      </DialogTrigger>
      <DialogContent className="w-[calc(100%-2rem)] max-w-[calc(100%-2rem)] sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Export project</DialogTitle>
          <DialogDescription>Choose a format to download your current workspace.</DialogDescription>
        </DialogHeader>
        <div className="grid gap-3">
          <Button
            variant="secondary"
            className={`border-border bg-secondary hover:bg-secondary/90 h-auto w-full items-start justify-between rounded-lg border border-l-4 px-3 py-3 text-left transition-colors sm:px-4 ${
              target === 'image' ? 'border-l-primary border-primary/70' : 'border-l-transparent'
            }`}
            onClick={() => setTarget('image')}
          >
            <div className="flex w-full flex-col items-start gap-1 text-left">
              <div className="flex w-1/2 flex-col items-start gap-1 sm:w-full sm:flex-row sm:items-center sm:justify-between sm:gap-3">
                <p className="text-sm font-medium sm:text-base">Download Image</p>
                <span className="text-muted-foreground text-xs sm:text-sm">.png</span>
              </div>
              <p className="text-muted-foreground text-xs sm:text-sm">
                High resolution image of the circuit diagram
              </p>
            </div>
          </Button>

          <Button
            variant="secondary"
            className={`border-border bg-secondary hover:bg-secondary/90 h-auto w-full items-start justify-between rounded-lg border border-l-4 px-3 py-3 text-left transition-colors sm:px-4 ${
              target === 'kicad' ? 'border-l-primary border-primary/70' : 'border-l-transparent'
            }`}
            onClick={() => setTarget('kicad')}
          >
            <div className="flex w-full flex-col items-start gap-1 text-left">
              <div className="flex w-1/2 flex-col items-start gap-1 sm:w-full sm:flex-row sm:items-center sm:justify-between sm:gap-3">
                <p className="text-sm font-medium sm:text-base">Download KiCad</p>
                <span className="text-muted-foreground text-xs sm:text-sm">.zip</span>
              </div>
              <p className="text-muted-foreground text-xs sm:text-sm">
                KiCad schematic file compatible with KiCad 7.0 and above
              </p>
            </div>
          </Button>

          <Button
            variant="secondary"
            className={`border-border bg-secondary hover:bg-secondary/90 h-auto w-full items-start justify-between rounded-lg border border-l-4 px-3 py-3 text-left transition-colors sm:px-4 ${
              target === 'report' ? 'border-l-primary border-primary/70' : 'border-l-transparent'
            }`}
            onClick={() => setTarget('report')}
          >
            <div className="flex flex-col items-start gap-1 text-left sm:w-full">
              <div className="flex w-1/2 w-full flex-col items-start gap-1 sm:flex-row sm:items-center sm:justify-between sm:gap-3">
                <p className="text-sm font-medium sm:text-base">Download Report</p>
                <span className="text-muted-foreground text-xs sm:text-sm">.pdf</span>
              </div>
              <p className="text-muted-foreground text-xs sm:text-sm">
                Comprehensive report of the circuit diagram
              </p>
            </div>
          </Button>
        </div>
        <DialogFooter className="flex-col-reverse gap-2 sm:flex-row sm:gap-3">
          <DialogClose asChild>
            <Button variant="ghost" className="w-full sm:w-auto">
              Cancel
            </Button>
          </DialogClose>
          <Button className="w-full sm:w-auto" onClick={handleExport}>
            Start export
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

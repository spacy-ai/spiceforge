'use client';

import { useMemo, useState } from 'react';
import { FolderOpen, Plus, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from '@/components/ui/drawer';
import { Input } from '@/components/ui/input';
import { useRouter } from 'next/navigation';
import { VisuallyHidden } from '@radix-ui/react-visually-hidden';
import { Eye } from 'lucide-react';

type CircuitListItem = {
  id: number;
  name: string | null;
  created_at: string;
  updated_at: string;
};

const formatDate = (value: string) => {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return 'Unknown';
  }
  return new Intl.DateTimeFormat('en', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(parsed);
};

export function ProjectDrawer({ currentCircuitId }: { currentCircuitId?: string | null }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [circuits, setCircuits] = useState<CircuitListItem[]>([]);

  const loadCircuits = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch('/api/circuits');
      if (!res.ok) {
        throw new Error('Failed to load projects');
      }
      const data = (await res.json()) as CircuitListItem[];
      setCircuits(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projects');
    } finally {
      setIsLoading(false);
    }
  };

  const filteredCircuits = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) {
      return circuits;
    }
    return circuits.filter((circuit) => {
      const name = circuit.name ?? '';
      return name.toLowerCase().includes(normalized);
    });
  }, [circuits, query]);

  const handleCreateProject = () => {
    setError(null);
    setOpen(false);
    router.push('/circuit');
  };

  return (
    <Drawer
      open={open}
      onOpenChange={(nextOpen) => {
        setOpen(nextOpen);
        if (nextOpen && !isLoading) {
          void loadCircuits();
        }
      }}
    >
      <DrawerTrigger asChild>
        <Button variant="outline" className="gap-2">
          <FolderOpen className="h-4 w-4" />
          <span className="hidden lg:inline">Projects</span>
        </Button>
      </DrawerTrigger>
      <DrawerContent className="max-h-[70vh] sm:max-h-[85vh]">
        <div className="mx-auto w-full max-w-5xl">
          <DrawerHeader>
            <VisuallyHidden>
              <DrawerTitle>Project Drawer</DrawerTitle>
            </VisuallyHidden>
            <DrawerDescription>Browse your saved circuits.</DrawerDescription>
          </DrawerHeader>

          <div className="px-4 pb-4">
            <div className="relative">
              <Search className="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2" />
              <Input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search circuits"
                className="pl-9"
              />
            </div>
          </div>

          <div className="px-4 pb-6">
            <div className="scrollbar-hidden grid max-h-[45vh] grid-cols-2 gap-4 overflow-y-auto pr-1 sm:grid-cols-3 md:grid-cols-4">
              <button
                type="button"
                onClick={handleCreateProject}
                className="border-border bg-card hover:bg-muted flex aspect-square flex-col items-center justify-center gap-3 rounded-lg border border-dashed p-3 text-sm font-semibold transition-colors"
              >
                <Plus className="h-5 w-5" />
                New Project
              </button>

              {filteredCircuits.map((circuit) => (
                <div
                  key={circuit.id}
                  className="border-border bg-card flex aspect-square flex-col justify-between rounded-lg border p-3 transition-colors hover:ring-1 hover:ring-orange-400/50"
                >
                  <div className="text-sm font-semibold">
                    {circuit.name?.trim() || `Circuit ${circuit.id}`}
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="text-muted-foreground text-xs">
                      Updated {formatDate(circuit.updated_at || circuit.created_at)}
                    </div>
                    <Button
                      size="icon"
                      className="bg-primary text-primary-foreground hover:bg-primary/80 shrink-0 sm:h-7 sm:w-7"
                      onClick={() => {
                        setOpen(false);
                        router.push(`/circuit?circuitid=${circuit.id}`);
                      }}
                    >
                      <Eye className="h-2 w-2 sm:h-5 sm:w-5" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>

            {isLoading ? (
              <div className="text-muted-foreground mt-3 text-sm">Loading projects...</div>
            ) : error ? (
              <div className="text-destructive mt-3 text-sm">{error}</div>
            ) : filteredCircuits.length === 0 ? (
              <div className="text-muted-foreground mt-3 text-sm">No projects found yet.</div>
            ) : null}
          </div>

          <DrawerFooter>
            <DrawerClose asChild>
              <Button variant="outline">Close</Button>
            </DrawerClose>
          </DrawerFooter>
        </div>
      </DrawerContent>
    </Drawer>
  );
}

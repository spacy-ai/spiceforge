'use client';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Sparkles, Sun, Moon } from 'lucide-react';
import { useTheme } from 'next-themes';
import Link from 'next/link';
import { UserMenu } from '@/components/custom/user-menu';
import { ProjectDrawer } from '@/components/custom/project-drawer';

interface HeaderProps {
  showCode: boolean;
  showChat: boolean;
  onToggleCode: () => void;
  onToggleChat: () => void;
  currentCircuitId?: string | null;
}

export function Header({
  showCode,
  showChat,
  onToggleCode,
  onToggleChat,
  currentCircuitId,
}: HeaderProps) {
  const { theme, setTheme } = useTheme();

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  return (
    <header className="border-border bg-card flex h-14 items-center justify-between border-b px-4">
      <Link href="/dashboard" className="hidden items-center gap-3 sm:flex">
        <div className="flex items-center gap-2">
          <div className="bg-primary flex h-8 w-8 items-center justify-center rounded-full">
            <Sparkles className="text-primary-foreground h-4 w-4" />
          </div>
          <span className="text-card-foreground text-lg font-semibold">Spacy AI</span>
        </div>
        <Badge variant="secondary" className="text-xs">
          BETA
        </Badge>
      </Link>

      <nav className="flex flex-1 items-center justify-center gap-2 sm:flex-none sm:justify-start">
        <Button
          onClick={onToggleCode}
          className={
            showCode
              ? 'bg-emerald-600 text-white hover:bg-emerald-700'
              : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
          }
        >
          Netlist
        </Button>
        <Button
          onClick={onToggleChat}
          className={
            showChat
              ? 'bg-primary text-primary-foreground hover:bg-primary/90'
              : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
          }
        >
          Chat
        </Button>
      </nav>

      {/* Right actions - hidden on very small screens */}
      <div className="hidden items-center gap-3 sm:flex">
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          className="text-muted-foreground hover:text-foreground"
        >
          <Sun className="h-5 w-5 scale-100 rotate-0 transition-all dark:scale-0 dark:-rotate-90" />
          <Moon className="absolute h-5 w-5 scale-0 rotate-90 transition-all dark:scale-100 dark:rotate-0" />
          <span className="sr-only">Toggle theme</span>
        </Button>
        <ProjectDrawer currentCircuitId={currentCircuitId} />
        <UserMenu />
      </div>
    </header>
  );
}

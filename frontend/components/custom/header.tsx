"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Sparkles, Plus, Sun, Moon } from "lucide-react"
import { useTheme } from "next-themes"

interface HeaderProps {
  showCode: boolean
  showChat: boolean
  onToggleCode: () => void
  onToggleChat: () => void
}

export function Header({ showCode, showChat, onToggleCode, onToggleChat }: HeaderProps) {
  const { theme, setTheme } = useTheme()

  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark")
  }

  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-card px-4">
      {/* Logo - hidden on very small screens */}
      <div className="hidden items-center gap-3 sm:flex">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary">
            <Sparkles className="h-4 w-4 text-primary-foreground" />
          </div>
          <span className="text-lg font-semibold text-card-foreground">Spacy AI</span>
        </div>
        <Badge variant="secondary" className="text-xs">
          BETA
        </Badge>
      </div>

      {/* Navigation - centered on small screens */}
      <nav className="flex flex-1 items-center justify-center gap-2 sm:flex-none sm:justify-start">
        <Button variant="ghost" className="text-muted-foreground hover:text-foreground">
          Projects
        </Button>
        <Button 
          onClick={onToggleCode}
          className={showCode 
            ? "bg-emerald-600 text-white hover:bg-emerald-700" 
            : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
          }
        >
          Netlist
        </Button>
        <Button 
          onClick={onToggleChat}
          className={showChat 
            ? "bg-primary text-primary-foreground hover:bg-primary/90" 
            : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
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
          <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          <span className="sr-only">Toggle theme</span>
        </Button>
        <Button className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90">
          <Plus className="h-4 w-4" />
          <span className="hidden lg:inline">New Project</span>
        </Button>
      </div>
    </header>
  )
}

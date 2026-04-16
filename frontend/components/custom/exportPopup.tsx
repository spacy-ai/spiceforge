"use client"

import { Download } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
	DialogTrigger,
} from "@/components/ui/dialog"

export function ExportPopup() {
	return (
		<Dialog>
			<DialogTrigger asChild>
				<Button
					variant="outline"
					size="sm"
					className="gap-2 border-sidebar-border text-sidebar-foreground hover:bg-sidebar-accent"
				>
					<Download className="h-4 w-4" />
					Export
				</Button>
			</DialogTrigger>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>Export project</DialogTitle>
					<DialogDescription>
						Choose a format to download your current workspace.
					</DialogDescription>
				</DialogHeader>
				<div className="grid gap-3">
					<Button variant="secondary" className="justify-between">
						PNG preview
						<span className="text-xs text-muted-foreground">.png</span>
					</Button>
					<Button variant="secondary" className="justify-between">
						Source bundle
						<span className="text-xs text-muted-foreground">.zip</span>
					</Button>
					<Button variant="secondary" className="justify-between">
						Report
						<span className="text-xs text-muted-foreground">.pdf</span>
					</Button>
				</div>
				<DialogFooter>
					<Button variant="ghost">Cancel</Button>
					<Button>Start export</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	)
}

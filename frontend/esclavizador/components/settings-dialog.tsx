"use client"

import { Sparkles } from "lucide-react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"

interface SettingsDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function SettingsDialog({ open, onOpenChange }: SettingsDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            Settings
          </DialogTitle>
        </DialogHeader>
        <div className="py-8 text-center space-y-4">
          <div className="flex justify-center">
            <Sparkles className="h-16 w-16 text-primary/60" />
          </div>
          <p className="text-foreground font-bold text-lg">
            It's so simple that there's nothing really to customize... yet
          </p>
        </div>
      </DialogContent>
    </Dialog>
  )
}


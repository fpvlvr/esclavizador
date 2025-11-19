"use client"

import { Cookie } from "lucide-react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import type { UserRole } from "@/lib/api/generated"

interface AccountSettingsDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  role: UserRole
}

export function AccountSettingsDialog({ open, onOpenChange, role }: AccountSettingsDialogProps) {
  const message = role === "boss" 
    ? "What account settings? You're the Boss already!"
    : "What account settings? You're just a simple worker, that's it!"

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            Account Settings
          </DialogTitle>
        </DialogHeader>
        <div className="py-8 text-center space-y-4">
          <div className="flex justify-center">
            <Cookie className="h-16 w-16 text-primary/60" />
          </div>
          <p className="text-foreground font-bold text-lg">
            {message}
          </p>
        </div>
      </DialogContent>
    </Dialog>
  )
}


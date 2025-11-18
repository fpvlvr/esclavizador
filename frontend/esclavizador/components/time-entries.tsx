"use client"

import { MoreHorizontal, Trash2, Clock } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Badge } from "@/components/ui/badge"
import { EmptyState } from "@/components/empty-state"
import { Skeleton } from "@/components/ui/skeleton"
import { useTimeEntries } from "@/hooks/use-time-entries"
import { useState } from "react"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"

export function TimeEntries() {
  const { entries, loading, deleteEntry } = useTimeEntries({
    is_running: false,
    limit: 20,
    offset: 0,
  })

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [entryToDelete, setEntryToDelete] = useState<string | null>(null)

  const formatDuration = (seconds: number | null | undefined): string => {
    if (!seconds) return "0:00:00"
    const hrs = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    return `${hrs}:${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
  }

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr) // Parse UTC timestamp, convert to local time
    const now = new Date()

    // Compare calendar dates in local timezone (not elapsed time)
    const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate())
    const nowOnly = new Date(now.getFullYear(), now.getMonth(), now.getDate())

    const diffTime = nowOnly.getTime() - dateOnly.getTime()
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return "Today"
    if (diffDays === 1) return "Yesterday"
    if (diffDays < 7) return `${diffDays} days ago`

    return date.toLocaleDateString()
  }

  const formatTime = (dateStr: string): string => {
    const date = new Date(dateStr)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const handleDelete = async () => {
    if (!entryToDelete) return

    try {
      await deleteEntry(entryToDelete)
      setDeleteDialogOpen(false)
      setEntryToDelete(null)
    } catch (err) {
      console.error('Failed to delete entry:', err)
    }
  }

  const openDeleteDialog = (entryId: string) => {
    setEntryToDelete(entryId)
    setDeleteDialogOpen(true)
  }

  return (
    <>
      <Card className="border-border">
        <CardHeader>
          <CardTitle>Recent Time Entries</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="flex items-center gap-4 p-4">
                  <Skeleton className="h-10 w-1" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3 w-1/2" />
                  </div>
                  <Skeleton className="h-6 w-20" />
                </div>
              ))}
            </div>
          ) : entries.length === 0 ? (
            <EmptyState
              icon={Clock}
              title="No time entries yet"
              description="Start tracking your time by using the timer above or create a manual entry."
              action={{
                label: "Start Timer",
                onClick: () => {
                  window.scrollTo({ top: 0, behavior: 'smooth' })
                },
              }}
            />
          ) : (
            <div className="space-y-2">
              {entries.map((entry) => (
                <div
                  key={entry.id}
                  className="flex items-center gap-4 p-4 rounded-lg hover:bg-muted/50 transition-colors group"
                >
                  <div
                    className="h-10 w-1 rounded-full"
                    style={{ backgroundColor: entry.project_name ? undefined : '#888' }}
                  />

                  <div className="flex-1 min-w-0 space-y-1">
                    <p className="font-medium text-sm truncate">
                      {entry.description || 'No description'}
                    </p>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{entry.project_name}</span>
                      {entry.task_name && (
                        <>
                          <span>•</span>
                          <span>{entry.task_name}</span>
                        </>
                      )}
                      <span>•</span>
                      <span>{formatDate(entry.start_time)}</span>
                      {entry.end_time && (
                        <>
                          <span>•</span>
                          <span>
                            {formatTime(entry.start_time)} - {formatTime(entry.end_time)}
                          </span>
                        </>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <Badge variant="secondary" className="font-mono">
                      {formatDuration(entry.duration_seconds)}
                    </Badge>

                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() => openDeleteDialog(entry.id)}
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete time entry?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete this time entry.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive hover:bg-destructive/90">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}

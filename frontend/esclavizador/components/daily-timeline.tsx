"use client"

import { useState, useMemo, useRef, useEffect } from "react"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Plus, Clock, CalendarIcon } from "lucide-react"
import { useTimeEntries } from "@/hooks/use-time-entries"
import { useProjects } from "@/hooks/use-projects"
import { Skeleton } from "@/components/ui/skeleton"
import { ManualEntryDialog } from "@/components/manual-entry-dialog"
import { EditEntryDialog } from "@/components/edit-entry-dialog"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { cn } from "@/lib/utils"
import type { TimeEntryResponse } from "@/lib/api/generated"

export function DailyTimeline() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [editingEntry, setEditingEntry] = useState<TimeEntryResponse | null>(null)
  const [hoveredEntry, setHoveredEntry] = useState<string | null>(null)
  const [selectedDate, setSelectedDate] = useState<Date>(new Date())
  const timelineRef = useRef<HTMLDivElement>(null)

  // Get selected date in local timezone as YYYY-MM-DD string
  const dateStr = useMemo(() => {
    const year = selectedDate.getFullYear()
    const month = String(selectedDate.getMonth() + 1).padStart(2, '0')
    const day = String(selectedDate.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }, [selectedDate])

  // Auto-scroll to 6am when date changes
  useEffect(() => {
    if (timelineRef.current) {
      timelineRef.current.scrollTop = 6 * 31.25
    }
  }, [dateStr])

  const { entries, loading: entriesLoading, refetch } = useTimeEntries({
    start_date: dateStr,
    end_date: dateStr,
    is_running: false,
    limit: 100,
  })

  const { projects } = useProjects()

  // Map project colors
  const projectColors = useMemo(() => {
    const map = new Map<string, string>()
    projects.forEach(p => map.set(p.id, p.color))
    return map
  }, [projects])

  const loading = entriesLoading

  // Calculate stats
  const stats = useMemo(() => {
    const total = entries.reduce((sum, e) => sum + (e.duration_seconds ?? 0), 0)
    const billable = entries
      .filter(e => e.is_billable)
      .reduce((sum, e) => sum + (e.duration_seconds ?? 0), 0)

    return { total, billable }
  }, [entries])

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${hours}h ${minutes.toString().padStart(2, '0')}min`
  }

  const formatTime = (dateStr: string): string => {
    const date = new Date(dateStr)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const formatDate = (date: Date): string => {
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)

    if (date.toDateString() === today.toDateString()) {
      return "Today"
    } else if (date.toDateString() === yesterday.toDateString()) {
      return "Yesterday"
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    }
  }

  // Vertical timeline helpers
  const getTimelinePosition = (dateStr: string, startHour: number, endHour: number) => {
    const date = new Date(dateStr)
    const hours = date.getHours() + date.getMinutes() / 60

    // Clamp to visible range
    const clampedHours = Math.max(startHour, Math.min(endHour, hours))
    const totalHours = endHour - startHour
    const relativeHours = clampedHours - startHour

    return (relativeHours / totalHours) * 100 // Return percentage
  }

  const handleEditEntry = (entry: TimeEntryResponse) => {
    setEditingEntry(entry)
    setEditDialogOpen(true)
  }

  if (loading) {
    return (
      <Card className="border-border">
        <CardHeader className="pb-2.5">
          <div className="flex items-center justify-between">
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-9 w-32" />
          </div>
        </CardHeader>
        <CardContent className="pt-0 pb-3.5">
          <Skeleton className="h-80 w-full" />
        </CardContent>
      </Card>
    )
  }

  // Timeline configuration (full 24 hours, 0-23)
  const startHour = 0
  const endHour = 24
  const hours = Array.from({ length: endHour - startHour }, (_, i) => startHour + i)

  // Calculate height: preserve spacing from 6am-10pm design (~31px per hour)
  const hourHeight = 31.25
  const totalHeight = 24 * hourHeight // ~750px

  return (
    <>
      <Card className="border-border">
        <CardHeader className="pb-2.5">
          <div className="flex items-center justify-between">
            <div className="flex gap-6 items-center">
              {/* Date Picker */}
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "justify-start text-left font-bold text-base px-4 py-6",
                      !selectedDate && "text-muted-foreground"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-5 w-5" />
                    {formatDate(selectedDate)}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={selectedDate}
                    onSelect={(date) => date && setSelectedDate(date)}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>

              {/* Stats */}
              <div className="flex gap-8">
                <div>
                  <p className="text-sm text-muted-foreground">Total</p>
                  <p className="text-2xl font-bold">{formatDuration(stats.total)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Billable</p>
                  <p className="text-2xl font-bold">{formatDuration(stats.billable)}</p>
                </div>
              </div>
            </div>
            <Button onClick={() => setDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Entry
            </Button>
          </div>
        </CardHeader>
        <CardContent className="pt-0 pb-3.5">
          <div className="grid md:grid-cols-2 gap-6 -mt-[7px]">
            {/* Vertical Timeline */}
            <div ref={timelineRef} className="overflow-y-auto pr-2" style={{ maxHeight: '500px' }}>
              <div className="relative pr-4" style={{ height: `${totalHeight}px` }}>
                {/* Hour labels and grid lines */}
                <div className="absolute inset-0 flex flex-col justify-between">
                  {hours.map((hour) => (
                    <div key={hour} className="flex items-center gap-3 relative">
                      <span className="text-xs text-muted-foreground font-medium w-12 text-right">
                        {String(hour).padStart(2, '0')}:00
                      </span>
                      <div className="flex-1 h-px bg-border" />
                    </div>
                  ))}
                </div>

                {/* Time entries */}
                <div className="absolute inset-0 ml-16">
                  {entries.map((entry) => {
                    if (!entry.end_time) return null

                    const startPos = getTimelinePosition(entry.start_time, startHour, endHour)
                    const endPos = getTimelinePosition(entry.end_time, startHour, endHour)
                    const heightPercent = endPos - startPos

                    // Skip entries outside the visible range
                    if (heightPercent <= 0) return null

                    const isHovered = hoveredEntry === entry.id
                    const projectColor = projectColors.get(entry.project_id) || '#3b82f6'

                    // Calculate actual pixel height to determine if we should show text
                    const pixelHeight = (heightPercent / 100) * totalHeight
                    const showFullText = pixelHeight >= 35 // Show both lines if tall enough
                    const showTitle = pixelHeight >= 20 // Show title only if medium
                    const showAnyText = pixelHeight >= 12 // Show at least something if not tiny

                    return (
                      <div
                        key={entry.id}
                        className="absolute left-0 right-0 cursor-pointer transition-all duration-200 rounded-md overflow-hidden"
                        style={{
                          top: `${startPos}%`,
                          height: `${heightPercent}%`,
                          minHeight: '4px', // Ensure very short entries are visible
                          backgroundColor: projectColor,
                          opacity: isHovered ? 1 : 0.85,
                          border: isHovered ? '2px solid hsl(var(--background))' : '2px solid transparent',
                          filter: isHovered ? 'brightness(1.1)' : 'none',
                          zIndex: isHovered ? 10 : 1,
                          padding: showAnyText ? '4px 8px' : '0',
                        }}
                        onClick={() => handleEditEntry(entry)}
                        onMouseEnter={() => setHoveredEntry(entry.id)}
                        onMouseLeave={() => setHoveredEntry(null)}
                        title={!showFullText ? `${entry.description || entry.project_name} (${formatTime(entry.start_time)} - ${formatTime(entry.end_time)})` : undefined}
                      >
                        {showFullText ? (
                          <>
                            <div className="text-xs font-medium text-white truncate">
                              {entry.description || entry.project_name}
                            </div>
                            <div className="text-[10px] text-white/80 truncate">
                              {formatTime(entry.start_time)} - {formatTime(entry.end_time)}
                            </div>
                          </>
                        ) : showTitle ? (
                          <div className="text-xs font-medium text-white truncate">
                            {entry.description || entry.project_name}
                          </div>
                        ) : showAnyText ? (
                          <div className="text-[10px] text-white/90 truncate font-medium">
                            {formatTime(entry.start_time)}
                          </div>
                        ) : null}
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>

            {/* Entries List */}
            <div className="space-y-2">
              <h3 className="font-semibold text-sm text-muted-foreground mb-2">{formatDate(selectedDate)}'s Entries</h3>
              {entries.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <Clock className="h-12 w-12 text-muted-foreground mb-3" />
                  <p className="text-sm text-muted-foreground">No entries for this date</p>
                  <p className="text-xs text-muted-foreground mt-1">Click "Add Entry" to get started</p>
                </div>
              ) : (
                entries.map((entry) => {
                  const isHovered = hoveredEntry === entry.id
                  const projectColor = projectColors.get(entry.project_id) || '#3b82f6'
                  return (
                    <div
                      key={entry.id}
                      className={`p-2.5 rounded-lg border transition-all cursor-pointer ${
                        isHovered
                          ? 'border-primary bg-primary/5 shadow-sm'
                          : 'border-border hover:border-muted-foreground/50'
                      }`}
                      onClick={() => handleEditEntry(entry)}
                      onMouseEnter={() => setHoveredEntry(entry.id)}
                      onMouseLeave={() => setHoveredEntry(null)}
                    >
                      <div className="flex items-start gap-2.5">
                        <div
                          className="h-3 w-3 rounded-full mt-1 flex-shrink-0"
                          style={{ backgroundColor: projectColor }}
                        />
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm truncate">
                            {entry.description || entry.project_name}
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            {entry.project_name}
                            {entry.task_name && ` • ${entry.task_name}`}
                          </p>
                          <div className="flex items-center gap-3 mt-2">
                            <span className="text-xs text-muted-foreground">
                              {formatTime(entry.start_time)} - {entry.end_time ? formatTime(entry.end_time) : '...'}
                            </span>
                            <span className="text-xs font-medium">
                              {formatDuration(entry.duration_seconds ?? 0)}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <ManualEntryDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onSuccess={refetch}
        selectedDate={selectedDate}
      />

      <EditEntryDialog
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
        onSuccess={refetch}
        entry={editingEntry}
      />
    </>
  )
}

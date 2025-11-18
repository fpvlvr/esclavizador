"use client"

import { useState, useEffect, useMemo } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Clock } from "lucide-react"
import { useProjects } from "@/hooks/use-projects"
import { useTasks } from "@/hooks/use-tasks"
import { useTimeEntries } from "@/hooks/use-time-entries"
import { toast } from "sonner"

interface ManualEntryDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: () => void
  selectedDate?: Date
}

export function ManualEntryDialog({ open, onOpenChange, onSuccess, selectedDate }: ManualEntryDialogProps) {
  const { projects } = useProjects()
  const { createEntry } = useTimeEntries()

  const [description, setDescription] = useState("")
  const [selectedProject, setSelectedProject] = useState("")
  const [selectedTask, setSelectedTask] = useState("")
  const [startTime, setStartTime] = useState("")
  const [endTime, setEndTime] = useState("")
  const [loading, setLoading] = useState(false)

  // Fetch tasks when project changes (auto-fetches via hook)
  const { tasks, loading: tasksLoading } = useTasks(selectedProject || undefined)

  // Reset form when dialog opens
  useEffect(() => {
    if (open) {
      setDescription("")
      setSelectedProject("")
      setSelectedTask("")

      // Set default times to current hour and next hour
      const now = new Date()
      const currentHour = now.getHours()
      const currentMinutes = now.getMinutes()

      const startHour = String(currentHour).padStart(2, '0')
      const startMinute = String(currentMinutes).padStart(2, '0')
      setStartTime(`${startHour}:${startMinute}`)

      const endHour = String(currentHour + 1).padStart(2, '0')
      setEndTime(`${endHour}:${startMinute}`)
    }
  }, [open])

  // Reset task when project changes
  useEffect(() => {
    setSelectedTask("")
  }, [selectedProject])

  // Calculate duration
  const duration = useMemo(() => {
    if (!startTime || !endTime) return "0 h 00 min"

    const [startHour, startMin] = startTime.split(':').map(Number)
    const [endHour, endMin] = endTime.split(':').map(Number)

    const startMinutes = startHour * 60 + startMin
    const endMinutes = endHour * 60 + endMin

    let diffMinutes = endMinutes - startMinutes
    if (diffMinutes < 0) diffMinutes += 24 * 60 // Handle overnight

    const hours = Math.floor(diffMinutes / 60)
    const minutes = diffMinutes % 60

    return `${hours} h ${String(minutes).padStart(2, '0')} min`
  }, [startTime, endTime])

  const setToNow = (field: 'start' | 'end') => {
    const now = new Date()
    const hours = String(now.getHours()).padStart(2, '0')
    const minutes = String(now.getMinutes()).padStart(2, '0')
    const timeStr = `${hours}:${minutes}`

    if (field === 'start') {
      setStartTime(timeStr)
    } else {
      setEndTime(timeStr)
    }
  }

  const handleSave = async () => {
    // Validation
    if (!selectedProject) {
      toast.error("Please select a project")
      return
    }

    if (!selectedTask) {
      toast.error("Please select a task")
      return
    }

    if (!startTime || !endTime) {
      toast.error("Please enter start and end times")
      return
    }

    // Parse times
    const [startHour, startMin] = startTime.split(':').map(Number)
    const [endHour, endMin] = endTime.split(':').map(Number)

    const startMinutes = startHour * 60 + startMin
    const endMinutes = endHour * 60 + endMin

    if (endMinutes <= startMinutes) {
      toast.error("End time must be after start time")
      return
    }

    try {
      setLoading(true)

      // Create ISO datetime strings for the selected date
      const targetDate = selectedDate || new Date()
      const year = targetDate.getFullYear()
      const month = String(targetDate.getMonth() + 1).padStart(2, '0')
      const day = String(targetDate.getDate()).padStart(2, '0')

      const startDateTime = new Date(`${year}-${month}-${day}T${startTime}:00`)
      const endDateTime = new Date(`${year}-${month}-${day}T${endTime}:00`)

      await createEntry({
        project_id: selectedProject,
        task_id: selectedTask,
        start_time: startDateTime.toISOString(),
        end_time: endDateTime.toISOString(),
        description: description || null,
        is_billable: false,
      })

      onOpenChange(false)
      onSuccess?.()
    } catch (err) {
      console.error('Failed to create entry:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Add Manual Time Entry</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Input
              id="description"
              placeholder="Describe your task"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          {/* Time inputs row */}
          <div className="grid grid-cols-3 gap-4">
            {/* Start Time */}
            <div className="space-y-2">
              <Label htmlFor="start-time">Start Time</Label>
              <div className="flex gap-2">
                <Input
                  id="start-time"
                  type="time"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                />
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={() => setToNow('start')}
                  title="Set to now"
                >
                  <Clock className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* End Time */}
            <div className="space-y-2">
              <Label htmlFor="end-time">End Time</Label>
              <div className="flex gap-2">
                <Input
                  id="end-time"
                  type="time"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                />
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={() => setToNow('end')}
                  title="Set to now"
                >
                  <Clock className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Duration */}
            <div className="space-y-2">
              <Label>Duration</Label>
              <Input value={duration} readOnly className="bg-muted" />
            </div>
          </div>

          {/* Project */}
          <div className="space-y-2">
            <Label htmlFor="project">
              Project <span className="text-destructive">*</span>
            </Label>
            <Select value={selectedProject} onValueChange={setSelectedProject}>
              <SelectTrigger id="project">
                <SelectValue placeholder="Select project" />
              </SelectTrigger>
              <SelectContent>
                {projects.map((project) => (
                  <SelectItem key={project.id} value={project.id}>
                    <div className="flex items-center gap-2">
                      <div
                        className="h-3 w-3 rounded-full"
                        style={{ backgroundColor: project.color }}
                      />
                      {project.name}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Task */}
          <div className="space-y-2">
            <Label htmlFor="task">
              Task <span className="text-destructive">*</span>
            </Label>
            <Select
              value={selectedTask}
              onValueChange={setSelectedTask}
              disabled={!selectedProject || tasksLoading}
            >
              <SelectTrigger id="task">
                <SelectValue placeholder={!selectedProject ? "Select project first" : "Select task"} />
              </SelectTrigger>
              <SelectContent>
                {tasks.length === 0 ? (
                  <div className="p-2 text-sm text-muted-foreground">
                    No tasks available for this project
                  </div>
                ) : (
                  tasks.map((task) => (
                    <SelectItem key={task.id} value={task.id}>
                      {task.name}
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={loading}>
            {loading ? "Saving..." : "Save"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

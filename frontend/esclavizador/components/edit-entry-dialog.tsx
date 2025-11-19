"use client"

import { useState, useEffect, useMemo } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Trash2 } from "lucide-react"
import { useProjects } from "@/hooks/use-projects"
import { useTasks } from "@/hooks/use-tasks"
import { useTimeEntries } from "@/hooks/use-time-entries"
import { toast } from "sonner"
import type { TimeEntryResponse } from "@/lib/api/generated"

interface EditEntryDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: () => void
  entry: TimeEntryResponse | null
}

export function EditEntryDialog({ open, onOpenChange, onSuccess, entry }: EditEntryDialogProps) {
  const { projects } = useProjects()
  const { updateEntry, deleteEntry } = useTimeEntries()

  const [description, setDescription] = useState("")
  const [selectedProject, setSelectedProject] = useState("")
  const [selectedTask, setSelectedTask] = useState("")
  const [startTime, setStartTime] = useState("")
  const [endTime, setEndTime] = useState("")
  const [loading, setLoading] = useState(false)

  // Fetch tasks when project changes
  const { tasks, loading: tasksLoading } = useTasks(selectedProject || undefined)

  // Populate form when entry changes
  useEffect(() => {
    if (open && entry) {
      setDescription(entry.description || "")
      setSelectedProject(entry.project_id)
      setSelectedTask(entry.task_id || "")

      // Extract time from ISO strings
      const start = new Date(entry.start_time)
      const startHour = String(start.getHours()).padStart(2, '0')
      const startMin = String(start.getMinutes()).padStart(2, '0')
      setStartTime(`${startHour}:${startMin}`)

      if (entry.end_time) {
        const end = new Date(entry.end_time)
        const endHour = String(end.getHours()).padStart(2, '0')
        const endMin = String(end.getMinutes()).padStart(2, '0')
        setEndTime(`${endHour}:${endMin}`)
      }
    }
  }, [open, entry])

  // Reset task when project changes
  useEffect(() => {
    if (entry && entry.project_id !== selectedProject) {
      setSelectedTask("")
    }
  }, [selectedProject, entry])

  // Calculate duration
  const duration = useMemo(() => {
    if (!startTime || !endTime) return "0 h 00 min"

    const [startHour, startMin] = startTime.split(':').map(Number)
    const [endHour, endMin] = endTime.split(':').map(Number)

    const startMinutes = startHour * 60 + startMin
    const endMinutes = endHour * 60 + endMin

    let diffMinutes = endMinutes - startMinutes
    if (diffMinutes < 0) diffMinutes += 24 * 60

    const hours = Math.floor(diffMinutes / 60)
    const minutes = diffMinutes % 60

    return `${hours} h ${String(minutes).padStart(2, '0')} min`
  }, [startTime, endTime])

  const handleSave = async () => {
    if (!entry) return

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

      // Use the date from the original entry
      const originalStart = new Date(entry.start_time)
      const year = originalStart.getFullYear()
      const month = String(originalStart.getMonth() + 1).padStart(2, '0')
      const day = String(originalStart.getDate()).padStart(2, '0')

      const startDateTime = new Date(`${year}-${month}-${day}T${startTime}:00`)
      const endDateTime = new Date(`${year}-${month}-${day}T${endTime}:00`)

      await updateEntry(entry.id, {
        project_id: selectedProject,
        task_id: selectedTask,
        start_time: startDateTime.toISOString(),
        end_time: endDateTime.toISOString(),
        description: description || null,
        is_billable: entry.is_billable,
      })

      onOpenChange(false)
      onSuccess?.()
    } catch (err) {
      console.error('Failed to update entry:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!entry) return

    if (!confirm('Are you sure you want to delete this time entry?')) {
      return
    }

    try {
      setLoading(true)
      await deleteEntry(entry.id)
      onOpenChange(false)
      onSuccess?.()
    } catch (err) {
      console.error('Failed to delete entry:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Edit Time Entry</DialogTitle>
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
              <Input
                id="start-time"
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
              />
            </div>

            {/* End Time */}
            <div className="space-y-2">
              <Label htmlFor="end-time">End Time</Label>
              <Input
                id="end-time"
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
              />
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
        <div className="flex justify-between">
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={loading}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Delete
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={loading}>
              {loading ? "Saving..." : "Save Changes"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

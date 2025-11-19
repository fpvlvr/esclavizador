"use client"

import { useState, useEffect } from "react"
import { Play, Square, AlertCircle } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useAuth } from "@/hooks/use-auth"
import { useProjects } from "@/hooks/use-projects"
import { useTasks } from "@/hooks/use-tasks"
import { useTimer } from "@/hooks/use-timer"
import { Skeleton } from "@/components/ui/skeleton"

export function TimeTracker() {
  const { user } = useAuth()
  const { projects, loading: projectsLoading } = useProjects()
  const { runningEntry, elapsedSeconds, isRunning, loading: timerLoading, startTimer, stopTimer } = useTimer()

  const [selectedProject, setSelectedProject] = useState("")
  const [selectedTask, setSelectedTask] = useState("")
  
  // Use running entry's project if timer is running, otherwise use selected project
  const projectForTasks = runningEntry?.project_id || selectedProject
  const { tasks, loading: tasksLoading } = useTasks(projectForTasks)

  const isBoss = user?.role === 'boss'
  const hasNoProjects = projects.length === 0
  const loading = projectsLoading || timerLoading || tasksLoading

  const formatTime = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    return `${hrs.toString().padStart(2, "0")}:${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
  }

  // Reset task selection when project changes
  useEffect(() => {
    if (!isRunning) {
      setSelectedTask("")
    }
  }, [selectedProject, isRunning])

  const handleStart = async () => {
    if (!selectedProject || !selectedTask) return

    try {
      await startTimer({
        project_id: selectedProject,
        task_id: selectedTask,
        is_billable: false,
      })
    } catch (err) {
      console.error('Failed to start timer:', err)
    }
  }

  const handleStop = async () => {
    try {
      await stopTimer()
      setSelectedTask("")
      setSelectedProject("")
    } catch (err) {
      console.error('Failed to stop timer:', err)
    }
  }

  if (loading) {
    return (
      <Card className="border-border">
        <CardContent className="px-6 py-4">
          <div className="flex flex-col md:flex-row items-center gap-3">
            <Skeleton className="h-12 w-32" />
            <Skeleton className="h-10 w-52" />
            <Skeleton className="h-10 w-64" />
            <Skeleton className="h-10 w-24" />
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border-border">
      <CardContent className="px-6 py-4">
        {hasNoProjects ? (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {isBoss
                ? "Create a project first to start tracking time. Go to the Projects page to get started."
                : "No projects available yet. Contact your admin to create projects before tracking time."}
            </AlertDescription>
          </Alert>
        ) : (
          <div className="flex flex-col md:flex-row items-center gap-3">
            <div className="text-4xl font-mono font-bold tabular-nums">{formatTime(elapsedSeconds)}</div>
            <Select
              value={isRunning ? runningEntry?.project_id : selectedProject}
              onValueChange={setSelectedProject}
              disabled={isRunning}
            >
              <SelectTrigger className="w-full md:w-52">
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
            <Select
              value={isRunning ? runningEntry?.task_id ?? "" : selectedTask}
              onValueChange={setSelectedTask}
              disabled={isRunning || !selectedProject}
            >
              <SelectTrigger className="w-full md:w-64">
                <SelectValue placeholder="Select task" />
              </SelectTrigger>
              <SelectContent>
                {tasks.length === 0 ? (
                  <div className="px-2 py-1.5 text-sm text-muted-foreground">
                    No tasks available
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
            <div className="flex items-center gap-2">
              {isRunning ? (
                <Button size="lg" variant="outline" onClick={handleStop}>
                  <Square className="h-5 w-5 mr-2" />
                  Stop
                </Button>
              ) : (
                <Button
                  size="lg"
                  onClick={handleStart}
                  disabled={!selectedProject || !selectedTask}
                >
                  <Play className="h-5 w-5 mr-2" />
                  Start
                </Button>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

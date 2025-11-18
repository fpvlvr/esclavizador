"use client"

import { useState } from "react"
import { Play, Square, AlertCircle } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useAuth } from "@/hooks/use-auth"
import { useProjects } from "@/hooks/use-projects"
import { useTimer } from "@/hooks/use-timer"
import { Skeleton } from "@/components/ui/skeleton"

export function TimeTracker() {
  const { user } = useAuth()
  const { projects, loading: projectsLoading } = useProjects()
  const { runningEntry, elapsedSeconds, isRunning, loading: timerLoading, startTimer, stopTimer } = useTimer()

  const [description, setDescription] = useState("")
  const [selectedProject, setSelectedProject] = useState("")

  const isBoss = user?.role === 'boss'
  const hasNoProjects = projects.length === 0
  const loading = projectsLoading || timerLoading

  const formatTime = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    return `${hrs.toString().padStart(2, "0")}:${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
  }

  const handleStart = async () => {
    if (!selectedProject) return

    try {
      await startTimer({
        project_id: selectedProject,
        description: description || null,
        is_billable: false,
      })
    } catch (err) {
      console.error('Failed to start timer:', err)
    }
  }

  const handleStop = async () => {
    try {
      await stopTimer()
      setDescription("")
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
            <Skeleton className="h-10 flex-1" />
            <Skeleton className="h-10 w-52" />
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
            <Input
              placeholder="What are you working on?"
              value={isRunning ? (runningEntry?.description ?? "") : description}
              onChange={(e) => setDescription(e.target.value)}
              className="flex-1"
              disabled={isRunning}
            />
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
                  disabled={!selectedProject}
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

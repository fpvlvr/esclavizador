"use client"

import { useState, useEffect } from "react"
import { Play, Pause, Square, AlertCircle } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useAuth } from "@/hooks/use-auth"

const projects = [
  { id: "1", name: "Website Redesign", color: "bg-chart-1" },
  { id: "2", name: "Mobile App Development", color: "bg-chart-2" },
  { id: "3", name: "API Integration", color: "bg-chart-3" },
  { id: "4", name: "Marketing Campaign", color: "bg-chart-4" },
]

const allTasks = [
  { id: "1-1", name: "Homepage mockup", projectId: "1", projectName: "Website Redesign", projectColor: "bg-chart-1" },
  { id: "1-2", name: "Component library", projectId: "1", projectName: "Website Redesign", projectColor: "bg-chart-1" },
  { id: "1-3", name: "Mobile responsive", projectId: "1", projectName: "Website Redesign", projectColor: "bg-chart-1" },
  { id: "2-1", name: "Authentication flow", projectId: "2", projectName: "Mobile App Development", projectColor: "bg-chart-2" },
  { id: "2-2", name: "Push notifications", projectId: "2", projectName: "Mobile App Development", projectColor: "bg-chart-2" },
  { id: "2-3", name: "Offline mode", projectId: "2", projectName: "Mobile App Development", projectColor: "bg-chart-2" },
  { id: "2-4", name: "UI polish", projectId: "2", projectName: "Mobile App Development", projectColor: "bg-chart-2" },
  { id: "3-1", name: "REST API endpoints", projectId: "3", projectName: "API Integration", projectColor: "bg-chart-3" },
  { id: "3-2", name: "GraphQL schema", projectId: "3", projectName: "API Integration", projectColor: "bg-chart-3" },
  { id: "3-3", name: "API documentation", projectId: "3", projectName: "API Integration", projectColor: "bg-chart-3" },
  { id: "4-1", name: "Social media content", projectId: "4", projectName: "Marketing Campaign", projectColor: "bg-chart-4" },
  { id: "4-2", name: "Email campaigns", projectId: "4", projectName: "Marketing Campaign", projectColor: "bg-chart-4" },
  { id: "4-3", name: "Landing page copy", projectId: "4", projectName: "Marketing Campaign", projectColor: "bg-chart-4" },
]

export function TimeTracker() {
  const { user } = useAuth()
  const [isRunning, setIsRunning] = useState(false)
  const [time, setTime] = useState(0)
  const [description, setDescription] = useState("")
  const [selectedProject, setSelectedProject] = useState("")
  const [selectedTask, setSelectedTask] = useState("")

  // TODO: Replace with real data from useProjects hook
  const availableProjects = projects
  const isBoss = user?.role === 'boss'
  const hasNoProjects = availableProjects.length === 0

  useEffect(() => {
    let interval: NodeJS.Timeout | undefined

    if (isRunning) {
      interval = setInterval(() => {
        setTime((prev) => prev + 1)
      }, 1000)
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [isRunning])

  const formatTime = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    return `${hrs.toString().padStart(2, "0")}:${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
  }

  const handleToggle = () => {
    setIsRunning(!isRunning)
  }

  const handleStop = () => {
    setIsRunning(false)
    setTime(0)
    setDescription("")
    setSelectedProject("")
    setSelectedTask("")
  }

  const handleTaskSelect = (taskId: string) => {
    setSelectedTask(taskId)
    const task = allTasks.find(t => t.id === taskId)
    if (task) {
      setSelectedProject(task.projectId)
      setDescription(task.name)
    }
  }

  return (
    <Card className="border-border">
      <CardContent className="p-6">
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
          <div className="flex flex-col md:flex-row items-center gap-4">
            <div className="text-4xl font-mono font-bold tabular-nums">{formatTime(time)}</div>
            <Input
              placeholder="What are you working on?"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="flex-1"
              disabled={hasNoProjects}
            />
            <Select value={selectedProject} onValueChange={setSelectedProject} disabled={hasNoProjects}>
              <SelectTrigger className="w-full md:w-52">
                <SelectValue placeholder="Select project" />
              </SelectTrigger>
              <SelectContent>
                {availableProjects.map((project) => (
                  <SelectItem key={project.id} value={project.id}>
                    <div className="flex items-center gap-2">
                      <div className={`h-3 w-3 rounded-full ${project.color}`} />
                      {project.name}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <div className="flex items-center gap-2">
              <Button
                size="lg"
                onClick={handleToggle}
                className={isRunning ? "bg-warning hover:bg-warning/90" : ""}
                disabled={hasNoProjects || !selectedProject}
              >
                {isRunning ? (
                  <>
                    <Pause className="h-5 w-5 mr-2" />
                    Pause
                  </>
                ) : (
                  <>
                    <Play className="h-5 w-5 mr-2" />
                    Start
                  </>
                )}
              </Button>
              {time > 0 && (
                <Button size="lg" variant="outline" onClick={handleStop}>
                  <Square className="h-5 w-5" />
                </Button>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

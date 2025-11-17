"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { ChevronDown, ChevronRight, Clock, Users, Plus } from 'lucide-react'
import { cn } from "@/lib/utils"

interface Task {
  id: string
  name: string
  description: string
  timeSpent: string
  assignedUsers: {
    name: string
    avatar: string
    initials: string
  }[]
}

interface Project {
  id: string
  name: string
  color: string
  totalTimeThisMonth: string
  totalTasks: number
  completedTasks: number
  assignedUsers: {
    name: string
    avatar: string
    initials: string
  }[]
  tasks: Task[]
}

const mockProjects: Project[] = [
  {
    id: "1",
    name: "Website Redesign",
    color: "bg-chart-1",
    totalTimeThisMonth: "42h 30m",
    totalTasks: 12,
    completedTasks: 8,
    assignedUsers: [
      { name: "Sarah Chen", avatar: "/professional-woman-avatar.png", initials: "SC" },
      { name: "Mike Johnson", avatar: "/professional-man-avatar.png", initials: "MJ" },
      { name: "Emily Davis", avatar: "/professional-woman-avatar-2.png", initials: "ED" },
    ],
    tasks: [
      {
        id: "1-1",
        name: "Homepage mockup",
        description: "Design new homepage layout with hero section",
        timeSpent: "8h 15m",
        assignedUsers: [
          { name: "Sarah Chen", avatar: "/professional-woman-avatar.png", initials: "SC" },
        ],
      },
      {
        id: "1-2",
        name: "Component library",
        description: "Build reusable UI components",
        timeSpent: "12h 45m",
        assignedUsers: [
          { name: "Mike Johnson", avatar: "/professional-man-avatar.png", initials: "MJ" },
          { name: "Emily Davis", avatar: "/professional-woman-avatar-2.png", initials: "ED" },
        ],
      },
      {
        id: "1-3",
        name: "Mobile responsive",
        description: "Implement responsive design for all pages",
        timeSpent: "6h 30m",
        assignedUsers: [
          { name: "Emily Davis", avatar: "/professional-woman-avatar-2.png", initials: "ED" },
        ],
      },
    ],
  },
  {
    id: "2",
    name: "Mobile App Development",
    color: "bg-chart-2",
    totalTimeThisMonth: "68h 15m",
    totalTasks: 18,
    completedTasks: 12,
    assignedUsers: [
      { name: "David Park", avatar: "/professional-man-avatar-2.png", initials: "DP" },
      { name: "Lisa Wang", avatar: "/professional-woman-avatar-3.jpg", initials: "LW" },
      { name: "Mike Johnson", avatar: "/professional-man-avatar.png", initials: "MJ" },
      { name: "Sarah Chen", avatar: "/professional-woman-avatar.png", initials: "SC" },
    ],
    tasks: [
      {
        id: "2-1",
        name: "Authentication flow",
        description: "Implement OAuth and biometric login",
        timeSpent: "14h 20m",
        assignedUsers: [
          { name: "David Park", avatar: "/professional-man-avatar-2.png", initials: "DP" },
          { name: "Mike Johnson", avatar: "/professional-man-avatar.png", initials: "MJ" },
        ],
      },
      {
        id: "2-2",
        name: "Push notifications",
        description: "Set up Firebase Cloud Messaging",
        timeSpent: "9h 45m",
        assignedUsers: [
          { name: "Lisa Wang", avatar: "/professional-woman-avatar-3.jpg", initials: "LW" },
        ],
      },
      {
        id: "2-3",
        name: "Offline mode",
        description: "Implement local data caching and sync",
        timeSpent: "18h 30m",
        assignedUsers: [
          { name: "David Park", avatar: "/professional-man-avatar-2.png", initials: "DP" },
        ],
      },
      {
        id: "2-4",
        name: "UI polish",
        description: "Refine animations and transitions",
        timeSpent: "5h 40m",
        assignedUsers: [
          { name: "Sarah Chen", avatar: "/professional-woman-avatar.png", initials: "SC" },
        ],
      },
    ],
  },
  {
    id: "3",
    name: "API Integration",
    color: "bg-chart-3",
    totalTimeThisMonth: "28h 45m",
    totalTasks: 8,
    completedTasks: 5,
    assignedUsers: [
      { name: "Mike Johnson", avatar: "/professional-man-avatar.png", initials: "MJ" },
      { name: "David Park", avatar: "/professional-man-avatar-2.png", initials: "DP" },
    ],
    tasks: [
      {
        id: "3-1",
        name: "REST API endpoints",
        description: "Create CRUD endpoints for all resources",
        timeSpent: "10h 15m",
        assignedUsers: [
          { name: "Mike Johnson", avatar: "/professional-man-avatar.png", initials: "MJ" },
        ],
      },
      {
        id: "3-2",
        name: "GraphQL schema",
        description: "Design and implement GraphQL API",
        timeSpent: "12h 30m",
        assignedUsers: [
          { name: "David Park", avatar: "/professional-man-avatar-2.png", initials: "DP" },
        ],
      },
      {
        id: "3-3",
        name: "API documentation",
        description: "Write comprehensive API docs with Swagger",
        timeSpent: "6h 00m",
        assignedUsers: [
          { name: "Mike Johnson", avatar: "/professional-man-avatar.png", initials: "MJ" },
          { name: "David Park", avatar: "/professional-man-avatar-2.png", initials: "DP" },
        ],
      },
    ],
  },
  {
    id: "4",
    name: "Marketing Campaign",
    color: "bg-chart-4",
    totalTimeThisMonth: "15h 20m",
    totalTasks: 6,
    completedTasks: 4,
    assignedUsers: [
      { name: "Emily Davis", avatar: "/professional-woman-avatar-2.png", initials: "ED" },
      { name: "Lisa Wang", avatar: "/professional-woman-avatar-3.jpg", initials: "LW" },
    ],
    tasks: [
      {
        id: "4-1",
        name: "Social media content",
        description: "Create posts for Instagram, Twitter, LinkedIn",
        timeSpent: "4h 30m",
        assignedUsers: [
          { name: "Lisa Wang", avatar: "/professional-woman-avatar-3.jpg", initials: "LW" },
        ],
      },
      {
        id: "4-2",
        name: "Email campaigns",
        description: "Design and send newsletter campaigns",
        timeSpent: "6h 15m",
        assignedUsers: [
          { name: "Emily Davis", avatar: "/professional-woman-avatar-2.png", initials: "ED" },
        ],
      },
      {
        id: "4-3",
        name: "Landing page copy",
        description: "Write compelling landing page content",
        timeSpent: "4h 35m",
        assignedUsers: [
          { name: "Emily Davis", avatar: "/professional-woman-avatar-2.png", initials: "ED" },
          { name: "Lisa Wang", avatar: "/professional-woman-avatar-3.jpg", initials: "LW" },
        ],
      },
    ],
  },
]

export function ProjectList() {
  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(new Set())
  const [isAddTaskDialogOpen, setIsAddTaskDialogOpen] = useState(false)
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const [newTaskName, setNewTaskName] = useState("")
  const [newTaskDescription, setNewTaskDescription] = useState("")

  const toggleProject = (projectId: string) => {
    setExpandedProjects((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(projectId)) {
        newSet.delete(projectId)
      } else {
        newSet.add(projectId)
      }
      return newSet
    })
  }

  const handleAddTask = (projectId: string) => {
    setSelectedProjectId(projectId)
    setIsAddTaskDialogOpen(true)
  }

  const handleSaveTask = () => {
    console.log("[v0] Adding task:", { projectId: selectedProjectId, name: newTaskName, description: newTaskDescription })
    setIsAddTaskDialogOpen(false)
    setNewTaskName("")
    setNewTaskDescription("")
    setSelectedProjectId(null)
  }

  return (
    <div className="space-y-4">
      {mockProjects.map((project) => {
        const isExpanded = expandedProjects.has(project.id)

        return (
          <Card key={project.id} className="overflow-hidden p-0">
            {/* Project Header - Clickable */}
            <div 
              className="p-6 cursor-pointer hover:bg-muted/50 transition-colors"
              onClick={() => toggleProject(project.id)}
            >
              <div className="flex items-center gap-4">
                <div className="flex items-center justify-center w-6 h-6">
                  {isExpanded ? (
                    <ChevronDown className="h-5 w-5 text-muted-foreground" />
                  ) : (
                    <ChevronRight className="h-5 w-5 text-muted-foreground" />
                  )}
                </div>

                <div className={cn("w-1 h-12 rounded-full", project.color)} />

                <div className="flex-1">
                  <h3 className="text-xl font-semibold">{project.name}</h3>
                </div>

                {/* Summary Stats */}
                <div className="flex items-center gap-6 text-sm">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">{project.totalTimeThisMonth}</span>
                    <span className="text-muted-foreground">this month</span>
                  </div>

                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-muted-foreground" />
                    <div className="flex -space-x-2">
                      {project.assignedUsers.slice(0, 3).map((user, idx) => (
                        <Avatar key={idx} className="h-8 w-8 border-2 border-card">
                          <AvatarImage src={user.avatar || "/placeholder.svg"} alt={user.name} />
                          <AvatarFallback>{user.initials}</AvatarFallback>
                        </Avatar>
                      ))}
                      {project.assignedUsers.length > 3 && (
                        <div className="flex items-center justify-center h-8 w-8 rounded-full bg-muted border-2 border-card text-xs font-medium">
                          +{project.assignedUsers.length - 3}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Expanded Task List */}
            {isExpanded && (
              <CardContent className="pt-0">
                <div className="space-y-3 ml-10">
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleAddTask(project.id)
                    }}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Task
                  </Button>

                  {project.tasks.map((task) => (
                    <div
                      key={task.id}
                      className="flex items-start gap-4 p-4 rounded-lg border bg-card hover:bg-muted/30 transition-colors"
                    >
                      <div className="flex-1 min-w-0">
                        <h4 className="font-semibold text-sm mb-1">{task.name}</h4>
                        <p className="text-sm text-muted-foreground">{task.description}</p>
                      </div>

                      <div className="flex items-center gap-4 shrink-0">
                        <div className="flex items-center gap-2 text-sm">
                          <Clock className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">{task.timeSpent}</span>
                        </div>

                        <div className="flex -space-x-2">
                          {task.assignedUsers.map((user, idx) => (
                            <Avatar
                              key={idx}
                              className="h-7 w-7 border-2 border-card"
                              title={user.name}
                            >
                              <AvatarImage src={user.avatar || "/placeholder.svg"} alt={user.name} />
                              <AvatarFallback>{user.initials}</AvatarFallback>
                            </Avatar>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            )}
          </Card>
        )
      })}

      <Dialog open={isAddTaskDialogOpen} onOpenChange={setIsAddTaskDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add New Task</DialogTitle>
            <DialogDescription>Create a new task for this project.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="task-name">Name</Label>
              <Input
                id="task-name"
                placeholder="Enter task name"
                value={newTaskName}
                onChange={(e) => setNewTaskName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="task-description">Description</Label>
              <Textarea
                id="task-description"
                placeholder="Enter task description"
                value={newTaskDescription}
                onChange={(e) => setNewTaskDescription(e.target.value)}
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsAddTaskDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveTask}>Add Task</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

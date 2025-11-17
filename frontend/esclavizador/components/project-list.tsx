"use client"

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
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
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { ChevronDown, ChevronRight, Clock, Plus, FolderKanban, Users, Trash2 } from 'lucide-react'
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"
import { EmptyState } from "@/components/empty-state"
import { useAuth } from "@/hooks/use-auth"
import { useTasks } from "@/hooks/use-tasks"
import type { ProjectResponse, TaskResponse } from "@/lib/api/generated"
import { Skeleton } from "@/components/ui/skeleton"

interface ProjectListProps {
  projects: ProjectResponse[]
  loading: boolean
  onDeleteProject?: (projectId: string) => Promise<void>
}

interface ProjectTasksState {
  [projectId: string]: {
    tasks: TaskResponse[]
    loading: boolean
  }
}

export function ProjectList({ projects, loading, onDeleteProject }: ProjectListProps) {
  const { user } = useAuth()
  const { createTask, deleteTask } = useTasks()
  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(new Set())
  const [projectTasks, setProjectTasks] = useState<ProjectTasksState>({})
  const [isAddTaskDialogOpen, setIsAddTaskDialogOpen] = useState(false)
  const [isAddProjectDialogOpen, setIsAddProjectDialogOpen] = useState(false)
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const [newTaskName, setNewTaskName] = useState("")
  const [newTaskDescription, setNewTaskDescription] = useState("")
  const [isCreatingTask, setIsCreatingTask] = useState(false)
  const [deleteProjectDialogOpen, setDeleteProjectDialogOpen] = useState(false)
  const [projectToDelete, setProjectToDelete] = useState<string | null>(null)
  const [deleteTaskDialogOpen, setDeleteTaskDialogOpen] = useState(false)
  const [taskToDelete, setTaskToDelete] = useState<{ taskId: string; projectId: string } | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const isBoss = user?.role === 'boss'

  // Fetch tasks when a project is expanded
  useEffect(() => {
    const loadTasksForExpandedProjects = async () => {
      const { listTasksApiV1TasksGet } = await import('@/lib/api/generated')
      const { getAuthHeaders } = await import('@/lib/api/client')

      for (const projectId of expandedProjects) {
        // Only fetch if we haven't already loaded tasks for this project
        if (!projectTasks[projectId]) {
          setProjectTasks(prev => ({
            ...prev,
            [projectId]: { tasks: [], loading: true }
          }))

          try {
            const { data, error } = await listTasksApiV1TasksGet({
              headers: getAuthHeaders(),
              query: {
                project_id: projectId,
                is_active: true,
                limit: 100,
                offset: 0,
              },
            })

            if (!error && data) {
              setProjectTasks(prev => ({
                ...prev,
                [projectId]: { tasks: data.items, loading: false }
              }))
            } else {
              setProjectTasks(prev => ({
                ...prev,
                [projectId]: { tasks: [], loading: false }
              }))
            }
          } catch (error) {
            setProjectTasks(prev => ({
              ...prev,
              [projectId]: { tasks: [], loading: false }
            }))
          }
        }
      }
    }

    if (expandedProjects.size > 0) {
      loadTasksForExpandedProjects()
    }
  }, [expandedProjects, projectTasks])

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

  const handleSaveTask = async () => {
    if (!selectedProjectId || !newTaskName.trim()) return

    setIsCreatingTask(true)
    try {
      await createTask({
        name: newTaskName,
        description: newTaskDescription || null,
        project_id: selectedProjectId,
      })

      // Refresh tasks for this project
      setProjectTasks(prev => {
        const updated = { ...prev }
        delete updated[selectedProjectId]
        return updated
      })

      setIsAddTaskDialogOpen(false)
      setNewTaskName("")
      setNewTaskDescription("")
      setSelectedProjectId(null)
    } catch (error) {
      // Error already shown via toast in hook
    } finally {
      setIsCreatingTask(false)
    }
  }

  const handleCreateProject = () => {
    setIsAddProjectDialogOpen(true)
  }

  const handleDeleteProjectClick = (projectId: string) => {
    setProjectToDelete(projectId)
    setDeleteProjectDialogOpen(true)
  }

  const handleConfirmDeleteProject = async () => {
    if (!projectToDelete || !onDeleteProject) return

    setIsDeleting(true)
    try {
      await onDeleteProject(projectToDelete)
      setDeleteProjectDialogOpen(false)
      setProjectToDelete(null)
    } catch (error) {
      // Error already shown via toast
    } finally {
      setIsDeleting(false)
    }
  }

  const handleDeleteTaskClick = (taskId: string, projectId: string) => {
    setTaskToDelete({ taskId, projectId })
    setDeleteTaskDialogOpen(true)
  }

  const handleConfirmDeleteTask = async () => {
    if (!taskToDelete) return

    setIsDeleting(true)
    try {
      await deleteTask(taskToDelete.taskId)

      // Invalidate cache for this project to force refetch on next expansion
      setProjectTasks(prev => {
        const updated = { ...prev }
        delete updated[taskToDelete.projectId]
        return updated
      })

      setDeleteTaskDialogOpen(false)
      setTaskToDelete(null)
    } catch (error) {
      // Error already shown via toast
    } finally {
      setIsDeleting(false)
    }
  }

  // Show loading skeleton
  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="p-6">
            <div className="flex items-center gap-4">
              <Skeleton className="h-5 w-5" />
              <Skeleton className="w-1 h-12 rounded-full" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-6 w-48" />
              </div>
              <Skeleton className="h-4 w-32" />
            </div>
          </Card>
        ))}
      </div>
    )
  }

  // Show empty state when no projects
  if (projects.length === 0) {
    return (
      <EmptyState
        icon={FolderKanban}
        title={isBoss ? "No projects yet" : "No projects available"}
        description={
          isBoss
            ? "Create your first project to start tracking time and organizing tasks."
            : "Your organization doesn't have any projects yet. Contact your admin to create projects."
        }
        action={
          isBoss
            ? {
                label: "Create Project",
                onClick: handleCreateProject,
              }
            : undefined
        }
      />
    )
  }

  return (
    <div className="space-y-4">
      {projects.map((project) => {
        const isExpanded = expandedProjects.has(project.id)
        const tasksState = projectTasks[project.id]
        const projectTasksList = tasksState?.tasks || []
        const tasksLoading = tasksState?.loading || false

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

                <div className="w-1 h-12 rounded-full bg-chart-1" />

                <div className="flex-1">
                  <h3 className="text-xl font-semibold">{project.name}</h3>
                  {project.description && (
                    <p className="text-sm text-muted-foreground mt-1">{project.description}</p>
                  )}
                </div>

                {/* Task count and delete button */}
                <div className="flex items-center gap-3">
                  {isExpanded && (
                    <div className="text-sm text-muted-foreground">
                      {projectTasksList.length} {projectTasksList.length === 1 ? 'task' : 'tasks'}
                    </div>
                  )}
                  {isBoss && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDeleteProjectClick(project.id)
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            </div>

            {/* Expanded Task List */}
            {isExpanded && (
              <CardContent className="pt-4 px-6 pb-6">
                <div className="space-y-3">
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

                  {tasksLoading ? (
                    <div className="space-y-3">
                      {[1, 2].map((i) => (
                        <div key={i} className="p-4 rounded-lg border">
                          <Skeleton className="h-4 w-32 mb-2" />
                          <Skeleton className="h-3 w-full" />
                        </div>
                      ))}
                    </div>
                  ) : projectTasksList.length === 0 ? (
                    <div className="p-8 text-center text-sm text-muted-foreground">
                      No tasks yet. Click "Add Task" to create one.
                    </div>
                  ) : (
                    projectTasksList.map((task) => (
                      <div
                        key={task.id}
                        className="flex items-start gap-4 p-4 rounded-lg border bg-card hover:bg-muted/30 transition-colors"
                      >
                        <div className="flex-1 min-w-0">
                          <h4 className="font-semibold text-sm mb-1">{task.name}</h4>
                          {task.description && (
                            <p className="text-sm text-muted-foreground">{task.description}</p>
                          )}
                        </div>
                        {isBoss && (
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDeleteTaskClick(task.id, project.id)
                            }}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    ))
                  )}
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
            <Button
              variant="outline"
              onClick={() => setIsAddTaskDialogOpen(false)}
              disabled={isCreatingTask}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSaveTask}
              disabled={isCreatingTask || !newTaskName.trim()}
            >
              {isCreatingTask ? "Creating..." : "Add Task"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Project Confirmation Dialog */}
      <AlertDialog open={deleteProjectDialogOpen} onOpenChange={setDeleteProjectDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Project</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this project? This action cannot be undone and will also delete all tasks associated with this project.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDeleteProject}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete Task Confirmation Dialog */}
      <AlertDialog open={deleteTaskDialogOpen} onOpenChange={setDeleteTaskDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Task</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this task? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDeleteTask}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

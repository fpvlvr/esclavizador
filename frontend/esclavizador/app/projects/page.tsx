"use client"

import { useState } from "react"
import { ProtectedRoute } from "@/components/protected-route"
import { Sidebar } from "@/components/sidebar"
import { ProjectList } from "@/components/project-list"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Plus } from 'lucide-react'
import { useProjects } from "@/hooks/use-projects"
import { useAuth } from "@/hooks/use-auth"

export default function ProjectsPage() {
  const { user } = useAuth()
  const { projects, loading, createProject } = useProjects()
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [projectName, setProjectName] = useState("")
  const [projectDescription, setProjectDescription] = useState("")
  const [isCreating, setIsCreating] = useState(false)

  const isBoss = user?.role === 'boss'

  const handleAddProject = async () => {
    if (!projectName.trim()) return

    setIsCreating(true)
    try {
      await createProject({
        name: projectName,
        description: projectDescription || null,
      })
      setIsDialogOpen(false)
      setProjectName("")
      setProjectDescription("")
    } catch (error) {
      // Error already shown via toast in hook
    } finally {
      setIsCreating(false)
    }
  }

  return (
    <ProtectedRoute>
      <div className="flex min-h-screen bg-background">
        <Sidebar />

        <main className="flex-1 lg:ml-64">
          <div className="container mx-auto p-4 lg:p-8 space-y-6">
            <div className="flex items-center justify-between">
              <h1 className="text-3xl font-bold text-balance">Projects</h1>

              {isBoss && (
                <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                  <DialogTrigger asChild>
                    <Button>
                      <Plus className="mr-2 h-4 w-4" />
                      Add Project
                    </Button>
                  </DialogTrigger>
                <DialogContent className="sm:max-w-[500px]">
                  <DialogHeader>
                    <DialogTitle>Add New Project</DialogTitle>
                    <DialogDescription>
                      Create a new project to organize your tasks and track time.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="grid gap-4 py-4">
                    <div className="grid gap-2">
                      <Label htmlFor="project-name">Name</Label>
                      <Input
                        id="project-name"
                        placeholder="Enter project name"
                        value={projectName}
                        onChange={(e) => setProjectName(e.target.value)}
                      />
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="project-description">Description</Label>
                      <Textarea
                        id="project-description"
                        placeholder="Enter project description"
                        value={projectDescription}
                        onChange={(e) => setProjectDescription(e.target.value)}
                        rows={4}
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsDialogOpen(false)} disabled={isCreating}>
                      Cancel
                    </Button>
                    <Button onClick={handleAddProject} disabled={isCreating || !projectName.trim()}>
                      {isCreating ? "Creating..." : "Add Project"}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
              )}
            </div>

            <ProjectList projects={projects} loading={loading} />
          </div>
        </main>
      </div>
    </ProtectedRoute>
  )
}

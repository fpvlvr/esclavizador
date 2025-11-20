"use client"

import { useState, useMemo } from "react"
import { HexColorPicker } from "react-colorful"
import { ProtectedRoute } from "@/components/protected-route"
import { Sidebar } from "@/components/sidebar"
import { ProjectList } from "@/components/project-list"
import { SearchInput } from "@/components/search-input"
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
  const { projects, loading, createProject, updateProject, deleteProject } = useProjects()
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [projectName, setProjectName] = useState("")
  const [projectDescription, setProjectDescription] = useState("")
  const [selectedColor, setSelectedColor] = useState("#3b82f6")
  const [isCreating, setIsCreating] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")

  const isBoss = user?.role === 'boss'

  // Filter projects based on search query
  const filteredProjects = useMemo(() => {
    if (!searchQuery.trim()) return projects
    const query = searchQuery.toLowerCase()
    return projects.filter((project) =>
      project.name.toLowerCase().includes(query) ||
      project.description?.toLowerCase().includes(query)
    )
  }, [projects, searchQuery])

  const handleAddProject = async () => {
    if (!projectName.trim()) return

    setIsCreating(true)
    try {
      await createProject({
        name: projectName,
        description: projectDescription || null,
        color: selectedColor,
      })
      setIsDialogOpen(false)
      setProjectName("")
      setProjectDescription("")
      setSelectedColor("#3b82f6")
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

              <div className="flex items-center gap-4">
                <SearchInput
                  placeholder="Search projects..."
                  value={searchQuery}
                  onChange={setSearchQuery}
                />
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
                    <div className="grid gap-2">
                      <Label>Color</Label>
                      <div className="flex gap-4 items-start">
                        <HexColorPicker color={selectedColor} onChange={setSelectedColor} />
                        <div className="flex flex-col gap-2">
                          <div
                            className="h-16 w-16 rounded-md border border-border"
                            style={{ backgroundColor: selectedColor }}
                          />
                          <Input
                            value={selectedColor}
                            onChange={(e) => setSelectedColor(e.target.value)}
                            placeholder="#000000"
                            className="w-28 text-xs font-mono"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setIsDialogOpen(false)
                        setProjectName("")
                        setProjectDescription("")
                        setSelectedColor("#3b82f6")
                      }}
                      disabled={isCreating}
                    >
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
            </div>

            <ProjectList projects={filteredProjects} loading={loading} onUpdateProject={updateProject} onDeleteProject={deleteProject} />
          </div>
        </main>
      </div>
    </ProtectedRoute>
  )
}

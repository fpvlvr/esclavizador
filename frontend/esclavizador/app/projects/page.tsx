"use client"

import { useState } from "react"
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

export default function ProjectsPage() {
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [projectName, setProjectName] = useState("")
  const [projectDescription, setProjectDescription] = useState("")

  const handleAddProject = () => {
    // TODO: Add logic to actually create the project
    console.log("Adding project:", { name: projectName, description: projectDescription })
    setIsDialogOpen(false)
    setProjectName("")
    setProjectDescription("")
  }

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <main className="flex-1 lg:ml-64">
        <div className="container mx-auto p-4 lg:p-8 space-y-6">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold text-balance">Projects</h1>
            
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
                  <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleAddProject}>Add Project</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
          
          <ProjectList />
        </div>
      </main>
    </div>
  )
}

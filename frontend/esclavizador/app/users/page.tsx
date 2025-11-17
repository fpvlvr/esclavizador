"use client"

import { useState } from "react"
import { ProtectedRoute } from "@/components/protected-route"
import { Sidebar } from "@/components/sidebar"
import { Plus, Trash2, Pencil } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

interface User {
  id: string
  name: string
  email: string
  avatar: string
  totalTime: string
  projects: { name: string; color: string }[]
  role: "Worker" | "Boss"
}

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([
    {
      id: "1",
      name: "Sarah Chen",
      email: "sarah@company.com",
      avatar: "/professional-woman-avatar.png",
      totalTime: "142h 35m",
      role: "Worker",
      projects: [
        { name: "Website Redesign", color: "#3b82f6" },
        { name: "Marketing Campaign", color: "#10b981" },
      ],
    },
    {
      id: "2",
      name: "Mike Torres",
      email: "mike@company.com",
      avatar: "/professional-man-avatar.png",
      totalTime: "98h 22m",
      role: "Worker",
      projects: [
        { name: "Mobile App", color: "#f59e0b" },
      ],
    },
    {
      id: "3",
      name: "Emma Watson",
      email: "emma@company.com",
      avatar: "/professional-woman-avatar-2.png",
      totalTime: "156h 10m",
      role: "Boss",
      projects: [
        { name: "Website Redesign", color: "#3b82f6" },
        { name: "Mobile App", color: "#f59e0b" },
        { name: "API Development", color: "#8b5cf6" },
        { name: "Marketing Campaign", color: "#10b981" },
        { name: "Client Portal", color: "#ef4444" },
      ],
    },
    {
      id: "4",
      name: "Alex Kim",
      email: "alex@company.com",
      avatar: "/professional-man-avatar-2.png",
      totalTime: "87h 45m",
      role: "Worker",
      projects: [
        { name: "Marketing Campaign", color: "#10b981" },
        { name: "API Development", color: "#8b5cf6" },
      ],
    },
  ])

  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    role: "Worker" as "Worker" | "Boss",
  })

  const handleAddUser = (e: React.FormEvent) => {
    e.preventDefault()
    // Add new user logic here
    console.log("Adding new user:", formData)
    setIsAddDialogOpen(false)
    setFormData({ name: "", email: "", password: "", role: "Worker" })
  }

  const handleEditUser = (e: React.FormEvent) => {
    e.preventDefault()
    if (selectedUser) {
      setUsers(
        users.map((user) =>
          user.id === selectedUser.id
            ? { ...user, name: formData.name, email: formData.email, role: formData.role }
            : user
        )
      )
    }
    setIsEditDialogOpen(false)
    setSelectedUser(null)
  }

  const openEditDialog = (user: User) => {
    setSelectedUser(user)
    setFormData({
      name: user.name,
      email: user.email,
      password: "",
      role: user.role,
    })
    setIsEditDialogOpen(true)
  }

  const handleDeleteUser = (id: string) => {
    setUsers(users.filter((user) => user.id !== id))
  }

  return (
    <ProtectedRoute>
      <div className="flex min-h-screen bg-background">
        <Sidebar />
        <main className="flex-1 lg:ml-64 p-8">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-foreground">Bosses & Workers</h1>
              <p className="text-muted-foreground mt-1">
                Manage your team members and their access
              </p>
            </div>
            <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
              <DialogTrigger asChild>
                <Button size="lg" className="gap-2">
                  <Plus className="h-5 w-5" />
                  Add Worker
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-md">
                <form onSubmit={handleAddUser}>
                  <DialogHeader>
                    <DialogTitle>Add New Worker</DialogTitle>
                    <DialogDescription>
                      Enter the details for the new team member
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="add-name">Name</Label>
                      <Input
                        id="add-name"
                        placeholder="John Doe"
                        value={formData.name}
                        onChange={(e) =>
                          setFormData({ ...formData, name: e.target.value })
                        }
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="add-email">Email</Label>
                      <Input
                        id="add-email"
                        type="email"
                        placeholder="john@company.com"
                        value={formData.email}
                        onChange={(e) =>
                          setFormData({ ...formData, email: e.target.value })
                        }
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="add-password">Temporary Password</Label>
                      <Input
                        id="add-password"
                        type="password"
                        placeholder="••••••••"
                        value={formData.password}
                        onChange={(e) =>
                          setFormData({ ...formData, password: e.target.value })
                        }
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="add-role">Role</Label>
                      <Select
                        value={formData.role}
                        onValueChange={(value: "Worker" | "Boss") =>
                          setFormData({ ...formData, role: value })
                        }
                      >
                        <SelectTrigger id="add-role">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Worker">Worker</SelectItem>
                          <SelectItem value="Boss">Boss</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setIsAddDialogOpen(false)}
                    >
                      Cancel
                    </Button>
                    <Button type="submit">Add Worker</Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
            <DialogContent className="sm:max-w-md">
              <form onSubmit={handleEditUser}>
                <DialogHeader>
                  <DialogTitle>Edit Worker</DialogTitle>
                  <DialogDescription>
                    Update the details for this team member
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label htmlFor="edit-name">Name</Label>
                    <Input
                      id="edit-name"
                      placeholder="John Doe"
                      value={formData.name}
                      onChange={(e) =>
                        setFormData({ ...formData, name: e.target.value })
                      }
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="edit-email">Email</Label>
                    <Input
                      id="edit-email"
                      type="email"
                      placeholder="john@company.com"
                      value={formData.email}
                      onChange={(e) =>
                        setFormData({ ...formData, email: e.target.value })
                      }
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="edit-role">Role</Label>
                    <Select
                      value={formData.role}
                      onValueChange={(value: "Worker" | "Boss") =>
                        setFormData({ ...formData, role: value })
                      }
                    >
                      <SelectTrigger id="edit-role">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Worker">Worker</SelectItem>
                        <SelectItem value="Boss">Boss</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setIsEditDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit">Save Changes</Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>

          {/* Users List */}
          <div className="space-y-4">
            {users.map((user) => {
              const maxVisibleProjects = 3
              const visibleProjects = user.projects.slice(0, maxVisibleProjects)
              const overflowCount = Math.max(0, user.projects.length - maxVisibleProjects)

              return (
                <div
                  key={user.id}
                  className={`bg-card rounded-lg p-6 hover:shadow-md transition-shadow ${
                    user.role === "Boss" 
                      ? "border-0" 
                      : "border border-border"
                  }`}
                >
                  <div className="flex items-start justify-between gap-6">
                    <div className="flex items-center gap-4">
                      {/* Avatar */}
                      <img
                        src={user.avatar || "/placeholder.svg"}
                        alt={user.name}
                        className="h-12 w-12 rounded-full object-cover"
                      />

                      {/* Info */}
                      <div className="min-w-[200px]">
                        <div className="flex items-center gap-2">
                          <h3 className="text-lg font-semibold text-foreground">
                            {user.name}
                          </h3>
                          {user.role === "Boss" && (
                            <Badge variant="secondary" className="text-xs bg-gray-400 dark:bg-gray-400 text-white border-gray-500">
                              Boss
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {user.email}
                        </p>
                      </div>
                    </div>

                    {/* Projects */}
                    <div className="min-w-[200px] flex-1">
                      <p className="text-sm text-muted-foreground mb-2">
                        Projects
                      </p>
                      <div className="space-y-1.5">
                        {visibleProjects.map((project, idx) => (
                          <div
                            key={idx}
                            className="flex items-center gap-2 text-sm"
                          >
                            <div
                              className="h-2 w-2 rounded-full flex-shrink-0"
                              style={{ backgroundColor: project.color }}
                            />
                            <span className="text-foreground truncate">
                              {project.name}
                            </span>
                          </div>
                        ))}
                        {overflowCount > 0 && (
                          <p className="text-sm text-muted-foreground pl-4">
                            and {overflowCount} more
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Total Time */}
                    <div className="text-right min-w-[140px]">
                      <p className="text-sm text-muted-foreground mb-1">
                        Total time this month
                      </p>
                      <p className="text-xl font-bold text-foreground">
                        {user.totalTime}
                      </p>
                    </div>

                    <div className="flex items-center gap-2 flex-shrink-0">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-muted-foreground hover:text-foreground hover:bg-accent"
                        onClick={() => openEditDialog(user)}
                      >
                        <Pencil className="h-5 w-5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-destructive hover:text-destructive hover:bg-destructive/10"
                        onClick={() => handleDeleteUser(user.id)}
                      >
                        <Trash2 className="h-5 w-5" />
                      </Button>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </main>
    </div>
    </ProtectedRoute>
  )
}

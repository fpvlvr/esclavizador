"use client"

import { useState, useMemo } from "react"
import { ProtectedRoute } from "@/components/protected-route"
import { Sidebar } from "@/components/sidebar"
import { UserList } from "@/components/user-list"
import { SearchInput } from "@/components/search-input"
import { useUsers } from "@/hooks/use-users"
import { useAuth } from "@/hooks/use-auth"
import { Plus } from 'lucide-react'
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
import { PasswordInput } from "@/components/ui/password-input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { UserStatsResponse } from "@/lib/api/generated"

export default function UsersPage() {
  const { user: currentUser } = useAuth()
  const { users, loading, createUser, updateUser, deleteUser } = useUsers()

  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState<UserStatsResponse | null>(null)
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    role: "worker" as "worker" | "boss",
  })
  const [editPassword, setEditPassword] = useState("")
  const [isActive, setIsActive] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")

  const isBoss = currentUser?.role === "boss"

  // Filter users based on search query
  const filteredUsers = useMemo(() => {
    if (!searchQuery.trim()) return users
    const query = searchQuery.toLowerCase()
    return users.filter((user) =>
      user.email.toLowerCase().includes(query) ||
      user.role.toLowerCase().includes(query)
    )
  }, [users, searchQuery])

  const resetForm = () => {
    setFormData({
      email: "",
      password: "",
      role: "worker",
    })
    setEditPassword("")
    setIsActive(true)
  }

  const handleAddUser = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      await createUser({
        email: formData.email,
        password: formData.password,
        role: formData.role,
      })
      setIsAddDialogOpen(false)
      resetForm()
    } catch (error) {
      // Error already shown via toast in hook
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleEditUser = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedUser) return

    setIsSubmitting(true)

    try {
      const updateData: { role?: "worker" | "boss"; is_active?: boolean; password?: string } = {
        role: formData.role,
        is_active: isActive,
      }
      
      // Only include password if it's provided and user is a worker
      if (editPassword.trim() && selectedUser.role === "worker") {
        updateData.password = editPassword
      }

      await updateUser(selectedUser.id, updateData)
      setIsEditDialogOpen(false)
      setSelectedUser(null)
      resetForm()
    } catch (error) {
      // Error already shown via toast in hook
    } finally {
      setIsSubmitting(false)
    }
  }

  const openEditDialog = (user: UserStatsResponse) => {
    setSelectedUser(user)
    setFormData({
      email: user.email,
      password: "",
      role: user.role,
    })
    setEditPassword("")
    setIsActive(user.is_active)
    setIsEditDialogOpen(true)
  }

  const handleDelete = async (userId: string) => {
    await deleteUser(userId)
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
              <div className="flex items-center gap-4">
                <SearchInput
                  placeholder="Search users..."
                  value={searchQuery}
                  onChange={setSearchQuery}
                />
                {isBoss && (
                <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
                  <DialogTrigger asChild>
                    <Button size="lg" className="gap-2">
                      <Plus className="h-5 w-5" />
                      Add User
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="sm:max-w-md">
                    <form onSubmit={handleAddUser}>
                      <DialogHeader>
                        <DialogTitle>Add New User</DialogTitle>
                        <DialogDescription>
                          Enter the details for the new team member
                        </DialogDescription>
                      </DialogHeader>
                      <div className="space-y-4 py-4">
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
                            disabled={isSubmitting}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="add-password">Password</Label>
                          <PasswordInput
                            id="add-password"
                            placeholder="Min 8 chars, uppercase, lowercase, digit, special char"
                            value={formData.password}
                            onChange={(e) =>
                              setFormData({ ...formData, password: e.target.value })
                            }
                            required
                            disabled={isSubmitting}
                          />
                          <p className="text-xs text-muted-foreground">
                            Must be 8-128 characters with uppercase, lowercase, digit, and special character
                          </p>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="add-role">Role</Label>
                          <Select
                            value={formData.role}
                            onValueChange={(value: "worker" | "boss") =>
                              setFormData({ ...formData, role: value })
                            }
                            disabled={isSubmitting}
                          >
                            <SelectTrigger id="add-role">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="worker">Worker</SelectItem>
                              <SelectItem value="boss">Boss</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      <DialogFooter>
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => {
                            setIsAddDialogOpen(false)
                            resetForm()
                          }}
                          disabled={isSubmitting}
                        >
                          Cancel
                        </Button>
                        <Button type="submit" disabled={isSubmitting}>
                          {isSubmitting ? "Adding..." : "Add User"}
                        </Button>
                      </DialogFooter>
                    </form>
                  </DialogContent>
                </Dialog>
                )}
              </div>
            </div>

            {/* Edit User Dialog */}
            <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
              <DialogContent className="sm:max-w-md">
                <form onSubmit={handleEditUser}>
                  <DialogHeader>
                    <DialogTitle>Edit User</DialogTitle>
                    <DialogDescription>
                      Update the role, status, and password for this team member. Password can only be updated for workers.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="edit-role">Role</Label>
                      <Select
                        value={formData.role}
                        onValueChange={(value: "worker" | "boss") => {
                          setFormData({ ...formData, role: value })
                          // Clear password if changing to boss
                          if (value === "boss") {
                            setEditPassword("")
                          }
                        }}
                        disabled={isSubmitting}
                      >
                        <SelectTrigger id="edit-role">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="worker">Worker</SelectItem>
                          <SelectItem value="boss">Boss</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="edit-status">Status</Label>
                      <Select
                        value={isActive ? "active" : "inactive"}
                        onValueChange={(value) => setIsActive(value === "active")}
                        disabled={isSubmitting}
                      >
                        <SelectTrigger id="edit-status">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="active">Active</SelectItem>
                          <SelectItem value="inactive">Inactive</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    {selectedUser && formData.role === "worker" && (
                      <div className="space-y-2">
                        <Label htmlFor="edit-password">New Password (optional)</Label>
                        <PasswordInput
                          id="edit-password"
                          placeholder="Leave empty to keep current password"
                          value={editPassword}
                          onChange={(e) => setEditPassword(e.target.value)}
                          disabled={isSubmitting}
                        />
                        <p className="text-xs text-muted-foreground">
                          Must be 8-128 characters with uppercase, lowercase, digit, and special character
                        </p>
                      </div>
                    )}
                    {selectedUser && formData.role === "boss" && (
                      <p className="text-xs text-muted-foreground">
                        Password updates are only available for workers
                      </p>
                    )}
                  </div>
                  <DialogFooter>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => {
                        setIsEditDialogOpen(false)
                        setSelectedUser(null)
                        resetForm()
                      }}
                      disabled={isSubmitting}
                    >
                      Cancel
                    </Button>
                    <Button type="submit" disabled={isSubmitting}>
                      {isSubmitting ? "Saving..." : "Save Changes"}
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>

            {/* Users List */}
            <UserList
              users={filteredUsers}
              loading={loading}
              isBoss={isBoss}
              onEdit={openEditDialog}
              onDelete={handleDelete}
            />
          </div>
        </main>
      </div>
    </ProtectedRoute>
  )
}

"use client"

import { useState } from "react"
import { Trash2, Pencil } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
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
import type { UserStatsResponse } from "@/lib/api/generated"

interface UserListProps {
  users: UserStatsResponse[]
  loading: boolean
  isBoss: boolean
  onEdit: (user: UserStatsResponse) => void
  onDelete: (userId: string) => Promise<void>
}

function formatTime(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return `${hours}h ${minutes}m`
}

export function UserList({ users, loading, isBoss, onEdit, onDelete }: UserListProps) {
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [userToDelete, setUserToDelete] = useState<string | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const handleDeleteClick = (userId: string) => {
    setUserToDelete(userId)
    setDeleteDialogOpen(true)
  }

  const handleConfirmDelete = async () => {
    if (!userToDelete) return

    setIsDeleting(true)
    try {
      await onDelete(userToDelete)
      setDeleteDialogOpen(false)
      setUserToDelete(null)
    } catch (error) {
      // Error already shown via toast
    } finally {
      setIsDeleting(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-card rounded-lg p-6 border border-border">
            <div className="flex items-start justify-between gap-6">
              <div className="flex items-center gap-4">
                <Skeleton className="h-12 w-12 rounded-full" />
                <div className="space-y-2">
                  <Skeleton className="h-5 w-32" />
                  <Skeleton className="h-4 w-48" />
                </div>
              </div>
              <div className="min-w-[200px]">
                <Skeleton className="h-4 w-16 mb-2" />
                <div className="space-y-1.5">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-full" />
                </div>
              </div>
              <div className="text-right min-w-[140px]">
                <Skeleton className="h-4 w-24 mb-1" />
                <Skeleton className="h-6 w-20" />
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (users.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">No users found</p>
      </div>
    )
  }

  return (
    <>
      <div className="space-y-4">
        {users.map((user) => {
          const maxVisibleProjects = 3
          const visibleProjects = user.projects.slice(0, maxVisibleProjects)
          const overflowCount = Math.max(0, user.projects.length - maxVisibleProjects)

          return (
            <div
              key={user.id}
              className={`bg-card rounded-lg p-6 hover:shadow-md transition-shadow ${
                user.role === "boss"
                  ? "border-0"
                  : "border border-border"
              }`}
            >
              <div className="flex items-start justify-between gap-6">
                <div className="flex items-center gap-4">
                  {/* Avatar - using initials */}
                  <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                    <span className="text-sm font-semibold text-primary">
                      {user.email.charAt(0).toUpperCase()}
                    </span>
                  </div>

                  {/* Info */}
                  <div className="min-w-[200px]">
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-semibold text-foreground">
                        {user.email.split('@')[0]}
                      </h3>
                      {user.role === "boss" && (
                        <Badge variant="secondary" className="text-xs bg-gray-400 dark:bg-gray-400 text-white border-gray-500">
                          Boss
                        </Badge>
                      )}
                      {!user.is_active && (
                        <Badge variant="outline" className="text-xs">
                          Inactive
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
                  {user.projects.length > 0 ? (
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
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      No projects this month
                    </p>
                  )}
                </div>

                {/* Total Time */}
                <div className="text-right min-w-[140px]">
                  <p className="text-sm text-muted-foreground mb-1">
                    Total time this month
                  </p>
                  <p className="text-xl font-bold text-foreground">
                    {formatTime(user.total_time_seconds)}
                  </p>
                </div>

                {/* Actions (Boss only) */}
                {isBoss && (
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-muted-foreground hover:text-foreground hover:bg-accent"
                      onClick={() => onEdit(user)}
                    >
                      <Pencil className="h-5 w-5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-destructive hover:text-destructive hover:bg-destructive/10"
                      onClick={() => handleDeleteClick(user.id)}
                    >
                      <Trash2 className="h-5 w-5" />
                    </Button>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete User</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this user? This action cannot be undone and will also delete all time entries associated with this user.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}

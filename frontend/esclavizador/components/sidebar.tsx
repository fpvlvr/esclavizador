"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Clock, FolderKanban, Settings, Menu, X, Timer, LogOut, ChevronUp, Users, BarChart3 } from 'lucide-react'
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"
import { useAuth } from "@/hooks/use-auth"
import { SettingsDialog } from "@/components/settings-dialog"
import { AccountSettingsDialog } from "@/components/account-settings-dialog"

const navigation = [
  { name: "Timer", href: "/", icon: Timer },
  { name: "Projects", href: "/projects", icon: FolderKanban },
  { name: "Reports", href: "/reports", icon: BarChart3 },
  { name: "Bosses & Workers", href: "/users", icon: Users },
  { name: "Settings", href: "#", icon: Settings, isButton: true },
]

export function Sidebar() {
  const [isOpen, setIsOpen] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [accountSettingsOpen, setAccountSettingsOpen] = useState(false)
  const pathname = usePathname()
  const { user, logout } = useAuth()

  const handleLogout = async () => {
    await logout()
  }

  // Get user initials for avatar
  const getInitials = (email: string) => {
    const parts = email.split('@')[0].split('.')
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
    }
    return email.substring(0, 2).toUpperCase()
  }

  return (
    <>
      {/* Mobile menu button */}
      <Button
        variant="ghost"
        size="icon"
        className="fixed top-4 left-4 z-50 lg:hidden bg-card"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </Button>

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 w-64 bg-card border-r border-border transition-transform duration-300 lg:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center gap-2 p-6 border-b border-border">
            <Clock className="h-6 w-6 text-primary" />
            <span className="text-xl font-semibold">{user?.organization_name || "Esclavizador"}</span>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1">
            {navigation
              .filter((item) => {
                // Hide "Bosses & Workers" for workers
                if (item.href === "/users" && user?.role === "worker") {
                  return false
                }
                return true
              })
              .map((item) => {
              const isActive = pathname === item.href
              if (item.isButton) {
                return (
                  <button
                    key={item.name}
                    onClick={() => {
                      setSettingsOpen(true)
                      setIsOpen(false)
                    }}
                    className={cn(
                      "w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors",
                      "text-muted-foreground hover:bg-muted hover:text-foreground",
                    )}
                  >
                    <item.icon className="h-5 w-5" />
                    {item.name}
                  </button>
                )
              }
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  onClick={() => setIsOpen(false)}
                  className={cn(
                    "flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground",
                  )}
                >
                  <item.icon className="h-5 w-5" />
                  {item.name}
                </Link>
              )
            })}
          </nav>

          {/* User section */}
          <div className="p-4 border-t border-border">
            {user && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    className="w-full flex items-center gap-3 px-4 py-3 h-auto hover:bg-muted"
                  >
                    <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center">
                      <span className="text-sm font-medium text-primary">
                        {getInitials(user.email)}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0 text-left">
                      <p className="text-sm font-medium truncate">{user.email}</p>
                      <p className="text-xs text-muted-foreground truncate capitalize">
                        {user.role}
                      </p>
                    </div>
                    <ChevronUp className="h-4 w-4 text-muted-foreground" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuItem className="cursor-pointer" onClick={() => setAccountSettingsOpen(true)}>
                    <Settings className="mr-2 h-4 w-4" />
                    Account Settings
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem className="cursor-pointer text-destructive" onClick={handleLogout}>
                    <LogOut className="mr-2 h-4 w-4" />
                    Log out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>
        </div>
      </aside>

      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-background/80 backdrop-blur-sm lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      <SettingsDialog open={settingsOpen} onOpenChange={setSettingsOpen} />
      {user && (
        <AccountSettingsDialog 
          open={accountSettingsOpen} 
          onOpenChange={setAccountSettingsOpen}
          role={user.role}
        />
      )}
    </>
  )
}

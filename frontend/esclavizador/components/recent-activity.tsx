"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

const teammates = [
  {
    id: "1",
    name: "Sarah Chen",
    avatar: "/professional-woman-avatar.png",
    project: "Client Website",
    projectColor: "bg-chart-1",
    lastActive: "Active now",
    initials: "SC",
  },
  {
    id: "2",
    name: "Michael Rodriguez",
    avatar: "/professional-man-avatar.png",
    project: "Mobile App",
    projectColor: "bg-chart-2",
    lastActive: "15 minutes ago",
    initials: "MR",
  },
  {
    id: "3",
    name: "Emily Watson",
    avatar: "/professional-woman-avatar-2.png",
    project: "Dashboard Design",
    projectColor: "bg-chart-3",
    lastActive: "1 hour ago",
    initials: "EW",
  },
  {
    id: "4",
    name: "David Kim",
    avatar: "/professional-man-avatar-2.png",
    project: "API Development",
    projectColor: "bg-chart-4",
    lastActive: "2 hours ago",
    initials: "DK",
  },
  {
    id: "5",
    name: "Jessica Park",
    avatar: "/professional-woman-avatar-3.jpg",
    project: "Client Website",
    projectColor: "bg-chart-1",
    lastActive: "3 hours ago",
    initials: "JP",
  },
]

export function RecentActivity() {
  return (
    <Card className="border-border">
      <CardHeader>
        <CardTitle>Working alongside you</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {teammates.map((teammate) => (
            <div key={teammate.id} className="flex items-center gap-3">
              <Avatar className="h-9 w-9">
                <AvatarImage src={teammate.avatar || "/placeholder.svg"} alt={teammate.name} />
                <AvatarFallback>{teammate.initials}</AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0 space-y-1">
                <p className="text-sm font-medium">{teammate.name}</p>
                <div className="flex items-center gap-2">
                  <div className={`h-2 w-2 rounded-full ${teammate.projectColor}`} />
                  <p className="text-xs text-muted-foreground">{teammate.project}</p>
                </div>
              </div>
              <p className="text-xs text-muted-foreground whitespace-nowrap">{teammate.lastActive}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

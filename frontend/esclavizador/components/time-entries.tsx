"use client"

import { MoreHorizontal, Play, Trash2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Badge } from "@/components/ui/badge"

const entries = [
  {
    id: "1",
    description: "Design homepage mockup",
    project: "Client Website",
    projectColor: "bg-chart-1",
    duration: "2:45:30",
    date: "Today",
    time: "09:00 - 11:45",
  },
  {
    id: "2",
    description: "API endpoint implementation",
    project: "API Development",
    projectColor: "bg-chart-4",
    duration: "1:30:15",
    date: "Today",
    time: "13:00 - 14:30",
  },
  {
    id: "3",
    description: "Client meeting and feedback review",
    project: "Mobile App",
    projectColor: "bg-chart-2",
    duration: "1:00:00",
    date: "Yesterday",
    time: "15:00 - 16:00",
  },
  {
    id: "4",
    description: "Dashboard components styling",
    project: "Dashboard Design",
    projectColor: "bg-chart-3",
    duration: "3:20:45",
    date: "Yesterday",
    time: "10:00 - 13:20",
  },
  {
    id: "5",
    description: "Bug fixes and testing",
    project: "Mobile App",
    projectColor: "bg-chart-2",
    duration: "2:15:00",
    date: "2 days ago",
    time: "14:00 - 16:15",
  },
]

export function TimeEntries() {
  return (
    <Card className="border-border">
      <CardHeader>
        <CardTitle>Recent Time Entries</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {entries.map((entry) => (
            <div
              key={entry.id}
              className="flex items-center gap-4 p-4 rounded-lg hover:bg-muted/50 transition-colors group"
            >
              <div className={`h-10 w-1 rounded-full ${entry.projectColor}`} />

              <div className="flex-1 min-w-0 space-y-1">
                <p className="font-medium text-sm truncate">{entry.description}</p>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span>{entry.project}</span>
                  <span>•</span>
                  <span>{entry.time}</span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Badge variant="secondary" className="font-mono">
                  {entry.duration}
                </Badge>

                <Button size="icon" variant="ghost" className="opacity-0 group-hover:opacity-100 transition-opacity">
                  <Play className="h-4 w-4" />
                </Button>

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      size="icon"
                      variant="ghost"
                      className="opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem>Edit</DropdownMenuItem>
                    <DropdownMenuItem>Duplicate</DropdownMenuItem>
                    <DropdownMenuItem className="text-destructive">
                      <Trash2 className="h-4 w-4 mr-2" />
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

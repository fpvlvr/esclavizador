import { ProtectedRoute } from "@/components/protected-route"
import { Sidebar } from "@/components/sidebar"
import { TimeTracker } from "@/components/time-tracker"
import { DailyTimeline } from "@/components/daily-timeline"
import { TimeEntries } from "@/components/time-entries"
import { Analytics } from "@/components/analytics"
import { RecentActivity } from "@/components/recent-activity"

export default function Home() {
  return (
    <ProtectedRoute>
      <div className="flex min-h-screen bg-background">
        <Sidebar />

        <main className="flex-1 lg:ml-64">
          <div className="container mx-auto px-4 lg:px-8 pt-6 pb-4 lg:pb-8 space-y-6">
            {/* Timer Section */}
            <TimeTracker />

            {/* Daily Timeline */}
            <DailyTimeline />

            {/* Analytics Grid */}
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              <Analytics />
            </div>

            {/* Time Entries and Recent Activity */}
            <div className="grid gap-6 lg:grid-cols-3">
              <div className="lg:col-span-2">
                <TimeEntries />
              </div>
              <div>
                <RecentActivity />
              </div>
            </div>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  )
}

import { ProtectedRoute } from "@/components/protected-route"
import { Sidebar } from "@/components/sidebar"
import { TimeTracker } from "@/components/time-tracker"
import { TimeEntries } from "@/components/time-entries"
import { Analytics } from "@/components/analytics"
import { RecentActivity } from "@/components/recent-activity"

export default function Home() {
  return (
    <ProtectedRoute>
      <div className="flex min-h-screen bg-background">
        <Sidebar />

        <main className="flex-1 lg:ml-64">
          <div className="container mx-auto p-4 lg:p-8 space-y-6">
            {/* Timer Section */}
            <TimeTracker />

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

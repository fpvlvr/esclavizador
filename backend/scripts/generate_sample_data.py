#!/usr/bin/env python3
"""
Sample Data Generator for Esclavizador

Generates realistic sample data including:
- Tasks for existing projects (5-10 per project)
- Time entries for all users (Sep 1 - Nov 21, 2025, weekdays only)

Usage:
    poetry run python scripts/generate_sample_data.py
"""

import argparse
import random
from datetime import datetime, timedelta, time
from typing import List, Dict, Optional
import requests
from collections import defaultdict

# Configuration
BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"
DEMO_EMAIL = "mike.oxlong@sample.org"
DEMO_PASSWORD = "SecurePass123!"

# Date range for time entries
START_DATE = datetime(2025, 9, 1)
END_DATE = datetime(2025, 11, 21)

# Work hours
WORK_START = time(8, 0)  # 8:00 AM
WORK_END = time(17, 0)   # 5:00 PM

# Task name pool
TASK_NAMES = [
    "Initial planning and requirements gathering",
    "Design mockups and wireframes",
    "Database schema design",
    "Backend API development",
    "Frontend component development",
    "User authentication implementation",
    "Code review and refactoring",
    "Unit testing and integration tests",
    "Bug fixes and optimization",
    "Performance tuning",
    "Security audit and fixes",
    "Documentation updates",
    "Deployment configuration",
    "CI/CD pipeline setup",
    "Monitoring and logging setup",
    "Feature implementation",
    "Third-party API integration",
    "Error handling improvements",
    "UI/UX improvements",
    "Accessibility enhancements",
]

# Work descriptions pool
WORK_DESCRIPTIONS = [
    "Working on feature implementation",
    "Fixing bugs and issues",
    "Code review session",
    "Meeting with team",
    "Research and planning",
    "Testing and QA",
    "Documentation work",
    "Refactoring code",
    "Implementing feedback",
    "Debugging production issue",
    None,  # Some entries have no description
]


class SampleDataGenerator:
    def __init__(self, base_url: str, email: str, password: str):
        self.base_url = base_url
        self.api_v1 = f"{base_url}/api/v1"
        self.email = email
        self.password = password
        self.token: Optional[str] = None
        self.session = requests.Session()

    def _headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        if not self.token:
            raise Exception("Not authenticated. Call login() first.")
        return {"Authorization": f"Bearer {self.token}"}

    def login(self) -> bool:
        """Authenticate and get access token."""
        print(f"🔐 Logging in as {self.email}...")
        try:
            response = self.session.post(
                f"{self.api_v1}/auth/login",
                json={"email": self.email, "password": self.password}
            )
            response.raise_for_status()
            data = response.json()
            self.token = data["access_token"]
            print("✅ Login successful")
            return True
        except Exception as e:
            print(f"❌ Login failed: {e}")
            return False

    def fetch_users(self) -> List[Dict]:
        """Fetch all users in the organization."""
        print("👥 Fetching users...")
        response = self.session.get(
            f"{self.api_v1}/users/stats",
            headers=self._headers(),
            params={"limit": 100}
        )
        response.raise_for_status()
        users = response.json()["items"]
        print(f"   Found {len(users)} users")
        return users

    def fetch_projects(self) -> List[Dict]:
        """Fetch all projects in the organization."""
        print("📁 Fetching projects...")
        response = self.session.get(
            f"{self.api_v1}/projects",
            headers=self._headers(),
            params={"is_active": True, "limit": 100}
        )
        response.raise_for_status()
        projects = response.json()["items"]
        print(f"   Found {len(projects)} projects")
        return projects

    def fetch_tasks(self, project_id: Optional[str] = None) -> List[Dict]:
        """Fetch tasks, optionally filtered by project."""
        # API limit is max 100
        params = {"limit": 100}

        response = self.session.get(
            f"{self.api_v1}/tasks",
            headers=self._headers(),
            params=params
        )
        response.raise_for_status()
        all_tasks = response.json()["items"]

        # Filter client-side if project_id specified
        if project_id:
            return [task for task in all_tasks if task["project_id"] == project_id]

        return all_tasks

    def create_task(self, name: str, project_id: str, description: Optional[str] = None) -> Dict:
        """Create a new task."""
        data = {
            "name": name,
            "project_id": project_id,
        }
        if description:
            data["description"] = description

        response = self.session.post(
            f"{self.api_v1}/tasks",
            headers=self._headers(),
            json=data
        )
        response.raise_for_status()
        return response.json()

    def create_time_entry(
        self,
        project_id: str,
        start_time: str,
        end_time: str,
        task_id: Optional[str] = None,
        is_billable: bool = True,
        description: Optional[str] = None
    ) -> Dict:
        """Create a manual time entry."""
        data = {
            "project_id": project_id,
            "start_time": start_time,
            "end_time": end_time,
            "is_billable": is_billable,
        }
        if task_id:
            data["task_id"] = task_id
        if description:
            data["description"] = description

        response = self.session.post(
            f"{self.api_v1}/time-entries",
            headers=self._headers(),
            json=data
        )
        response.raise_for_status()
        return response.json()

    def generate_tasks_for_project(self, project: Dict) -> List[Dict]:
        """Generate 5-10 random tasks for a project."""
        num_tasks = random.randint(5, 10)
        print(f"   📝 Generating {num_tasks} tasks for '{project['name']}'")

        # Get existing tasks to avoid duplicates
        existing_tasks = self.fetch_tasks(project["id"])
        existing_names = {task["name"] for task in existing_tasks}

        # Select unique task names
        available_names = [name for name in TASK_NAMES if name not in existing_names]
        if len(available_names) < num_tasks:
            print(f"      ⚠️  Only {len(available_names)} unique tasks available")
            num_tasks = len(available_names)

        task_names = random.sample(available_names, num_tasks)

        created_tasks = []
        for task_name in task_names:
            try:
                task = self.create_task(
                    name=task_name,
                    project_id=project["id"],
                    description=f"Work related to {task_name.lower()}"
                )
                created_tasks.append(task)
            except Exception as e:
                print(f"      ❌ Failed to create task '{task_name}': {e}")

        print(f"      ✅ Created {len(created_tasks)} tasks")
        return created_tasks

    def get_weekdays(self, start_date: datetime, end_date: datetime) -> List[datetime]:
        """Generate list of weekdays between start and end date."""
        weekdays = []
        current = start_date
        while current <= end_date:
            # 0 = Monday, 6 = Sunday
            if current.weekday() < 5:
                weekdays.append(current)
            current += timedelta(days=1)
        return weekdays

    def generate_workday_entries(
        self,
        date: datetime,
        user_projects: List[Dict],
        project_tasks: Dict[str, List[Dict]]
    ) -> List[Dict]:
        """Generate time entries for a single workday with random breaks and task switches."""
        entries = []

        # Start and end of workday
        current_time = datetime.combine(date, WORK_START)
        end_of_day = datetime.combine(date, WORK_END)

        while current_time < end_of_day:
            # Random entry duration: 15 min to 3 hours
            duration_minutes = random.choice([15, 30, 45, 60, 90, 120, 180])
            entry_end = current_time + timedelta(minutes=duration_minutes)

            # Don't exceed end of day
            if entry_end > end_of_day:
                entry_end = end_of_day

            # Select random project and task
            project = random.choice(user_projects)
            tasks = project_tasks.get(project["id"], [])
            task = random.choice(tasks) if tasks else None

            # 80% billable, 20% non-billable
            is_billable = random.random() < 0.8

            # Random description (30% have no description)
            description = random.choice(WORK_DESCRIPTIONS)

            entry_data = {
                "project_id": project["id"],
                "task_id": task["id"] if task else None,
                "start_time": current_time.isoformat() + "Z",
                "end_time": entry_end.isoformat() + "Z",
                "is_billable": is_billable,
                "description": description,
            }
            entries.append(entry_data)

            # Move to next entry with optional short break (0-15 min)
            break_minutes = random.choice([0, 0, 0, 5, 10, 15])  # Most entries have no break
            current_time = entry_end + timedelta(minutes=break_minutes)

        return entries

    def generate_time_entries_for_user(
        self,
        user: Dict,
        projects: List[Dict],
        project_tasks: Dict[str, List[Dict]]
    ) -> int:
        """Generate time entries for a user across the date range."""
        # Assign user to at least 2 different projects
        num_projects = random.randint(2, min(4, len(projects)))
        user_projects = random.sample(projects, num_projects)

        print(f"   👤 {user['email']}")
        print(f"      Projects: {[p['name'] for p in user_projects]}")

        # Get all weekdays in range
        weekdays = self.get_weekdays(START_DATE, END_DATE)
        print(f"      Generating entries for {len(weekdays)} workdays...")

        total_entries = 0
        for day in weekdays:
            # Generate entries for this day
            day_entries = self.generate_workday_entries(day, user_projects, project_tasks)

            # Create entries via API
            for entry_data in day_entries:
                try:
                    self.create_time_entry(**entry_data)
                    total_entries += 1
                except Exception as e:
                    print(f"         ❌ Failed to create entry: {e}")

        print(f"      ✅ Created {total_entries} time entries")
        return total_entries

    def run(self, dry_run: bool = False):
        """Run the complete data generation process."""
        print("=" * 60)
        print("🚀 Sample Data Generator for Esclavizador")
        print("=" * 60)

        if dry_run:
            print("⚠️  DRY RUN MODE - No data will be created")

        # Step 1: Login
        if not self.login():
            return

        print()

        # Step 2: Fetch existing data
        users = self.fetch_users()
        projects = self.fetch_projects()

        if not projects:
            print("❌ No projects found. Please create some projects first.")
            return

        if not users:
            print("❌ No users found.")
            return

        print()

        # Step 3: Generate tasks
        print("📝 GENERATING TASKS")
        print("-" * 60)

        project_tasks = {}
        total_tasks_created = 0

        for project in projects:
            if not dry_run:
                created_tasks = self.generate_tasks_for_project(project)
                total_tasks_created += len(created_tasks)
            else:
                num_tasks = random.randint(5, 10)
                print(f"   [DRY RUN] Would create {num_tasks} tasks for '{project['name']}'")
                created_tasks = []

            # Fetch all tasks for this project
            all_tasks = self.fetch_tasks(project["id"])
            project_tasks[project["id"]] = all_tasks

        print()
        print(f"✅ Total tasks created: {total_tasks_created}")
        print(f"📊 Total tasks available: {sum(len(tasks) for tasks in project_tasks.values())}")

        print()

        # Step 4: Generate time entries
        print("⏱️  GENERATING TIME ENTRIES")
        print("-" * 60)

        total_entries_created = 0

        for user in users:
            if not dry_run:
                entries_created = self.generate_time_entries_for_user(
                    user, projects, project_tasks
                )
                total_entries_created += entries_created
            else:
                weekdays = self.get_weekdays(START_DATE, END_DATE)
                estimated_entries = len(weekdays) * random.randint(3, 6)
                print(f"   [DRY RUN] Would create ~{estimated_entries} entries for {user['email']}")

        print()
        print("=" * 60)
        print("✅ GENERATION COMPLETE!")
        print("=" * 60)
        print(f"📊 Summary:")
        print(f"   - Tasks created: {total_tasks_created}")
        print(f"   - Time entries created: {total_entries_created}")
        print(f"   - Users processed: {len(users)}")
        print(f"   - Projects: {len(projects)}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Generate sample data for Esclavizador")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be created without actually creating it"
    )
    parser.add_argument(
        "--url",
        default=BASE_URL,
        help=f"Base URL of the API (default: {BASE_URL})"
    )

    args = parser.parse_args()

    generator = SampleDataGenerator(
        base_url=args.url,
        email=DEMO_EMAIL,
        password=DEMO_PASSWORD
    )

    try:
        generator.run(dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("\n\n⚠️  Generation interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()

"""
Tests for ProjectRepository.

Tests CRUD operations and multi-tenant isolation.
"""

import pytest

from app.models.organization import Organization
from app.models.project import Project
from app.models.task import Task
from app.repositories.project_repo import project_repo


class TestProjectRepository:
    """Test ProjectRepository methods."""

    async def test_create_project(self, test_org):
        """Test creating a project."""
        project = await project_repo.create(
            name="New Project",
            description="Test description",
            org_id=str(test_org.id)
        )

        assert project.id is not None
        assert project.name == "New Project"
        assert project.description == "Test description"
        assert str(project.organization_id) == str(test_org.id)
        assert project.is_active is True
        assert project.task_count == 0  # New project has no tasks

        # Cleanup
        await project.delete()

    async def test_get_by_id_success(self, test_org):
        """Test getting project by ID."""
        # Create project
        created_project = await Project.create(
            name="Test Project",
            description="Test description",
            organization=test_org
        )

        # Get by ID
        project = await project_repo.get_by_id(
            str(created_project.id),
            str(test_org.id)
        )

        assert project is not None
        assert project.id == created_project.id
        assert project.name == "Test Project"
        assert project.task_count == 0

        # Cleanup
        await created_project.delete()

    async def test_get_by_id_returns_task_count(self, test_org):
        """Test that get_by_id includes accurate task_count."""
        # Create project
        created_project = await Project.create(
            name="Test Project",
            organization=test_org
        )

        # Create some tasks
        task1 = await Task.create(name="Task 1", project=created_project)
        task2 = await Task.create(name="Task 2", project=created_project)

        # Get project
        project = await project_repo.get_by_id(
            str(created_project.id),
            str(test_org.id)
        )

        assert project is not None
        assert project.task_count == 2

        # Cleanup
        await task1.delete()
        await task2.delete()
        await created_project.delete()

    async def test_get_by_id_wrong_org_returns_none(self, test_org):
        """Test multi-tenant isolation - wrong org returns None."""
        # Create second org
        second_org = await Organization.create(name="Second Org")

        # Create project in test_org
        created_project = await Project.create(
            name="Test Project",
            organization=test_org
        )

        # Try to get with wrong org_id
        project = await project_repo.get_by_id(
            str(created_project.id),
            str(second_org.id)  # Wrong org
        )

        assert project is None  # Multi-tenant isolation working

        # Cleanup
        await created_project.delete()
        await second_org.delete()

    async def test_list_projects(self, test_org):
        """Test listing projects with pagination."""
        # Create multiple projects
        project1 = await Project.create(name="Project 1", organization=test_org)
        project2 = await Project.create(name="Project 2", organization=test_org)
        project3 = await Project.create(name="Project 3", organization=test_org)

        # List all
        result = await project_repo.list(
            org_id=str(test_org.id),
            filters={},
            limit=10,
            offset=0
        )

        assert result["total"] == 3
        assert len(result["items"]) == 3

        # Test pagination
        result = await project_repo.list(
            org_id=str(test_org.id),
            filters={},
            limit=2,
            offset=0
        )

        assert result["total"] == 3
        assert len(result["items"]) == 2

        # Cleanup
        await project1.delete()
        await project2.delete()
        await project3.delete()

    async def test_list_filter_by_is_active(self, test_org):
        """Test filtering projects by is_active."""
        # Create active and inactive projects
        active_project = await Project.create(
            name="Active Project",
            organization=test_org,
            is_active=True
        )
        inactive_project = await Project.create(
            name="Inactive Project",
            organization=test_org,
            is_active=False
        )

        # Filter by active only
        result = await project_repo.list(
            org_id=str(test_org.id),
            filters={"is_active": True},
            limit=10,
            offset=0
        )

        assert result["total"] == 1
        assert result["items"][0].name == "Active Project"

        # Filter by inactive only
        result = await project_repo.list(
            org_id=str(test_org.id),
            filters={"is_active": False},
            limit=10,
            offset=0
        )

        assert result["total"] == 1
        assert result["items"][0].name == "Inactive Project"

        # Cleanup
        await active_project.delete()
        await inactive_project.delete()

    async def test_update_project(self, test_org):
        """Test updating project."""
        # Create project
        project = await Project.create(
            name="Original Name",
            description="Original description",
            organization=test_org
        )

        # Update
        updated_project = await project_repo.update(
            project_id=str(project.id),
            org_id=str(test_org.id),
            data={
                "name": "Updated Name",
                "description": "Updated description"
            }
        )

        assert updated_project is not None
        assert updated_project.name == "Updated Name"
        assert updated_project.description == "Updated description"
        assert updated_project.task_count == 0

        # Cleanup
        await project.delete()

    async def test_update_wrong_org_returns_none(self, test_org):
        """Test multi-tenant isolation on update."""
        # Create second org
        second_org = await Organization.create(name="Second Org")

        # Create project in test_org
        project = await Project.create(
            name="Test Project",
            organization=test_org
        )

        # Try to update with wrong org_id
        updated_project = await project_repo.update(
            project_id=str(project.id),
            org_id=str(second_org.id),  # Wrong org
            data={"name": "Should Not Update"}
        )

        assert updated_project is None

        # Verify original not changed
        project = await Project.get(id=project.id)
        assert project.name == "Test Project"

        # Cleanup
        await project.delete()
        await second_org.delete()

    async def test_soft_delete(self, test_org):
        """Test soft deleting project."""
        # Create project
        project = await Project.create(
            name="Test Project",
            organization=test_org,
            is_active=True
        )

        # Soft delete
        deleted = await project_repo.soft_delete(
            project_id=str(project.id),
            org_id=str(test_org.id)
        )

        assert deleted is True

        # Verify is_active set to False
        project = await Project.get(id=project.id)
        assert project.is_active is False

        # Cleanup
        await project.delete()

    async def test_soft_delete_wrong_org_returns_false(self, test_org):
        """Test multi-tenant isolation on delete."""
        # Create second org
        second_org = await Organization.create(name="Second Org")

        # Create project in test_org
        project = await Project.create(
            name="Test Project",
            organization=test_org,
            is_active=True
        )

        # Try to delete with wrong org_id
        deleted = await project_repo.soft_delete(
            project_id=str(project.id),
            org_id=str(second_org.id)  # Wrong org
        )

        assert deleted is False

        # Verify project still active
        project = await Project.get(id=project.id)
        assert project.is_active is True

        # Cleanup
        await project.delete()
        await second_org.delete()

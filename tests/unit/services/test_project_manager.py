"""
Unit tests for ProjectManager service.

Tests cover:
- Project CRUD operations (create, read, list, delete)
- Project validation
- Caching behavior
- Directory management (default and environment override)
- Error handling
- Edge cases

Target: 80%+ code coverage
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from pydantic import ValidationError

# Enable async support for all tests in this module
pytestmark = pytest.mark.asyncio

from extract_transform_platform.models.project_config import (
    DataSourceConfig,
    DataSourceType,
    OutputConfig,
    OutputDestinationConfig,
    OutputFormat,
    ProjectConfig,
    ProjectMetadata,
)
from extract_transform_platform.services.project_manager import (
    InvalidConfigError,
    ProjectAlreadyExistsError,
    ProjectInfo,
    ProjectManager,
    ProjectNotFoundError,
    ValidationResult,
)

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def tmp_projects_dir(tmp_path):
    """Create temporary projects directory."""
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()
    return projects_dir


@pytest.fixture
def project_manager(tmp_projects_dir):
    """Create ProjectManager with temporary directory."""
    return ProjectManager(base_dir=tmp_projects_dir)


@pytest.fixture
def sample_project_config():
    """Sample project configuration for testing."""
    return ProjectConfig(
        project=ProjectMetadata(
            name="test_project",
            description="Test project description",
            version="1.0.0",
            author="Test Author",
            tags=["test", "sample"],
        ),
        data_sources=[
            DataSourceConfig(
                type=DataSourceType.API,
                name="example_api",
                endpoint="https://api.example.com",
            )
        ],
        output=OutputConfig(
            formats=[
                OutputDestinationConfig(type=OutputFormat.JSON, path="output/data.json")
            ]
        ),
    )


@pytest.fixture
def sample_project_yaml(tmp_projects_dir, sample_project_config):
    """Create a sample project with valid project.yaml."""
    project_dir = tmp_projects_dir / "test_project"
    project_dir.mkdir()
    (project_dir / "examples").mkdir()
    (project_dir / "src").mkdir()
    (project_dir / "tests").mkdir()
    (project_dir / "output").mkdir()

    # Write project.yaml
    sample_project_config.to_yaml(project_dir / "project.yaml")

    return project_dir


def create_project_yaml(project_dir: Path, name: str, **kwargs):
    """Helper to create valid project.yaml for testing.

    Args:
        project_dir: Project directory path
        name: Project name
        **kwargs: Additional ProjectMetadata fields
    """
    project_dir.mkdir(parents=True, exist_ok=True)

    config = ProjectConfig(
        project=ProjectMetadata(name=name, **kwargs),
        data_sources=[
            DataSourceConfig(
                type=DataSourceType.API,
                name="example_api",
                endpoint="https://api.example.com",
            )
        ],
        output=OutputConfig(
            formats=[
                OutputDestinationConfig(type=OutputFormat.JSON, path="output/data.json")
            ]
        ),
    )

    config.to_yaml(project_dir / "project.yaml")
    return project_dir


# ============================================================================
# TEST: CRUD OPERATIONS (40% of tests)
# ============================================================================


class TestCRUDOperations:
    """Test project CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_project_success(self, project_manager):
        """Test successful project creation with default template."""
        project_info = await project_manager.create_project("my_project")

        assert project_info is not None
        assert project_info.name == "my_project"
        assert project_info.exists
        assert project_info.path.exists()

        # Verify directory structure
        assert (project_info.path / "examples").exists()
        assert (project_info.path / "src").exists()
        assert (project_info.path / "tests").exists()
        assert (project_info.path / "output").exists()

        # Verify project.yaml exists
        assert (project_info.path / "project.yaml").exists()

    @pytest.mark.asyncio
    async def test_create_project_with_template(self, project_manager):
        """Test project creation with specified template."""
        # Currently template is not implemented, but should not fail
        project_info = await project_manager.create_project(
            "template_project", template="weather"
        )

        assert project_info is not None
        assert project_info.name == "template_project"
        assert project_info.path.exists()

    @pytest.mark.asyncio
    async def test_create_project_duplicate(self, project_manager):
        """Test that creating duplicate project raises error."""
        await project_manager.create_project("duplicate")

        with pytest.raises(ProjectAlreadyExistsError) as exc_info:
            await project_manager.create_project("duplicate")

        assert "duplicate" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_project_success(self, project_manager, sample_project_yaml):
        """Test retrieving existing project."""
        project = await project_manager.get_project("test_project")

        assert project is not None
        assert project.name == "test_project"
        assert project.path == sample_project_yaml
        assert project.exists
        assert project.is_valid

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, project_manager):
        """Test retrieving non-existent project returns None."""
        project = await project_manager.get_project("nonexistent")

        assert project is None

    @pytest.mark.asyncio
    async def test_list_projects_empty(self, project_manager):
        """Test listing projects in empty directory."""
        projects = await project_manager.list_projects()

        assert isinstance(projects, list)
        assert len(projects) == 0

    @pytest.mark.asyncio
    async def test_list_projects_single(self, project_manager, sample_project_yaml):
        """Test listing single project."""
        projects = await project_manager.list_projects()

        assert len(projects) == 1
        assert projects[0].name == "test_project"

    @pytest.mark.asyncio
    async def test_list_projects_multiple(self, project_manager, tmp_projects_dir):
        """Test listing multiple projects."""
        # Create multiple projects
        for i in range(3):
            name = f"project_{i}"
            create_project_yaml(tmp_projects_dir / name, name)

        projects = await project_manager.list_projects()

        assert len(projects) == 3

        # Verify sorted by name
        names = [p.name for p in projects]
        assert names == sorted(names)

    @pytest.mark.asyncio
    async def test_delete_project_success(self, project_manager, sample_project_yaml):
        """Test successful project deletion."""
        # Verify project exists
        project = await project_manager.get_project("test_project")
        assert project is not None

        # Delete project
        result = await project_manager.delete_project("test_project")

        assert result is True
        assert not sample_project_yaml.exists()

        # Verify project no longer listed
        projects = await project_manager.list_projects()
        assert len(projects) == 0

    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, project_manager):
        """Test deleting non-existent project returns False."""
        result = await project_manager.delete_project("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_project_info_alias(self, project_manager, sample_project_yaml):
        """Test get_project_info is alias for get_project."""
        project1 = await project_manager.get_project("test_project")
        project2 = await project_manager.get_project_info("test_project")

        assert project1 is not None
        assert project2 is not None
        assert project1.name == project2.name
        assert project1.path == project2.path


# ============================================================================
# TEST: VALIDATION (20% of tests)
# ============================================================================


class TestValidation:
    """Test project validation."""

    @pytest.mark.asyncio
    async def test_validate_project_valid(self, project_manager, sample_project_yaml):
        """Test validation of valid project."""
        result = await project_manager.validate_project("test_project")

        assert isinstance(result, ValidationResult)
        assert result.project_name == "test_project"
        assert result.is_valid
        assert not result.has_errors
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_project_not_found(self, project_manager):
        """Test validation of non-existent project."""
        result = await project_manager.validate_project("nonexistent")

        assert not result.is_valid
        assert result.has_errors
        assert len(result.errors) == 1
        assert "not found" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_validate_project_missing_config(
        self, project_manager, tmp_projects_dir
    ):
        """Test validation when project.yaml is missing."""
        # Create project directory without config
        project_dir = tmp_projects_dir / "no_config"
        project_dir.mkdir()

        # Note: Project won't be discovered without project.yaml
        result = await project_manager.validate_project("no_config")

        assert not result.is_valid
        assert result.has_errors

    @pytest.mark.asyncio
    async def test_validate_project_invalid_yaml(
        self, project_manager, tmp_projects_dir
    ):
        """Test validation with malformed YAML."""
        project_dir = tmp_projects_dir / "bad_yaml"
        project_dir.mkdir()

        # Write invalid YAML
        (project_dir / "project.yaml").write_text("invalid: yaml: content: [")

        # Project won't be discovered due to YAML error
        result = await project_manager.validate_project("bad_yaml")

        assert not result.is_valid
        assert result.has_errors

    @pytest.mark.asyncio
    async def test_validate_project_missing_directories(
        self, project_manager, sample_project_yaml
    ):
        """Test validation warns about missing directories."""
        # Remove some directories
        shutil.rmtree(sample_project_yaml / "examples")
        shutil.rmtree(sample_project_yaml / "src")

        result = await project_manager.validate_project("test_project")

        # Should still be valid but have warnings
        assert result.is_valid
        assert result.has_warnings
        assert any("examples" in w.lower() for w in result.warnings)
        assert any("src" in w.lower() for w in result.warnings)

    @pytest.mark.asyncio
    async def test_validate_project_no_examples(
        self, project_manager, sample_project_yaml
    ):
        """Test validation warns when no example files exist."""
        # Examples directory exists but is empty (created in fixture)
        result = await project_manager.validate_project("test_project")

        # Should have warning about missing examples
        assert result.has_warnings
        assert any("example" in w.lower() for w in result.warnings)

    @pytest.mark.asyncio
    async def test_validation_result_to_dict(self):
        """Test ValidationResult serialization."""
        result = ValidationResult(
            project_name="test",
            is_valid=False,
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"],
            recommendations=["Recommendation 1"],
        )

        result_dict = result.to_dict()

        assert result_dict["project_name"] == "test"
        assert result_dict["is_valid"] is False
        assert len(result_dict["errors"]) == 2
        assert len(result_dict["warnings"]) == 1
        assert len(result_dict["recommendations"]) == 1


# ============================================================================
# TEST: CACHING (15% of tests)
# ============================================================================


class TestCaching:
    """Test project caching behavior."""

    @pytest.mark.asyncio
    async def test_cache_on_list(self, project_manager, sample_project_yaml):
        """Test that projects are cached after list()."""
        # First list - should load from disk
        projects1 = await project_manager.list_projects()
        assert len(projects1) == 1

        # Cache should now be populated
        assert project_manager._projects_cache is not None
        assert len(project_manager._projects_cache) == 1

        # Second list - should use cache
        projects2 = await project_manager.list_projects()
        assert len(projects2) == 1

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_create(self, project_manager):
        """Test that cache is cleared when creating project."""
        # Initial list to populate cache
        await project_manager.list_projects()
        assert project_manager._projects_cache is not None

        # Create new project
        await project_manager.create_project("new_project")

        # Cache should be invalidated
        assert project_manager._projects_cache is None

        # Next list should reload
        projects = await project_manager.list_projects()
        assert len(projects) == 1
        assert projects[0].name == "new_project"

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_delete(
        self, project_manager, sample_project_yaml
    ):
        """Test that cache is cleared when deleting project."""
        # Initial list to populate cache
        projects = await project_manager.list_projects()
        assert len(projects) == 1
        assert project_manager._projects_cache is not None

        # Delete project
        await project_manager.delete_project("test_project")

        # Cache should be invalidated
        assert project_manager._projects_cache is None

        # Next list should reload (empty)
        projects = await project_manager.list_projects()
        assert len(projects) == 0

    @pytest.mark.asyncio
    async def test_cache_populated_on_get(self, project_manager, sample_project_yaml):
        """Test that get_project populates cache."""
        # Cache should be None initially
        assert project_manager._projects_cache is None

        # Get project
        project = await project_manager.get_project("test_project")
        assert project is not None

        # Cache should now be populated
        assert project_manager._projects_cache is not None
        assert "test_project" in project_manager._projects_cache


# ============================================================================
# TEST: DIRECTORY MANAGEMENT (10% of tests)
# ============================================================================


class TestDirectoryManagement:
    """Test directory management and environment override."""

    def test_default_projects_dir_in_repo(self, tmp_path, monkeypatch):
        """Test default directory when no environment variable set."""
        # Ensure no environment variable
        monkeypatch.delenv("EDGAR_ARTIFACTS_DIR", raising=False)

        # Create manager without base_dir (uses default)
        manager = ProjectManager()

        # Should default to ./projects
        assert manager._projects_dir == Path("projects")

    def test_projects_dir_env_override(self, tmp_path, monkeypatch):
        """Test EDGAR_ARTIFACTS_DIR environment variable override."""
        # Set environment variable
        artifacts_dir = tmp_path / "external_artifacts"
        monkeypatch.setenv("EDGAR_ARTIFACTS_DIR", str(artifacts_dir))

        # Create manager without base_dir (uses env)
        manager = ProjectManager()

        # Should use environment variable
        expected_path = artifacts_dir / "projects"
        assert manager._projects_dir == expected_path

    def test_projects_dir_env_expanduser(self, monkeypatch):
        """Test that ~ is expanded in EDGAR_ARTIFACTS_DIR."""
        # Set environment variable with tilde
        monkeypatch.setenv("EDGAR_ARTIFACTS_DIR", "~/my_artifacts")

        # Create manager
        manager = ProjectManager()

        # Should expand tilde
        assert "~" not in str(manager._projects_dir)
        assert manager._projects_dir.is_absolute()

    def test_projects_dir_env_empty_string(self, monkeypatch):
        """Test that empty EDGAR_ARTIFACTS_DIR is ignored."""
        # Set environment variable to empty string
        monkeypatch.setenv("EDGAR_ARTIFACTS_DIR", "")

        # Create manager
        manager = ProjectManager()

        # Should fall back to default
        assert manager._projects_dir == Path("projects")

    def test_projects_dir_env_whitespace_only(self, monkeypatch):
        """Test that whitespace-only EDGAR_ARTIFACTS_DIR is ignored."""
        # Set environment variable to whitespace
        monkeypatch.setenv("EDGAR_ARTIFACTS_DIR", "   ")

        # Create manager
        manager = ProjectManager()

        # Should fall back to default
        assert manager._projects_dir == Path("projects")

    @pytest.mark.asyncio
    async def test_create_project_creates_base_directory(self, tmp_path):
        """Test that base directory is created if it doesn't exist."""
        # Use non-existent directory
        projects_dir = tmp_path / "new_projects"
        assert not projects_dir.exists()

        # Create manager
        manager = ProjectManager(base_dir=projects_dir)

        # Directory should be created
        assert projects_dir.exists()

    @pytest.mark.asyncio
    async def test_load_projects_nonexistent_directory(self, tmp_path):
        """Test loading projects from non-existent directory."""
        # Use non-existent directory but don't create manager
        # (which would create it)
        projects_dir = tmp_path / "nonexistent"

        # Manually create manager with directory that will be deleted
        manager = ProjectManager(base_dir=projects_dir)

        # Delete the directory
        shutil.rmtree(projects_dir)

        # Loading should return empty dict, not crash
        projects = await manager._load_projects()

        assert isinstance(projects, dict)
        assert len(projects) == 0


# ============================================================================
# TEST: ERROR HANDLING (10% of tests)
# ============================================================================


class TestErrorHandling:
    """Test error handling in various scenarios."""

    @pytest.mark.asyncio
    async def test_invalid_project_name_empty(self, project_manager):
        """Test that empty project name raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            await project_manager.create_project("")

        assert "invalid project name" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_invalid_project_name_special_chars(self, project_manager):
        """Test that special characters in name raise ValueError."""
        invalid_names = [
            "project with spaces",
            "project@special",
            "project/slash",
            "project\\backslash",
            "project.dot",
        ]

        for name in invalid_names:
            with pytest.raises(ValueError) as exc_info:
                await project_manager.create_project(name)

            assert "invalid project name" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_valid_project_names(self, project_manager):
        """Test that valid names with underscores and hyphens work."""
        valid_names = [
            "project_with_underscores",
            "project-with-hyphens",
            "project123",
            "ProjectMixedCase",
        ]

        for name in valid_names:
            project = await project_manager.create_project(name)
            assert project is not None

    @pytest.mark.asyncio
    async def test_load_projects_malformed_yaml(
        self, project_manager, tmp_projects_dir
    ):
        """Test that malformed YAML is logged and skipped."""
        # Create project with bad YAML
        project_dir = tmp_projects_dir / "bad_yaml"
        project_dir.mkdir()
        (project_dir / "project.yaml").write_text("bad: yaml: [")

        # Should not crash, just skip the project
        projects = await project_manager.list_projects()

        assert len(projects) == 0

    @pytest.mark.asyncio
    async def test_load_projects_validation_error(
        self, project_manager, tmp_projects_dir
    ):
        """Test that validation errors are logged and skipped."""
        # Create project with invalid config
        project_dir = tmp_projects_dir / "invalid_config"
        project_dir.mkdir()

        # Write YAML with missing required fields
        (project_dir / "project.yaml").write_text(
            """
project:
  name: ""  # Invalid: empty name
data_sources: []
output:
  formats: []
        """
        )

        # Should not crash, just skip the project
        projects = await project_manager.list_projects()

        assert len(projects) == 0

    @pytest.mark.asyncio
    async def test_delete_project_permission_error(
        self, project_manager, sample_project_yaml
    ):
        """Test that OSError is raised on deletion failure."""
        # Mock shutil.rmtree to raise OSError
        with patch("shutil.rmtree") as mock_rmtree:
            mock_rmtree.side_effect = OSError("Permission denied")

            with pytest.raises(OSError):
                await project_manager.delete_project("test_project")


# ============================================================================
# TEST: EDGE CASES (5% of tests)
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_project_name_with_underscores(self, project_manager):
        """Test project name with underscores."""
        project = await project_manager.create_project("my_project_name")

        assert project.name == "my_project_name"

    @pytest.mark.asyncio
    async def test_project_name_with_hyphens(self, project_manager):
        """Test project name with hyphens."""
        project = await project_manager.create_project("my-project-name")

        assert project.name == "my-project-name"

    @pytest.mark.asyncio
    async def test_project_name_numeric(self, project_manager):
        """Test project name with only numbers."""
        project = await project_manager.create_project("123456")

        assert project.name == "123456"

    @pytest.mark.asyncio
    async def test_very_long_project_name(self, project_manager):
        """Test project with very long name."""
        # Most filesystems support 255 character filenames
        long_name = "a" * 200
        project = await project_manager.create_project(long_name)

        assert project.name == long_name
        assert project.path.exists()

    @pytest.mark.asyncio
    async def test_list_projects_with_non_directory_items(
        self, project_manager, tmp_projects_dir
    ):
        """Test that non-directory items are ignored."""
        # Create a file (not directory) in projects directory
        (tmp_projects_dir / "not_a_project.txt").write_text("test")

        # Create valid project
        create_project_yaml(tmp_projects_dir / "valid_project", "valid_project")

        # Should only list valid project
        projects = await project_manager.list_projects()

        assert len(projects) == 1
        assert projects[0].name == "valid_project"

    @pytest.mark.asyncio
    async def test_list_projects_with_directory_without_yaml(
        self, project_manager, tmp_projects_dir
    ):
        """Test that directories without project.yaml are ignored."""
        # Create directory without project.yaml
        (tmp_projects_dir / "no_yaml_dir").mkdir()

        # Create valid project
        create_project_yaml(tmp_projects_dir / "valid_project", "valid_project")

        # Should only list valid project
        projects = await project_manager.list_projects()

        assert len(projects) == 1
        assert projects[0].name == "valid_project"

    @pytest.mark.asyncio
    async def test_project_info_to_dict(self, sample_project_config):
        """Test ProjectInfo serialization to dict."""
        project_path = Path("/tmp/test_project")
        project_info = ProjectInfo.from_config(sample_project_config, project_path)

        result = project_info.to_dict()

        assert isinstance(result, dict)
        assert result["name"] == "test_project"
        assert result["path"] == str(project_path)
        assert result["exists"] in [True, False]
        assert result["is_valid"] is True
        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_project_info_from_config(self, sample_project_config):
        """Test ProjectInfo creation from ProjectConfig."""
        project_path = Path("/tmp/test_project")
        project_info = ProjectInfo.from_config(sample_project_config, project_path)

        assert project_info.name == "test_project"
        assert project_info.path == project_path
        assert project_info.config == sample_project_config
        assert project_info.metadata["description"] == "Test project description"
        assert project_info.metadata["version"] == "1.0.0"
        assert project_info.metadata["author"] == "Test Author"
        assert "test" in project_info.metadata["tags"]

    @pytest.mark.asyncio
    async def test_load_projects_with_file_disappearing(
        self, project_manager, tmp_projects_dir, monkeypatch
    ):
        """Test handling of race condition when config disappears during scan."""
        # Create a project
        project_dir = tmp_projects_dir / "disappearing"
        create_project_yaml(project_dir, "disappearing")

        # Mock ProjectConfig.from_yaml to simulate file disappearing
        original_from_yaml = ProjectConfig.from_yaml

        def mock_from_yaml(path):
            if "disappearing" in str(path):
                raise FileNotFoundError("File disappeared")
            return original_from_yaml(path)

        monkeypatch.setattr(ProjectConfig, "from_yaml", mock_from_yaml)

        # Should not crash, just skip the project
        projects = await project_manager.list_projects()

        assert len(projects) == 0

    @pytest.mark.asyncio
    async def test_load_projects_unexpected_error(
        self, project_manager, tmp_projects_dir, monkeypatch
    ):
        """Test handling of unexpected errors during project loading."""
        # Create a project
        project_dir = tmp_projects_dir / "error_project"
        create_project_yaml(project_dir, "error_project")

        # Mock ProjectConfig.from_yaml to raise unexpected error
        def mock_from_yaml(path):
            raise RuntimeError("Unexpected error")

        monkeypatch.setattr(ProjectConfig, "from_yaml", mock_from_yaml)

        # Should not crash, just skip the project
        projects = await project_manager.list_projects()

        assert len(projects) == 0

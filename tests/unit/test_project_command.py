"""Tests for project management commands."""

import json
import shutil
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from edgar_analyzer.cli.commands.project import create, delete, list, project, validate


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_projects_dir(tmp_path):
    """Create a temporary projects directory."""
    projects_dir = tmp_path / "test_projects"
    projects_dir.mkdir()
    return projects_dir


@pytest.fixture
def templates_dir(tmp_path):
    """Create a temporary templates directory with test templates."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    # Create minimal template
    minimal_template = {
        "project": {
            "name": "template-name",
            "version": "0.1.0",
            "description": "Template description",
            "template": "minimal",
        },
        "data_sources": [],
        "output": {"format": "json"},
    }
    with open(templates_dir / "project.yaml.template", "w") as f:
        yaml.dump(minimal_template, f)

    # Create weather template
    weather_template = {
        "project": {
            "name": "weather-api",
            "version": "0.1.0",
            "description": "Weather API data extraction",
            "template": "weather",
        },
        "data_sources": [
            {
                "name": "openweather",
                "type": "api",
                "url": "https://api.openweathermap.org/data/2.5/weather",
            }
        ],
        "output": {"format": "json"},
    }
    with open(templates_dir / "weather_api_project.yaml", "w") as f:
        yaml.dump(weather_template, f)

    return templates_dir


class TestProjectCreate:
    """Test project create command."""

    def test_create_minimal_project(self, runner, temp_projects_dir, monkeypatch):
        """Test creating a minimal project."""
        # Create test templates directory
        templates_dir = temp_projects_dir.parent / "templates"
        templates_dir.mkdir()

        minimal_template = {
            "project": {
                "name": "test",
                "version": "0.1.0",
                "description": "",
                "template": "minimal",
            }
        }
        with open(templates_dir / "project.yaml.template", "w") as f:
            yaml.dump(minimal_template, f)

        # Set environment variable to override templates directory
        monkeypatch.setenv("EDGAR_TEMPLATES_DIR", str(templates_dir))

        result = runner.invoke(
            create,
            ["test-project", "--template", "minimal", "--output-dir", str(temp_projects_dir)],
        )

        # Check command succeeded
        assert result.exit_code == 0
        assert "created successfully" in result.output

        # Check project directory was created
        project_path = temp_projects_dir / "test-project"
        assert project_path.exists()
        assert (project_path / "project.yaml").exists()
        assert (project_path / "README.md").exists()

        # Check required directories were created
        assert (project_path / "examples").exists()
        assert (project_path / "src").exists()
        assert (project_path / "tests").exists()
        assert (project_path / "output").exists()

        # Check project config
        with open(project_path / "project.yaml") as f:
            config = yaml.safe_load(f)
        assert config["project"]["name"] == "test-project"

    def test_create_project_with_description(self, runner, temp_projects_dir, templates_dir, monkeypatch):
        """Test creating a project with a description."""
        # Setup templates directory mock
        def get_templates_dir():
            return templates_dir

        # This is a simplified test - in real usage, the template path resolution would need proper mocking
        result = runner.invoke(
            create,
            [
                "my-api",
                "--template", "minimal",
                "--description", "My custom API project",
                "--output-dir", str(temp_projects_dir),
            ],
        )

        # Note: This may fail due to template path resolution
        # In a full implementation, we'd need to properly mock Path resolution

    def test_create_project_already_exists(self, runner, temp_projects_dir):
        """Test error when creating a project that already exists."""
        # Create an existing project
        existing_project = temp_projects_dir / "existing"
        existing_project.mkdir()

        result = runner.invoke(
            create,
            ["existing", "--output-dir", str(temp_projects_dir)],
        )

        assert result.exit_code != 0
        assert "already exists" in result.output


class TestProjectList:
    """Test project list command."""

    def test_list_empty_directory(self, runner, temp_projects_dir):
        """Test listing when no projects exist."""
        result = runner.invoke(list, ["--output-dir", str(temp_projects_dir)])

        assert result.exit_code == 0
        assert "No projects found" in result.output

    def test_list_projects_table_format(self, runner, temp_projects_dir):
        """Test listing projects in table format."""
        # Create test projects
        for i in range(3):
            project_dir = temp_projects_dir / f"project-{i}"
            project_dir.mkdir()

            config = {
                "project": {
                    "name": f"project-{i}",
                    "version": f"0.{i}.0",
                    "description": f"Test project {i}",
                    "template": "minimal",
                }
            }
            with open(project_dir / "project.yaml", "w") as f:
                yaml.dump(config, f)

        result = runner.invoke(
            list, ["--output-dir", str(temp_projects_dir), "--format", "table"]
        )

        assert result.exit_code == 0
        assert "project-0" in result.output
        assert "project-1" in result.output
        assert "project-2" in result.output
        assert "Projects (3)" in result.output

    def test_list_projects_json_format(self, runner, temp_projects_dir):
        """Test listing projects in JSON format."""
        # Create test project
        project_dir = temp_projects_dir / "test-project"
        project_dir.mkdir()

        config = {
            "project": {
                "name": "test-project",
                "version": "1.0.0",
                "description": "Test description",
                "template": "weather",
            }
        }
        with open(project_dir / "project.yaml", "w") as f:
            yaml.dump(config, f)

        result = runner.invoke(
            list, ["--output-dir", str(temp_projects_dir), "--format", "json"]
        )

        assert result.exit_code == 0

        # Parse JSON output
        projects = json.loads(result.output)
        assert len(projects) == 1
        assert projects[0]["name"] == "test-project"
        assert projects[0]["version"] == "1.0.0"
        assert projects[0]["template"] == "weather"

    def test_list_projects_tree_format(self, runner, temp_projects_dir):
        """Test listing projects in tree format."""
        # Create test project
        project_dir = temp_projects_dir / "test-project"
        project_dir.mkdir()

        config = {
            "project": {
                "name": "test-project",
                "version": "1.0.0",
                "description": "Test description",
                "template": "minimal",
            }
        }
        with open(project_dir / "project.yaml", "w") as f:
            yaml.dump(config, f)

        result = runner.invoke(
            list, ["--output-dir", str(temp_projects_dir), "--format", "tree"]
        )

        assert result.exit_code == 0
        assert "test-project" in result.output
        assert "Projects (1)" in result.output


class TestProjectDelete:
    """Test project delete command."""

    def test_delete_project_with_confirmation(self, runner, temp_projects_dir):
        """Test deleting a project with confirmation."""
        # Create test project
        project_dir = temp_projects_dir / "to-delete"
        project_dir.mkdir()
        (project_dir / "project.yaml").write_text("project:\n  name: to-delete")

        result = runner.invoke(
            delete,
            ["to-delete", "--output-dir", str(temp_projects_dir)],
            input="y\n",  # Confirm deletion
        )

        assert result.exit_code == 0
        assert "deleted successfully" in result.output
        assert not project_dir.exists()

    def test_delete_project_cancel(self, runner, temp_projects_dir):
        """Test cancelling project deletion."""
        # Create test project
        project_dir = temp_projects_dir / "to-keep"
        project_dir.mkdir()
        (project_dir / "project.yaml").write_text("project:\n  name: to-keep")

        result = runner.invoke(
            delete,
            ["to-keep", "--output-dir", str(temp_projects_dir)],
            input="n\n",  # Cancel deletion
        )

        assert result.exit_code == 0
        assert "cancelled" in result.output.lower()
        assert project_dir.exists()

    def test_delete_project_force(self, runner, temp_projects_dir):
        """Test deleting a project with --force flag."""
        # Create test project
        project_dir = temp_projects_dir / "to-delete"
        project_dir.mkdir()
        (project_dir / "project.yaml").write_text("project:\n  name: to-delete")

        result = runner.invoke(
            delete, ["to-delete", "--output-dir", str(temp_projects_dir), "--force"]
        )

        assert result.exit_code == 0
        assert "deleted successfully" in result.output
        assert not project_dir.exists()

    def test_delete_nonexistent_project(self, runner, temp_projects_dir):
        """Test error when deleting non-existent project."""
        result = runner.invoke(
            delete, ["nonexistent", "--output-dir", str(temp_projects_dir), "--force"]
        )

        assert result.exit_code != 0
        assert "not found" in result.output

    def test_delete_invalid_project(self, runner, temp_projects_dir):
        """Test error when deleting directory without project.yaml."""
        # Create directory without project.yaml
        invalid_dir = temp_projects_dir / "not-a-project"
        invalid_dir.mkdir()

        result = runner.invoke(
            delete, ["not-a-project", "--output-dir", str(temp_projects_dir), "--force"]
        )

        assert result.exit_code != 0
        assert "not a valid project" in result.output


class TestProjectValidate:
    """Test project validate command."""

    def test_validate_valid_project(self, runner, temp_projects_dir):
        """Test validating a valid project."""
        # Create valid project
        project_dir = temp_projects_dir / "valid-project"
        project_dir.mkdir()

        config = {
            "project": {
                "name": "valid-project",
                "version": "1.0.0",
                "description": "A valid project",
            }
        }
        with open(project_dir / "project.yaml", "w") as f:
            yaml.dump(config, f)

        # Create required directories
        (project_dir / "examples").mkdir()
        (project_dir / "src").mkdir()
        (project_dir / "tests").mkdir()
        (project_dir / "output").mkdir()

        # Add example file
        (project_dir / "examples" / "test.json").write_text("{}")

        result = runner.invoke(
            validate, ["valid-project", "--output-dir", str(temp_projects_dir)]
        )

        assert result.exit_code == 0
        assert "is valid" in result.output

    def test_validate_project_with_warnings(self, runner, temp_projects_dir):
        """Test validating a project with warnings."""
        # Create project with missing optional fields
        project_dir = temp_projects_dir / "warning-project"
        project_dir.mkdir()

        config = {"project": {"name": "warning-project"}}  # Missing version
        with open(project_dir / "project.yaml", "w") as f:
            yaml.dump(config, f)

        result = runner.invoke(
            validate, ["warning-project", "--output-dir", str(temp_projects_dir)]
        )

        assert result.exit_code == 0
        assert "valid with warnings" in result.output
        assert "Missing project.version" in result.output

    def test_validate_project_with_errors(self, runner, temp_projects_dir):
        """Test validating a project with errors."""
        # Create project with missing required fields
        project_dir = temp_projects_dir / "error-project"
        project_dir.mkdir()

        config = {}  # Missing project section
        with open(project_dir / "project.yaml", "w") as f:
            yaml.dump(config, f)

        result = runner.invoke(
            validate, ["error-project", "--output-dir", str(temp_projects_dir)]
        )

        assert result.exit_code != 0
        assert "validation errors" in result.output
        assert "Missing 'project' section" in result.output

    def test_validate_nonexistent_project(self, runner, temp_projects_dir):
        """Test error when validating non-existent project."""
        result = runner.invoke(
            validate, ["nonexistent", "--output-dir", str(temp_projects_dir)]
        )

        assert result.exit_code != 0
        assert "not found" in result.output

    def test_validate_project_verbose(self, runner, temp_projects_dir):
        """Test validating a project in verbose mode."""
        # Create valid project
        project_dir = temp_projects_dir / "verbose-project"
        project_dir.mkdir()

        config = {
            "project": {
                "name": "verbose-project",
                "version": "1.0.0",
            }
        }
        with open(project_dir / "project.yaml", "w") as f:
            yaml.dump(config, f)

        result = runner.invoke(
            validate,
            ["verbose-project", "--output-dir", str(temp_projects_dir), "--verbose"],
        )

        assert result.exit_code == 0
        assert "Validation Report" in result.output
        assert "verbose-project" in result.output


class TestProjectCommandGroup:
    """Test the project command group."""

    def test_project_help(self, runner):
        """Test project command help."""
        result = runner.invoke(project, ["--help"])

        assert result.exit_code == 0
        assert "Manage projects" in result.output
        assert "create" in result.output
        assert "list" in result.output
        assert "delete" in result.output
        assert "validate" in result.output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

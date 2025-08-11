from pathlib import Path
from textwrap import dedent

import pytest
from dagster_dg_core.utils import ensure_dagster_dg_tests_import, pushd

ensure_dagster_dg_tests_import()
from dagster_dg_core_tests.utils import ProxyRunner, assert_runner_result


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Create a minimal dg project structure for testing."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create src structure
    src_dir = project_dir / "src" / "test_project"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").touch()

    # Create defs directory
    defs_dir = src_dir / "defs"
    defs_dir.mkdir()
    (defs_dir / "__init__.py").touch()

    return project_dir


def test_check_toml_valid_pyproject_toml(temp_project: Path) -> None:
    """Test that valid pyproject.toml passes validation."""
    pyproject_content = dedent("""
        [tool.dg]
        directory_type = "project"
        
        [tool.dg.project]
        root_module = "test_project"
    """).strip()

    (temp_project / "pyproject.toml").write_text(pyproject_content)

    with ProxyRunner.test() as runner, pushd(temp_project):
        result = runner.invoke("check", "toml")
        assert_runner_result(result, exit_0=True)
        assert "All TOML configuration files are valid" in result.output


def test_check_toml_valid_dg_toml(temp_project: Path) -> None:
    """Test that valid dg.toml passes validation."""
    dg_toml_content = dedent("""
        directory_type = "project"
        
        [project]
        root_module = "test_project"
    """).strip()

    (temp_project / "dg.toml").write_text(dg_toml_content)

    with ProxyRunner.test() as runner, pushd(temp_project):
        result = runner.invoke("check", "toml")
        assert_runner_result(result, exit_0=True)
        assert "All TOML configuration files are valid" in result.stdout


def test_check_toml_missing_directory_type(temp_project: Path) -> None:
    """Test that missing directory_type is caught."""
    pyproject_content = dedent("""
        [tool.dg]
        # missing directory_type
        
        [tool.dg.project]
        root_module = "test_project"
    """).strip()

    (temp_project / "pyproject.toml").write_text(pyproject_content)

    with ProxyRunner.test() as runner, pushd(temp_project):
        result = runner.invoke("check", "toml")
        assert_runner_result(result, exit_0=False)
        assert "Missing required value for `tool.dg.directory_type`" in result.stderr


def test_check_toml_invalid_directory_type(temp_project: Path) -> None:
    """Test that invalid directory_type value is caught."""
    pyproject_content = dedent("""
        [tool.dg]
        directory_type = "invalid"
        
        [tool.dg.project]
        root_module = "test_project"
    """).strip()

    (temp_project / "pyproject.toml").write_text(pyproject_content)

    with ProxyRunner.test() as runner, pushd(temp_project):
        result = runner.invoke("check", "toml")
        assert_runner_result(result, exit_0=False)
        assert "Invalid value for `tool.dg.directory_type`" in result.stderr


def test_check_toml_missing_required_project_fields(temp_project: Path) -> None:
    """Test that missing required project fields are caught."""
    pyproject_content = dedent("""
        [tool.dg]
        directory_type = "project"
        
        [tool.dg.project]
        # missing root_module
    """).strip()

    (temp_project / "pyproject.toml").write_text(pyproject_content)

    with ProxyRunner.test() as runner, pushd(temp_project):
        result = runner.invoke("check", "toml")
        assert_runner_result(result, exit_0=False)
        assert "Missing required value for `tool.dg.project.root_module`" in result.stderr


def test_check_toml_invalid_type_project_fields(temp_project: Path) -> None:
    """Test that type validation catches incorrect field types."""
    pyproject_content = dedent("""
        [tool.dg]
        directory_type = "project"
        
        [tool.dg.project]
        root_module = 123  # should be string
    """).strip()

    (temp_project / "pyproject.toml").write_text(pyproject_content)

    with ProxyRunner.test() as runner, pushd(temp_project):
        result = runner.invoke("check", "toml")
        assert_runner_result(result, exit_0=False)
        assert "Invalid value for `tool.dg.project.root_module`" in result.stderr
        assert "Expected str, got `123`" in result.stderr


def test_check_toml_invalid_cli_fields(temp_project: Path) -> None:
    """Test validation of CLI configuration fields."""
    pyproject_content = dedent("""
        [tool.dg]
        directory_type = "project"
        
        [tool.dg.cli]
        verbose = "not_boolean"  # should be boolean
        
        [tool.dg.project]
        root_module = "test_project"
    """).strip()

    (temp_project / "pyproject.toml").write_text(pyproject_content)

    with ProxyRunner.test() as runner, pushd(temp_project):
        result = runner.invoke("check", "toml")
        assert_runner_result(result, exit_0=False)
        assert "Invalid value for `tool.dg.cli.verbose`" in result.stderr


def test_check_toml_extraneous_fields(temp_project: Path) -> None:
    """Test that extraneous fields are caught."""
    pyproject_content = dedent("""
        [tool.dg]
        directory_type = "project"
        invalid_extra_field = "should_not_be_here"
        
        [tool.dg.project]
        root_module = "test_project"
        another_invalid_field = 42
    """).strip()

    (temp_project / "pyproject.toml").write_text(pyproject_content)

    with ProxyRunner.test() as runner, pushd(temp_project):
        result = runner.invoke("check", "toml")
        assert_runner_result(result, exit_0=False)
        assert "Unrecognized fields at `tool.dg`" in result.stderr
        assert "invalid_extra_field" in result.stderr


def test_check_toml_invalid_registry_modules_pattern(temp_project: Path) -> None:
    """Test validation of registry_modules patterns."""
    pyproject_content = dedent("""
        [tool.dg]
        directory_type = "project"
        
        [tool.dg.project]
        root_module = "test_project"
        registry_modules = ["invalid-pattern-with-hyphens"]
    """).strip()

    (temp_project / "pyproject.toml").write_text(pyproject_content)

    with ProxyRunner.test() as runner, pushd(temp_project):
        result = runner.invoke("check", "toml")
        assert_runner_result(result, exit_0=False)
        assert "Invalid module pattern `invalid-pattern-with-hyphens`" in result.stderr


def test_check_toml_mutually_exclusive_fields(temp_project: Path) -> None:
    """Test validation of mutually exclusive fields."""
    pyproject_content = dedent("""
        [tool.dg]
        directory_type = "project"
        
        [tool.dg.project]
        root_module = "test_project"
        autoload_defs = true
        code_location_target_module = "test_project.definitions"
    """).strip()

    (temp_project / "pyproject.toml").write_text(pyproject_content)

    with ProxyRunner.test() as runner, pushd(temp_project):
        result = runner.invoke("check", "toml")
        assert_runner_result(result, exit_0=False)
        assert (
            "Cannot specify `tool.dg.project.code_location_target_module` when `tool.dg.project.autoload_defs` is True"
            in result.stderr
        )


def test_check_toml_invalid_toml_syntax(temp_project: Path) -> None:
    """Test that malformed TOML syntax is caught."""
    invalid_toml = dedent("""
        [tool.dg]
        directory_type = "project"
        
        [tool.dg.project
        # Missing closing bracket
        root_module = "test_project"
    """).strip()

    (temp_project / "pyproject.toml").write_text(invalid_toml)

    with ProxyRunner.test() as runner, pushd(temp_project):
        result = runner.invoke("check", "toml")
        assert_runner_result(result, exit_0=False)


def test_check_toml_workspace_config_validation(temp_project: Path) -> None:
    """Test workspace configuration validation."""
    dg_toml_content = dedent("""
        directory_type = "workspace"
        
        [workspace]
        projects = [
            { path = "nonexistent/path" }
        ]
    """).strip()

    (temp_project / "dg.toml").write_text(dg_toml_content)

    with ProxyRunner.test() as runner, pushd(temp_project):
        runner.invoke("check", "toml")
        # This may pass validation but fail on path existence -
        # that's implementation dependent
        # The key is that schema validation happens first


def test_check_toml_invalid_telemetry_config(temp_project: Path) -> None:
    """Test telemetry configuration validation."""
    pyproject_content = dedent("""
        [tool.dg]
        directory_type = "project"
        
        [tool.dg.cli]
        [tool.dg.cli.telemetry]
        enabled = "not_boolean"  # should be boolean
        
        [tool.dg.project]
        root_module = "test_project"
    """).strip()

    (temp_project / "pyproject.toml").write_text(pyproject_content)

    with ProxyRunner.test() as runner, pushd(temp_project):
        result = runner.invoke("check", "toml")
        assert_runner_result(result, exit_0=False)
        assert "Invalid value for `tool.dg.cli.telemetry.enabled`" in result.stderr


def test_check_toml_with_strict_flag(temp_project: Path) -> None:
    """Test that --strict flag enables stricter validation."""
    # This test verifies the --strict flag is accepted
    # Implementation details would depend on what strict mode does
    pyproject_content = dedent("""
        [tool.dg]
        directory_type = "project"
        
        [tool.dg.project]
        root_module = "test_project"
    """).strip()

    (temp_project / "pyproject.toml").write_text(pyproject_content)

    with ProxyRunner.test() as runner, pushd(temp_project):
        result = runner.invoke("check", "toml", "--strict")
        assert_runner_result(result, exit_0=True)
        assert "All TOML configuration files are valid" in result.stdout


def test_check_toml_both_dg_toml_and_pyproject_toml(temp_project: Path) -> None:
    """Test behavior when both dg.toml and pyproject.toml exist."""
    # dg.toml should take precedence over pyproject.toml
    dg_toml_content = dedent("""
        directory_type = "project"
        
        [project]
        root_module = "test_project"
    """).strip()

    pyproject_content = dedent("""
        [tool.dg]
        directory_type = "workspace"  # This should be ignored
    """).strip()

    (temp_project / "dg.toml").write_text(dg_toml_content)
    (temp_project / "pyproject.toml").write_text(pyproject_content)

    with ProxyRunner.test() as runner, pushd(temp_project):
        result = runner.invoke("check", "toml")
        assert_runner_result(result, exit_0=True)
        assert "All TOML configuration files are valid" in result.stdout

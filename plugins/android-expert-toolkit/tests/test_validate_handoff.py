#!/usr/bin/env python3
"""
Tests for validate-handoff.py hook.
Tests both CLI integration and internal validation functions.
"""

import subprocess
import sys
from pathlib import Path

import pytest

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent
VALIDATE_SCRIPT = PROJECT_ROOT / "hooks" / "validate-handoff.py"
FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"

# Import the module directly for unit tests
sys.path.insert(0, str(PROJECT_ROOT / "hooks"))
from importlib import import_module
validate_handoff_mod = import_module("validate-handoff")


def run_validation(fixture_name: str) -> tuple[int, str, str]:
    """Run validation on a fixture file. Returns (exit_code, stdout, stderr)."""
    fixture_path = FIXTURES_DIR / fixture_name

    result = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), str(fixture_path)],
        capture_output=True,
        text=True
    )

    return result.returncode, result.stdout, result.stderr


# --- Existing integration tests ---

def test_valid_architecture_blueprint():
    """Test that a valid architecture blueprint passes validation."""
    exit_code, stdout, stderr = run_validation("architecture-blueprint-valid.md")

    assert exit_code == 0, f"Valid blueprint should pass. stderr: {stderr}"
    assert "✓" in stdout, "Success message should contain checkmark"
    assert "valid" in stdout.lower(), "Success message should mention validity"


def test_invalid_architecture_blueprint():
    """Test that an invalid architecture blueprint fails validation."""
    exit_code, stdout, stderr = run_validation("architecture-blueprint-invalid.md")

    assert exit_code == 1, "Invalid blueprint should fail"
    assert "validation failed" in stderr.lower(), "Should report validation failure"


def test_template_file_validation():
    """Test that template files can be validated (with -template suffix stripped)."""
    template_path = PROJECT_ROOT / "templates" / "architecture-blueprint-template.md"

    result = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), str(template_path)],
        capture_output=True,
        text=True
    )

    exit_code = result.returncode
    stdout = result.stdout
    stderr = result.stderr

    assert exit_code == 0, f"Template should validate. stderr: {stderr}"
    assert "✓" in stdout, "Template validation should succeed"


def test_unknown_artifact_type():
    """Test that unknown artifact types are rejected."""
    unknown_file = FIXTURES_DIR / "unknown-artifact.md"
    unknown_file.write_text("# Unknown\n## Summary\nTest")

    try:
        result = subprocess.run(
            [sys.executable, str(VALIDATE_SCRIPT), str(unknown_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 1, "Unknown artifact type should fail"
        assert "Unknown artifact type" in result.stderr, "Should report unknown type"
    finally:
        unknown_file.unlink(missing_ok=True)


def test_missing_file():
    """Test that missing files are handled gracefully."""
    result = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), "/nonexistent/file.md"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 1, "Missing file should fail"
    assert "validation failed" in result.stderr.lower() or "not found" in result.stderr.lower()


# --- Phase 2.3: Content quality tests ---

class TestSectionDepth:
    """Test that each required section has >2 lines of content."""

    def test_section_with_sufficient_content(self):
        content = """## Summary

This is a summary line one.
This is a summary line two.
This is a summary line three.
"""
        ok, msg = validate_handoff_mod.check_section_depth(content, "Summary")
        assert ok, f"Should pass with 3 lines: {msg}"

    def test_section_with_insufficient_content(self):
        content = """## Summary

Just one line.
"""
        ok, msg = validate_handoff_mod.check_section_depth(content, "Summary")
        assert not ok, "Should fail with only 1 non-empty line"
        assert "insufficient content" in msg

    def test_section_with_exactly_two_lines(self):
        content = """## Summary

Line one.
Line two.
"""
        ok, msg = validate_handoff_mod.check_section_depth(content, "Summary")
        assert not ok, "Should fail with exactly 2 lines (need >2)"

    def test_missing_section_returns_empty(self):
        content = """## Other Section

Some content here.
"""
        body = validate_handoff_mod.get_section_content(content, "Summary")
        assert body == "", "Missing section should return empty string"


class TestNoPlaceholders:
    """Test that placeholder text is detected."""

    def test_todo_placeholder(self):
        errors = validate_handoff_mod.check_no_placeholders("Some text [TODO] more text")
        assert len(errors) == 1
        assert "TODO" in errors[0]

    def test_fill_in_placeholder(self):
        errors = validate_handoff_mod.check_no_placeholders("Some text [FILL IN] here")
        assert len(errors) == 1
        assert "FILL" in errors[0]

    def test_tbd_placeholder(self):
        errors = validate_handoff_mod.check_no_placeholders("[TBD] details later")
        assert len(errors) == 1
        assert "TBD" in errors[0]

    def test_html_placeholder(self):
        errors = validate_handoff_mod.check_no_placeholders("Use <placeholder> for now")
        assert len(errors) == 1
        assert "placeholder" in errors[0].lower()

    def test_lorem_ipsum(self):
        errors = validate_handoff_mod.check_no_placeholders("Lorem ipsum dolor sit amet")
        assert len(errors) == 1
        assert "lorem ipsum" in errors[0].lower()

    def test_clean_content(self):
        errors = validate_handoff_mod.check_no_placeholders(
            "This is real content with actual decisions and rationale."
        )
        assert len(errors) == 0

    def test_case_insensitive(self):
        errors = validate_handoff_mod.check_no_placeholders("[todo] fix this")
        assert len(errors) == 1


class TestArtifactsCreatedPaths:
    """Test that Artifacts Created section lists actual file paths."""

    def test_with_paths(self):
        content = """## Artifacts Created

- feature/feed/api/src/main/kotlin/FeedApi.kt
- feature/feed/impl/src/main/kotlin/FeedRepository.kt
- core/database/src/main/kotlin/FeedDao.kt
"""
        ok, msg = validate_handoff_mod.check_artifacts_created_paths(content)
        assert ok, f"Should pass with file paths: {msg}"

    def test_without_paths(self):
        content = """## Artifacts Created

- Some module
- Another thing
"""
        ok, msg = validate_handoff_mod.check_artifacts_created_paths(content)
        assert not ok, "Should fail without file paths"
        assert "file paths" in msg

    def test_missing_section(self):
        content = """## Summary

Just a summary.
"""
        ok, msg = validate_handoff_mod.check_artifacts_created_paths(content)
        assert ok, "Missing section should not trigger path check error"


class TestNextStepsActionable:
    """Test that Next Steps section has actionable items."""

    def test_actionable_steps(self):
        content = """## Next Steps

- gradle-build-engineer: Create feature/feed/api and feature/feed/impl modules
- android-developer: Implement FeedRepository with Room database
- compose-expert: Build FeedScreen with Material 3 components
"""
        ok, msg = validate_handoff_mod.check_next_steps_actionable(content)
        assert ok, f"Should pass with actionable steps: {msg}"

    def test_generic_continue_development(self):
        content = """## Next Steps

Continue development
"""
        ok, msg = validate_handoff_mod.check_next_steps_actionable(content)
        assert not ok, "Should fail with generic 'continue development'"
        assert "generic filler" in msg

    def test_generic_tbd(self):
        content = """## Next Steps

TBD
"""
        ok, msg = validate_handoff_mod.check_next_steps_actionable(content)
        assert not ok, "Should fail with generic 'TBD'"

    def test_missing_section(self):
        content = """## Summary

Just a summary.
"""
        ok, msg = validate_handoff_mod.check_next_steps_actionable(content)
        assert ok, "Missing section should not trigger actionable check error"


class TestIntegrationContentQuality:
    """Integration tests that run full validation with content quality checks via CLI."""

    def test_placeholder_in_blueprint_fails(self):
        """A blueprint with [TODO] placeholder should fail validation."""
        tmp_path = FIXTURES_DIR / "architecture-blueprint-test.md"
        tmp_path.write_text("""# Architecture Blueprint

## Summary

This feature does [TODO] things.
With multiple lines of content.
And more detail here.

## Decisions

### Decision 1
[FILL IN] the decision details.
More context about the decision.
And the rationale behind it.

## Artifacts Created

feature/test/api/src/main/kotlin/Api.kt
feature/test/impl/src/main/kotlin/Impl.kt
feature/test/impl/src/main/kotlin/Repo.kt

## Next Steps

- gradle-build-engineer: Create modules for the feature
- android-developer: Implement the data layer
- compose-expert: Build the UI screens

## Constraints

- Must use Hilt for DI
- Offline-first required
- StateFlow for state management
""")

        try:
            result = subprocess.run(
                [sys.executable, str(VALIDATE_SCRIPT), str(tmp_path)],
                capture_output=True, text=True
            )
            assert result.returncode == 1, f"Should fail with placeholders. stdout: {result.stdout}"
            assert "Placeholder text found" in result.stderr
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_no_paths_in_artifacts_fails(self):
        """A blueprint where Artifacts Created has no file paths should fail."""
        tmp_path = FIXTURES_DIR / "2026-01-01-000000-architecture-blueprint.md"
        tmp_path.write_text("""# Architecture Blueprint

## Summary

This is a proper summary with enough content.
Multiple lines describing the architecture.
And a third line for good measure.

## Decisions

### Decision 1: Use StateFlow
Context: Need reactive state.
Decision: StateFlow chosen.
Rationale: Modern Kotlin-first approach.

## Artifacts Created

- Feed module
- Database module
- Network module

## Next Steps

- gradle-build-engineer: Create feed module with convention plugins
- android-developer: Implement FeedRepository with Room
- compose-expert: Build FeedScreen composable

## Constraints

- Must use Hilt for DI
- Offline-first pattern required
- StateFlow for all state
""")

        try:
            result = subprocess.run(
                [sys.executable, str(VALIDATE_SCRIPT), str(tmp_path)],
                capture_output=True, text=True
            )
            assert result.returncode == 1, f"Should fail without paths. stdout: {result.stdout}"
            assert "file paths" in result.stderr
        finally:
            tmp_path.unlink(missing_ok=True)

#!/usr/bin/env python3
"""
End-to-end pipeline tests.
Validates pipeline state transitions, artifact creation, and validation flow.
"""

import json
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"
SAMPLE_PROJECT = FIXTURES_DIR / "sample-project"

sys.path.insert(0, str(PROJECT_ROOT / "hooks"))
from importlib import import_module
track_progress = import_module("track-progress")
validate_handoff_mod = import_module("validate-handoff")


@pytest.fixture
def pipeline_project():
    """Create a temp project mimicking a real pipeline run."""
    temp_dir = Path(tempfile.mkdtemp())

    # Copy sample project files
    shutil.copytree(SAMPLE_PROJECT, temp_dir / "project", dirs_exist_ok=True)
    project_dir = temp_dir / "project"

    # Create pipeline directories
    aet_dir = project_dir / ".artifacts" / "aet"
    aet_dir.mkdir(parents=True)
    handoffs_dir = aet_dir / "handoffs" / "social-feed"
    handoffs_dir.mkdir(parents=True)

    yield project_dir
    shutil.rmtree(temp_dir)


class TestPipelineStateTransitions:
    """Test that pipeline state transitions correctly through stages."""

    def test_initial_state_creation(self, pipeline_project):
        state_path = pipeline_project / ".artifacts" / "aet" / "state.json"

        state = {
            "pipeline_type": "feature-build",
            "feature_name": "Social Feed",
            "feature_slug": "social-feed",
            "run_timestamp": "2026-03-01-100000",
            "started_at": "2026-03-01T10:00:00Z",
            "completed_at": None,
            "status": "in_progress",
            "current_stage": None,
            "completed_stages": [],
            "artifacts": {}
        }
        state_path.write_text(json.dumps(state, indent=2))

        loaded = json.loads(state_path.read_text())
        assert loaded["status"] == "in_progress"
        assert loaded["completed_stages"] == []
        assert loaded["pipeline_type"] == "feature-build"

    def test_stage_progression(self, pipeline_project):
        """Simulate progressing through multiple pipeline stages."""
        state_path = pipeline_project / ".artifacts" / "aet" / "state.json"
        handoffs_dir = pipeline_project / ".artifacts" / "aet" / "handoffs" / "social-feed"

        state = {
            "pipeline_type": "feature-build",
            "feature_name": "Social Feed",
            "feature_slug": "social-feed",
            "run_timestamp": "2026-03-01-100000",
            "started_at": "2026-03-01T10:00:00Z",
            "completed_at": None,
            "status": "in_progress",
            "current_stage": None,
            "completed_stages": [],
            "artifacts": {}
        }
        state_path.write_text(json.dumps(state, indent=2))

        with patch.object(track_progress, 'get_state_file_path', return_value=state_path):
            # Stage 1: Architect writes blueprint
            blueprint_content = """# Architecture Blueprint: Social Feed

## Pipeline Context

**Original Prompt:** Build a social feed with offline support

**Business Purpose:** Let users browse and create posts in a social feed, even when offline.

**UX Intent:** Card-based vertical feed with pull-to-refresh, detail view on tap.

## Summary

Social feed feature with offline-first architecture.
Uses MVVM pattern with StateFlow for state management.
Hilt for dependency injection across all modules.

## Decisions

### Decision 1: Use StateFlow
Context: Need reactive state management.
Decision: StateFlow for modern Kotlin-first approach.
Rationale: Coroutine-integrated, lifecycle-aware.

## Artifacts Created

feature/social-feed/api/src/main/kotlin/FeedApi.kt
feature/social-feed/impl/src/main/kotlin/FeedRepository.kt
feature/social-feed/impl/src/main/kotlin/FeedViewModel.kt

## Next Steps

- gradle-build-engineer: Create feature/social-feed/api and impl modules
- android-developer: Implement FeedRepository with Room and Retrofit
- compose-expert: Build FeedScreen with LazyColumn

## Constraints

- Must use Hilt for DI in all feature modules
- Offline-first: Room as source of truth
- StateFlow for all ViewModel state exposure
"""
            blueprint_path = handoffs_dir / "2026-03-01-100000-architecture-blueprint.md"
            blueprint_path.write_text(blueprint_content)

            track_progress.update_pipeline_state(
                "Write",
                {
                    "file_path": str(blueprint_path),
                    "content": blueprint_content
                },
                ""
            )

            updated = json.loads(state_path.read_text())
            assert len(updated["completed_stages"]) == 1
            assert updated["completed_stages"][0]["agent"] == "android-architect"
            assert updated["current_stage"] == "android-architect"
            assert "architecture-blueprint" in updated["artifacts"]

    def test_full_pipeline_completion(self, pipeline_project):
        """Simulate completing all stages of a feature-build pipeline."""
        state_path = pipeline_project / ".artifacts" / "aet" / "state.json"

        completed_state = {
            "pipeline_type": "feature-build",
            "feature_name": "Social Feed",
            "feature_slug": "social-feed",
            "run_timestamp": "2026-03-01-100000",
            "started_at": "2026-03-01T10:00:00Z",
            "completed_at": "2026-03-01T12:00:00Z",
            "status": "completed",
            "current_stage": "android-testing-specialist",
            "completed_stages": [
                {"agent": "android-architect", "completed_at": "2026-03-01T10:15:00Z", "validation_passed": True},
                {"agent": "gradle-build-engineer", "completed_at": "2026-03-01T10:30:00Z", "validation_passed": True},
                {"agent": "android-developer", "completed_at": "2026-03-01T11:00:00Z", "validation_passed": True},
                {"agent": "compose-expert", "completed_at": "2026-03-01T11:30:00Z", "validation_passed": True},
                {"agent": "android-testing-specialist", "completed_at": "2026-03-01T12:00:00Z", "validation_passed": True},
            ],
            "artifacts": {
                "architecture-blueprint": ".artifacts/aet/handoffs/social-feed/2026-03-01-100000-architecture-blueprint.md",
                "module-setup": ".artifacts/aet/handoffs/social-feed/2026-03-01-100000-module-setup.md",
                "implementation-report": ".artifacts/aet/handoffs/social-feed/2026-03-01-100000-implementation-report.md",
                "ui-report": ".artifacts/aet/handoffs/social-feed/2026-03-01-100000-ui-report.md",
                "test-report": ".artifacts/aet/handoffs/social-feed/2026-03-01-100000-test-report.md",
            }
        }
        state_path.write_text(json.dumps(completed_state, indent=2))

        loaded = json.loads(state_path.read_text())
        assert loaded["status"] == "completed"
        assert len(loaded["completed_stages"]) == 5
        assert all(s["validation_passed"] for s in loaded["completed_stages"])


class TestArtifactValidationFlow:
    """Test the artifact creation -> validation flow."""

    def test_valid_artifact_passes_cli(self, pipeline_project):
        """Create a valid artifact and validate it via CLI."""
        handoffs_dir = pipeline_project / ".artifacts" / "aet" / "handoffs" / "social-feed"
        blueprint_path = handoffs_dir / "2026-03-01-100000-architecture-blueprint.md"

        # Write a valid blueprint
        blueprint_path.write_text("""# Architecture Blueprint: Social Feed

## Pipeline Context

**Original Prompt:** Build a social feed with offline support

**Business Purpose:** Let users browse and create posts in a social feed, even when offline.

**UX Intent:** Card-based vertical feed with pull-to-refresh, detail view on tap.

## Summary

Social feed feature with offline-first architecture.
Uses MVVM pattern with StateFlow for state management.
Hilt for dependency injection across modules.

## Decisions

### Decision 1: Use StateFlow
Context: Need reactive state management.
Decision: StateFlow for modern Kotlin patterns.
Rationale: Coroutine-integrated, lifecycle-aware.

## Artifacts Created

feature/social-feed/api/src/main/kotlin/FeedApi.kt
feature/social-feed/impl/src/main/kotlin/FeedRepository.kt
feature/social-feed/impl/src/main/kotlin/FeedViewModel.kt

## Next Steps

- gradle-build-engineer: Create feature modules with convention plugins
- android-developer: Implement FeedRepository with Room database
- compose-expert: Build FeedScreen with Material 3 components

## Constraints

- Must use Hilt for DI in all feature modules
- Offline-first: Room as source of truth
- StateFlow for all ViewModel state exposure
""")

        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "hooks" / "validate-handoff.py"), str(blueprint_path)],
            capture_output=True, text=True
        )
        assert result.returncode == 0, f"Valid blueprint should pass. stderr: {result.stderr}"

    def test_invalid_artifact_fails_cli(self, pipeline_project):
        """Create an invalid artifact and verify it fails validation."""
        handoffs_dir = pipeline_project / ".artifacts" / "aet" / "handoffs" / "social-feed"
        blueprint_path = handoffs_dir / "2026-03-01-100000-architecture-blueprint.md"

        # Write a blueprint missing sections
        blueprint_path.write_text("""# Architecture Blueprint: Social Feed

## Summary

Incomplete blueprint.
""")

        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "hooks" / "validate-handoff.py"), str(blueprint_path)],
            capture_output=True, text=True
        )
        assert result.returncode == 1
        assert "validation failed" in result.stderr.lower()

    def test_dependency_validation_with_sample_project(self):
        """Test dependency validation against the sample project fixture."""
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "hooks" / "validate-dependencies.py"),
                "android-architect",
                str(SAMPLE_PROJECT)
            ],
            capture_output=True, text=True
        )
        # android-architect has no dependencies, should pass
        assert result.returncode == 0
        assert "prerequisites met" in result.stdout.lower()


class TestSampleProjectFixture:
    """Test that the sample project fixture has the expected structure."""

    def test_build_gradle_exists(self):
        assert (SAMPLE_PROJECT / "build.gradle.kts").exists()

    def test_settings_gradle_exists(self):
        assert (SAMPLE_PROJECT / "settings.gradle.kts").exists()

    def test_source_files_exist(self):
        assert (SAMPLE_PROJECT / "app" / "src" / "main" / "kotlin" / "com" / "example" / "MainActivity.kt").exists()

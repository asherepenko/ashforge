#!/usr/bin/env python3
"""
Tests for track-progress.py hook.
Tests artifact detection, stage updates, validation marking, timing data.
"""

import json
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent

# Import the module
sys.path.insert(0, str(PROJECT_ROOT / "hooks"))
from importlib import import_module
track_progress = import_module("track-progress")


@pytest.fixture
def temp_project():
    """Create a temporary project with .artifacts/aet directory."""
    temp_dir = Path(tempfile.mkdtemp())
    aet_dir = temp_dir / ".artifacts" / "aet"
    aet_dir.mkdir(parents=True)
    handoffs_dir = aet_dir / "handoffs" / "test-feature"
    handoffs_dir.mkdir(parents=True)

    state = {
        "pipeline_type": "feature-build",
        "feature_name": "Test Feature",
        "feature_slug": "test-feature",
        "run_timestamp": "2026-03-01-100000",
        "started_at": "2026-03-01T10:00:00Z",
        "completed_at": None,
        "status": "in_progress",
        "current_stage": None,
        "completed_stages": [],
        "artifacts": {}
    }
    (aet_dir / "state.json").write_text(json.dumps(state, indent=2))

    yield temp_dir
    shutil.rmtree(temp_dir)


class TestArtifactDetection:
    """Test that Write tool calls to handoff paths are detected."""

    def test_detects_architecture_blueprint(self, temp_project):
        with patch.object(track_progress, 'get_state_file_path',
                          return_value=temp_project / ".artifacts" / "aet" / "state.json"):
            track_progress.update_pipeline_state(
                "Write",
                {
                    "file_path": f"{temp_project}/.artifacts/aet/handoffs/test-feature/2026-03-01-100000-architecture-blueprint.md",
                    "content": "# Blueprint\n## Summary\nLine 1\nLine 2\nLine 3\n"
                },
                ""
            )
            state = track_progress.load_state()
            assert len(state["completed_stages"]) == 1
            assert state["completed_stages"][0]["agent"] == "android-architect"

    def test_ignores_non_handoff_writes(self, temp_project):
        with patch.object(track_progress, 'get_state_file_path',
                          return_value=temp_project / ".artifacts" / "aet" / "state.json"):
            track_progress.update_pipeline_state(
                "Write",
                {"file_path": "/some/other/file.md", "content": "test"},
                ""
            )
            state = track_progress.load_state()
            assert len(state["completed_stages"]) == 0

    def test_ignores_non_write_tools(self, temp_project):
        with patch.object(track_progress, 'get_state_file_path',
                          return_value=temp_project / ".artifacts" / "aet" / "state.json"):
            track_progress.update_pipeline_state(
                "Read",
                {"file_path": f"{temp_project}/.artifacts/aet/handoffs/test-feature/architecture-blueprint.md"},
                ""
            )
            state = track_progress.load_state()
            assert len(state["completed_stages"]) == 0

    def test_detects_all_artifact_types(self, temp_project):
        artifact_agent_pairs = [
            ("architecture-blueprint", "android-architect"),
            ("module-setup", "gradle-build-engineer"),
            ("implementation-report", "android-developer"),
            ("ui-report", "compose-expert"),
            ("test-report", "android-testing-specialist"),
        ]

        with patch.object(track_progress, 'get_state_file_path',
                          return_value=temp_project / ".artifacts" / "aet" / "state.json"):
            for artifact_type, expected_agent in artifact_agent_pairs:
                # Reset state between iterations
                state_path = temp_project / ".artifacts" / "aet" / "state.json"
                state = json.loads(state_path.read_text())
                state["completed_stages"] = []
                state["artifacts"] = {}
                state_path.write_text(json.dumps(state, indent=2))

                track_progress.update_pipeline_state(
                    "Write",
                    {
                        "file_path": f"{temp_project}/.artifacts/aet/handoffs/test-feature/2026-03-01-100000-{artifact_type}.md",
                        "content": "content\n" * 10
                    },
                    ""
                )
                updated = track_progress.load_state()
                assert len(updated["completed_stages"]) == 1, f"Failed for {artifact_type}"
                assert updated["completed_stages"][0]["agent"] == expected_agent


class TestStageUpdates:
    """Test stage update behavior."""

    def test_updates_existing_stage(self, temp_project):
        with patch.object(track_progress, 'get_state_file_path',
                          return_value=temp_project / ".artifacts" / "aet" / "state.json"):
            # First write
            track_progress.update_pipeline_state(
                "Write",
                {
                    "file_path": f"{temp_project}/.artifacts/aet/handoffs/test-feature/2026-03-01-100000-architecture-blueprint.md",
                    "content": "v1\n" * 5
                },
                ""
            )
            # Second write (update)
            track_progress.update_pipeline_state(
                "Write",
                {
                    "file_path": f"{temp_project}/.artifacts/aet/handoffs/test-feature/2026-03-01-100000-architecture-blueprint.md",
                    "content": "v2\n" * 10
                },
                ""
            )
            state = track_progress.load_state()
            assert len(state["completed_stages"]) == 1, "Should update, not duplicate"
            assert state["completed_stages"][0]["artifact_size_lines"] == 11

    def test_creates_state_if_missing(self, temp_project):
        # Remove existing state
        state_path = temp_project / ".artifacts" / "aet" / "state.json"
        state_path.unlink()

        with patch.object(track_progress, 'get_state_file_path',
                          return_value=state_path):
            track_progress.update_pipeline_state(
                "Write",
                {
                    "file_path": f"{temp_project}/.artifacts/aet/handoffs/test-feature/2026-03-01-100000-architecture-blueprint.md",
                    "content": "new state\n" * 5
                },
                ""
            )
            assert state_path.exists()
            state = json.loads(state_path.read_text())
            assert state["status"] == "in_progress"


class TestValidationMarking:
    """Test validation passed/failed marking via Bash tool."""

    def test_marks_validation_passed(self, temp_project):
        state_path = temp_project / ".artifacts" / "aet" / "state.json"
        state = json.loads(state_path.read_text())
        state["completed_stages"] = [{
            "agent": "android-architect",
            "artifact": ".artifacts/aet/handoffs/test-feature/2026-03-01-100000-architecture-blueprint.md",
            "completed_at": "2026-03-01T10:05:00Z",
            "validation_passed": False,
            "validation_errors": []
        }]
        state_path.write_text(json.dumps(state, indent=2))

        with patch.object(track_progress, 'get_state_file_path', return_value=state_path):
            track_progress.mark_validation_passed(
                {"command": "python3 hooks/validate-handoff.py .artifacts/aet/handoffs/test-feature/2026-03-01-100000-architecture-blueprint.md"},
                "✓ .artifacts/aet/handoffs/test-feature/2026-03-01-100000-architecture-blueprint.md is valid"
            )
            updated = json.loads(state_path.read_text())
            assert updated["completed_stages"][0]["validation_passed"] is True
            assert updated["completed_stages"][0]["validation_errors"] == []

    def test_marks_validation_failed_with_errors(self, temp_project):
        state_path = temp_project / ".artifacts" / "aet" / "state.json"
        state = json.loads(state_path.read_text())
        state["completed_stages"] = [{
            "agent": "android-architect",
            "artifact": ".artifacts/aet/handoffs/test-feature/2026-03-01-100000-architecture-blueprint.md",
            "completed_at": "2026-03-01T10:05:00Z",
            "validation_passed": False,
            "validation_errors": []
        }]
        state_path.write_text(json.dumps(state, indent=2))

        with patch.object(track_progress, 'get_state_file_path', return_value=state_path):
            track_progress.mark_validation_passed(
                {"command": "python3 hooks/validate-handoff.py .artifacts/aet/handoffs/test-feature/2026-03-01-100000-architecture-blueprint.md"},
                "✗ validation failed\n  - Missing section: Decisions\n  - Missing section: Constraints"
            )
            updated = json.loads(state_path.read_text())
            assert updated["completed_stages"][0]["validation_passed"] is False
            assert len(updated["completed_stages"][0]["validation_errors"]) > 0

    def test_ignores_non_validation_bash(self, temp_project):
        with patch.object(track_progress, 'get_state_file_path',
                          return_value=temp_project / ".artifacts" / "aet" / "state.json"):
            track_progress.mark_validation_passed(
                {"command": "ls -la"},
                "some output"
            )
            # Should not crash or modify state


class TestTimingData:
    """Test that timing fields are populated."""

    def test_completed_at_is_set(self, temp_project):
        with patch.object(track_progress, 'get_state_file_path',
                          return_value=temp_project / ".artifacts" / "aet" / "state.json"):
            track_progress.update_pipeline_state(
                "Write",
                {
                    "file_path": f"{temp_project}/.artifacts/aet/handoffs/test-feature/2026-03-01-100000-architecture-blueprint.md",
                    "content": "line\n" * 5
                },
                ""
            )
            state = track_progress.load_state()
            step = state["completed_stages"][0]
            assert "completed_at" in step
            assert step["completed_at"].endswith("Z")

    def test_started_at_is_set(self, temp_project):
        with patch.object(track_progress, 'get_state_file_path',
                          return_value=temp_project / ".artifacts" / "aet" / "state.json"):
            track_progress.update_pipeline_state(
                "Write",
                {
                    "file_path": f"{temp_project}/.artifacts/aet/handoffs/test-feature/2026-03-01-100000-architecture-blueprint.md",
                    "content": "line\n" * 5
                },
                ""
            )
            state = track_progress.load_state()
            step = state["completed_stages"][0]
            assert "started_at" in step

    def test_artifact_size_lines(self, temp_project):
        with patch.object(track_progress, 'get_state_file_path',
                          return_value=temp_project / ".artifacts" / "aet" / "state.json"):
            content = "line\n" * 25
            track_progress.update_pipeline_state(
                "Write",
                {
                    "file_path": f"{temp_project}/.artifacts/aet/handoffs/test-feature/2026-03-01-100000-architecture-blueprint.md",
                    "content": content
                },
                ""
            )
            state = track_progress.load_state()
            step = state["completed_stages"][0]
            assert step["artifact_size_lines"] == 26

    def test_validation_errors_default_empty(self, temp_project):
        with patch.object(track_progress, 'get_state_file_path',
                          return_value=temp_project / ".artifacts" / "aet" / "state.json"):
            track_progress.update_pipeline_state(
                "Write",
                {
                    "file_path": f"{temp_project}/.artifacts/aet/handoffs/test-feature/2026-03-01-100000-architecture-blueprint.md",
                    "content": "line\n" * 5
                },
                ""
            )
            state = track_progress.load_state()
            step = state["completed_stages"][0]
            assert step["validation_errors"] == []


class TestBashToolHandling:
    """Test that Bash tool calls are routed to validation marking only."""

    def test_bash_routes_to_validation(self, temp_project):
        with patch.object(track_progress, 'get_state_file_path',
                          return_value=temp_project / ".artifacts" / "aet" / "state.json"):
            # Bash tool should not create new stages
            track_progress.update_pipeline_state(
                "Bash",
                {"command": "echo hello"},
                "hello"
            )
            state = track_progress.load_state()
            assert len(state["completed_stages"]) == 0

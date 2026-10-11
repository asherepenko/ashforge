#!/usr/bin/env python3
"""
Tests for track-progress.py hook.
Tests artifact detection, stage updates, validation marking, timing data.
"""

import json
import io
import sys
import tempfile
import shutil
import subprocess
import time
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent

# Import the module
sys.path.insert(0, str(PROJECT_ROOT / "hooks"))
from importlib import import_module
track_progress = import_module("track-progress")


def test_unavailable_lock_backend_leaves_authoritative_state_unchanged(temp_project, monkeypatch):
    state_path = temp_project / ".artifacts" / "aet" / "state.json"
    before = state_path.read_bytes()
    monkeypatch.setattr(track_progress, "fcntl", None)
    monkeypatch.setattr(track_progress, "get_state_file_path", lambda: state_path)
    track_progress.update_pipeline_state("Write", {
        "file_path": ".artifacts/aet/handoffs/test-feature/module-setup.md",
        "content": "# Report\ncontent\n"
    }, "")
    assert state_path.read_bytes() == before


@pytest.mark.skipif(track_progress.fcntl is None, reason="optional hook cache needs a POSIX lock backend")
def test_concurrent_hook_processes_retain_both_handoffs(temp_project):
    """Exercise the real update transaction with overlapping process reads."""
    marker = temp_project / "first-loaded"
    worker = r'''
import importlib.util, json, pathlib, sys, time
spec = importlib.util.spec_from_file_location("progress", sys.argv[1])
progress = importlib.util.module_from_spec(spec)
spec.loader.exec_module(progress)
if sys.argv[2] == "first":
    original_load = progress.load_state
    def delayed_load():
        state = original_load()
        pathlib.Path("first-loaded").touch()
        time.sleep(0.4)
        return state
    progress.load_state = delayed_load
artifact = sys.argv[3]
progress.update_pipeline_state("Write", {
    "file_path": ".artifacts/aet/handoffs/test-feature/" + artifact + ".md",
    "content": "# report\ncontent\n"
}, "")
'''
    command = [sys.executable, "-c", worker, str(PROJECT_ROOT / "hooks" / "track-progress.py")]
    first = subprocess.Popen(command + ["first", "module-setup"], cwd=temp_project,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 5
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert marker.exists(), "first hook did not reach its state read"
        second = subprocess.run(command + ["second", "implementation-report"],
                                cwd=temp_project, capture_output=True, text=True, timeout=5)
        first_output = first.communicate(timeout=5)
        assert first.returncode == 0, first_output
        assert second.returncode == 0, second.stderr
        state = json.loads((temp_project / ".artifacts" / "aet" / "state.json").read_text())
        assert {stage["agent"] for stage in state["completed_stages"]} == {
            "gradle-build-engineer", "android-developer"
        }
        assert set(state["artifacts"]) == {"module-setup", "implementation-report"}
    finally:
        if first.poll() is None:
            first.kill()
            first.communicate()


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

    def test_main_passes_tool_response_to_validation(self, temp_project):
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

        payload = {
            "tool_name": "exec_command",
            "tool_input": {
                "cmd": "python3 hooks/validate-handoff.py .artifacts/aet/handoffs/test-feature/2026-03-01-100000-architecture-blueprint.md"
            },
            "tool_response": "validation failed\n  - Missing section: Decisions"
        }

        with patch.object(track_progress, 'get_state_file_path', return_value=state_path):
            with patch.object(sys, 'stdin', io.StringIO(json.dumps(payload))):
                with pytest.raises(SystemExit) as exc:
                    track_progress.main()

        assert exc.value.code == 0
        updated = json.loads(state_path.read_text())
        assert updated["completed_stages"][0]["validation_passed"] is False
        assert updated["completed_stages"][0]["validation_errors"] == ["Missing section: Decisions"]

    def test_main_falls_back_to_tool_output(self, temp_project):
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

        payload = {
            "tool_name": "exec_command",
            "tool_input": {
                "cmd": "python3 hooks/validate-handoff.py .artifacts/aet/handoffs/test-feature/2026-03-01-100000-architecture-blueprint.md"
            },
            "tool_output": "validation failed\n  - Missing section: Risks"
        }

        with patch.object(track_progress, 'get_state_file_path', return_value=state_path):
            with patch.object(sys, 'stdin', io.StringIO(json.dumps(payload))):
                with pytest.raises(SystemExit) as exc:
                    track_progress.main()

        assert exc.value.code == 0
        updated = json.loads(state_path.read_text())
        assert updated["completed_stages"][0]["validation_passed"] is False
        assert updated["completed_stages"][0]["validation_errors"] == ["Missing section: Risks"]

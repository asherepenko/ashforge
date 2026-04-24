#!/usr/bin/env python3
"""
Tests for session-start.py hook.
Tests YAML settings parsing, interrupted pipeline detection, state file loading.
"""

import json
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch
from io import StringIO

import pytest

PROJECT_ROOT = Path(__file__).parent.parent

sys.path.insert(0, str(PROJECT_ROOT / "hooks"))
from importlib import import_module
session_start = import_module("session-start")


class TestParseYamlFrontmatter:
    """Test the simple YAML frontmatter parser."""

    def test_basic_key_value(self):
        content = """---
di_framework: hilt
state_management: stateflow
---

# Rest of file
"""
        result = session_start.parse_yaml_frontmatter(content)
        assert result["di_framework"] == "hilt"
        assert result["state_management"] == "stateflow"

    def test_empty_list(self):
        content = """---
skip_stages: []
---
"""
        result = session_start.parse_yaml_frontmatter(content)
        assert result["skip_stages"] == []

    def test_list_values(self):
        content = """---
skip_stages: [architecture, testing]
---
"""
        result = session_start.parse_yaml_frontmatter(content)
        assert result["skip_stages"] == ["architecture", "testing"]

    def test_quoted_values(self):
        content = """---
di_framework: "hilt"
state_management: 'stateflow'
---
"""
        result = session_start.parse_yaml_frontmatter(content)
        assert result["di_framework"] == "hilt"
        assert result["state_management"] == "stateflow"

    def test_comment_stripping(self):
        content = """---
di_framework: hilt # Google's recommended
---
"""
        result = session_start.parse_yaml_frontmatter(content)
        assert result["di_framework"] == "hilt"

    def test_no_frontmatter(self):
        content = "# Just a markdown file\n\nSome content."
        result = session_start.parse_yaml_frontmatter(content)
        assert result == {}

    def test_empty_content(self):
        result = session_start.parse_yaml_frontmatter("")
        assert result == {}

    def test_numeric_values(self):
        content = """---
cold_start_target_ms: 300
memory_baseline_mb: 150
test_coverage_target: 80
---
"""
        result = session_start.parse_yaml_frontmatter(content)
        assert result["cold_start_target_ms"] == "300"
        assert result["memory_baseline_mb"] == "150"
        assert result["test_coverage_target"] == "80"


class TestCheckInterruptedPipeline:
    """Test interrupted pipeline detection."""

    def test_detects_in_progress_pipeline(self, capsys):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            aet_dir = temp_path / ".artifacts" / "aet"
            aet_dir.mkdir(parents=True)

            state = {
                "pipeline_type": "feature-build",
                "feature_name": "Social Feed",
                "status": "in_progress",
                "current_stage": "android-developer",
                "completed_stages": [
                    {"agent": "android-architect"},
                    {"agent": "gradle-build-engineer"}
                ],
                "run_timestamp": "2026-03-01-100000"
            }
            (aet_dir / "state.json").write_text(json.dumps(state))

            with patch.object(Path, 'cwd', return_value=temp_path):
                session_start.check_interrupted_pipeline()

            captured = capsys.readouterr()
            assert "Interrupted pipeline detected" in captured.out
            assert "feature-build" in captured.out
            assert "Social Feed" in captured.out
            assert "2/5" in captured.out

    def test_ignores_completed_pipeline(self, capsys):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            aet_dir = temp_path / ".artifacts" / "aet"
            aet_dir.mkdir(parents=True)

            state = {
                "pipeline_type": "feature-build",
                "feature_name": "Done Feature",
                "status": "completed",
                "current_stage": None,
                "completed_stages": []
            }
            (aet_dir / "state.json").write_text(json.dumps(state))

            with patch.object(Path, 'cwd', return_value=temp_path):
                session_start.check_interrupted_pipeline()

            captured = capsys.readouterr()
            assert "Interrupted" not in captured.out

    def test_no_state_file(self, capsys):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(Path, 'cwd', return_value=Path(temp_dir)):
                session_start.check_interrupted_pipeline()

            captured = capsys.readouterr()
            assert captured.out == ""


class TestCheckSettings:
    """Test settings file loading."""

    def test_loads_settings_file(self, capsys):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            settings_content = """---
di_framework: hilt
state_management: stateflow
skip_stages: []
cold_start_target_ms: 300
---

# Project Settings
"""
            (temp_path / "android-expert-toolkit.local.md").write_text(settings_content)

            with patch.object(Path, 'cwd', return_value=temp_path):
                session_start.check_settings()

            captured = capsys.readouterr()
            assert "Settings loaded" in captured.out
            assert "hilt" in captured.out.lower() or "Hilt" in captured.out

    def test_no_settings_file(self, capsys):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(Path, 'cwd', return_value=Path(temp_dir)):
                session_start.check_settings()

            captured = capsys.readouterr()
            assert captured.out == ""

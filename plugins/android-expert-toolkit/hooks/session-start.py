#!/usr/bin/env python3
"""
SessionStart hook for Android Expert Toolkit.
Loads project settings and detects interrupted pipelines.
"""

import json
import subprocess
import sys
from pathlib import Path


def parse_yaml_frontmatter(content: str) -> dict:
    """Parse simple YAML frontmatter (key: value pairs) without external deps."""
    settings = {}
    lines = content.split('\n')

    in_frontmatter = False
    for line in lines:
        stripped = line.strip()
        if stripped == '---':
            if in_frontmatter:
                break
            in_frontmatter = True
            continue
        if in_frontmatter and ':' in stripped:
            key, _, value = stripped.partition(':')
            key = key.strip()
            value = value.strip()
            if value == '[]':
                settings[key] = []
            elif value.startswith('[') and value.endswith(']'):
                items = [item.strip().strip('"').strip("'") for item in value[1:-1].split(',') if item.strip()]
                settings[key] = items
            else:
                if '#' in value:
                    value = value[:value.index('#')].strip()
                value = value.strip('"').strip("'")
                settings[key] = value

    return settings


def check_settings():
    """Check for project-local settings file."""
    cwd = Path.cwd()
    settings_file = cwd / "android-expert-toolkit.local.md"

    if not settings_file.exists():
        return

    try:
        content = settings_file.read_text(encoding='utf-8')
        settings = parse_yaml_frontmatter(content)

        if not settings:
            return

        print("  Settings loaded from android-expert-toolkit.local.md:")

        display_keys = {
            'di_framework': 'DI Framework',
            'state_management': 'State Management',
            'testing_strategy': 'Testing Strategy',
            'feature_module_prefix': 'Feature Module Prefix',
            'cold_start_target_ms': 'Cold Start Target',
            'memory_baseline_mb': 'Memory Baseline',
            'test_coverage_target': 'Test Coverage Target',
            'skip_stages': 'Skip Stages',
        }

        for key, label in display_keys.items():
            if key in settings:
                value = settings[key]
                if isinstance(value, list):
                    value = ', '.join(value) if value else 'none'
                if key == 'cold_start_target_ms':
                    value = f"{value}ms"
                elif key == 'memory_baseline_mb':
                    value = f"{value}MB"
                elif key == 'test_coverage_target':
                    value = f"{value}%"
                print(f"    {label}: {value}")
    except Exception as e:
        print(f"  Warning: Could not load settings: {e}", file=sys.stderr)


def check_git_state():
    """Warn if git has uncommitted changes."""
    cwd = Path.cwd()
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, check=False, cwd=cwd
        )
        if result.returncode == 0 and result.stdout.strip():
            changed_count = len(result.stdout.strip().split('\n'))
            print(f"  Warning: {changed_count} uncommitted git change(s) detected")
            print(f"    Consider committing or stashing before starting a pipeline")
    except FileNotFoundError:
        pass  # git not available


def check_project_structure():
    """Validate minimal Android project structure."""
    cwd = Path.cwd()
    has_build = (cwd / "build.gradle.kts").exists() or (cwd / "build.gradle").exists()
    has_settings = (cwd / "settings.gradle.kts").exists() or (cwd / "settings.gradle").exists()

    if not has_build and not has_settings:
        print("  Warning: No build.gradle.kts or settings.gradle.kts found")
        print("    Pipeline commands require an Android project structure")


def check_artifact_existence():
    """Check if artifacts referenced in aet/state.json still exist on disk."""
    cwd = Path.cwd()
    state_file = cwd / ".artifacts" / "aet" / "state.json"

    if not state_file.exists():
        return

    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)

        missing_artifacts = []
        for artifact_name, artifact_path in state.get("artifacts", {}).items():
            full_path = Path(artifact_path) if Path(artifact_path).is_absolute() else cwd / artifact_path
            if not full_path.exists():
                missing_artifacts.append(artifact_name)

        if missing_artifacts:
            print(f"  Warning: {len(missing_artifacts)} artifact(s) referenced in pipeline state are missing from disk:")
            for name in missing_artifacts:
                print(f"    - {name}")
            print(f"    Pipeline may need to re-run affected stages")
    except Exception:
        pass


def check_interrupted_pipeline():
    """Check for interrupted pipeline state."""
    cwd = Path.cwd()
    state_file = cwd / ".artifacts" / "aet" / "state.json"

    if not state_file.exists():
        return

    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)

        status = state.get("status", "unknown")
        if status == "completed":
            return

        pipeline_type = state.get("pipeline_type", "unknown")
        feature_name = state.get("feature_name", "")
        current_stage = state.get("current_stage", "unknown")
        completed = len(state.get("completed_stages", []))
        stage_counts = {
            "feature-build": 5,
            "architecture-review": 1,
            "migration": 3,
            "ui-redesign": 3,
            "build-optimization": 2,
            "test": 1,
            "code-review": 1
        }
        total = stage_counts.get(pipeline_type, "?")

        feature_str = f' "{feature_name}"' if feature_name else ''
        run_timestamp = state.get("run_timestamp", "")
        print(f"  Warning: Interrupted pipeline detected!")
        print(f"    Type: {pipeline_type}{feature_str}")
        if run_timestamp:
            print(f"    Run: {run_timestamp}")
        print(f"    Progress: {completed}/{total} stages completed")
        print(f"    Last stage: {current_stage}")
        print(f"    Resume with: /aet-pipeline resume")
    except Exception as e:
        print(f"  Warning: Could not read pipeline state: {e}", file=sys.stderr)


def main():
    print("Android Expert Toolkit loaded")
    check_settings()
    check_git_state()
    check_project_structure()
    check_artifact_existence()
    check_interrupted_pipeline()
    sys.exit(0)


if __name__ == "__main__":
    main()

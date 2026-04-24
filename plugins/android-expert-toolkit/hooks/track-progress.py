#!/usr/bin/env python3
"""
Progress tracking hook for Android Expert Toolkit pipelines.
Post Tool Use hook that monitors handoff artifact creation and updates pipeline state.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Map artifact type (no extension) to agent
ARTIFACT_TO_AGENT: Dict[str, str] = {
    "architecture-blueprint": "android-architect",
    "module-setup": "gradle-build-engineer",
    "implementation-report": "android-developer",
    "ui-report": "compose-expert",
    "test-report": "android-testing-specialist"
}

# Pipeline sequences (for determining next step)
PIPELINE_SEQUENCES: Dict[str, list] = {
    "feature-build": [
        "android-architect",
        "gradle-build-engineer",  # Can be parallel with android-developer
        "android-developer",
        "compose-expert",
        "android-testing-specialist"
    ],
    "architecture-review": [
        "android-architect"
    ],
    "migration": [
        "android-architect",
        "android-developer",
        "android-testing-specialist"
    ],
    "ui-redesign": [
        "android-architect",  # Optional
        "compose-expert",
        "android-testing-specialist"  # Optional
    ],
    "build-optimization": [
        "android-architect",
        "gradle-build-engineer"
    ],
    "test": [
        "android-testing-specialist"
    ],
    "code-review": [
        "android-architect"  # Review mode, not design mode
    ]
}


def get_state_file_path() -> Path:
    """Get the path to the pipeline state file."""
    cwd = Path.cwd()

    # Look for .artifacts/aet directory (walk up to find it)
    current = cwd
    while current != current.parent:
        aet_dir = current / ".artifacts" / "aet"
        if aet_dir.exists() and aet_dir.is_dir():
            return aet_dir / "state.json"
        current = current.parent

    # Default to current directory
    return cwd / ".artifacts" / "aet" / "state.json"


def load_state() -> Optional[Dict[str, Any]]:
    """Load existing pipeline state if it exists."""
    state_file = get_state_file_path()
    if not state_file.exists():
        return None

    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load pipeline state: {e}", file=sys.stderr)
        return None


def save_state(state: Dict[str, Any]):
    """Save pipeline state to file."""
    state_file = get_state_file_path()

    # Ensure .artifacts/aet directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save pipeline state: {e}", file=sys.stderr)


def detect_pipeline_type(state: Optional[Dict[str, Any]]) -> Optional[str]:
    """Try to detect pipeline type from existing state or context."""
    if state and "pipeline_type" in state:
        return state["pipeline_type"]

    return None


def mark_validation_passed(tool_input: Dict[str, Any], tool_output: str):
    """Mark artifact as validated when validate-handoff.py succeeds, or record errors on failure."""
    command = tool_input.get("command", "")
    if "validate-handoff.py" not in command:
        return

    validation_failed = "validation failed" in tool_output

    # Extract the artifact path from the command arguments
    parts = command.split()
    artifact_path = None
    for i, part in enumerate(parts):
        if part.endswith("validate-handoff.py") and i + 1 < len(parts):
            artifact_path = parts[i + 1]
            break

    if not artifact_path:
        return

    state = load_state()
    if not state:
        return

    # Find the matching completed stage by artifact path
    normalized_path = artifact_path.replace("\\", "/")
    for step in state.get("completed_stages", []):
        step_artifact = step.get("artifact", "").replace("\\", "/")
        if step_artifact and (
            normalized_path.endswith(Path(step_artifact).name)
            or step_artifact.endswith(Path(normalized_path).name)
        ):
            if validation_failed:
                errors = [
                    line.strip().lstrip("- ")
                    for line in tool_output.split('\n')
                    if line.strip().startswith("- ") or line.strip().startswith("  -")
                ]
                step["validation_passed"] = False
                step["validation_errors"] = errors if errors else [tool_output.strip()]
                save_state(state)
                print(f"✗ Validation failed for {step['agent']}")
            else:
                step["validation_passed"] = True
                step["validation_errors"] = []
                save_state(state)
                print(f"✓ Validation passed for {step['agent']}")
            return


def update_pipeline_state(tool_name: str, tool_input: Dict[str, Any], tool_output: str):
    """Update pipeline state after a tool use."""

    # Track Bash calls for validation results
    if tool_name == "Bash":
        mark_validation_passed(tool_input, tool_output)
        return

    # Only track Write tool for handoff artifacts
    if tool_name != "Write":
        return

    file_path = tool_input.get("file_path", "")

    # Only track writes to .artifacts/aet/handoffs/
    normalized = file_path.replace("\\", "/")
    if ".artifacts/aet/handoffs/" not in normalized:
        return

    # Detect artifact type by suffix: filename ends with -{artifact_type}.md
    filename = Path(file_path).name
    artifact_type = None
    agent = None
    for known_type, known_agent in ARTIFACT_TO_AGENT.items():
        if filename.endswith(f"-{known_type}.md") or filename == f"{known_type}.md":
            artifact_type = known_type
            agent = known_agent
            break

    if not artifact_type:
        return

    # Extract feature_slug from path: .artifacts/aet/handoffs/{feature_slug}/filename
    parts = Path(normalized.lstrip("/")).parts
    try:
        handoffs_idx = next(i for i, p in enumerate(parts) if p == "handoffs")
        feature_slug = parts[handoffs_idx + 1] if handoffs_idx + 1 < len(parts) else "unknown"
    except StopIteration:
        feature_slug = "unknown"

    # Load existing state or create new one
    state = load_state()

    if state is None:
        # Initialize new pipeline state
        state = {
            "pipeline_type": None,
            "feature_name": None,
            "started_at": datetime.utcnow().isoformat() + "Z",
            "completed_at": None,
            "status": "in_progress",
            "current_stage": None,
            "completed_stages": [],
            "artifacts": {}
        }

    # Detect or update pipeline type
    pipeline_type = detect_pipeline_type(state)
    if pipeline_type:
        state["pipeline_type"] = pipeline_type

    # Check if this step already exists
    existing_step = None
    for step in state["completed_stages"]:
        if step["agent"] == agent:
            existing_step = step
            break

    # Count artifact lines
    content = tool_input.get("content", "")
    artifact_size_lines = len(content.split('\n')) if content else 0

    now = datetime.utcnow().isoformat() + "Z"

    if existing_step:
        existing_step["completed_at"] = now
        existing_step["artifact"] = file_path
        existing_step["artifact_size_lines"] = artifact_size_lines
        existing_step["validation_passed"] = False
        existing_step["validation_errors"] = []
    else:
        new_step = {
            "agent": agent,
            "artifact": file_path,
            "started_at": state.get("_stage_started_at", now),
            "completed_at": now,
            "artifact_size_lines": artifact_size_lines,
            "validation_passed": False,
            "validation_errors": []
        }
        state["completed_stages"].append(new_step)
        state["current_stage"] = agent

    # Update artifacts map (key is artifact type without extension)
    state["artifacts"][artifact_type] = file_path

    # Save updated state
    save_state(state)

    print(f"✓ Pipeline state updated: {agent} completed ({filename})")


def main():
    """Main entry point for PostToolUse hook."""
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    try:
        update_pipeline_state(tool_name, tool_input, "")
    except Exception as e:
        print(f"Warning: Progress tracking error: {e}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()

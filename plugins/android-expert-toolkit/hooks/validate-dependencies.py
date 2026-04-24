#!/usr/bin/env python3
"""
Validation hook for Android Expert Toolkit agent prerequisites.
Validates that agent prerequisites are met before dispatching agents in pipelines.
"""

import json
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Optional


# Agent dependencies configuration (artifact type names, not paths)
AGENT_DEPENDENCIES: Dict[str, Dict] = {
    "android-architect": {
        "required_files": [],
        "required_artifacts": [],
        "blocking_agents": []
    },
    "android-developer": {
        "required_files": ["build.gradle.kts"],
        "required_artifacts": ["architecture-blueprint"],
        "blocking_agents": ["android-architect"]
    },
    "android-testing-specialist": {
        "required_files": ["build.gradle.kts"],
        "required_artifacts": ["implementation-report"],
        "blocking_agents": ["android-developer"]
    },
    "compose-expert": {
        "required_files": ["build.gradle.kts"],
        "required_artifacts": [],
        "required_artifacts_or": ["architecture-blueprint", "implementation-report"],
        "blocking_agents": []  # Flexible: either android-architect OR android-developer
    },
    "gradle-build-engineer": {
        "required_files": ["settings.gradle.kts"],
        "required_artifacts": ["architecture-blueprint"],
        "blocking_agents": ["android-architect"]
    }
}

# Pipeline-specific dependency overrides
# Some pipelines relax the default agent dependencies
PIPELINE_DEPENDENCY_OVERRIDES: Dict[str, Dict[str, Dict]] = {
    "test": {
        "android-testing-specialist": {
            "required_files": ["build.gradle.kts"],
            "required_artifacts": [],
            "blocking_agents": []
        }
    },
    "code-review": {
        "android-architect": {
            "required_files": [],
            "required_artifacts": [],
            "blocking_agents": []
        }
    }
}

# Map agent name to the artifact type it produces
AGENT_TO_ARTIFACT: Dict[str, str] = {
    "android-architect": "architecture-blueprint",
    "android-developer": "implementation-report",
    "compose-expert": "ui-report",
    "gradle-build-engineer": "module-setup",
    "android-testing-specialist": "test-report"
}


def load_pipeline_state(project_root: Optional[Path] = None) -> Optional[Dict]:
    """Load pipeline state from .artifacts/aet/state.json."""
    base = project_root or Path.cwd()
    state_file = base / ".artifacts" / "aet" / "state.json"
    if not state_file.exists():
        return None
    try:
        with open(state_file, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def find_artifact_path(artifact_type: str, project_root: Optional[Path] = None, state: Optional[Dict] = None) -> Optional[Path]:
    """Find artifact file path: check state first, then glob fallback."""
    base = project_root or Path.cwd()

    # 1. Check pipeline state artifacts map
    if state and "artifacts" in state:
        path_str = state["artifacts"].get(artifact_type)
        if path_str:
            candidate = base / path_str if not Path(path_str).is_absolute() else Path(path_str)
            if candidate.exists():
                return candidate

    # 2. Glob fallback: find any *-{artifact_type}.md under .artifacts/aet/handoffs/
    handoffs_dir = base / ".artifacts" / "aet" / "handoffs"
    if handoffs_dir.exists():
        matches = sorted(handoffs_dir.glob(f"**/*-{artifact_type}.md"))
        # Also match exact name without timestamp prefix
        matches += sorted(handoffs_dir.glob(f"**/{artifact_type}.md"))
        if matches:
            return matches[-1]  # most recently modified (sorted by name, timestamp prefix ensures order)

    return None


def check_file_exists(filepath: str, project_root: Optional[Path] = None) -> bool:
    """Check if a required file exists."""
    if project_root:
        full_path = project_root / filepath
        return full_path.exists()
    return Path(filepath).exists()


def validate_handoff(handoff_path, project_root: Optional[Path] = None) -> tuple[bool, Optional[str]]:
    """
    Validate a handoff artifact by calling validate-handoff.py.
    Accepts a Path object or string. project_root is ignored when a Path is passed directly.
    Returns (is_valid, error_message).
    """
    # Accept Path directly or resolve via project_root
    if isinstance(handoff_path, Path):
        full_path = handoff_path
    elif project_root:
        full_path = project_root / handoff_path
    else:
        full_path = Path(handoff_path)

    if not full_path.exists():
        return False, f"File not found: {handoff_path}"

    # Get the directory of this script to locate validate-handoff.py
    script_dir = Path(__file__).parent
    validate_handoff_script = script_dir / "validate-handoff.py"

    if not validate_handoff_script.exists():
        return False, f"validate-handoff.py not found at {validate_handoff_script}"

    try:
        result = subprocess.run(
            ["python3", str(validate_handoff_script), str(full_path)],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            return True, None
        else:
            return False, result.stderr.strip()
    except Exception as e:
        return False, f"Error validating handoff: {e}"


def check_blocking_agents_complete(blocking_agents: List[str], project_root: Optional[Path] = None, state: Optional[Dict] = None) -> tuple[bool, List[str]]:
    """
    Check if blocking agents have completed by verifying their artifact files exist.
    Returns (all_complete, incomplete_agents).
    """
    incomplete = []

    for agent in blocking_agents:
        artifact_type = AGENT_TO_ARTIFACT.get(agent)
        if artifact_type:
            path = find_artifact_path(artifact_type, project_root, state)
            if not path:
                incomplete.append(agent)

    return len(incomplete) == 0, incomplete


def validate_agent_dependencies(agent_name: str, project_root: Optional[Path] = None) -> tuple[bool, List[str]]:
    """
    Validate all prerequisites for an agent.
    Returns (is_valid, error_messages).
    """
    if agent_name not in AGENT_DEPENDENCIES:
        return False, [f"Unknown agent: {agent_name}. Expected one of: {', '.join(AGENT_DEPENDENCIES.keys())}"]

    state = load_pipeline_state(project_root)

    # Check for pipeline-specific dependency overrides
    pipeline_type = state.get("pipeline_type") if state else None
    if pipeline_type and pipeline_type in PIPELINE_DEPENDENCY_OVERRIDES:
        overrides = PIPELINE_DEPENDENCY_OVERRIDES[pipeline_type]
        if agent_name in overrides:
            deps = overrides[agent_name]
        else:
            deps = AGENT_DEPENDENCIES[agent_name]
    else:
        deps = AGENT_DEPENDENCIES[agent_name]
    errors = []

    # Check required files
    for filepath in deps.get("required_files", []):
        if not check_file_exists(filepath, project_root):
            errors.append(f"Missing required file: {filepath}")

    # Check required artifacts (standard case)
    for artifact_type in deps.get("required_artifacts", []):
        path = find_artifact_path(artifact_type, project_root, state)
        if not path:
            errors.append(f"Handoff validation failed: File not found for artifact type: {artifact_type}")
        else:
            is_valid, error_msg = validate_handoff(path)
            if not is_valid:
                errors.append(f"Handoff validation failed: {error_msg}")

    # Check required_artifacts_or (special case for compose-expert)
    if "required_artifacts_or" in deps:
        artifacts_or = deps["required_artifacts_or"]
        at_least_one_found = False

        for artifact_type in artifacts_or:
            path = find_artifact_path(artifact_type, project_root, state)
            if path:
                is_valid, error_msg = validate_handoff(path)
                if is_valid:
                    at_least_one_found = True
                    break

        if not at_least_one_found:
            errors.append(f"Missing at least one required handoff: {' OR '.join(artifacts_or)}")

    # Check blocking agents
    blocking_agents = deps.get("blocking_agents", [])
    if blocking_agents:
        all_complete, incomplete = check_blocking_agents_complete(blocking_agents, project_root, state)
        if not all_complete:
            errors.append(f"Blocked by incomplete agents: {', '.join(incomplete)}")

    is_valid = len(errors) == 0
    return is_valid, errors


def main():
    """Main entry point for the validation hook."""
    if len(sys.argv) < 2:
        print("Usage: validate-dependencies.py <agent-name> [project-root]", file=sys.stderr)
        print(f"Available agents: {', '.join(AGENT_DEPENDENCIES.keys())}", file=sys.stderr)
        sys.exit(1)

    agent_name = sys.argv[1]
    project_root = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    is_valid, errors = validate_agent_dependencies(agent_name, project_root)

    if is_valid:
        print(f"✓ All prerequisites met for {agent_name}")
        sys.exit(0)
    else:
        print(f"✗ Prerequisites check failed for {agent_name}", file=sys.stderr)
        print(f"Missing prerequisites:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

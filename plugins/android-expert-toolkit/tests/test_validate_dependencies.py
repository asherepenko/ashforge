#!/usr/bin/env python3
"""
Integration tests for validate-dependencies.py hook.
"""

import json
import subprocess
import sys
from pathlib import Path
import tempfile
import shutil

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent
VALIDATE_SCRIPT = PROJECT_ROOT / "hooks" / "validate-dependencies.py"


def create_mock_project(with_blueprint: bool = False, feature_slug: str = "test-feature") -> Path:
    """Create a temporary mock Android project structure."""
    temp_dir = Path(tempfile.mkdtemp())

    # Create Android project marker files
    (temp_dir / "build.gradle.kts").write_text("// Mock Android build file")
    (temp_dir / "settings.gradle.kts").write_text("// Mock settings file")

    # Create .artifacts/aet/handoffs/{feature_slug} directory
    handoffs_dir = temp_dir / ".artifacts" / "aet" / "handoffs" / feature_slug
    handoffs_dir.mkdir(parents=True, exist_ok=True)

    # Create pipeline state
    state_dir = temp_dir / ".artifacts" / "aet"
    state_dir.mkdir(parents=True, exist_ok=True)

    run_timestamp = "2026-02-18-000000"
    state = {
        "pipeline_type": "feature-build",
        "feature_name": "Test Feature",
        "feature_slug": feature_slug,
        "run_timestamp": run_timestamp,
        "started_at": "2026-02-18T00:00:00Z",
        "status": "in_progress",
        "current_stage": "android-architect",
        "completed_stages": [],
        "artifacts": {}
    }

    if with_blueprint:
        blueprint_filename = f"{run_timestamp}-architecture-blueprint.md"
        blueprint_path = handoffs_dir / blueprint_filename
        blueprint_path.write_text("""# Architecture Blueprint

## Pipeline Context

**Original Prompt:** Build a test feature

**Business Purpose:** Test feature for validation.

**UX Intent:** Simple list screen with detail view.

## Summary

Test blueprint for the test feature.
Uses MVVM architecture with StateFlow.
Hilt for dependency injection throughout.

## Decisions

### Decision 1: Use StateFlow
Context: Need reactive state management.
Decision: StateFlow for modern Kotlin patterns.
Rationale: Coroutine-integrated, lifecycle-aware.

## Artifacts Created

feature/test/api/src/main/kotlin/TestApi.kt
feature/test/impl/src/main/kotlin/TestImpl.kt
feature/test/impl/src/main/kotlin/TestRepo.kt

## Next Steps

- gradle-build-engineer: Create feature modules with convention plugins
- android-developer: Implement data layer with Room
- compose-expert: Build UI screens with Material 3

## Constraints

- Must use Hilt for DI
- Offline-first pattern required
- StateFlow for all state management
""")
        relative_path = f".artifacts/aet/handoffs/{feature_slug}/{blueprint_filename}"
        state["artifacts"]["architecture-blueprint"] = relative_path
        state["completed_stages"].append({
            "agent": "android-architect",
            "artifact": relative_path,
            "completed_at": "2026-02-18T00:01:00Z",
            "validation_passed": True
        })

    (state_dir / "state.json").write_text(json.dumps(state, indent=2))

    return temp_dir


def run_validation(agent_name: str, project_root: Path) -> tuple[int, str, str]:
    """Run dependency validation. Returns (exit_code, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), agent_name, str(project_root)],
        capture_output=True,
        text=True
    )

    return result.returncode, result.stdout, result.stderr


def test_android_architect_no_dependencies():
    """Test that android-architect has no dependencies and always passes."""
    project_dir = create_mock_project(with_blueprint=False)

    try:
        exit_code, stdout, stderr = run_validation("android-architect", project_dir)

        assert exit_code == 0, f"android-architect should pass (no deps). stderr: {stderr}"
        assert "prerequisites met" in stdout.lower(), "Should report success"
    finally:
        shutil.rmtree(project_dir)


def test_android_developer_needs_blueprint():
    """Test that android-developer requires architecture-blueprint artifact."""
    # Without blueprint
    project_dir = create_mock_project(with_blueprint=False)

    try:
        exit_code, stdout, stderr = run_validation("android-developer", project_dir)

        assert exit_code == 1, "android-developer should fail without blueprint"
        assert "architecture-blueprint" in stderr.lower(), "Should mention missing blueprint"
    finally:
        shutil.rmtree(project_dir)


def test_android_developer_with_blueprint():
    """Test that android-developer passes when blueprint exists."""
    # With blueprint
    project_dir = create_mock_project(with_blueprint=True)

    try:
        exit_code, stdout, stderr = run_validation("android-developer", project_dir)

        assert exit_code == 0, f"android-developer should pass with blueprint. stderr: {stderr}"
        assert "prerequisites met" in stdout.lower(), "Should report success"
    finally:
        shutil.rmtree(project_dir)


def test_compose_expert_needs_blueprint_or_implementation():
    """Test that compose-expert requires at least ONE of blueprint OR implementation-report."""
    # With neither blueprint nor implementation-report
    project_dir = create_mock_project(with_blueprint=False)

    try:
        exit_code, stdout, stderr = run_validation("compose-expert", project_dir)

        assert exit_code == 1, "compose-expert should fail without any handoffs"
        assert "handoff" in stderr.lower(), "Should mention missing handoff"

        # Now test with blueprint (should pass)
        run_timestamp = "2026-02-18-000000"
        feature_slug = "test-feature"
        blueprint_dir = project_dir / ".artifacts" / "aet" / "handoffs" / feature_slug
        blueprint_dir.mkdir(parents=True, exist_ok=True)
        blueprint_filename = f"{run_timestamp}-architecture-blueprint.md"
        (blueprint_dir / blueprint_filename).write_text("""# Architecture Blueprint

## Pipeline Context

**Original Prompt:** Build a test feature

**Business Purpose:** Test feature for compose-expert validation.

**UX Intent:** Simple list screen with detail view.

## Summary

Test blueprint for compose-expert validation.
Uses MVVM architecture with StateFlow.
Hilt for dependency injection throughout.

## Decisions

### Decision 1: Use StateFlow
Context: Need reactive state management.
Decision: StateFlow for modern Kotlin patterns.
Rationale: Coroutine-integrated, lifecycle-aware.

## Artifacts Created

feature/test/api/src/main/kotlin/TestApi.kt
feature/test/impl/src/main/kotlin/TestImpl.kt
feature/test/impl/src/main/kotlin/TestRepo.kt

## Next Steps

- gradle-build-engineer: Create feature modules with convention plugins
- android-developer: Implement data layer with Room
- compose-expert: Build UI screens with Material 3

## Constraints

- Must use Hilt for DI
- Offline-first pattern required
- StateFlow for all state management
""")
        # Update pipeline state to reference the new artifact
        state_file = project_dir / ".artifacts" / "aet" / "state.json"
        state = json.loads(state_file.read_text())
        state["artifacts"]["architecture-blueprint"] = f".artifacts/aet/handoffs/{feature_slug}/{blueprint_filename}"
        state_file.write_text(json.dumps(state, indent=2))

        exit_code2, stdout2, stderr2 = run_validation("compose-expert", project_dir)
        assert exit_code2 == 0, f"compose-expert should pass with blueprint. stderr: {stderr2}"

    finally:
        shutil.rmtree(project_dir)


def test_unknown_agent():
    """Test that unknown agent names are handled."""
    project_dir = create_mock_project(with_blueprint=False)

    try:
        exit_code, stdout, stderr = run_validation("unknown-agent", project_dir)

        assert exit_code == 1, "Unknown agent should fail"
        assert "unknown agent" in stderr.lower(), "Should report unknown agent"
    finally:
        shutil.rmtree(project_dir)


def test_nonexistent_project():
    """Test that nonexistent project directories are handled."""
    # Note: The script doesn't explicitly check if project_root exists,
    # it just checks for files within it. So android-architect (no deps) will pass even with nonexistent root.
    # android-developer will fail because required files don't exist.
    result = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), "android-developer", "/nonexistent/project"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 1, "Should fail when required files don't exist"
    assert "build.gradle.kts" in result.stderr.lower() or "missing" in result.stderr.lower()


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        ("android-architect (no dependencies)", test_android_architect_no_dependencies),
        ("android-developer needs blueprint", test_android_developer_needs_blueprint),
        ("android-developer with blueprint", test_android_developer_with_blueprint),
        ("compose-expert needs blueprint or implementation", test_compose_expert_needs_blueprint_or_implementation),
        ("Unknown agent", test_unknown_agent),
        ("Nonexistent project", test_nonexistent_project),
    ]

    passed = 0
    failed = 0

    print("Running validate-dependencies.py integration tests...\n")

    for name, test_func in tests:
        try:
            test_func()
            print(f"✓ {name}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {name}: Unexpected error: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())

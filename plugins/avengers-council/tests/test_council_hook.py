#!/usr/bin/env python3
"""
Integration tests for council-plan-hook.sh

Tests all 3 modes: off, prompt, auto
"""

import subprocess
import json
import os
from pathlib import Path

# Locate hook script
PROJECT_ROOT = Path(__file__).parent.parent
HOOK_SCRIPT = PROJECT_ROOT / "hooks" / "council-plan-hook.sh"


def run_hook(mode: str) -> tuple[int, dict]:
    """
    Run the hook with specified mode.
    Returns (exit_code, parsed_json_output).
    """
    env = os.environ.copy()
    env["AVENGERS_COUNCIL_ON_PLAN"] = mode

    result = subprocess.run(
        ["bash", str(HOOK_SCRIPT)],
        env=env,
        capture_output=True,
        text=True
    )

    # Parse JSON output (if any)
    output_json = {}
    if result.stdout.strip():
        try:
            output_json = json.loads(result.stdout)
        except json.JSONDecodeError:
            pass

    return result.returncode, output_json


def test_mode_off():
    """Test that 'off' mode does nothing."""
    exit_code, output = run_hook("off")

    assert exit_code == 0, "Hook should exit successfully"
    assert output == {}, "Hook should produce no output in off mode"

    print("✓ Mode 'off' produces no output")


def test_mode_prompt():
    """Test that 'prompt' mode suggests council review."""
    exit_code, output = run_hook("prompt")

    assert exit_code == 0, "Hook should exit successfully"
    assert "hookSpecificOutput" in output, "Should have hookSpecificOutput"
    assert "additionalContext" in output["hookSpecificOutput"], "Should have additionalContext"

    context = output["hookSpecificOutput"]["additionalContext"]
    assert "consider running" in context.lower(), "Should suggest (not require) review"
    assert "/avengers-council:plan-review" in context, "Should mention command"

    print("✓ Mode 'prompt' suggests council review")


def test_mode_auto():
    """Test that 'auto' mode blocks ExitPlanMode and requires council review."""
    exit_code, output = run_hook("auto")

    assert exit_code == 0, "Hook should exit successfully"

    # Verify decision field blocks the tool call
    assert "decision" in output, "Should have decision field"
    assert output["decision"] == "block", "Should block ExitPlanMode"
    assert "reason" in output, "Should have reason field"

    # Verify hookSpecificOutput still present
    assert "hookSpecificOutput" in output, "Should have hookSpecificOutput"
    assert "additionalContext" in output["hookSpecificOutput"], "Should have additionalContext"

    context = output["hookSpecificOutput"]["additionalContext"]
    assert "before proceeding" in context.lower(), "Should require (not suggest) review"
    assert "invoke" in context.lower() or "run" in context.lower(), "Should instruct Claude to run command"
    assert "/avengers-council:plan-review" in context, "Should mention command"
    assert "do not continue" in context.lower() or "wait" in context.lower(), "Should block until review complete"

    print("✓ Mode 'auto' blocks ExitPlanMode and requires council review")


def test_mode_unknown():
    """Test that unknown modes are handled gracefully."""
    exit_code, output = run_hook("invalid_mode")

    assert exit_code == 0, "Hook should not crash on unknown mode"
    assert output == {}, "Unknown mode should behave like 'off'"

    print("✓ Unknown mode handled gracefully")


def test_json_format_valid():
    """Test that JSON output is valid for both modes."""
    for mode in ["prompt", "auto"]:
        exit_code, output = run_hook(mode)

        # Verify JSON structure
        assert "hookSpecificOutput" in output, f"Mode '{mode}' missing hookSpecificOutput"
        assert "hookEventName" in output["hookSpecificOutput"], f"Mode '{mode}' missing hookEventName"
        assert "additionalContext" in output["hookSpecificOutput"], f"Mode '{mode}' missing additionalContext"

        # Verify hookEventName is correct
        assert output["hookSpecificOutput"]["hookEventName"] == "PreToolUse", \
            f"Mode '{mode}' has wrong hookEventName"

        # Verify additionalContext is a string
        assert isinstance(output["hookSpecificOutput"]["additionalContext"], str), \
            f"Mode '{mode}' additionalContext should be string"

    # Verify auto mode has decision field
    _, auto_output = run_hook("auto")
    assert auto_output.get("decision") == "block", "Auto mode should have decision: block"
    assert "reason" in auto_output, "Auto mode should have reason field"

    # Verify prompt mode does NOT have decision field
    _, prompt_output = run_hook("prompt")
    assert "decision" not in prompt_output, "Prompt mode should not block"

    print("✓ JSON format valid for prompt and auto modes")


def test_hook_executable():
    """Test that hook file is executable."""
    assert HOOK_SCRIPT.exists(), f"Hook script not found at {HOOK_SCRIPT}"

    # Check if executable
    is_executable = os.access(HOOK_SCRIPT, os.X_OK)
    assert is_executable, f"Hook script not executable: {HOOK_SCRIPT}"

    print("✓ Hook script exists and is executable")


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        ("Hook script exists and executable", test_hook_executable),
        ("Mode 'off' behavior", test_mode_off),
        ("Mode 'prompt' behavior", test_mode_prompt),
        ("Mode 'auto' behavior", test_mode_auto),
        ("Unknown mode handling", test_mode_unknown),
        ("JSON format validation", test_json_format_valid),
    ]

    passed = 0
    failed = 0

    print("Running council-plan-hook.sh integration tests...\n")

    for name, test_func in tests:
        try:
            test_func()
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
    import sys
    sys.exit(run_all_tests())

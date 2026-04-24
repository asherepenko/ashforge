#!/usr/bin/env python3
"""
Validation hook for Android Expert Toolkit handoff artifacts.
Validates that handoff artifacts contain required sections based on artifact type.
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple

# Required sections by artifact type
REQUIRED_SECTIONS: Dict[str, List[str]] = {
    "architecture-blueprint": [
        "Pipeline Context",
        "Summary",
        "Decisions",
        "Artifacts Created",
        "Next Steps",
        "Constraints"
    ],
    "module-setup": [
        "Pipeline Context",
        "Summary",
        "Modules Created",
        "Dependencies Added",
        "Next Steps"
    ],
    "implementation-report": [
        "Pipeline Context",
        "Summary",
        "Decisions",
        "Artifacts Created",
        "Next Steps",
        "Constraints"
    ],
    "ui-report": [
        "Pipeline Context",
        "Summary",
        "Screens Implemented",
        "Components Created",
        "Next Steps"
    ],
    "test-report": [
        "Pipeline Context",
        "Summary",
        "Test Doubles Created",
        "Tests Implemented",
        "Coverage",
        "Next Steps"
    ],
    "code-review-report": [
        "Summary",
        "Findings",
        "Severity Summary",
        "Recommendations",
        "Patterns Observed"
    ]
}


def extract_artifact_type(filename: str) -> str:
    """Extract artifact type from filename.

    Handles:
    - 'architecture-blueprint.md' -> 'architecture-blueprint'
    - '2026-02-18-143022-architecture-blueprint.md' -> 'architecture-blueprint' (timestamped)
    - 'architecture-blueprint-template.md' -> 'architecture-blueprint' (template)
    - 'architecture-blueprint-valid.md' -> 'architecture-blueprint' (test fixture)
    - 'architecture-blueprint-invalid.md' -> 'architecture-blueprint' (test fixture)
    """
    path = Path(filename)
    stem = path.stem

    # Check for exact match first (most common case)
    if stem in REQUIRED_SECTIONS:
        return stem

    # Strip run timestamp prefix: YYYY-MM-DD-HHMMSS- (e.g., "2026-02-18-143022-")
    timestamp_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}-\d{6}-(.+)$')
    match = timestamp_pattern.match(stem)
    if match:
        without_timestamp = match.group(1)
        if without_timestamp in REQUIRED_SECTIONS:
            return without_timestamp
        stem = without_timestamp

    # Remove common suffixes for templates and test fixtures
    suffixes_to_remove = ['-template', '-valid', '-invalid', '-test', '-example']
    for suffix in suffixes_to_remove:
        if stem.endswith(suffix):
            stem = stem[:-len(suffix)]
            if stem in REQUIRED_SECTIONS:
                return stem

    # If still no match, return the stem for error reporting
    return stem


def parse_yaml_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from content if present. Returns empty dict if none."""
    lines = content.split('\n')
    if not lines or lines[0].strip() != '---':
        return {}

    frontmatter = {}
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == '---':
            break
        if ':' in stripped:
            key, _, value = stripped.partition(':')
            key = key.strip()
            value = value.strip()
            if value == '[]':
                frontmatter[key] = []
            elif value.startswith('[') and value.endswith(']'):
                items = [item.strip().strip('"').strip("'") for item in value[1:-1].split(',') if item.strip()]
                frontmatter[key] = items
            elif value.startswith('"') and value.endswith('"'):
                frontmatter[key] = value.strip('"')
            else:
                frontmatter[key] = value
    return frontmatter


def find_sections(content: str) -> List[str]:
    """Find all markdown sections (## Section Name) in the content."""
    # Match markdown section headers (## Section Name)
    pattern = r'^##\s+(.+)$'
    sections = re.findall(pattern, content, re.MULTILINE)
    # Strip whitespace and normalize
    return [section.strip() for section in sections]


PLACEHOLDER_PATTERNS = [
    re.compile(r'\[TODO\]', re.IGNORECASE),
    re.compile(r'\[FILL\s*IN\]', re.IGNORECASE),
    re.compile(r'\[TBD\]', re.IGNORECASE),
    re.compile(r'<placeholder>', re.IGNORECASE),
    re.compile(r'lorem ipsum', re.IGNORECASE),
]

GENERIC_NEXT_STEPS = [
    "continue development",
    "proceed with next steps",
    "tbd",
    "to be determined",
]


def get_section_content(content: str, section_name: str) -> str:
    """Extract content under a specific ## section, up to the next ## or end of file."""
    pattern = rf'^##\s+{re.escape(section_name)}\s*$'
    match = re.search(pattern, content, re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    next_section = re.search(r'^##\s+', content[start:], re.MULTILINE)
    if next_section:
        return content[start:start + next_section.start()].strip()
    return content[start:].strip()


def check_section_depth(content: str, section_name: str) -> Tuple[bool, str]:
    """Check that a section has >2 lines of content (not just the header)."""
    body = get_section_content(content, section_name)
    non_empty_lines = [line for line in body.split('\n') if line.strip()]
    if len(non_empty_lines) <= 2:
        return False, f"Section '{section_name}' has insufficient content ({len(non_empty_lines)} lines, need >2)"
    return True, ""


def check_no_placeholders(content: str) -> List[str]:
    """Check that no placeholder text exists in the content."""
    errors = []
    for pattern in PLACEHOLDER_PATTERNS:
        matches = pattern.findall(content)
        if matches:
            errors.append(f"Placeholder text found: {matches[0]}")
    return errors


def check_artifacts_created_paths(content: str) -> Tuple[bool, str]:
    """Check that 'Artifacts Created' section lists actual file paths (contains '/')."""
    body = get_section_content(content, "Artifacts Created")
    if not body:
        return True, ""  # Section missing is caught by required sections check
    if '/' not in body:
        return False, "Section 'Artifacts Created' does not list any file paths (expected paths containing '/')"
    return True, ""


def check_next_steps_actionable(content: str) -> Tuple[bool, str]:
    """Check that 'Next Steps' section has actionable items, not generic filler."""
    body = get_section_content(content, "Next Steps")
    if not body:
        return True, ""  # Section missing is caught by required sections check
    body_lower = body.lower().strip()
    for generic in GENERIC_NEXT_STEPS:
        if body_lower == generic or (len(body_lower) < 50 and generic in body_lower):
            return False, f"Section 'Next Steps' contains generic filler: '{generic}'"
    return True, ""


def validate_handoff(filename: str) -> tuple[bool, List[str]]:
    """
    Validate a handoff artifact file.
    Returns (is_valid, errors).
    """
    # Extract artifact type from filename
    artifact_type = extract_artifact_type(filename)

    # Check if this is a known artifact type
    if artifact_type not in REQUIRED_SECTIONS:
        return False, [f"Unknown artifact type: {artifact_type}. Expected one of: {', '.join(REQUIRED_SECTIONS.keys())}"]

    # Read file content
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        return False, [f"File not found: {filename}"]
    except Exception as e:
        return False, [f"Error reading file: {e}"]

    errors = []

    # Parse optional YAML frontmatter (backwards-compatible — pure markdown still passes)
    frontmatter = parse_yaml_frontmatter(content)

    # Find all sections in the file
    found_sections = find_sections(content)

    # Check for required sections
    required = REQUIRED_SECTIONS[artifact_type]
    for section in required:
        if section not in found_sections:
            errors.append(f"Missing section: {section}")

    # Content quality checks (only for sections that exist)
    for section in required:
        if section in found_sections:
            ok, msg = check_section_depth(content, section)
            if not ok:
                errors.append(msg)

    # Placeholder text check
    placeholder_errors = check_no_placeholders(content)
    errors.extend(placeholder_errors)

    # Artifacts Created path check
    if "Artifacts Created" in found_sections:
        ok, msg = check_artifacts_created_paths(content)
        if not ok:
            errors.append(msg)

    # Next Steps actionable check
    if "Next Steps" in found_sections:
        ok, msg = check_next_steps_actionable(content)
        if not ok:
            errors.append(msg)

    is_valid = len(errors) == 0
    return is_valid, errors


def main():
    """Main entry point for the validation hook."""
    if len(sys.argv) < 2:
        print("Usage: validate-handoff.py <handoff-artifact-file>", file=sys.stderr)
        sys.exit(1)

    filename = sys.argv[1]

    is_valid, missing_sections = validate_handoff(filename)

    if is_valid:
        print(f"✓ {filename} is valid")
        sys.exit(0)
    else:
        print(f"✗ {filename} validation failed", file=sys.stderr)
        print(f"Validation errors:", file=sys.stderr)
        for error in missing_sections:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

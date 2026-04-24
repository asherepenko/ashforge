#!/usr/bin/env python3
"""
Tests for agent prompt files.
Validates structure, frontmatter, references, and size constraints.
"""

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
AGENTS_DIR = PROJECT_ROOT / "agents"
REFERENCES_DIR = PROJECT_ROOT / "references"

REQUIRED_FRONTMATTER_FIELDS = ["name", "description", "tools", "model"]
MAX_DESCRIPTION_LENGTH = 700
MAX_AGENT_LINE_COUNT = 500


def get_agent_files():
    """Get all agent .md files."""
    return sorted(AGENTS_DIR.glob("*.md"))


def parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from agent file."""
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
            frontmatter[key.strip()] = value.strip()
    return frontmatter


def get_body_after_frontmatter(content: str) -> str:
    """Get content after the closing --- of frontmatter."""
    lines = content.split('\n')
    if not lines or lines[0].strip() != '---':
        return content

    in_frontmatter = True
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == '---':
            return '\n'.join(lines[i + 1:])
    return content


@pytest.fixture(params=get_agent_files(), ids=lambda p: p.stem)
def agent_file(request):
    """Parametrize over all agent files."""
    return request.param


class TestAgentFrontmatter:
    """Test that agent files have valid frontmatter."""

    def test_has_frontmatter(self, agent_file):
        content = agent_file.read_text(encoding='utf-8')
        assert content.startswith('---'), f"{agent_file.name} must start with YAML frontmatter"

    def test_has_required_fields(self, agent_file):
        content = agent_file.read_text(encoding='utf-8')
        fm = parse_frontmatter(content)
        for field in REQUIRED_FRONTMATTER_FIELDS:
            assert field in fm, f"{agent_file.name} missing frontmatter field: {field}"

    def test_description_length(self, agent_file):
        content = agent_file.read_text(encoding='utf-8')
        fm = parse_frontmatter(content)
        desc = fm.get("description", "")
        assert len(desc) <= MAX_DESCRIPTION_LENGTH, (
            f"{agent_file.name} description is {len(desc)} chars, max {MAX_DESCRIPTION_LENGTH}"
        )

    def test_model_is_valid(self, agent_file):
        content = agent_file.read_text(encoding='utf-8')
        fm = parse_frontmatter(content)
        model = fm.get("model", "")
        valid_models = ["opus", "sonnet", "haiku"]
        assert model in valid_models, (
            f"{agent_file.name} has invalid model '{model}', expected one of {valid_models}"
        )


class TestAgentReferences:
    """Test that references in agent files point to existing files."""

    def test_references_exist(self, agent_file):
        content = agent_file.read_text(encoding='utf-8')
        # Find all references/*.md patterns
        ref_pattern = re.compile(r'references/[\w-]+\.md')
        refs = ref_pattern.findall(content)

        for ref in refs:
            ref_path = PROJECT_ROOT / ref
            assert ref_path.exists(), (
                f"{agent_file.name} references '{ref}' which does not exist"
            )

    def test_no_broken_template_refs(self, agent_file):
        content = agent_file.read_text(encoding='utf-8')
        # Check for template variable patterns that weren't filled in
        template_patterns = [
            r'\{\{[^}]+\}\}',  # {{variable}}
            r'\$\{[^}]+\}',   # ${variable} (but not in code blocks)
        ]
        body = get_body_after_frontmatter(content)
        # Skip code blocks
        body_no_code = re.sub(r'```[\s\S]*?```', '', body)

        for pattern in template_patterns:
            matches = re.findall(pattern, body_no_code)
            assert len(matches) == 0, (
                f"{agent_file.name} has unresolved template references: {matches}"
            )


class TestAgentSize:
    """Test that agent files are within size constraints."""

    def test_line_count_under_limit(self, agent_file):
        content = agent_file.read_text(encoding='utf-8')
        line_count = len(content.split('\n'))
        assert line_count <= MAX_AGENT_LINE_COUNT, (
            f"{agent_file.name} has {line_count} lines, max {MAX_AGENT_LINE_COUNT}"
        )


class TestAgentStructure:
    """Test that agent files have required structural sections."""

    def test_has_scope_boundaries(self, agent_file):
        content = agent_file.read_text(encoding='utf-8')
        assert "## Scope Boundaries" in content, (
            f"{agent_file.name} missing '## Scope Boundaries' section"
        )

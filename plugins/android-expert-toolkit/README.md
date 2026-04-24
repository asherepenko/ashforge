# Android Expert Toolkit

Production-grade Android development plugin for Claude Code with specialized agents, pattern detection, and decision support.

## What It Does

- **5 Specialized Agents** — Architecture, development, testing, Compose UI, Gradle builds
- **7 Pipeline Types** — `feature-build`, `architecture-review`, `migration`, `ui-redesign`, `build-optimization`, `test`, `code-review`
- **Pattern Detection (80/20 Rule)** — Matches existing codebase conventions when ≥80% consistent; proposes modern alternatives below that threshold
- **Decision Council** — 3-perspective deliberation (status quo / best practices / pragmatic) for major architectural decisions
- **Handoff Artifacts** — Agents communicate through structured markdown reports, not in-context conversation
- **Validation Hooks** — Pipeline state tracking, handoff schema validation, dependency-graph checks

## Installation

Install as a user-scope Claude Code plugin:

```bash
mkdir -p ~/.claude/plugins/cache/local/android-expert-toolkit/latest

ln -sf /path/to/android-expert-toolkit/* \
  ~/.claude/plugins/cache/local/android-expert-toolkit/latest/
ln -sf /path/to/android-expert-toolkit/.claude-plugin \
  ~/.claude/plugins/cache/local/android-expert-toolkit/latest/.claude-plugin
```

Register in `~/.claude/plugins/installed_plugins.json`:

```json
[
  {
    "name": "android-expert-toolkit",
    "version": "latest",
    "source": "local"
  }
]
```

Enable in `~/.claude/settings.json`:

```json
{
  "enabledPlugins": [
    "android-expert-toolkit"
  ]
}
```

Restart Claude Code to activate.

## Usage

```bash
/aet-pipeline feature-build "Social Feed"    # Multi-agent feature build
/aet-pipeline architecture-review            # Analyze codebase
/aet-pipeline migration "LiveData to StateFlow"
/aet-pipeline test "User Profile"            # Add tests only
/aet-pipeline code-review "Auth Module"      # Code review
/aet-status                                  # Check pipeline progress
/aet-check di                                # Detect DI patterns
```

See [QUICK_START.md](QUICK_START.md) for guided examples and scenarios.

## Agents

| Agent | Purpose | Model | Plan Mode |
|-------|---------|-------|-----------|
| android-architect | Architecture, ADRs, pattern detection | Opus | Yes |
| android-developer | ViewModels, repositories, data layer | Sonnet | No |
| compose-expert | Compose UI, Material 3, adaptive layouts | Sonnet | No |
| gradle-build-engineer | Convention plugins, version catalogs | Sonnet | No |
| android-testing-specialist | Test doubles, Turbine, coverage | Sonnet | No |

**Default pipeline flow** (`feature-build`): architect → gradle-build-engineer + android-developer (parallel) → compose-expert → android-testing-specialist

Agents hand off through markdown artifacts under `.artifacts/aet/handoffs/{feature_slug}/` — each agent reads its predecessor's report and writes its own before the next agent starts.

## Plugin Structure

```
android-expert-toolkit/
├── .claude-plugin/plugin.json    # Plugin manifest
├── agents/                       # 5 specialized agents
├── commands/                     # pipeline, status, check
├── skills/android-expert/        # Core Android skill (SKILL.md)
├── hooks/                        # Session-start, progress tracking, validators
├── references/                   # 18 deep-dive references with "When to use"
├── templates/                    # Handoff artifact scaffolds + project settings
├── examples/                     # Example pipeline outputs
└── tests/                        # Hook validation tests
```

## Per-Project Configuration

Copy `templates/android-expert-toolkit.local.md.template` to your project root as `android-expert-toolkit.local.md` and set DI framework, state management, and pipeline skip flags. When all values are set, the pipeline skips the interactive configuration prompt.

## Documentation

| Doc | Purpose |
|-----|---------|
| [QUICK_START.md](QUICK_START.md) | Getting started with slash commands and scenarios |
| [CLAUDE.md](CLAUDE.md) | Plugin internals (for maintainers) |
| [references/scenarios.md](references/scenarios.md) | End-to-end pipeline walkthroughs |
| [references/agent-routing.md](references/agent-routing.md) | Agent selection matrix |
| [references/pattern-detection.md](references/pattern-detection.md) | Detection commands and 80/20 framework |
| [references/conflict-resolution.md](references/conflict-resolution.md) | Priority hierarchy (P0–P3) |

## Credits

Built on [Now in Android](https://github.com/android/nowinandroid) patterns, Modern Android Development guides, and validated on production codebases.

## License

MIT

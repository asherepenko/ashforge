# Android Expert Toolkit

Expert Android engineering agents, interactive multi-agent pipelines, and 80/20 pattern detection for modern Kotlin/Compose/Gradle development.

## What It Does

- **5 Specialized Agents** — Architecture, development, testing, Compose UI, Gradle builds
- **7 Pipeline Types** — `feature-build`, `architecture-review`, `migration`, `ui-redesign`, `build-optimization`, `test`, `code-review`
- **Pattern Detection (80/20 Rule)** — Matches existing codebase conventions when ≥80% consistent; proposes modern alternatives below that threshold
- **Decision Council** — 3-perspective deliberation (status quo / best practices / pragmatic) for major architectural decisions
- **Handoff Artifacts** — Agents communicate through structured markdown reports, not in-context conversation
- **Validation Hooks** — Pipeline state tracking, handoff schema validation, dependency-graph checks

## Installation

Install via the [ashforge](https://github.com/asherepenko/ashforge) marketplace:

```
/plugin marketplace add asherepenko/ashforge
/plugin install android-expert-toolkit@ashforge
/reload-plugins
```

Plugin assets land in `~/.claude/plugins/cache/`. Use `${CLAUDE_PLUGIN_ROOT}` inside hooks/configs rather than relative paths.

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

[MIT](./LICENSE)

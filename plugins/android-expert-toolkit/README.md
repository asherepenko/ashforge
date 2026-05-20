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

The toolkit ships in the [ashforge](https://github.com/asherepenko/ashforge) marketplace and works on both Claude Code and Codex (CLI / App).

### Claude Code

```
/plugin marketplace add asherepenko/ashforge
/plugin install android-expert-toolkit@ashforge
/reload-plugins
```

Plugin assets land in `~/.claude/plugins/cache/`. Hooks use `${CLAUDE_PLUGIN_ROOT}` to resolve plugin paths.

### Codex (CLI / App)

```bash
codex plugin marketplace add asherepenko/ashforge
```

Then enable the plugin — either via the Codex UI or by adding to `~/.codex/config.toml`:

```toml
[plugins."android-expert-toolkit@ashforge"]
enabled = true

[features]
hooks = true            # enable hooks at all
plugin_hooks = true     # enable plugin-bundled hooks (gated separately while in beta)
multi_agent = true      # required for aet-pipeline parallel agent dispatch
```

On first run Codex will prompt to trust each plugin hook command — accept to record the `trusted_hash` entries. Without trust, hooks register but never execute.

Plugin assets land under `~/.codex/plugins/cache/`. Hooks use `${PLUGIN_ROOT}` (not `${CLAUDE_PLUGIN_ROOT}`). The Codex manifest lives at `.codex-plugin/plugin.json`; hooks at `.codex-plugin/hooks.json`. See [`references/codex-tools.md`](references/codex-tools.md) for the full Claude → Codex tool mapping and the PreToolUse deny-only caveat.

## Usage

The toolkit ships as **skills** — invoke by intent on Claude Code or Codex CLI/App. No slash commands.

```
aet-pipeline feature-build "Social Feed"       # Multi-agent feature build
aet-pipeline architecture-review               # Analyze codebase
aet-pipeline migration "LiveData to StateFlow"
aet-pipeline test "User Profile"               # Add tests only
aet-pipeline code-review "Auth Module"         # Code review
aet-status                                     # Check pipeline progress
aet-check di                                   # Detect DI patterns
aet-check                                      # Run all pattern checks
android-expert "ViewModel StateFlow pattern"   # Ad-hoc Android question
```

Claude: the Skill tool auto-triggers on description match, or invoke explicitly with `Skill(skill="aet-pipeline", args="feature-build Social Feed")`. Codex: state the intent in natural language — the multi-agent feature must be enabled (`multi_agent = true` in `~/.codex/config.toml`) for parallel agent dispatch.

See [QUICK_START.md](QUICK_START.md) for guided examples and scenarios, and [codex-tools](references/codex-tools.md) for the Claude → Codex tool mapping used inside the skills.

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
├── .claude-plugin/plugin.json    # Claude Code manifest
├── .codex-plugin/
│   ├── plugin.json               # Codex CLI / Codex App manifest
│   └── hooks.json                # Codex hooks (mirrors hooks/hooks.json with Codex matchers + ${PLUGIN_ROOT})
├── agents/                       # 5 specialized agents (subagent_type on Claude; persona templates on Codex)
├── skills/
│   ├── android-expert/           # Ad-hoc Android Q&A
│   ├── aet-pipeline/             # Multi-agent orchestration
│   ├── aet-status/               # Pipeline status & recovery
│   └── aet-check/                # Pattern detection (80/20)
├── hooks/                        # Shared Python scripts — registered by both .claude-plugin and .codex-plugin manifests
├── references/                   # Deep-dive references with "When to use" + codex-tools.md mapping
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
| [scenarios](references/scenarios.md) | End-to-end pipeline walkthroughs |
| [agent-routing](references/agent-routing.md) | Agent selection matrix |
| [pattern-detection](references/pattern-detection.md) | Detection commands and 80/20 framework |
| [conflict-resolution](references/conflict-resolution.md) | Priority hierarchy (P0–P3) |

## Credits

Built on [Now in Android](https://github.com/android/nowinandroid) patterns, Modern Android Development guides, and validated on production codebases.

## License

[MIT](./LICENSE)

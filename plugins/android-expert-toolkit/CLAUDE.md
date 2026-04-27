# Android Expert Toolkit

Maintainer notes for the plugin itself. For user-facing usage, see `README.md` and `QUICK_START.md`.

## Plugin Structure

```
android-expert-toolkit/
├── .claude-plugin/plugin.json    # Manifest (name, version, description)
├── agents/                       # 5 specialized agents (functional, not roleplay)
├── commands/                     # pipeline, status, check (slash commands)
├── skills/android-expert/        # SKILL.md — core Android engineering knowledge
├── hooks/                        # Python hooks (session-start, track-progress, validators)
├── references/                   # 18 deep-dive references (read on demand)
├── templates/                    # Handoff artifact scaffolds
├── examples/                     # End-to-end example pipeline output
└── tests/                        # Hook validation tests
```

## Commands

| Command | Purpose |
|---------|---------|
| `/aet-pipeline <type> "<name>"` | Multi-agent pipeline execution |
| `/aet-status` | Read `.artifacts/aet/state.json`, show progress |
| `/aet-check [category]` | Run pattern detection (80/20 matrix) |

Pipeline types: `feature-build`, `architecture-review`, `migration`, `ui-redesign`, `build-optimization`, `test`, `code-review`.

## Pipeline Decision Points

Interactive pipeline has 4 user-gated decisions:
1. **Configuration** — DI framework, state management, stages to skip
2. **Architecture Approval** — review blueprint before implementation proceeds
3. **Pattern Conflict** — when no clear winner in 80/20 detection matrix
4. **Error Recovery** — auto-fix, manual fix, skip, or abort on failures

When `android-expert-toolkit.local.md` exists in the project root with all values set, step 1 is skipped.

## Agents

| Agent | Role | Plan Mode | Model |
|-------|------|-----------|-------|
| android-architect | Architecture design, ADRs, pattern detection | Yes (feature-build, migration, conflict) | Opus |
| android-developer | Data layer, ViewModels, repositories | No | Sonnet |
| compose-expert | Compose UI, Material 3, adaptive layouts | No | Sonnet |
| gradle-build-engineer | Convention plugins, version catalogs | No | Sonnet |
| android-testing-specialist | Test doubles, Turbine, coverage | No | Sonnet |

"Plan Mode = Yes" means the agent enters Claude Code plan mode before acting, so the user approves the plan before file changes happen. Only the architect gates this way because its output (blueprints, ADRs) needs explicit approval before downstream agents consume it.

### Agent template asymmetry (intentional)

`Red Flags` and `Common Rationalizations` sections appear only in `android-architect` and `android-developer` because those agents exercise discretion on judgment calls (pattern choice, module boundaries, error handling, null safety) where bad-faith shortcuts tempt. `compose-expert`, `gradle-build-engineer`, and `android-testing-specialist` operate against well-defined standards (Material 3 rubric, Gradle conventions, no-mock policy) that serve the same guardrail function. Do not normalize this asymmetry away — it reflects real domain risk, not template drift.

### Tool-list asymmetry (intentional)

`android-architect`, `android-developer`, and `compose-expert` have `WebFetch`/`WebSearch` for researching patterns and design inspiration. `gradle-build-engineer` and `android-testing-specialist` don't — their work is deterministic (build config, local code testing) and shouldn't drift based on web content.

## Skill

`skills/android-expert/SKILL.md` is the entry point for ad-hoc Android questions ("Room offline-first", "ViewModel StateFlow pattern", etc.) — used when the user isn't running a full pipeline. It points to `references/` for deep dives.

## References

18 deep-dive references under `references/`. Each starts with `## When to use` so agents (and humans) know when to load the file. Organized by role:

- **Architect-facing**: `architecture-patterns.md`, `architect-code-examples.md`, `pattern-detection.md`, `rubric-android-architecture.md`
- **Developer-facing**: `developer-patterns.md`, `data-layer-patterns.md`, `ui-patterns.md`
- **Compose-facing**: `compose-patterns.md`, `rubric-compose-ui.md`
- **Gradle-facing**: `gradle-patterns.md`
- **Testing-facing**: `testing-patterns.md`, `testing-patterns-detail.md`
- **Cross-cutting**: `conflict-resolution.md`, `performance-targets.md`, `pragmatic-examples.md`, `agent-routing.md`, `scenarios.md`, `pipeline-error-scenarios.md`

The **80/20 rule** (in `pattern-detection.md`) is the core decision framework: if a pattern has ≥80% prevalence in the codebase, match it; below 80%, propose a modern alternative. This keeps agents consistent with existing code instead of imposing ideal-world patterns.

## Handoff Artifacts

Written to `.artifacts/aet/handoffs/{feature_slug}/` with run timestamp prefix:

- `{run_timestamp}-architecture-blueprint.md` — module structure, data flow, ADRs
- `{run_timestamp}-module-setup.md` — convention plugins, dependencies
- `{run_timestamp}-implementation-report.md` — ViewModels, repositories
- `{run_timestamp}-ui-report.md` — composables, Material 3 components
- `{run_timestamp}-test-report.md` — test doubles, coverage
- `{run_timestamp}-code-review-report.md` — findings with severity ratings

Scaffolds live in `templates/` — each agent reads its template before writing to keep artifact structure consistent.

Example path: `.artifacts/aet/handoffs/social-feed/2026-02-18-143022-architecture-blueprint.md`

## Hooks

Registered in `hooks/hooks.json`:

| Hook | Trigger | Purpose |
|------|---------|---------|
| `session-start.py` | SessionStart | Emits plugin-loaded banner, warns if no Android project detected |
| `track-progress.py` | PostToolUse (Write, Bash) | Updates `.artifacts/aet/state.json` as agents produce artifacts |
| `validate-handoff.py` | (invoked by agents) | Validates handoff artifact schema before downstream agent consumes it |
| `validate-dependencies.py` | (invoked by agents) | Validates module dependency graph for circularity |

## State

- Pipeline state: `.artifacts/aet/state.json` — includes `feature_slug`, `run_timestamp`, completed stages, current agent
- Project settings: `android-expert-toolkit.local.md` (project root, optional)
- Settings template: `templates/android-expert-toolkit.local.md.template`

## Tests

Python tests for hooks and agent prompts under `tests/`. Run:

```bash
pytest tests/
```

## Versioning

Semantic versioning in `.claude-plugin/plugin.json`:
- **Major**: breaking changes to command/agent contracts
- **Minor**: new commands, agents, or pipeline types
- **Patch**: docs, references, hook fixes, agent prompt tuning

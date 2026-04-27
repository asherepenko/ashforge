# Android Expert Toolkit — Quick Start

Get productive with the toolkit in 5 minutes.

---

## Installation

Install via the [ashforge](https://github.com/asherepenko/ashforge) marketplace:

```
/plugin marketplace add asherepenko/ashforge
/plugin install android-expert-toolkit@ashforge
/reload-plugins
```

### Optional: Per-Project Settings

Skip the pipeline's interactive configuration step by copying the template into your project root:

```bash
cp "$CLAUDE_PLUGIN_ROOT/templates/android-expert-toolkit.local.md.template" \
  ./android-expert-toolkit.local.md
# Edit to set DI framework, state management, and stages to skip.
```

(`$CLAUDE_PLUGIN_ROOT` resolves to the cached plugin location — `~/.claude/plugins/cache/...`.)

---

## Commands

| Command | Use when |
|---------|----------|
| `/aet-pipeline <type> "<name>"` | You want a multi-agent workflow (default entry point) |
| `/aet-status` | You want to see where an in-flight pipeline stopped and resume |
| `/aet-check [category]` | You want pattern detection only (DI, state, UI, etc.) — no code changes |

---

## Pipeline Types

```bash
/aet-pipeline feature-build "Social Feed"
/aet-pipeline architecture-review
/aet-pipeline migration "LiveData to StateFlow"
/aet-pipeline ui-redesign "Profile Screen"
/aet-pipeline build-optimization
/aet-pipeline test "User Profile"
/aet-pipeline code-review "Auth Module"
```

| Type | What happens | Agents involved |
|------|--------------|-----------------|
| `feature-build` | End-to-end feature: architecture → modules → data layer → UI → tests | all 5 |
| `architecture-review` | Codebase audit, pattern detection, technical debt report | architect |
| `migration` | Pattern-to-pattern migration (e.g. LiveData → StateFlow) | architect → developer → testing-specialist |
| `ui-redesign` | Screen or component redesign | (optional architect) → compose-expert → (optional testing) |
| `build-optimization` | Module setup, convention plugins, build speed | architect → gradle-build-engineer |
| `test` | Add tests to existing code | testing-specialist |
| `code-review` | Review code for issues with severity ratings | architect (review mode) |

Each pipeline has up to 4 interactive decision points: configuration, architecture approval, pattern conflict, and error recovery. You control direction at each gate.

---

## Scenarios

### Scenario 1 — Greenfield feature in an existing codebase

Goal: Add a social feed feature that matches the codebase's established patterns.

```bash
/aet-pipeline feature-build "Social Feed"
```

What happens:
1. **Configuration gate** — confirm DI framework, state management, modules to generate
2. **Architecture blueprint** — architect detects existing patterns (e.g., "83.9% LiveData → match it"), produces `architecture-blueprint.md`, asks you to approve
3. **Parallel implementation** — gradle-build-engineer wires up modules while android-developer implements data layer + ViewModels
4. **UI** — compose-expert builds screens with Material 3
5. **Tests** — android-testing-specialist adds test doubles and coverage

All artifacts land in `.artifacts/aet/handoffs/social-feed/`. Resume anytime with `/aet-status`.

### Scenario 2 — Migrating from LiveData to StateFlow

Goal: Decide whether to migrate, then execute phased migration.

```bash
/aet-pipeline migration "LiveData to StateFlow"
```

What happens:
1. Architect runs pattern detection — counts LiveData vs StateFlow, computes 80/20 consistency
2. If below the 80% threshold or at a conflict point, **Decision Council** runs: Status Quo Advocate vs Best Practices Advocate vs Pragmatic Mediator
3. You pick the resolution (keep, migrate in phases, migrate fully)
4. Developer executes the migration, testing-specialist adds regression coverage

### Scenario 3 — Just review, no code changes

Goal: Understand an unfamiliar codebase before making changes.

```bash
/aet-pipeline architecture-review
```

You get a report in `.artifacts/aet/handoffs/` with pattern detection, module structure analysis, technical debt priorities, and recommendations.

### Scenario 4 — Pattern detection only

Goal: Quick check without running a full pipeline.

```bash
/aet-check di          # Hilt vs Koin vs manual
/aet-check state       # LiveData vs StateFlow
/aet-check ui          # Compose vs XML
/aet-check             # All categories
```

Reports consistency percentages and applies the 80/20 rule to recommend matching existing patterns or proposing alternatives.

### Scenario 5 — Add tests to existing code

Goal: Improve coverage without touching production code.

```bash
/aet-pipeline test "ProfileViewModel"
```

testing-specialist creates test doubles (no mocking framework), Turbine Flow tests, and Given-When-Then structured unit tests targeting 80%+ coverage.

---

## The 80/20 Rule

The toolkit's core decision heuristic:

- **≥ 80% consistency** → match the existing pattern (even if not ideal)
- **< 80% consistency** → propose a modern alternative

Rationale: codebase consistency beats perfection. A single "ideal" ViewModel sitting among 40 LiveData ones creates more friction than value. Document the diverge as tech debt instead:

```kotlin
// TODO(JIRA-456): Migrate to StateFlow when codebase consistency reaches 50%
```

See [references/pattern-detection.md](references/pattern-detection.md) for detection commands per category.

---

## Resuming an Interrupted Pipeline

If a pipeline stops mid-flow (error, Claude session ended, you paused):

```bash
/aet-status
```

This reads `.artifacts/aet/state.json` and shows:
- Which stages completed
- Which artifacts exist
- The next action (resume, retry last stage, abort)

---

## Troubleshooting

**"Command not found: /aet-pipeline"**

Plugin isn't installed or active. Run `/plugin marketplace list` (should show `ashforge`) and `/plugin` to confirm `android-expert-toolkit` is installed and enabled. Run `/reload-plugins` or restart Claude Code.

**"Agent keeps producing wrong patterns for my codebase"**

Run `/aet-check` to surface what the 80/20 detection actually sees. If detection is wrong (e.g., project uses Dagger, not Hilt), pass explicit context in your next pipeline invocation or pin the value in `android-expert-toolkit.local.md`.

**"Pipeline stalled at a decision gate"**

Decision gates are intentional — architecture approval and pattern conflicts need user input. If you want to skip them in future runs, set the corresponding values in `android-expert-toolkit.local.md`.

**"Handoff artifact missing fields"**

The `validate-handoff.py` hook should catch this before the next agent runs. If it didn't, check `hooks/hooks.json` is registered and `session-start.py` emitted the load banner on Claude Code startup.

---

## Further Reading

- **[README.md](README.md)** — Plugin overview, installation, plugin structure
- **[CLAUDE.md](CLAUDE.md)** — Plugin internals (for maintainers)
- **[references/scenarios.md](references/scenarios.md)** — Full walkthrough examples
- **[references/agent-routing.md](references/agent-routing.md)** — When each agent is the right choice
- **[references/conflict-resolution.md](references/conflict-resolution.md)** — Priority hierarchy when principles conflict
- **[references/pattern-detection.md](references/pattern-detection.md)** — All detection commands + 80/20 framework
- **[skills/android-expert/SKILL.md](skills/android-expert/SKILL.md)** — Ad-hoc Android questions (outside pipelines)

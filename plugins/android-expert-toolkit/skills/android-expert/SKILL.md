---
name: android-expert
description: "Use for ad-hoc Android/Kotlin questions, pattern guidance, and code review — Jetpack Compose, ViewModel, StateFlow, Hilt/Koin, Room, Coroutines/Flow, Navigation, DataStore, WorkManager, Gradle convention plugins, ProGuard/R8, Material 3, or Android architecture. Trigger whenever the user mentions Android, Kotlin, Compose, or any Android framework — even if they don't explicitly ask for an 'expert'. NOT for multi-agent pipeline execution (use /aet-pipeline for end-to-end feature builds, migrations, or reviews)."
argument-hint: "[question or topic] — e.g. 'Room offline-first', 'ViewModel StateFlow pattern', 'Hilt setup for feature module', 'best practice for offline sync'"
---

# Android Engineering Expert

Apply modern Android patterns (Now in Android reference) with 5 specialized agents, automated pipelines, and 80/20 pattern detection.

## Quick Start

**Choose your path:**

1. **Automated Multi-Agent Workflows**
   - Use `/aet-pipeline` command for end-to-end orchestration
   - 7 pipeline types: `feature-build`, `architecture-review`, `migration`, `ui-redesign`, `build-optimization`, `test`, `code-review`
   - Automatic validation, handoff artifacts, error recovery
   - See [Pipeline Commands](#pipeline-commands) section below

2. **Pattern Reference & Guidelines**
   - Browse [Core Principles](#core-principles) for Android best practices
   - Check [Pragmatic Development Principles](#pragmatic-development-principles) for real-world guidance
   - Review detailed patterns in `references/` (see pointers below)

3. **Manual Agent Orchestration**
   - Use individual agents for specific tasks
   - See [Agent Orchestration](#agent-orchestration) section for coordination patterns
   - Refer to `references/agent-routing.md` for agent selection guidance

**New to the toolkit?** Start with automated workflows (`/aet-pipeline`) for guided multi-agent execution.

---

## Core Principles

1. **Kotlin-First Development** - Modern Kotlin features, coroutines, Flow, extension functions
2. **Reactive Architecture** - Unidirectional data flow, StateFlow/Flow throughout
3. **Offline-First** - Local database as source of truth with remote sync
4. **Modular Design** - Feature modules with clear boundaries and dependency rules
5. **Testability by Design** - Constructor injection, test doubles (no mocking)
6. **Type Safety** - Sealed interfaces, value objects, compile-time verification
7. **Convention Over Configuration** - Gradle convention plugins for standardization

For detailed architecture, DI, module organization, and Kotlin patterns, read `references/architecture-patterns.md`.

For detailed data layer, persistence, networking, and sync patterns, read `references/data-layer-patterns.md`.

For detailed Compose, navigation, and UI implementation patterns, read `references/ui-patterns.md`.

For detailed testing strategy, test doubles, and coverage guidance, read `references/testing-patterns.md`.

For detailed security architecture and hardening guidance, see the Security Architecture section in `references/architecture-patterns.md`.

For detailed performance benchmarks and monitoring thresholds, read `references/performance-targets.md`.

## Pragmatic Development Principles

### Working with Existing Codebases

Real-world Android development often involves legacy code, tight deadlines, and technical constraints. These principles guide how to balance ideal patterns with practical reality.

**Consistency Over Perfection:**
- Match existing patterns even if they're not ideal
- Consistency within a codebase > theoretical best practices
- Only introduce new patterns if explicitly approved or mandated
- A consistent suboptimal pattern is better than mixed patterns

**The Boy Scout Rule:**
- Leave code slightly better than you found it
- Small, safe improvements within task scope
- Don't rewrite working code just because it's not perfect
- Examples: Add missing nullability annotations, extract magic numbers, improve variable names

**Respect Constraints:**
- **Technical constraints**: Legacy dependencies, API contracts, performance requirements, existing architecture
- **Business constraints**: Deadlines, risk tolerance, budget limitations, production stability
- **Organizational constraints**: Team expertise, approval processes, testing capacity, deployment windows
- Acknowledge constraints explicitly and work within them

**Scope Discipline:**
- Only fix what's blocking the current task
- Document other technical debt for future work (TODO comments, tickets)
- Don't expand scope without explicit approval
- Create follow-up tickets for improvements outside current scope
- Resist the urge to "fix everything" in one change

**When NOT to Refactor:**
- Working code with stable behavior (if it ain't broke...)
- Code that would require extensive testing without clear benefit
- Changes that affect API contracts or public interfaces
- Refactors without clear business value or user impact
- When deadline pressure is high and risk must be minimized
- When the team lacks expertise in the "better" approach

**Incremental Improvement Strategy:**
- Make the smallest change that solves the problem
- If major refactoring is needed, break it into phases
- Use adapter/wrapper patterns to bridge old and new code
- Write characterization tests before touching legacy code
- Migrate one module/feature at a time
- Keep the app working at every step

**Document Technical Debt:** Use `TODO(tech-debt):` comments with ticket references and suppression annotations.

See `references/pragmatic-examples.md` for Good/Bad code examples demonstrating these principles.

## Conflict Resolution Hierarchy

When multiple guidelines conflict, apply this priority order:

**P0 - User Instructions (Highest)**
- Explicit requirements from current task/conversation
- Project-specific CLAUDE.md instructions
- Overrides all defaults and best practices

**P1 - Codebase Consistency**
- Match existing patterns in current project
- Maintain architectural decisions already in place
- Use established naming conventions and file structure

**P2 - Pragmatic Constraints**
- Technical limitations (API contracts, dependencies, performance)
- Business constraints (deadlines, risk, budget)
- Team constraints (expertise, capacity, tooling)

**P3 - Best Practices (Lowest)**
- Theoretical ideal patterns from this skill
- Industry recommendations
- Latest framework features

**Quick Examples:**

User says "use LiveData" -> P0 wins, use LiveData even if StateFlow is better practice

Codebase uses manual DI -> P1 wins, don't introduce Hilt without approval

Legacy API requires callback pattern -> P2 wins, wrap in Flow at boundary

All else equal -> P3 wins, apply modern best practices

**Resolution Process:**
1. Check for explicit user instruction
2. If none, check codebase pattern
3. If inconsistent, check constraints
4. If no constraints, apply best practice

**See also:** [Conflict Resolution Guide](../../references/conflict-resolution.md) for decision trees and edge cases.

## Checklist: New Feature Implementation

When implementing a new feature, verify (adapt to match detected codebase patterns):

- [ ] Sealed interface for UI state (Loading, Error, Success)
- [ ] StateFlow in ViewModel
- [ ] Repository exposes Flow (not suspend fun returning snapshot)
- [ ] Hilt injection in ViewModel and Repository
- [ ] Test doubles for all dependencies (no mocking)
- [ ] Convention plugins applied (feature.impl, compose, hilt)
- [ ] Navigation route defined in feature API module
- [ ] Room entities and DAOs if data persistence needed
- [ ] Proto DataStore for feature preferences
- [ ] Unit tests with MainDispatcherRule
- [ ] Documentation in README
- [ ] UI implementation (see **compose-expert** for Route/Screen patterns, Material 3, adaptive UI)

## Agent Orchestration

### Agent Selection

| Agent | Model | Use When |
|-------|-------|----------|
| `android-architect` | Opus | Architecture decisions, pattern detection, technical debt review, Decision Council |
| `android-developer` | Sonnet | Feature implementation, ViewModels, repositories, data layer |
| `android-testing-specialist` | Sonnet | Test doubles, Flow testing with Turbine, Compose UI tests |
| `compose-expert` | Sonnet | Compose screens, Material 3, adaptive UI, accessibility |
| `gradle-build-engineer` | Sonnet | Convention plugins, version catalogs, module setup, build optimization |

### Workflow Pipelines

Use `/aet-pipeline <pipeline> [feature_name]` for automated orchestration with validation and error recovery. For manual orchestration, here's the agent sequence for each pipeline type:

| Pipeline | Agent Sequence | Artifacts Produced |
|----------|---------------|--------------------|
| `feature-build` | architect → gradle + developer (parallel) → compose → testing | blueprint, module-setup, implementation, ui, test |
| `architecture-review` | architect | blueprint |
| `migration` | architect → developer → testing | blueprint, implementation, test |
| `ui-redesign` | (architect) → compose → (testing) | (blueprint), ui, (test) |
| `build-optimization` | architect → gradle | blueprint, module-setup |
| `test` | testing (reads source directly, no prerequisite) | test |
| `code-review` | architect (review mode) | code-review |

Parentheses indicate optional stages. For the full execution protocol, parallel dispatch rules, and handoff validation, see `commands/aet-pipeline.md`.

### Handoff Artifact Protocol

Agents communicate through structured handoff files in `.artifacts/aet/handoffs/{feature_slug}/{run_timestamp}-{artifact-name}.md`. Each artifact must contain these sections so downstream agents can consume it unambiguously:

```markdown
# [Artifact Type]: [Feature Name]
<!-- Written by: [agent-name] -->
<!-- Timestamp: [ISO 8601] -->

## Summary
[1-3 sentence overview]

## Decisions
- [Key decision]: [choice] — [rationale]

## Artifacts Created
- `path/to/File.kt` — [purpose]

## Next Steps
- [What the downstream agent should do]

## Constraints
- [Limits the downstream agent must respect]
```

For artifact types by agent, reading protocol, and parallel dispatch rules, see `commands/aet-pipeline.md` § Handoff Artifact Protocol.

## Pipeline Commands

For pipeline orchestration (types, execution protocol, handoff validation, error recovery), see `commands/aet-pipeline.md`.

- `/aet-pipeline <type> "<name>"` — run a pipeline
- `/aet-status` — check progress
- `/aet-check [category]` — detect patterns

7 pipeline types: `feature-build`, `architecture-review`, `migration`, `ui-redesign`, `build-optimization`, `test`, `code-review`.

## Error Recovery

Pipeline error handling is defined in `commands/aet-pipeline.md` (Decision Point 4 and Error Recovery sections). Key principle: auto-fix first (max 2 retries), then escalate to user. Escalate to manual intervention after 3+ failed attempts or when root cause is unclear.

## Reference Projects

- **Now in Android** - Google's official reference app
- **dpconde/claude-android-skill** - Existing Claude skill
- **futurice/android-best-practices** - Industry standards
- **awesome-claude-code-subagents** - Subagent patterns

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The codebase uses LiveData, but StateFlow is better — I'll migrate" | P1 (codebase consistency) beats P3 (best practices). Match existing patterns unless explicitly approved to migrate. |
| "This working code is ugly, I'll refactor it while I'm here" | Scope discipline. Only fix what's blocking the current task. Document tech debt for future work. |
| "Pattern detection found 60% Hilt / 40% Koin — just pick Hilt" | Below 80% threshold means conflict. Surface it (DP3) — don't silently resolve. |
| "Convention plugins are overkill for this small project" | Convention plugins enforce consistency. Even small projects grow — and inconsistent build config is painful to fix later. |
| "I'll skip the pipeline and manually orchestrate agents" | Pipelines exist for validation, handoff quality, and error recovery. Manual orchestration skips all three. |
| "The agent scope boundaries are too restrictive" | Boundaries prevent scope creep and merge conflicts in parallel dispatch. One agent doing two jobs produces worse results than two focused agents. |

## Red Flags

- Introducing new patterns without checking codebase consistency first
- Refactoring working code outside the current task scope
- Agents writing code outside their scope boundaries
- Skipping pattern detection before making technology choices
- Manual agent orchestration when a pipeline type exists for the task
- Ignoring the conflict resolution hierarchy (P0 > P1 > P2 > P3)

## Verification

After using the Android Expert skill, confirm:

- [ ] Pattern detection ran for relevant categories (or valid cache used)
- [ ] Technology choices align with conflict resolution hierarchy
- [ ] Agent scope boundaries respected (no cross-boundary work)
- [ ] Handoff artifacts validated between stages
- [ ] Implementation follows detected codebase patterns (or deviation documented)

## Version Requirements

- Minimum SDK: 24 (Android 7.0)
- Target SDK: Latest stable
- Kotlin: 2.3.0+
- Compose: BOM 2025.09.01+
- AGP: 9.0.0+

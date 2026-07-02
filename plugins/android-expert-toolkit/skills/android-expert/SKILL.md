---
name: android-expert
description: "Use for ad-hoc Android app development questions, pattern guidance, and code review — Jetpack Compose UI, ViewModel, StateFlow, Hilt/Koin, Room, Coroutines/Flow, Navigation, DataStore, WorkManager, Android Gradle convention plugins, ProGuard/R8, Material 3, or Android app architecture. Trigger on Android app work (Compose UI, Android framework, app architecture) — NOT for backend/server Kotlin or plain Gradle JVM builds. NOT for multi-agent pipeline execution (use the `aet-pipeline` skill for end-to-end feature builds, migrations, or reviews)."
argument-hint: "[question or topic] — e.g. 'Room offline-first', 'ViewModel StateFlow pattern'"
metadata:
  short-description: "Ad-hoc Android app development guidance — Compose, architecture, DI, testing patterns"
---

# Android Engineering Expert

Apply modern Android patterns (Now in Android reference) with 5 specialized agents, automated pipelines, and 80/20 pattern detection.

## Quick Start

**Choose your path:**

1. **Automated Multi-Agent Workflows**
   - Use the `aet-pipeline` skill for end-to-end orchestration
   - 7 pipeline types: `feature-build`, `architecture-review`, `migration`, `ui-redesign`, `build-optimization`, `test`, `code-review`
   - Automatic validation, handoff artifacts, error recovery
   - Companion skills: `aet-status` (progress + recovery), `aet-check` (80/20 pattern detection)

2. **Pattern Reference & Guidelines**
   - Browse [Core Principles](#core-principles) for Android best practices
   - Check [Pragmatic Development Principles](#pragmatic-development-principles) for real-world guidance
   - Review detailed patterns in `${CLAUDE_PLUGIN_ROOT}/references/` (see pointers below)

3. **Manual Agent Orchestration**
   - Use individual agents for specific tasks
   - See [Agent Orchestration](#agent-orchestration) section for coordination patterns
   - Refer to `${CLAUDE_PLUGIN_ROOT}/references/agent-routing.md` for agent selection guidance

**New to the toolkit?** Start with the `aet-pipeline` skill for guided multi-agent execution.

---

## Core Principles

1. **Kotlin-First Development** - Modern Kotlin features, coroutines, Flow, extension functions
2. **Reactive Architecture** - Unidirectional data flow, StateFlow/Flow throughout
3. **Offline-First** - Local database as source of truth with remote sync
4. **Modular Design** - Feature modules with clear boundaries and dependency rules
5. **Testability by Design** - Constructor injection, test doubles (no mocking)
6. **Type Safety** - Sealed interfaces, value objects, compile-time verification
7. **Convention Over Configuration** - Gradle convention plugins for standardization

For detailed architecture, DI, module organization, and Kotlin patterns, read `${CLAUDE_PLUGIN_ROOT}/references/architecture-patterns.md`.

For detailed data layer, persistence, networking, and sync patterns, read `${CLAUDE_PLUGIN_ROOT}/references/data-layer-patterns.md`.

For detailed Compose, navigation, and UI implementation patterns, read `${CLAUDE_PLUGIN_ROOT}/references/ui-patterns.md`.

For detailed testing strategy, test doubles, and coverage guidance, read `${CLAUDE_PLUGIN_ROOT}/references/testing-patterns.md`.

For detailed security architecture and hardening guidance, see the Security Architecture section in `${CLAUDE_PLUGIN_ROOT}/references/architecture-patterns.md`.

For detailed performance benchmarks and monitoring thresholds, read `${CLAUDE_PLUGIN_ROOT}/references/performance-targets.md`.

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

See `${CLAUDE_PLUGIN_ROOT}/references/pragmatic-examples.md` for Good/Bad code examples demonstrating these principles.

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

**See also:** `${CLAUDE_PLUGIN_ROOT}/references/conflict-resolution.md` for decision trees and edge cases.

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

### Pipeline Work

Multi-agent pipeline work → `/aet-pipeline` (pipeline types, execution protocol, parallel dispatch rules, error recovery; the handoff contract is enforced by its validator — do not hand-maintain section lists here). Companions: `/aet-status` (progress + recovery), `/aet-check` (pattern detection).

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
- Target SDK: latest stable
- Kotlin, AGP, Compose BOM: latest stable releases — verify current versions against the project's version catalog rather than pinning here

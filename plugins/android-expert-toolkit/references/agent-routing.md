# Agent Routing Decision Matrix

## When to use

Read this reference when deciding which android-expert agent to invoke for a given request, or when building orchestration logic that routes between agents. Skip when the agent has already been selected.

## Quick Decision Tree

```
User Request
    |
    +-- Architecture keywords? --> android-architect
    |   (design, architecture, decision, assess, review, pattern choice)
    |
    +-- Implementation keywords? --> android-developer
    |   (implement, build, create, code, feature, ViewModel, repository)
    |
    +-- Testing keywords? --> android-testing-specialist
    |   (test, coverage, verify, test double, unit test)
    |
    +-- UI keywords? --> compose-expert
    |   (UI, Compose, screen, layout, Material 3, animation)
    |
    +-- Build keywords? --> gradle-build-engineer
        (build, Gradle, dependency, module, convention plugin)
```

## Agent Profiles

### android-architect (Opus Model)
**When to Use:**
- Designing new features or modules from scratch
- Evaluating architectural approaches or patterns
- Making framework/pattern decisions (Hilt vs Koin, MVVM vs MVI)
- Reviewing existing architecture for issues or improvements
- Planning multi-phase projects or migrations
- Resolving architectural conflicts or tech debt
- **Using Decision Council Protocol for major decisions**

**Trigger Keywords:**
`design`, `architecture`, `module structure`, `data flow`, `planning`, `assess`, `review`, `decision`, `pattern choice`, `evaluate`, `should we use`

**Example Requests:**
- "Design the module structure for a social feed feature"
- "Should we use Hilt or Koin for dependency injection?"
- "Review the current repository pattern for issues"
- "Evaluate whether to migrate from LiveData to StateFlow"
- "Design the data flow for offline-first sync"

**Output:**
- Module structure diagrams
- Data flow documentation
- ADRs (Architecture Decision Records)
- Pattern recommendations with trade-offs
- Implementation guidelines for team

---

### android-developer (Sonnet Model)
**When to Use:**
- Implementing features (data layer, ViewModel, business logic)
- Writing repositories with offline-first patterns
- Creating ViewModels with StateFlow/LiveData
- Adding business logic and use cases
- Integrating with APIs (Retrofit, GraphQL)
- Bug fixes in implementation layer
- **Applying pragmatic principles (match existing patterns)**

**Trigger Keywords:**
`implement`, `build`, `create`, `code`, `write`, `add`, `feature`, `ViewModel`, `repository`, `data layer`, `API integration`, `fix bug`

**Example Requests:**
- "Implement a user profile screen with ViewModel and repository"
- "Add repository for managing favorites with offline-first"
- "Create ViewModel for items list with StateFlow"
- "Fix the null pointer bug in ProfileViewModel"
- "Integrate with the REST API for posts"

**Output:**
- ViewModels with state management
- Repository implementations (offline-first)
- Data layer code (Room, Retrofit)
- Business logic and use cases
- Hilt/Koin modules for DI

---

### android-testing-specialist (Sonnet Model)
**When to Use:**
- Creating test doubles (fake repositories, test data sources)
- Writing unit tests for ViewModels and repositories
- Improving test coverage (80%+ target for business logic)
- Testing reactive code with Flow and Turbine
- Creating Compose UI tests
- Designing test strategy for features
- **Following "No Mocking" philosophy (test doubles only)**

**Trigger Keywords:**
`test`, `coverage`, `test double`, `verify`, `assertion`, `unit test`, `integration test`, `UI test`, `Turbine`, `fake`

**Example Requests:**
- "Create test doubles for ItemRepository and UserRepository"
- "Write unit tests for ProfileViewModel with 80%+ coverage"
- "Add Flow testing with Turbine for repository streams"
- "Create Compose UI tests for the items screen"
- "Improve test coverage for the data layer"

**Output:**
- Test doubles (interfaces with MutableStateFlow)
- ViewModel unit tests (Given-When-Then)
- Repository unit tests (offline-first logic)
- Compose UI tests (semantic testing)
- Flow tests with Turbine

---

### compose-expert (Sonnet Model)
**When to Use:**
- Implementing Compose UI screens and components
- Creating custom composables
- Adaptive layouts for tablets and foldables
- Material 3 design system implementation
- Performance optimization (recomposition, LazyList)
- Accessibility improvements (semantics, screen readers)
- **View system interoperability (ComposeView, AndroidView)**

**Trigger Keywords:**
`UI`, `Compose`, `screen`, `layout`, `Material 3`, `animation`, `adaptive`, `responsive`, `accessibility`, `custom component`

**Example Requests:**
- "Implement a responsive items list screen with Compose"
- "Create a custom bottom sheet with Material 3 components"
- "Add accessibility support to the profile screen"
- "Optimize recomposition for the feed screen"
- "Create adaptive UI for tablets (master-detail pattern)"

**Output:**
- Route/Screen separated composables
- Material 3 UI components
- Adaptive layouts with WindowSizeClass
- Accessibility annotations (semantics)
- Performance-optimized composables

---

### gradle-build-engineer (Sonnet Model)
**When to Use:**
- Setting up new modules and build configuration
- Managing dependencies and version catalog
- Creating convention plugins for build standardization
- Build performance optimization
- Multi-module project configuration
- Version updates and dependency management

**Trigger Keywords:**
`build`, `Gradle`, `dependency`, `module setup`, `convention plugin`, `version catalog`, `build performance`, `multi-module`

**Example Requests:**
- "Set up convention plugins for feature modules"
- "Add Room dependency to the database module"
- "Create a new feature module with standard build config"
- "Optimize build performance (configuration cache)"
- "Update dependencies in the version catalog"

**Output:**
- Convention plugin implementations
- Module build.gradle.kts files
- Version catalog entries
- Build performance configurations
- Gradle settings updates

---

## Pipeline-Based Orchestration

The Android Expert Toolkit uses automated pipeline orchestration to coordinate agent workflows. Instead of manually sequencing agents, Claude Code triggers predefined pipelines that execute agent sequences with validation checkpoints and handoff artifacts.

**Key Benefits:**
- Consistent agent coordination patterns
- Automatic validation of handoff artifacts
- Built-in error recovery protocols
- Dependency management between pipeline stages
- Reduced manual orchestration overhead

---

## Triggering Pipelines

Use `/aet-pipeline` command to trigger automated orchestration.

| Request Pattern | Pipeline Type | Command |
|----------------|---------------|---------|
| "Build a [feature] feature" | feature-build | `/aet-pipeline feature-build` |
| "Design/review [architecture]" | architecture-review | `/aet-pipeline architecture-review` |
| "Migrate [pattern] to [pattern]" | migration | `/aet-pipeline migration` |
| "Redesign [screen] UI" | ui-redesign | `/aet-pipeline ui-redesign` |
| "Optimize build performance" | build-optimization | `/aet-pipeline build-optimization` |

**Manual Execution:**
For non-pipeline workflows or custom sequences, select agents directly using the routing matrix above.

---

## Pipeline Execution Protocol

When a pipeline is triggered, Claude Code follows this 7-step execution protocol:

1. **Pipeline Selection**: Identify the appropriate pipeline type based on the user's request
2. **Context Gathering**: Collect all necessary context (existing code, architecture docs, constraints)
3. **Agent Dispatch**: Execute agents in pipeline sequence, respecting dependencies
4. **Handoff Creation**: Each agent writes handoff artifacts to `.artifacts/aet/handoffs/` directory
5. **Artifact Validation**: Validate handoff artifacts using `hooks/validate-handoff.py`
6. **Dependency Checking**: Validate inter-agent dependencies using `hooks/validate-dependencies.py`
7. **Error Recovery**: If validation fails, invoke error recovery protocol (see SKILL.md)

**Validation Gates:**
- Handoff artifacts must pass structural validation (required sections present)
- Dependencies must be satisfied before proceeding to next pipeline stage
- Validation failures trigger error recovery protocols

---

## Handoff Artifact Protocol

**Location:** All handoff artifacts are written to `.artifacts/aet/handoffs/{feature_slug}/` directory with a run timestamp prefix.

**Naming Convention:** `{run_timestamp}-{artifact-name}.md`
- `{run_timestamp}-architecture-blueprint.md` - Architectural decisions and module structure
- `{run_timestamp}-module-setup.md` - Build configuration and module creation
- `{run_timestamp}-implementation-report.md` - Implementation completion and interfaces
- `{run_timestamp}-ui-report.md` - Compose UI implementation details
- `{run_timestamp}-test-report.md` - Test coverage and testability feedback

Example: `.artifacts/aet/handoffs/social-feed/2026-02-18-143022-architecture-blueprint.md`

**Structure:** Each handoff artifact must contain required sections validated by `validate-handoff.py`:
- **Summary**: Brief overview of work completed
- **Type-specific sections**: Varies by artifact (see validation hook)
- **Next Steps**: Explicit handoff instructions for downstream agents
- **Constraints**: Any limitations or decisions that constrain future work

**Validation:** Run `hooks/validate-handoff.py <artifact-file>` to verify artifact structure before handoff.

---

## Pipeline Definitions

### Pipeline 1: feature-build
**Trigger:** "Build a [feature name] feature"

**Agent Sequence:**
```
1. android-architect
   - Reads: Existing architecture docs
   - Writes: {run_timestamp}-architecture-blueprint.md
   - Output: Module structure, data flow, UI state design, ADRs
   - Duration: 2-3 hours

2. gradle-build-engineer (parallel with step 3 if no dependencies)
   - Reads: {run_timestamp}-architecture-blueprint.md
   - Writes: {run_timestamp}-module-setup.md
   - Output: Modules created, convention plugins applied, dependencies configured
   - Duration: 30 minutes

3. android-developer
   - Reads: {run_timestamp}-architecture-blueprint.md, {run_timestamp}-module-setup.md
   - Writes: {run_timestamp}-implementation-report.md
   - Output: ViewModels, repositories, data layer implementations
   - Duration: 4-6 hours

4. compose-expert (can run parallel with step 5 if UI and tests are independent)
   - Reads: {run_timestamp}-architecture-blueprint.md, {run_timestamp}-implementation-report.md
   - Writes: {run_timestamp}-ui-report.md
   - Output: Compose UI screens, Route/Screen separation, Material 3 components
   - Duration: 3-4 hours

5. android-testing-specialist
   - Reads: {run_timestamp}-architecture-blueprint.md, {run_timestamp}-implementation-report.md, {run_timestamp}-ui-report.md
   - Writes: {run_timestamp}-test-report.md
   - Output: Test doubles, unit tests, Compose UI tests, coverage report
   - Duration: 2-3 hours
```

**Total Duration:** 2-3 days with parallel execution
**Validation Checkpoints:** After each agent writes handoff artifact

---

### Pipeline 2: architecture-review
**Trigger:** "Review current architecture" or "Assess architectural decisions"

**Agent Sequence:**
```
1. android-architect
   - Reads: Existing codebase, architecture docs
   - Writes: {run_timestamp}-architecture-blueprint.md (assessment mode)
   - Output: Architecture analysis, identified issues, improvement recommendations
   - Duration: 3-4 hours

2. Optional follow-up agents (based on findings):
   - android-developer: If implementation patterns need review
   - android-testing-specialist: If test coverage assessment needed
   - gradle-build-engineer: If build system needs optimization

3. android-architect (synthesis)
   - Reads: All review artifacts
   - Writes: Updated {run_timestamp}-architecture-blueprint.md
   - Output: Prioritized improvement plan, migration strategy
   - Duration: 2-3 hours
```

**Total Duration:** 1-2 days
**Validation Checkpoints:** After architecture-blueprint.md creation

---

### Pipeline 3: migration
**Trigger:** "Migrate [old pattern] to [new pattern]"

**Agent Sequence:**
```
1. android-architect
   - Reads: Existing codebase, migration requirements
   - Writes: {run_timestamp}-architecture-blueprint.md (migration plan)
   - Output: Migration strategy, phases, risk assessment
   - Duration: 2-3 hours

2. android-developer
   - Reads: {run_timestamp}-architecture-blueprint.md
   - Writes: {run_timestamp}-implementation-report.md
   - Output: Migrated implementations, backward compatibility handling
   - Duration: 4-8 hours (depends on scope)

3. android-testing-specialist
   - Reads: {run_timestamp}-implementation-report.md
   - Writes: {run_timestamp}-test-report.md
   - Output: Migration tests, regression tests, coverage verification
   - Duration: 2-3 hours
```

**Total Duration:** 2-4 days depending on migration scope
**Validation Checkpoints:** After each handoff artifact

---

### Pipeline 4: ui-redesign
**Trigger:** "Redesign [screen/feature] UI"

**Agent Sequence:**
```
1. android-architect (optional if data layer unchanged)
   - Reads: Existing UI and data layer
   - Writes: {run_timestamp}-architecture-blueprint.md (UI architecture updates)
   - Output: UI state design, navigation updates, component hierarchy
   - Duration: 1-2 hours

2. compose-expert
   - Reads: {run_timestamp}-architecture-blueprint.md (if exists), {run_timestamp}-implementation-report.md
   - Writes: {run_timestamp}-ui-report.md
   - Output: Redesigned Compose UI, Material 3 updates, accessibility improvements
   - Duration: 4-6 hours

3. android-testing-specialist (optional)
   - Reads: {run_timestamp}-ui-report.md
   - Writes: {run_timestamp}-test-report.md
   - Output: Updated Compose UI tests, accessibility tests, screenshot tests
   - Duration: 1-2 hours
```

**Total Duration:** 1 day
**Validation Checkpoints:** After ui-report.md creation

---

### Pipeline 5: build-optimization
**Trigger:** "Optimize build performance" or "Improve build times"

**Agent Sequence:**
```
1. android-architect
   - Reads: Current build configuration, performance metrics
   - Writes: {run_timestamp}-architecture-blueprint.md (build optimization plan)
   - Output: Build performance targets, optimization strategy
   - Duration: 1-2 hours

2. gradle-build-engineer
   - Reads: {run_timestamp}-architecture-blueprint.md
   - Writes: {run_timestamp}-module-setup.md
   - Output: Optimized build configuration, convention plugins, configuration cache
   - Duration: 2-3 hours
```

**Total Duration:** Half day
**Validation Checkpoints:** After module-setup.md creation

---

### Pipeline 6: test
**Trigger:** "Add tests for [module]" or "Improve test coverage"

**Agent Sequence:**
```
1. android-testing-specialist
   - Reads: Existing source code directly (no handoff prerequisite)
   - Writes: {run_timestamp}-test-report.md
   - Output: Test doubles, unit tests, coverage report
   - Duration: 2-3 hours
```

**Total Duration:** 2-3 hours
**Validation Checkpoints:** After test-report.md creation

---

### Pipeline 7: code-review
**Trigger:** "Review [module] code" or "Code review [feature]"

**Agent Sequence:**
```
1. android-architect (review mode)
   - Reads: Existing codebase
   - Writes: {run_timestamp}-code-review-report.md
   - Output: Findings report with severity ratings, recommendations
   - Duration: 1-2 hours
```

**Total Duration:** 1-2 hours
**Validation Checkpoints:** After code-review-report.md creation
**Note:** Architect operates in review mode — produces findings, not blueprints. No follow-up agents.

---

## Parallel Dispatch Rules

Agents can execute in parallel when:
1. **No handoff dependency**: Agent B doesn't need to read Agent A's output
2. **Independent work streams**: Agents work on different modules/layers
3. **Validation passes**: Previous validation checkpoints passed

**Examples of parallel execution:**
- `gradle-build-engineer` + `android-developer` (if module already exists)
- `compose-expert` + `android-testing-specialist` (unit tests only — UI tests wait for compose-expert)
- Multiple review agents in `architecture-review` pipeline

**Parallel dependency graph for `feature-build`:**
```
android-architect
    ├── gradle-build-engineer ──┐
    └── android-developer ──────┤
                                ├── compose-expert ──────────────┐
                                └── android-testing-specialist   │
                                    [unit tests]                 │
                                         └── android-testing-specialist
                                             [UI tests, after compose-expert]
```

**Sequential execution required when:**
- Agent B reads handoff artifact from Agent A
- Validation checkpoint fails (triggers error recovery)
- Architecture decisions must precede implementation
- UI tests require compose-expert output

---

## Error Recovery in Pipelines

When validation fails or agents report issues, the pipeline invokes error recovery protocols:

1. **Validation Failure**: If `validate-handoff.py` fails, pipeline pauses and requests artifact fix
2. **Dependency Failure**: If `validate-dependencies.py` fails, pipeline backtracks to unblock dependency
3. **Agent Handoff Issues**: Agent writes explicit error in handoff artifact triggering remediation

**Error Recovery Protocols:** See android-expert-toolkit SKILL.md "Error Recovery" section for detailed protocols.

---

## Agent Selection FAQ

### Q: Multiple agents could do this. Which should I choose?

**Rule of thumb:**
- If it requires **design decisions** -> Start with architect
- If it's **straightforward implementation** -> Developer
- If it's **purely UI** -> Compose expert
- If you're **unsure** -> Start with architect for assessment

**Example:**
- "Add a delete button to items screen"
  - Simple? -> compose-expert (just UI change)
  - Complex? -> android-developer (if needs ViewModel changes)
  - Very complex? -> android-architect (if changes data flow)

### Q: Should I run agents sequentially or in parallel?

**Run in parallel when:**
- Tasks are independent (review different areas)
- One agent doesn't need the other's output
- Time is critical

**Run sequentially when:**
- One agent's output is input to another
- Architectural decisions must be made first
- Risk of conflicting changes

### Q: How do I know if I need Decision Council Protocol?

**Invoke Decision Council when:**
- Choosing between two valid approaches
- Existing pattern conflicts with best practice
- Framework/pattern decision has long-term impact
- Team is divided on approach
- You need documented justification (ADR)

**Example:**
"Should we use Hilt or Koin?" -> Invoke Decision Council (android-architect)

### Q: Can I skip the architect for small changes?

**Yes, skip architect if:**
- Bug fix with no architectural impact
- UI-only change (no data layer changes)
- Adding test coverage (no implementation changes)
- Dependency updates (no architectural changes)

**No, consult architect if:**
- Creating new modules
- Changing data flow patterns
- Migrating frameworks or patterns
- Making decisions with long-term impact

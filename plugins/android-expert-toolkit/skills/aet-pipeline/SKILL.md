---
name: aet-pipeline
description: "Use when running a multi-agent Android development pipeline end-to-end — feature builds, architecture reviews, migrations, UI redesigns, build optimizations, test backfills, or code reviews. Triggers on 'build a feature', 'review architecture', 'migrate to X', 'redesign UI', 'optimize build', 'add tests', 'code review module'. Not for ad-hoc Android questions (use android-expert)."
argument-hint: "<feature-build|architecture-review|migration|ui-redesign|build-optimization|test|code-review>"
---

# Android Expert Pipeline Orchestration

Automated multi-agent workflows with validation checkpoints and handoff artifacts.

> **Platform notes:** Tool names in this skill use Claude Code primitives (`Agent`, `TaskCreate`, `AskUserQuestion`). Every other runtime maps onto the capability axes in `${CLAUDE_PLUGIN_ROOT}/references/runtime-adapters.md` — dispatch per the preflight's `== Runtime capability ==` profile (Codex, Zcode, pi, Antigravity). On Claude Code the tool names below work as written.

## Pre-flight Context

Run the pre-flight script — all probes parallelize and emit labeled `== section ==` headers:

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-${PLUGIN_ROOT:-${ZCODE_PLUGIN_ROOT:-}}}"
if [ -z "$PLUGIN_ROOT" ]; then
  # Runtimes without a plugin-root env var install into a versioned cache —
  # resolve the newest cached copy (see references/runtime-adapters.md).
  for base in \
    "$HOME/.zcode/cli/plugins/cache"/*/android-expert-toolkit \
    "$HOME/.claude/plugins/cache"/*/android-expert-toolkit \
    "$HOME/.claude/plugins/cache/android-expert-toolkit" \
    "$HOME/.codex/plugins/cache"/*/android-expert-toolkit \
    "$HOME/.codex/plugins/cache/android-expert-toolkit"; do
    [ -d "$base" ] || continue
    latest="$(ls -1 "$base" 2>/dev/null | sort -t. -k1,1n -k2,2n -k3,3n | tail -1)"
    [ -n "$latest" ] && PLUGIN_ROOT="$base/$latest" && break
  done
fi
if [ -z "$PLUGIN_ROOT" ]; then
  echo "ERROR: cannot locate the android-expert-toolkit plugin directory. Tried CLAUDE_PLUGIN_ROOT, PLUGIN_ROOT, ZCODE_PLUGIN_ROOT, and the runtime plugin caches under ~. Set one of those variables to the plugin root and retry." >&2
  exit 1
fi
bash "$PLUGIN_ROOT/skills/aet-pipeline/scripts/preflight.sh"
```

The script collects: settings file, module count, top-level modules, existing pipeline state, active branch, and per-project settings (`android-expert-toolkit.local.md`).

Use the output to skip the project-discovery phase and pass values through to dispatched agents (architect, gradle-build-engineer) so they don't re-scan. If the `Settings file` section reports `NO_SETTINGS_GRADLE`, abort early — pipeline requires a Gradle project.

## Multi-Agent Capability Check

Inspect the actual exposed spawn/continuation tools and schemas first; they override preflight/config hints. The preflight's `== Runtime capability ==` section emits an advisory profile (RUNTIME / SPAWN / TRANSPORT / NOTES — interpret per `${CLAUDE_PLUGIN_ROOT}/references/runtime-adapters.md`):

| Profile | Action |
|---------|--------|
| `SPAWN=registry` or `SPAWN=prompt-embed` | Proceed with the full flow — dispatch per the SPAWN axis (`Agent(subagent_type)` on registry runtimes, `spawn_agent` with the persona embedded on prompt-embed runtimes). |
| `SPAWN=none` | **After tool discovery confirms no spawn tool**, read `${CLAUDE_PLUGIN_ROOT}/references/runtime-fallback.md` and run sequential single-orchestrator dispatch. An exposed working spawn tool overrides this hint. |
| `SPAWN=unknown` | Discover tools and resolve the spawn shape from their schemas; choose fallback only when spawning is unavailable. |

The fallback produces the same pipeline artifacts (`architecture-blueprint.md`, `module-setup.md`, etc.) via sequential persona dispatch by the orchestrating model. Stages run sequentially without independent worker cross-review. The state.json records `dispatch_mode: "single-orchestrator-fallback"` so downstream tooling knows what produced the artifacts.

## Available Pipelines

| Pipeline Type | Purpose | Agents Involved | When to Use |
|---------------|---------|-----------------|-------------|
| `feature-build` | Build complete feature end-to-end | architect → gradle-build-engineer + developer → compose-expert → testing-specialist | "Build a [feature] feature", "Implement [feature] end-to-end" |
| `architecture-review` | Review and assess architecture | architect → (optional follow-ups) → architect (synthesis) | "Review architecture", "Assess decisions", "Analyze codebase" |
| `migration` | Migrate patterns or frameworks | architect → developer → testing-specialist | "Migrate [X] to [Y]", "Refactor [pattern]", "Modernize codebase" |
| `ui-redesign` | Redesign screens or UI | (optional architect) → compose-expert → (optional testing-specialist) | "Redesign [screen] UI", "Update UI to Material 3" |
| `build-optimization` | Optimize build performance | architect → gradle-build-engineer | "Optimize build", "Improve build times", "Set up modules" |
| `test` | Add tests to existing code | testing-specialist only | "Add tests for [module]", "Improve test coverage" |
| `code-review` | Review code for issues | architect (review mode) | "Review [module] code", "Code review [PR/feature]" |

## Flags

| Flag | Description |
|------|-------------|
| `--verbose` | Enable detailed logging to `.artifacts/aet/log.md`. Logs agent dispatch times, validation results, artifact sizes, and error details for each stage. |

## Argument Parsing

Parse the arguments string:
1. Split into tokens. First token = pipeline type, remaining tokens = feature name (joined).
2. If first token is `resume` → jump to Step 0 (Resume Check).
3. If first token is not a valid pipeline type → error: "Unknown pipeline type. Valid: feature-build, architecture-review, migration, ui-redesign, build-optimization, test, code-review"
4. If pipeline type requires a feature name (feature-build, migration, ui-redesign, test, code-review) and none given → prompt the user: "What feature/module should this pipeline target?" (structured-ask runtimes: `AskUserQuestion`; plain-text runtimes: print the question and parse the reply)
5. Extract flags: `--verbose` enables detailed logging.

## Execution Protocol

When a pipeline is triggered, follow this protocol:

### Step 0: Resume Check
**If arguments start with `resume`:**
1. Read `.artifacts/aet/state.json` — abort with error if missing
2. Extract `feature_slug`, `run_timestamp`, `pipeline_type`, `completed_stages`, and `artifacts` from existing state
3. **Do NOT generate a new run_timestamp or feature_slug** — reuse the values from state to preserve artifact continuity
4. Determine the next uncompleted stage from the pipeline sequence
5. Re-validate the last completed artifact before proceeding:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/hooks/validate-handoff.py" <last_completed_artifact_path>
   ```
6. Jump directly to Step 4 (Execute Agent Sequence), starting from the next stage
7. Update `status` back to `in_progress` in state if it was `aborted`

**Otherwise:** Continue with Step 1 below.

### Step 1: Validate Structure
- Verify Android project structure exists (build.gradle.kts or settings.gradle.kts)
- Generate run_timestamp: run `date "+%Y-%m-%d-%H%M%S"` (e.g., `2026-02-18-143022`)
- Derive feature_slug from feature_name: lowercase, spaces to hyphens (e.g., "Social Feed" → `social-feed`). For pipelines without feature_name, use pipeline_type as slug.
- Create `.artifacts/aet/handoffs/{feature_slug}/` directory

### Step 2: Create Pipeline Branch
Create a dedicated branch for pipeline work to enable safe rollback:
```bash
git checkout -b aet/{feature_slug}/{run_timestamp}
```
This isolates all pipeline changes from the main working branch. Store the original branch name in pipeline state for later merge-back.

**Codex App sandbox:** If branch creation fails with a permission error (detached HEAD in a managed worktree), skip the branch step and continue — emit a handoff note at the end describing what would have been committed, and direct the user to the App's "Create branch" / "Hand off to local" controls.

### Step 3: Initialize State
```json
{
  "pipeline_type": "feature-build",
  "feature_name": "Social Feed",
  "feature_slug": "social-feed",
  "run_timestamp": "2026-02-18-143022",
  "original_prompt": "Build a social feed with offline support",
  "pipeline_context": null,
  "started_at": "2026-02-18T14:30:22Z",
  "completed_at": null,
  "status": "in_progress",
  "current_stage": "android-architect",
  "completed_stages": [],
  "artifacts": {}
}
```

`original_prompt`: stored at pipeline start from user's input. `pipeline_context`: populated after android-architect completes — the full Pipeline Context Block (business purpose, key constraints) extracted from the blueprint. Used on resume to reconstruct agent task prompts without re-reading the blueprint.

**State file maintenance:** Update `state.json` inline at each stage transition. The `PostToolUse:Write` hook (`track-progress.py`) is the fast path on Claude and is also wired into Codex via `hooks/hooks-codex.json`, but it only fires on Codex when `[features] hooks = true, plugin_hooks = true` and the user has trusted the hook command. Treat inline updates as the source of truth and the hook as a write-through cache. Hook transactions lock `state.lock` and atomically replace state. Inline orchestrator writes must happen before dispatch or after the entire active batch finishes and all worker tool calls/hooks have completed; do not overwrite state while workers/hooks are still running. On platforms without `fcntl` (including Windows Python), the optional progress cache safely no-ops and inline barrier updates remain required. Read the latest state and preserve fields from every completed stage.

### Step 4: Execute Agent Sequence
Follow pipeline definition order, respecting dependencies:
- Dispatch agents sequentially when handoff dependency exists
- Dispatch agents in parallel when no dependency exists (see Parallel Dispatch)
- Each agent reads handoff artifacts from previous stages
- Each agent writes handoff artifact to `.artifacts/aet/handoffs/{feature_slug}/`
- Orchestrator passes feature_slug and run_timestamp to each agent so they can construct output paths
- **Context budget warning:** If the codebase has >500 source files, instruct agents to reference file paths in handoff artifacts instead of inlining file content. This prevents context window exhaustion in downstream agents.

**Agent dispatch — platform mapping:**

- Registry runtimes (Claude Code, Zcode): `Agent({subagent_type: 'android-expert-toolkit:android-architect', name: 'android-architect', prompt: ...})` — inspect the exposed schema, retain the returned agent ID, and use a unique invocation name when supported. Resume by recorded ID through the available continuation tool; do not assume a reused name reaches the intended agent. With Claude teams enabled, named launches may be teammates and final answers arrive through idle notifications rather than the initial spawn result. No explicit team creation is needed; AET keeps all handoffs through the orchestrator.
- Prompt-embed runtimes (Codex): `spawn_agent(prompt)` — the prompt must include the full agent persona (read from `${CLAUDE_PLUGIN_ROOT}/agents/android-architect.md`, with `${CLAUDE_PLUGIN_ROOT}` rewritten to the resolved root) plus the Pipeline Context Block. There is no `subagent_type` registry. Use the exposed collaboration or CLI namespace and argument schema; collect final notifications/results, run bounded batches and reuse workers when no close tool exists, as specified in runtime-adapters.md.

**Pipeline Context Block (mandatory in every agent task prompt):**

Each agent runs as a clean-slate subagent (Sonnet-class). Compaction may discard conversational context mid-task. To ensure the agent can always recover the "why," include this block verbatim at the top of every agent's task prompt:

```
PIPELINE CONTEXT (carry-forward — do not discard)
Original prompt: "{original user prompt}"
Feature: {feature_name} ({feature_slug})
Business purpose: {1-2 sentence purpose from planner/blueprint Summary}
Key constraints: {top 3 non-negotiable constraints from blueprint}
Pipeline stage: {current_agent} (stage N of M)
Prior artifacts: {comma-separated list of completed artifact paths}
```

The orchestrator constructs this block after android-architect completes (extracting business purpose and constraints from the blueprint's Summary and Constraints sections). For the architect's own dispatch, use only the original prompt and feature name.

**Why:** Sonnet-class models degrade when context compacts away the original intent. This block sits at the top of the task prompt (highest retention priority) and gives every agent enough context to course-correct if handoff artifacts are ambiguous.

**Git Checkpoints (after each agent completes):**
After each agent finishes and its handoff artifact passes validation, create a checkpoint commit:
```bash
git add -A
git commit -m "aet: {agent_name} completed for {feature_slug}

Pipeline: {pipeline_type}
Stage: {agent_name}
Artifact: {run_timestamp}-{artifact_type}.md"
```

This enables:
- Rollback to any stage: `git reset --hard HEAD~1` to undo last agent's changes
- Comparison between stages: `git diff HEAD~1` to see what an agent changed
- Clean merge back: `git merge --squash aet/{feature_slug}/{run_timestamp}` for a single commit

**Codex App sandbox:** If commits are blocked, stage changes with `git add -A` and record the intended commit message in `.artifacts/aet/log.md` instead.

**Dispatch for `feature-build` pipelines:**
After android-architect completes and DP2 is approved, inspect the target modules and required build/source files identified in the blueprint.

- **Existing modules and no setup handoff dependency:** Gradle and developer may run in parallel when their owned files are independent. Dispatch both calls in one orchestrator turn if worker slots permit; follow runtime-adapters.md for completion delivery.
- **New modules, missing required files, or setup handoff dependency:** dispatch gradle-build-engineer first, wait for its final answer, validate `module-setup.md`, then dispatch android-developer with that handoff. Never ask the developer to guess module scaffolding or wait on a live peer.

Wait for both stages and validate both handoffs before proceeding to compose-expert. Record the chosen ordering and prerequisite evidence in state.

#### Stage Dependency Graph (feature-build)

```
android-architect → DP2
    ├─ new/missing setup: gradle-build-engineer → android-developer
    └─ existing, independent: gradle-build-engineer + android-developer
                                  ↓ both handoffs validated
                     compose-expert + testing-specialist [unit tests]
                                  ↓ ui-report validated
                     testing-specialist [UI tests]
```

**Rules:**
- Gradle/developer parallelism requires existing target modules, required files, and no setup handoff dependency; sequential setup is required otherwise.
- compose-expert + testing-specialist (unit tests): parallel after implementation and build setup complete, if available worker slots permit.
- testing-specialist UI tests: sequential after compose-expert (needs ui-report.md).
- Collect final answers and validate handoffs before dispatching any dependent stage; an idle status alone is insufficient.

#### Agent Budget (tool calls)

**Stalled agent detection:** If an agent has made >35 tool calls without producing a handoff artifact, treat as stalled. Trigger DP4 (Error Recovery). Tool-call count is the only budget the orchestrator can observe — there is no per-subagent token telemetry.

### Step 5: Validate Handoffs
After each agent completes, validate handoff artifact:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/validate-handoff.py" .artifacts/aet/handoffs/{feature_slug}/{run_timestamp}-<artifact-file>.md
```

The validator (`${CLAUDE_PLUGIN_ROOT}/hooks/validate-handoff.py`) is the single source of truth for what each artifact must contain — see § Validation below.

### Step 6: Check Dependencies
Before dispatching next agent, validate dependencies:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/validate-dependencies.py" .artifacts/aet/handoffs/{feature_slug}/{run_timestamp}-<artifact-file>.md
```

Dependency validation ensures:
- Referenced files exist
- Module dependencies valid
- Constraints respected by downstream agents

### Step 7: Handle Errors
If validation fails:

**Validation Failure (artifact structure)**:
1. Pause pipeline
2. Request producing agent to fix artifact
3. Re-validate before proceeding

**Dependency Failure (missing files, invalid references)**:
1. Backtrack to unblock dependency
2. Re-run blocking agent if needed
3. Resume pipeline after resolution

**Build/Test Failure (implementation issues)**:
1. Pause pipeline
2. Report failure to user with logs
3. Wait for manual intervention or agent remediation

**Rollback to Checkpoint (git)**:
When an agent writes incorrect code that cannot be auto-fixed:
1. Identify the last good checkpoint: `git log --oneline | head -5`
2. Reset to that checkpoint: `git reset --hard <commit-hash>`
3. Update pipeline state: set `current_stage` back to the reverted stage
4. Re-dispatch the agent with corrected instructions
5. Continue pipeline from that point

**Edit Handoff**:
When the handoff artifact has minor issues that don't require re-running the agent:
1. Pause pipeline
2. User or orchestrator edits the handoff artifact directly
3. Re-validate: `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/validate-handoff.py" <artifact-path>`
4. Resume pipeline if validation passes

**Switch Agent Model**:
When an agent fails repeatedly (3+ auto-fix attempts):
1. Record failure in pipeline state with `model_switch_reason`
2. Re-dispatch the same agent role with a different model tier (e.g., Sonnet to Opus)
3. Pass all previous context plus failure history to the new model
4. Continue pipeline from that stage

### Step 8: Generate Summary

After pipeline completes, generate a summary report, store completion metrics in pipeline state, and offer to squash-merge the pipeline branch. See `${CLAUDE_PLUGIN_ROOT}/templates/pipeline-summary-template.md` for the report template, metrics schema, and merge commands.

## Interactive Decision Points

The pipeline includes 4 interactive decision points (DPs) that involve the user at critical moments. Structured-ask runtimes use `AskUserQuestion`; plain-text runtimes print the question and options as plain text and parse the free-form reply (see `references/runtime-adapters.md` ASK axis).

**Unattended runs (user unavailable):** DP1 takes auto-detect/cached defaults, DP3 matches the majority pattern, DP4 auto-fixes (max 2 retries) then pauses — and DP2 always pauses for approval (never auto-approved). Never choose Abort or Skip-validation autonomously. Record every autonomous choice in `state.json`.

### DP1 — Pipeline Configuration (before agent dispatch)

**When**: Step 4 begins, before dispatching the first agent.

**Skip if**: `android-expert-toolkit.local.md` exists in project root with all values explicitly set (not `auto-detect`).

**Pattern Detection Cache**: Before prompting, check `.artifacts/aet/cache/detected-patterns.json` for a valid cache (see `${CLAUDE_PLUGIN_ROOT}/references/pattern-detection.md` § Pattern Detection Cache). If the cache is fresh, pre-populate auto-detect answers from cached values and log `"pattern_cache_status": "hit"` in pipeline state. If stale or missing, run detection and write the cache, logging `"pattern_cache_status": "miss"` or `"stale"`.

**Question 1** (header: "DI Framework"):
"Which dependency injection framework should the pipeline use?"
- Auto-detect from codebase (Recommended) — Run pattern detection and use 80/20 matrix
- Hilt — Google's official Android DI framework
- Koin — Pure Kotlin, fast builds
- Dagger — Maximum control, KMP compatible

**Question 2** (header: "State Mgmt"):
"Which state management approach should be used?"
- Auto-detect from codebase (Recommended) — Match existing patterns via detection
- StateFlow — Modern Kotlin-first reactive state
- LiveData — Legacy but well-supported

**Question 3** (header: "Skip Stages", multiSelect: true):
"Which pipeline stages should be skipped?"
- Architecture — Skip android-architect stage
- Gradle — Skip gradle-build-engineer stage
- Implementation — Skip android-developer stage
- Testing — Skip android-testing-specialist stage

**Behavior**: Store answers in pipeline state. Pass as constraints to each agent's task description.

### DP2 — Architecture Approval (after architect completes)

**When**: After android-architect writes `architecture-blueprint.md`, before dispatching next agents.

Present a summary of key decisions from the blueprint (module count, DI choice, state management pattern, key ADRs), then ask:

**Question** (header: "Architecture"):
"How should the pipeline proceed with this architecture?"
- Approve and continue (Recommended) — Accept blueprint, dispatch next agents
- Review blueprint in detail — Pause pipeline, let user read full artifact
- Request changes — Describe modifications needed (pipeline pauses for architect revision)
- Abort pipeline — Cancel pipeline execution

**Behavior**:
- **Approve**: Continue to next stage
- **Review**: Print full path to artifact, pause, wait for user to say "continue"
- **Request changes**: Re-invoke android-architect with user's feedback, re-validate, then re-ask DP2
- **Abort**: Set pipeline state to "aborted", clean up

### DP3 — Pattern Conflict (when <80% consistency detected)

**When**: During pattern detection (either in DP1 auto-detect or android-architect analysis), when the 80/20 decision matrix has no clear winner (no pattern reaches 80% threshold).

Present the detection results (e.g., "LiveData: 51%, StateFlow: 49%"), then ask:

**Question** (header: "Conflict"):
"Pattern conflict detected — no clear winner. How should this be resolved?"
- Match majority pattern — Use the pattern with highest percentage
- Use modern alternative — Adopt the modern best-practice pattern
- Invoke Decision Council — Full 3-perspective analysis (Status Quo, Best Practices, Pragmatic)

**Behavior**:
- **Match majority**: Use highest-percentage pattern, document tech debt
- **Modern alternative**: Use best-practice pattern, note migration context
- **Decision Council**: android-architect runs Decision Council Protocol, writes ADR, then re-asks DP2 with the decision included

### DP4 — Error Recovery (on validation/build/test failure)

**When**: Any validation failure (handoff validation, dependency validation, build failure, test failure) during pipeline execution. Replaces the current silent "pause" behavior.

Present the error details (which validation failed, error message, affected stage), then ask:

**Question** (header: "Recovery"):
"Pipeline error: [error summary]. How should recovery proceed?"
- Auto-fix: re-run agent with fix instructions (Recommended) — Re-invoke the producing agent with error context
- Manual fix: pause for user edits — Pause pipeline, user fixes manually, then invoke with `resume`
- Skip validation: continue anyway — Mark validation as skipped, proceed (not recommended)
- Abort pipeline — Cancel pipeline execution

**Behavior**:
- **Auto-fix**: Re-invoke agent with error feedback (max 2 retries), then fall back to manual fix
- **Manual fix**: Print error details and affected file paths, pause pipeline
- **Skip validation**: Log warning in pipeline state, continue to next stage
- **Abort**: Set pipeline state to "aborted"

### Settings Integration

When `android-expert-toolkit.local.md` exists in the project root:
1. Read YAML frontmatter at pipeline start (Step 1)
2. Use settings as defaults for DP1 prompts
3. If ALL settings are explicitly set (no `auto-detect` values, no empty `skip_stages`), skip DP1 entirely
4. Settings do NOT skip DP2, DP3, or DP4 — those always require user input

## Handoff Artifact Protocol

### Artifact Types

| Producing Agent | Artifact Name | Filename |
|-----------------|---------------|----------|
| android-architect | Architecture Blueprint | `architecture-blueprint.md` |
| gradle-build-engineer | Module Setup Report | `module-setup.md` |
| android-developer | Implementation Report | `implementation-report.md` |
| compose-expert | UI Report | `ui-report.md` |
| android-testing-specialist | Test Report | `test-report.md` |
| android-architect | Code Review Report | `code-review-report.md` |

### Validation

Required sections per artifact type are defined in `${CLAUDE_PLUGIN_ROOT}/hooks/validate-handoff.py` (REQUIRED_SECTIONS dict) — that is the source of truth. Templates in `${CLAUDE_PLUGIN_ROOT}/templates/` show the expected structure. Do not maintain a separate list here.

## Progress Tracking

Pipeline state stored in `.artifacts/aet/state.json`:

```json
{
  "pipeline_type": "feature-build",
  "feature_name": "Social Feed",
  "feature_slug": "social-feed",
  "run_timestamp": "2026-02-18-143022",
  "started_at": "2026-02-18T14:30:22Z",
  "completed_at": null,
  "status": "in_progress",
  "current_stage": "compose-expert",
  "completed_stages": [
    {
      "agent": "android-architect",
      "artifact": ".artifacts/aet/handoffs/social-feed/2026-02-18-143022-architecture-blueprint.md",
      "completed_at": "2026-02-18T15:00:00Z",
      "validation_passed": true
    },
    {
      "agent": "android-developer",
      "artifact": ".artifacts/aet/handoffs/social-feed/2026-02-18-143022-implementation-report.md",
      "completed_at": "2026-02-18T18:00:00Z",
      "validation_passed": true
    }
  ],
  "artifacts": {
    "architecture-blueprint": ".artifacts/aet/handoffs/social-feed/2026-02-18-143022-architecture-blueprint.md",
    "implementation-report": ".artifacts/aet/handoffs/social-feed/2026-02-18-143022-implementation-report.md"
  }
}
```

## Resuming Interrupted Pipelines

Resume by re-invoking with `resume` as the first argument — see Step 0 (Resume Check) above for the full protocol.

### Common Error Scenarios

See `${CLAUDE_PLUGIN_ROOT}/references/pipeline-error-scenarios.md` for detailed recovery walkthroughs covering:
- Incomplete handoff artifact (missing sections)
- Build failure after implementation (compilation errors)
- Test failures after implementation (assertion mismatches)
- Pattern conflict detected (no 80% winner)
- User constraint violation (blueprint vs requirements mismatch)

## Common Rationalizations

| Rationalization | Reality |
|-----------------|---------|
| "Validation is slowing the pipeline, skip it" | Validation catches issues when they're cheap to fix. Skipping it pushes problems downstream where they cost 3x more to debug. |
| "The handoff artifact is close enough" | "Close enough" handoffs produce ambiguous downstream work. 5 minutes fixing the artifact saves an hour re-running the agent. |
| "I'll run the agents sequentially, it's simpler" | Parallel dispatch is valid only for existing modules with independent files and no setup prerequisite. New module setup must finish before implementation; worker limits can also require sequential dispatch. |
| "The architect's blueprint needs adjustments, I'll tweak it in the developer stage" | Scope violation. Developers implement the blueprint — they don't redesign it. Escalate to the architect. |
| "Auto-fix failed twice, but one more try should work" | Max 2 retries. After that, escalate to user (DP4). Infinite retry loops waste tokens and mask root causes. |
| "This is a simple feature, skip DP2 architecture approval" | DP2 always requires user input. Simple features still have surprising architectural implications. |

## Red Flags

- Dispatching agents without Pipeline Context Block in the task prompt
- Skipping handoff validation between stages
- Dispatching android-developer before required module setup is available and validated
- Agent exceeding 35 tool calls without producing a handoff artifact (stalled)
- Proceeding after validation failure without DP4 recovery decision
- Not creating git checkpoints after each stage (Codex App sandbox exempt — see notes above)
- Agent writing code outside its scope boundaries (architect writing implementation, developer writing tests)

## Verification

After pipeline completion, confirm:

- [ ] Every stage produced a validated handoff artifact
- [ ] Dispatch ordering respected prerequisites and available worker slots
- [ ] Git checkpoints exist for each completed stage (or sandbox-handoff note if Codex App)
- [ ] Pipeline summary generated with metrics
- [ ] No scope violations (each agent stayed within boundaries)
- [ ] Pipeline state file reflects accurate completion status

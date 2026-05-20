---
name: aet-status
description: "Use when checking on an Android Expert Toolkit pipeline run — show progress, completed stages, generated artifacts, timing, and recovery options. Trigger on 'pipeline status', 'aet status', 'what's running', 'where are we in the pipeline', 'show pipeline progress'."
argument-hint: "(no arguments)"
---

# Android Expert Pipeline Status

Read `.artifacts/aet/state.json` and display the current pipeline status with actionable options.

> **Platform notes:** This skill references `AskUserQuestion` for the action menu — on Codex, print the options as plain text and parse the user's reply. See `references/codex-tools.md`. The state file is normally updated inline by `aet-pipeline` (the `track-progress.py` hook is a write-through cache that fires on Claude always and on Codex only when `[features] hooks = true, plugin_hooks = true` and the user has trusted the hook). When `state.json` is stale or missing — e.g. hooks disabled on Codex, or stage written before inline update — fall back to deriving stage progress from the handoff directory.

## Pre-flight Context

Run the pre-flight script — all probes parallelize and emit labeled `== section ==` headers:

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-${PLUGIN_ROOT:-}}"
bash "$PLUGIN_ROOT/skills/aet-status/scripts/preflight.sh"
```

The script collects: state file content, handoff directory listing, recent pipeline commits, active branch, and the five most-recent handoff artifacts by mtime.

Use the output to skip the initial Read steps below. If the `State file` section reports `NO_STATE_FILE` and `Handoff directories` reports `NO_HANDOFFS`, jump straight to Step 6 (Feature History). If `NO_STATE_FILE` but artifacts exist, run the filesystem fallback (Step 1b) to reconstruct stage status from the mtime listing.

## Execution

### 1. Read State File

Read `.artifacts/aet/state.json` from the project root.

**If file does not exist**: Run filesystem fallback (Step 1b) before declaring no active pipeline. Then continue to Step 6 (Feature History).

**If file exists**: Continue with Step 2.

### 1b. Filesystem Fallback (Codex-safe)

If `state.json` is missing or older than the most recent handoff artifact, derive stage status from the filesystem:

1. List subdirectories under `.artifacts/aet/handoffs/`. Each subdirectory is a `feature_slug`.
2. For each subdirectory, list files matching `<run_timestamp>-*.md`. Group by `run_timestamp` prefix.
3. The newest `run_timestamp` group is the active or most-recent pipeline.
4. Map artifact filenames back to stage names:
   - `architecture-blueprint.md` → `android-architect`
   - `module-setup.md` → `gradle-build-engineer`
   - `implementation-report.md` → `android-developer`
   - `ui-report.md` → `compose-expert`
   - `test-report.md` → `android-testing-specialist`
   - `code-review-report.md` → `android-architect` (review mode)
5. Build a synthetic state record from the discovered artifacts and proceed with Step 2.
6. If no handoff directory exists either, display "No active pipeline. Start one with the `aet-pipeline` skill." and continue to Step 6.

### 2. Parse State

Extract from the state JSON:
- `pipeline_type` — type of pipeline
- `feature_name` — feature being built (may be null)
- `started_at` — when pipeline started
- `status` — current status (in_progress, completed, aborted)
- `steps` or `completed_stages` — array of stage completion records
- `artifacts` — map of artifact name to file path
- `current_stage` or `current_step` — what's currently running

### 3. Calculate Progress

Determine:
- Total stages for this pipeline type
- Completed stages (count of steps with status "completed")
- Current/in-progress stage
- Pending stages (not yet started)
- Elapsed time since `started_at`

Pipeline stage counts:
- `feature-build`: 5 stages (architect → gradle → developer → compose → testing)
- `architecture-review`: 1-3 stages (architect, optional follow-ups)
- `migration`: 3 stages (architect → developer → testing)
- `ui-redesign`: 2-3 stages (optional architect → compose → optional testing)
- `build-optimization`: 2 stages (architect → gradle)
- `test`: 1 stage (testing-specialist)
- `code-review`: 1 stage (architect in review mode)

### 4. Display Status

Format output as:

```
## Pipeline Status

**Type**: feature-build
**Feature**: Social Feed
**Started**: 2026-02-18 10:30 UTC
**Elapsed**: 1h 45m
**Status**: in_progress

### Stages
- [x] android-architect (completed 10:45)
      → .artifacts/aet/handoffs/social-feed/2026-02-18-103000-architecture-blueprint.md
- [x] gradle-build-engineer (completed 11:15)
      → .artifacts/aet/handoffs/social-feed/2026-02-18-103000-module-setup.md
- [ ] **android-developer** ← current
- [ ] compose-expert
- [ ] android-testing-specialist

### Artifacts Created
| Artifact | Path | Lines | Validated |
|----------|------|-------|-----------|
| architecture-blueprint.md | .artifacts/aet/handoffs/social-feed/2026-02-18-103000-architecture-blueprint.md | 45 | Yes |
| module-setup.md | .artifacts/aet/handoffs/social-feed/2026-02-18-103000-module-setup.md | 32 | Yes |

### Timing
| Stage | Started | Completed | Duration |
|-------|---------|-----------|----------|
| android-architect | 10:30 | 10:45 | 15m |
| gradle-build-engineer | 10:45 | 11:15 | 30m |
```

When this section is built from the filesystem fallback (Step 1b), mark it `(derived from filesystem — state.json missing or stale)` so the user knows timing fields may be approximations from file mtimes.

### 4b. Pipeline Summary (completed pipelines only)

When status is `completed`, also display metrics from pipeline state:

```
### Pipeline Summary
| Metric | Value |
|--------|-------|
| Total Duration | 1h 15m |
| Stages Completed | 5/5 |
| Artifacts Generated | 5 |
| Total Artifact Size | 25.6 KB |
| Validations Passed | 5/5 |
| Validations Failed | 0 |

### Per-Stage Duration
| Stage | Duration | Artifact Size |
|-------|----------|---------------|
| android-architect | 12m | 4.2 KB |
| gradle-build-engineer | 5m | 2.1 KB |
| android-developer | 18m | 6.8 KB |
| compose-expert | 15m | 5.4 KB |
| android-testing-specialist | 10m | 7.1 KB |
```

Read metrics from `stage_durations`, `artifact_sizes`, and `validation_counts` in pipeline state.
If these fields are not present (older state files or filesystem-derived state), skip this section.

### 5. Offer Actions

After displaying status, offer context-appropriate actions (Claude: `AskUserQuestion`; Codex: print options and parse free-form reply):

**If status is `in_progress`**:

Question (header: "Action"):
"Pipeline is in progress. What would you like to do?"
- Continue pipeline (Recommended) — Resume from current stage
- View artifact — Read a specific handoff artifact
- Re-run current stage — Re-dispatch the current agent
- Abort pipeline — Cancel pipeline execution

**If status is `completed`**:

Question (header: "Action"):
"Pipeline completed successfully. What would you like to do?"
- View summary — Display the pipeline completion summary
- View artifact — Read a specific handoff artifact
- Start new pipeline — Begin a new pipeline run
- Clean up state — Remove the state file

**If status is `aborted` or has errors**:

Question (header: "Recovery"):
"Pipeline was interrupted. How should recovery proceed?"
- Resume from last checkpoint (Recommended) — Re-validate last successful artifact, continue from next stage
- Re-run failed stage — Re-dispatch the agent that failed
- Revert to checkpoint — Roll back to last successful git checkpoint, re-run from there
- Edit handoff — Manually fix the last handoff artifact, then re-validate and continue
- Restart pipeline — Start over from the beginning
- Clean up state — Remove state file and start fresh

**When showing recovery options, also display:**
```
### Last Successful Checkpoint
- Stage: gradle-build-engineer
- Artifact: .artifacts/aet/handoffs/social-feed/2026-02-18-103000-module-setup.md
- Git commit: abc1234 (aet: gradle-build-engineer completed for social-feed)
- Validated: Yes

### Failure Details
- Failed stage: android-developer
- Error: Validation failed — missing "Constraints" section
- Attempts: 2/2 auto-fix attempts exhausted
```

### 6. Feature History

Always display this section — even when no active pipeline exists.

Scan `.artifacts/aet/handoffs/` for feature directories:

```bash
ls .artifacts/aet/handoffs/
```

For each subdirectory found, list its artifacts sorted by name (timestamp prefix ensures chronological order):

```
## Past Runs

social-feed/
  2026-02-18-143022 — architecture-blueprint, module-setup, implementation-report, ui-report, test-report ✓
  2026-02-17-091500 — architecture-blueprint, module-setup (incomplete)

settings-screen/
  2026-02-19-090000 — architecture-blueprint, ui-report, test-report ✓
```

**Format per feature directory:**
- Group runs by `run_timestamp` prefix
- List artifact types present (strip timestamp prefix and `.md` extension)
- Mark a run `✓` if all expected artifacts for the pipeline type are present
- Mark `(incomplete)` if some artifacts are missing

**If `.artifacts/aet/handoffs/` does not exist or is empty**: Skip this section silently.

### 7. Execute Action

Based on user's choice:
- **Continue/Resume**: Read state, dispatch next agent in sequence (invoke the `aet-pipeline` skill with `resume`)
- **View artifact**: Ask which artifact, then read and display it
- **Re-run stage**: Re-dispatch the specified agent
- **Abort/Clean up**: Delete `.artifacts/aet/state.json`
- **Start new**: Delete state file, prompt for new pipeline parameters

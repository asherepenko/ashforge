## When to use

Read this when the `aet-pipeline` skill's preflight reports `== Codex multi_agent capability ==` value of `DISABLED` or `NO_CONFIG`. The Codex `multi_agent` feature flag is off, so `spawn_agent` / `wait_agent` / `close_agent` are unavailable. Do NOT attempt parallel agent dispatch — the tool calls will fail at the runtime layer.

This file documents the sequential-orchestrator fallback. Claude users never hit this path (Claude has no equivalent gate). Codex users with `multi_agent = true` use the normal flow in `skills/aet-pipeline/SKILL.md`.

## Capability Decision Matrix

| Preflight value | Mode | Source |
|---|---|---|
| `NOT_CODEX` | Full flow (Claude path) | Claude Code; parallel `Agent` always available |
| `ENABLED` | Full flow (Codex path) | `multi_agent = true` in `~/.codex/config.toml` |
| `DISABLED` | This fallback | `multi_agent` set false or unset |
| `NO_CONFIG` | This fallback + warning | `~/.codex/config.toml` not found |

## Fallback Behavior

### Step 1 — Announce the mode

Tell the user explicitly at the start of execution:

```
⚠ Codex `multi_agent` feature is disabled. Falling back to sequential single-orchestrator dispatch.
  Parallel agent fan-out is unavailable, so this pipeline run will be slower than normal
  (no parallel gradle/developer stage). Debate-like cross-validation between agents is
  also unavailable — each stage's output is consumed by the orchestrator and not
  cross-reviewed by peers.

  To enable the full multi-agent path, add to ~/.codex/config.toml:
      [features]
      multi_agent = true
  Then restart Codex.
```

### Step 2 — Sequential agent dispatch

Replace every `spawn_agent` callsite from `skills/aet-pipeline/SKILL.md` with an inline persona walk by the orchestrating model:

1. **For each stage in pipeline order** (per the stage graph in `SKILL.md` Step 4):
   - Read the corresponding `agents/<agent-name>.md` persona file
   - Adopt the persona's specialty lens and checklists
   - Read prior-stage handoff artifacts (per the dependency graph)
   - Produce the stage's deliverable artifact under `.artifacts/aet/handoffs/{feature_slug}/{run_timestamp}-<artifact>.md`
   - Update `.artifacts/aet/state.json` inline (don't rely on the PostToolUse hook — it can still fire on Codex but the apply_patch branch no-ops)
   - Run `python hooks/validate-handoff.py <artifact>` to validate

2. **No parallel dispatch.** The normal full mode dispatches gradle-build-engineer and android-developer in parallel after architect completes. In fallback mode, run them sequentially:
   - gradle-build-engineer → completes → handoff
   - android-developer → reads architecture-blueprint AND module-setup → completes → handoff

3. **Decision points stay interactive.** DP1-DP4 still use the same `AskUserQuestion`-equivalent plain-prompt pattern. The user-gated decisions don't depend on parallel dispatch.

4. **Token budget consideration.** Sequential dispatch keeps everything in one model context. If the project exceeds 500 source files, reference handoff artifact paths instead of inlining content — the orchestrator's context window is the bottleneck now.

### Step 3 — Mark the pipeline state

In the final `.artifacts/aet/state.json` and the Step 8 summary, include:

```json
{
  "dispatch_mode": "single-orchestrator-fallback",
  "fallback_reason": "codex_multi_agent_disabled",
  "fidelity_note": "Stages produced sequentially by the orchestrator; no peer cross-review."
}
```

And in the human-readable summary:

```
> Run mode: Single-orchestrator fallback (Codex multi_agent disabled)
> Stages were produced sequentially. Cross-stage validation was performed by the
> orchestrator only — there is no peer review from independent agent instances.
```

### Step 4 — Git checkpoints

Still create per-stage commits (`aet: {agent_name} completed for {feature_slug}` etc.) — single-orchestrator mode doesn't change rollback semantics. If the Codex App sandbox blocks commits, skip them per the normal sandbox handling in `SKILL.md`.

## What does NOT change

- Pipeline state schema (`.artifacts/aet/state.json` structure)
- Handoff artifact format (`templates/*-template.md` still applies)
- `hooks/validate-handoff.py` and `hooks/validate-dependencies.py` still run after each stage
- DP1-DP4 user interaction points
- Stage dependency graph (architect → gradle + developer → compose + testing)
- The `aet-status` skill — it reads filesystem state, agnostic to dispatch mode

## Detection failure cases

- **`NO_CONFIG` (no `~/.codex/config.toml`)** — almost always means the user is on Codex CLI before first config write. Treat as `DISABLED`, but mention in the announcement that the config file is missing.
- **Probe reports `ENABLED` but `spawn_agent` still fails** — the feature flag is on but the runtime hasn't enabled it (Codex version mismatch, flag deprecated, etc.). Surface the tool error directly; don't try to fall back mid-run.

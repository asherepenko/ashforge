## When to use

Read this when the `aet-pipeline` skill's preflight reports `SPAWN=none` in the `== Runtime capability ==` section. No subagent dispatch is available on this runtime — `Agent` / `spawn_agent` / `wait_agent` / `close_agent` calls would fail at the tool layer. Do NOT attempt any spawn.

Typical causes: Codex with `multi_agent = false` (or no `~/.codex/config.toml`), pi without a subagent skill/extension installed. Runtimes with working spawns never hit this file. Codex users with `multi_agent = true` use the normal flow in `skills/aet-pipeline/SKILL.md`.

## Capability Decision Matrix

| Profile | Mode | Source |
|---------|------|--------|
| `SPAWN=registry` | Full flow (parallel `Agent` dispatch) | Claude Code, Zcode |
| `SPAWN=prompt-embed` | Full flow (parallel `spawn_agent` dispatch) | Codex with `multi_agent = true`; subagent-equipped pi |
| `SPAWN=none` | This fallback | Codex `multi_agent` off/missing; pi without a subagent skill |
| `SPAWN=unknown` | Resolve conversationally first (see runtime-adapters.md SPAWN axis) — only fall back if no subagent tool exists | undetected runtimes |

## Fallback Behavior

### Step 1 — Announce the mode

Tell the user explicitly at the start of execution:

```
⚠ No subagent spawning available on this runtime (SPAWN=none). Falling back to
  sequential single-orchestrator dispatch. Parallel agent fan-out is unavailable,
  so this pipeline run will be slower than normal (no parallel gradle/developer
  stage). Cross-validation between agents is also unavailable — each stage's
  output is consumed by the orchestrator and not cross-reviewed by peers.

  Remediation depends on the runtime — e.g. on Codex, add to ~/.codex/config.toml:
      [features]
      multi_agent = true
  then restart. On pi, install a subagent skill/extension.
```

### Step 2 — Sequential agent dispatch

Replace every spawn callsite from `skills/aet-pipeline/SKILL.md` with an inline persona walk by the orchestrating model:

1. **For each stage in pipeline order** (per the stage graph in `SKILL.md` Step 4):
   - Read the corresponding `agents/<agent-name>.md` persona file
   - Adopt the persona's specialty lens and checklists
   - Read prior-stage handoff artifacts (per the dependency graph)
   - Produce the stage's deliverable artifact under `.artifacts/aet/handoffs/{feature_slug}/{run_timestamp}-<artifact>.md`
   - Update `.artifacts/aet/state.json` inline (don't rely on the PostToolUse hook — it may not fire on this runtime)
   - Run `python3 "${PLUGIN_ROOT}/hooks/validate-handoff.py" <artifact>` to validate

2. **No parallel dispatch.** The normal full mode dispatches gradle-build-engineer and android-developer in parallel after architect completes. In fallback mode, run them sequentially:
   - gradle-build-engineer → completes → handoff
   - android-developer → reads architecture-blueprint AND module-setup → completes → handoff

3. **Decision points stay interactive.** DP1-DP4 still use the same ask mechanics (structured or plain-text per the ASK axis in `references/runtime-adapters.md`). The user-gated decisions don't depend on parallel dispatch. Unattended runs follow the unattended rule there: DP1 defaults, DP3 majority, DP4 auto-fix-then-pause, DP2 always pauses — never autonomous Abort or Skip-validation.

4. **Context budget consideration.** Sequential dispatch keeps everything in one model context. If the project exceeds 500 source files, reference handoff artifact paths instead of inlining content — the orchestrator's context window is the bottleneck now.

### Step 3 — Mark the pipeline state

In the final `.artifacts/aet/state.json` and the Step 8 summary, include:

```json
{
  "dispatch_mode": "single-orchestrator-fallback",
  "fallback_reason": "spawn_unavailable",
  "runtime_profile": "<RUNTIME value from preflight, e.g. codex / pi / unknown>",
  "fidelity_note": "Stages produced sequentially by the orchestrator; no peer cross-review."
}
```

And in the human-readable summary:

```
> Run mode: Single-orchestrator fallback (no subagent spawning available)
> Stages were produced sequentially. Cross-stage validation was performed by the
> orchestrator only — there is no peer review from independent agent instances.
```

### Step 4 — Git checkpoints

Still create per-stage commits (`aet: {agent_name} completed for {feature_slug}` etc.) — single-orchestrator mode doesn't change rollback semantics. If the runtime's sandbox blocks commits, skip them per the normal sandbox handling in `SKILL.md`.

## What does NOT change

- Pipeline state schema (`.artifacts/aet/state.json` structure)
- Handoff artifact format (`templates/*-template.md` still applies)
- `hooks/validate-handoff.py` and `hooks/validate-dependencies.py` still run after each stage
- DP1-DP4 user interaction points
- Stage dependency graph (architect → gradle + developer → compose + testing)
- The `aet-status` skill — it reads filesystem state, agnostic to dispatch mode

## Detection failure cases

- **Fresh installs with no runtime config** (e.g. no `~/.codex/config.toml`) — typically a first run. Treat as `SPAWN=none`, but mention the missing config in the announcement.
- **Profile reports spawns available but the first spawn still fails** — flag on but runtime lagging (version mismatch, registry not loaded). Surface the tool error directly; don't try to fall back mid-run.

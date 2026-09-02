# Runtime Adapters — Capability Profiles for Council Skills

Canonical cross-runtime scaffolding shared by `council-plan-review` and `council-code-review`. The council was built around Claude Code's agent-team primitives (parallel `Agent`, peer-to-peer `SendMessage`); every other runtime is supported by mapping the same **capability axes**, not by branching on runtime names.

Read the preflight's `== Runtime capability ==` section, then resolve each axis below. If the profile reports `unknown` for an axis, resolve it conversationally with the user ("do you have a subagent tool? does it return results or stay alive?") before spawning anything.

## Contents

- [Capability Axes](#capability-axes) — spawn / transport / progress / ask / root env / hooks / sandbox
- [Known Runtime Profiles](#known-runtime-profiles) — advisory table; detection wins
- [Hub-Mediated Debate](#hub-mediated-debate) — the 3-round fan-out for result-returning runtimes
- [`update_plan` example](#update_plan-example) — plan-tool runtimes
- [`--quick` mode](#--quick-mode-single-round) — single fan-out on every runtime
- [Plugin Root Resolution](#plugin-root-resolution) — works without a plugin-root env var
- [Read-Only Environments](#read-only-environments) — sandboxed runtimes
- [Fallback Verdict Cap](#fallback-verdict-cap) — pointer to runtime-fallback.md
- [What Stays Identical](#what-stays-identical-across-runtimes)

## Capability Axes

### SPAWN — how council members are dispatched

| Value | Dispatch | Used by |
|-------|----------|---------|
| `registry` | `Agent({subagent_type: 'avengers-council:<name>', name: '<name>', prompt: ...})` — personas come from the agent registry; pass `name` so the stage is labelled. Never pass `team_name` (deprecated and ignored). | Claude Code, Zcode |
| `prompt-embed` | `spawn_agent(prompt)` — read `agents/<name>.md` and paste the persona body verbatim above the `REVIEW CONTEXT` block (no `subagent_type` registry exists). **Rewrite every `${CLAUDE_PLUGIN_ROOT}` in the persona text to the resolved plugin root** — member bodies reference `${CLAUDE_PLUGIN_ROOT}/references/*.md`, and the var is not exported to spawned workers on these runtimes. Discard persona frontmatter (`tools:`, `model:` — Claude-only registry metadata). | Codex (`multi_agent = true`), pi (subagent skill/extension installed) |
| `none` | No subagent dispatch available. **Read `${CLAUDE_PLUGIN_ROOT}/references/runtime-fallback.md`** and run the single-orchestrator persona walk. Do NOT attempt any spawn — it fails at the tool layer. | Codex (`multi_agent` off), pi (no subagent skill) |
| `unknown` | Ask the user whether a subagent tool exists before proceeding. | undetected runtimes |

### TRANSPORT — how findings move between members

| Value | Mechanics |
|-------|-----------|
| `stay-alive` | Spawned teammates stay alive; messages are delivered automatically on the team channel. The lead's wire name is `team-lead` (harness-owned — `captain-america` is NOT a routable recipient). Round 1: each member sends its assessment to `team-lead`, then one `SendMessage` per teammate sharing findings (no broadcast recipient exists). Rounds 2–3: the lead DMs each teammate the debate block; members DM each other to challenge. Cleanup: `shutdown_request` per teammate; no team to delete (the session team is implicit — do not call `TeamCreate`/`TeamDelete`). |
| `hub` | Spawns are result-returning: the worker terminates after returning. Round 1 verdicts arrive as tool results (`wait_agent(agent_id)` on Codex; `close_agent(agent_id)` frees slots). There is no peer messaging and no broadcast — the Captain consolidates each round's outputs and re-spawns members for the next round with the consolidated context inlined (see [Hub-Mediated Debate](#hub-mediated-debate)). Cleanup: workers are already terminated; `close_agent` any still in-flight at the timeout boundary. Zcode note: `Agent` results return as tool results; `SendMessage` may resume a completed agent by id for Round 2/3 — use it when available, otherwise re-spawn. |

### PROGRESS — phase tracking

| Value | Tool |
|-------|------|
| `task-list` | `TaskCreate` / `TaskUpdate` (Claude Code) |
| `todo` | `TodoWrite` (Zcode) |
| `plan-tool` | `update_plan` (Codex — see [example](#update_plan-example)) |
| `none` | Skip phase tracking; announce phases in text. |

### ASK — structured questions

| Value | Mechanics |
|-------|-----------|
| `structured` | `AskUserQuestion({questions: [{options: [...]}]})` (Claude Code, Zcode) |
| `plain-text` | Print the question and numbered options as plain text; wait for and parse the free-form reply (Codex, pi, most others). |

### ROOT_ENV — plugin root variable

| Value | Variable |
|-------|----------|
| `CLAUDE_PLUGIN_ROOT` | Claude Code |
| `PLUGIN_ROOT` | Codex |
| `ZCODE_PLUGIN_ROOT` | Zcode (expected; if unset, the [cache-glob fallback](#plugin-root-resolution) resolves the root) |
| none | Use the cache-glob fallback below, or fail fast with instructions. |

`allowed-tools` skill frontmatter is Claude-only — other runtimes inherit whatever the session permits.

### HOOKS — hook event support

| Value | Meaning |
|-------|---------|
| `full` | `hooks/hooks.json` fires as declared (Claude Code). |
| `gated` | Hooks need `[features] hooks = true, plugin_hooks = true` plus per-command user trust; `PreToolUse` is deny-only (Codex). |
| `unverified` | Zcode / Antigravity / pi hook parity not verified — skills never *depend* on hooks; the plan-review hook is Claude-only until verified otherwise. |

The `if [ -f "${CLAUDE_PLUGIN_ROOT}/…" ]` wrapper on every command in `hooks/hooks.json` keeps that manifest a no-op on runtimes that auto-discover it without the variable set. Keep the wrapper on anything added there.

### SANDBOX — git-operation limits

Managed/sandboxed worktrees (Codex App and any runtime that blocks branch creation, commits, or pushes): the review still produces its verdict — writes under `.artifacts/reviews/` work in any sandbox. What is NOT available: post-verdict actions that commit or push ("Apply suggested fixes", "Address findings now" when it would commit), re-reviews needing branch creation, and possibly `gh pr view`/`gh pr diff` without authenticated `gh` + network. Surface the limit explicitly and direct the user to the runtime's native branch-creation / hand-off-to-local controls.

## Known Runtime Profiles

Advisory only — the preflight detection wins over this table.

| Runtime | SPAWN | TRANSPORT | PROGRESS | ASK | Notes |
|---------|-------|-----------|----------|-----|-------|
| claude-code | `registry` | `stay-alive` | `task-list` | `structured` | Reference runtime; `CLAUDE_PLUGIN_ROOT` set. |
| codex | `prompt-embed` | `hub` | `plan-tool` | `plain-text` | Requires `[features] multi_agent = true` in `~/.codex/config.toml`; without it SPAWN=`none`. Hooks gated + trust. |
| zcode | `registry` | `hub` | `todo` | `structured` | Result-returning `Agent` spawns; `SendMessage` resume of completed agents available; `ExitPlanMode` exists, hook parity unverified. |
| pi | `none`* | `hub` | `none`/extension | `plain-text` | *No native subagent tool — SPAWN=`none` unless a subagent skill/extension is installed (then `prompt-embed`). Skills format is compatible; verify spawn availability conversationally. |
| antigravity | `unknown` | `hub` | internal | interactive | Claude Agent Skills standard; custom subagents exist — confirm spawn shape conversationally before dispatch. |

## Hub-Mediated Debate

The 3-round flow stay-alive runtimes get from live teammates + `SendMessage` becomes 3 sequential parallel fan-outs on hub-transport runtimes:

```
Round 1 — Initial Assessment
    Captain assembles REVIEW CONTEXT (standards, codebase audit, domain model)
    spawn × N in parallel, each with: persona + REVIEW CONTEXT + Round 1 instructions
    collect × N → verdicts
    Captain aggregates Round-1 findings into "Round-2 Challenge Context"

Round 2 — Challenge
    spawn × N in parallel, each with: persona + REVIEW CONTEXT + Round-1 findings + Round 2 instructions
    collect × N → challenges
    Captain aggregates into "Round-3 Final Context"

Round 3 — Final Position
    spawn × N in parallel, each with: persona + REVIEW CONTEXT + Round-2 challenges + Round 3 instructions
    collect × N → final verdicts
    Captain applies verdict-rules.md, surfaces verdict
```

**Cost:** ~3× the spawn count vs a stay-alive roster (3 rounds × N members vs N stay-alive). **Fidelity:** preserved — every cross-agent finding flows through the orchestrator's next-round prompt instead of through `SendMessage`.

This cost is exactly what the orchestration protocol's **Mode Selection & Cost-Controlled Degradation** section gates: on a hub-only runtime, a full-mode council spends 3N heavy spawns, and the protocol may autonomously drop to Quick Mode when its three triggers hold.

**Persona embedding:** before each spawn on a `prompt-embed` runtime, Captain reads `agents/<member>.md` and pastes the full persona text into the spawn prompt (with `${CLAUDE_PLUGIN_ROOT}` rewritten to the resolved root — see SPAWN axis). Personas stay a single source of truth across runtimes. (Captain America is never spawned — the orchestrator role is defined in `references/captain-america-orchestrator.md`.)

On `registry` + `hub` runtimes (Zcode): use `Agent({subagent_type: ...})` for dispatch and collect results as tool results — no persona embedding needed, but Rounds 2–3 still flow through the Captain (fresh spawns, or `SendMessage` resume by agent id where supported).

## `update_plan` example

Where the orchestration protocol says "TaskCreate / TaskUpdate", plan-tool runtimes use `update_plan`. Pass the full list of steps each call; mark each step `pending`, `in_progress`, or `completed`.

```javascript
update_plan({
  steps: [
    { label: "Phase 1 — Assemble Council (roster + spawn)",   status: "completed"   },
    { label: "Phase 2 — Round 1 Initial Assessment",          status: "completed"   },
    { label: "Phase 3 — Round 2 Challenge",                   status: "in_progress" },
    { label: "Phase 3 — Round 3 Final Position",              status: "pending"     },
    { label: "Phase 4 — Synthesize Verdict",                  status: "pending"     },
    { label: "Phase 5 — Save Verdict to .artifacts/reviews/", status: "pending"     },
    { label: "Phase 6 — Interactive Follow-up",               status: "pending"     }
  ]
})
```

The plan renders to the user as a checklist. Update it at each phase transition; updates are cheap — call them liberally.

## `--quick` mode (single round)

Every runtime collapses to a single fan-out:

- `registry` runtimes: parallel `Agent({...})` for the 3-member quorum → assessments return → Captain aggregates.
- `prompt-embed` runtimes: parallel `spawn_agent` × 3 → `wait_agent` × 3 → Captain aggregates.

No debate rounds. Same UX everywhere. This is also the shape cost-controlled degraded runs take (see orchestration-protocol.md → Mode Selection).

## Plugin Root Resolution

Skill bodies resolve the plugin root with this chain (order matters — the first hit wins):

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-${PLUGIN_ROOT:-${ZCODE_PLUGIN_ROOT:-}}}"
```

If still empty, fall back to the newest cached copy (runtimes without a plugin-root env var install into a versioned cache):

```bash
for base in \
  "$HOME/.zcode/cli/plugins/cache"/*/avengers-council \
  "$HOME/.claude/plugins/cache"/*/avengers-council \
  "$HOME/.claude/plugins/cache/avengers-council" \
  "$HOME/.codex/plugins/cache"/*/avengers-council \
  "$HOME/.codex/plugins/cache/avengers-council"; do
  [ -d "$base" ] || continue
  latest="$(ls -1 "$base" 2>/dev/null | sort -t. -k1,1n -k2,2n -k3,3n | tail -1)"
  [ -n "$latest" ] && PLUGIN_ROOT="$base/$latest" && break
done
```

Only fail when every option is exhausted — and then say WHICH variables/paths were tried, so the fix is obvious. Note the cached copy may trail the repo source; surface `PLUGIN_ROOT` in preflight output when the fallback resolved it.

## Read-Only Environments

If commits / branch creation are blocked (Codex App sandbox, or any managed worktree): skip git checkpoints or stage-only, emit a handoff describing what would have been committed, and direct the user to the runtime's native "Create branch" / "Hand off to local" controls. The verdict artifact under `.artifacts/reviews/` is always writable. See the SANDBOX axis above.

## Fallback Verdict Cap

When SPAWN=`none`, the single-orchestrator fallback skips debate rounds and caps the verdict at APPROVED WITH CONDITIONS (lower fidelity — no independent-instance challenge dynamic, no Black Widow security veto from a separate agent). Full behavior: `references/runtime-fallback.md`.

## What Stays Identical Across Runtimes

- All persona files in `agents/`
- `references/verdict-rules.md`, `shared-principles.md`, `red-lines.md`, `member-registry.md`, `standards-protocol.md`, and `assets/verdict-template.md`
- Domain-scoring math (1-10 per member, aggregate < 5.0 → NEEDS REVISION)
- Black Widow's veto on unmitigated CRITICAL security findings
- Optional-member auto-join based on topic-tag matching (decided pre-spawn by the orchestrator)
- Captain America always played by the orchestrating model — never spawned (on stay-alive runtimes the orchestrator's wire name is `team-lead`; on hub runtimes there is no wire name at all)
- Verdict save path under `.artifacts/reviews/` and the Run Mode disclosure in `assets/verdict-template.md`

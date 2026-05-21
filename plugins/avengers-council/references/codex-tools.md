## When to use

Read this when running the `council-plan-review` or `council-code-review` skill on Codex CLI / Codex App. The council was built around Claude Code's agent-team primitives (`TeamCreate`, parallel `Agent`, peer-to-peer `SendMessage`); Codex lacks the team primitive and peer-to-peer comms, so debate is restructured as hub-mediated context propagation through the orchestrator (Captain America).

The Claude path is **unchanged** — team primitives still drive Round-1 broadcast and Round-2/3 DMs. This file documents only the Codex substitutions.

## Tool Mapping

| Council primitive | Claude Code | Codex equivalent |
|---|---|---|
| Team scope | `TeamCreate({team_name: 'avengers-council'})` then `TeamDelete` at end | **Skip** — Codex has no team primitive. Concurrency = parallel `spawn_agent` calls in one turn. |
| Spawn a council member | `Agent({subagent_type: 'avengers-council:<name>', team_name: 'avengers-council', prompt: ...})` | `spawn_agent(prompt)` — embed the persona text from `agents/<name>.md` verbatim into the prompt (Codex has no `subagent_type` registry). |
| Spawn whole active roster in parallel | Multiple `Agent({...})` calls in one orchestrator message | Multiple `spawn_agent` calls in one turn |
| Read council member's verdict | Tool result returned inline | `wait_agent(agent_id)` returns the result; `close_agent(agent_id)` frees the slot |
| Peer-to-peer broadcast (Round 1) | `SendMessage({type: 'broadcast', content: ...})` between teammates | **No equivalent.** Captain captures each agent's Round-1 verdict via `wait_agent`, consolidates them, and re-issues a Round-2 `spawn_agent` to each member with the consolidated context inlined. |
| Peer-to-peer DM (Round 2/3 challenge) | `SendMessage({to: 'iron-man', content: ...})` | **No equivalent.** Captain assembles per-recipient "challenge" prompts and includes them in the next round's `spawn_agent` call. |
| Round-tracking task list | `TaskCreate` / `TaskUpdate` (optional, for progress) | `update_plan` |
| Post-verdict action menu | `AskUserQuestion({questions: [{options: [...]}]})` | Print the question and options as plain text and wait for the user's reply. Parse free-form answer. |
| Plan-mode entry hook | `PreToolUse:ExitPlanMode` (Claude `hooks/council-plan-hook.sh`) | **Claude-only.** Codex has no `ExitPlanMode` tool. Skip the hook — the user invokes the skill explicitly. |
| `@references/foo.md` mention in skill/agent text | Claude @-mention — auto-resolves and inlines the file content | No @-mention syntax. Treat any `@references/<file>.md` reference as a `Read` instruction — load the file at that relative path before continuing. The skill bodies use this for `references/orchestration-protocol.md`, `references/codex-tools.md`, `references/codex-fallback.md`, `references/red-lines.md`, `references/verdict-rules.md`, etc. |

## Hub-mediated debate (Codex full mode)

The 3-round flow Claude runs via stay-alive agents + `SendMessage` becomes 3 sequential parallel fan-outs on Codex:

```
Round 1 — Initial Assessment
    Captain assembles REVIEW CONTEXT (standards, codebase audit, domain model)
    spawn_agent × N in parallel, each with: persona + REVIEW CONTEXT + Round 1 instructions
    wait_agent × N → collect verdicts
    Captain aggregates Round-1 findings into "Round-2 Challenge Context"

Round 2 — Challenge
    spawn_agent × N in parallel, each with: persona + REVIEW CONTEXT + Round-1 findings + Round 2 instructions
    wait_agent × N → collect challenges
    Captain aggregates into "Round-3 Final Context"

Round 3 — Final Position
    spawn_agent × N in parallel, each with: persona + REVIEW CONTEXT + Round 2 challenges + Round 3 instructions
    wait_agent × N → collect final verdicts
    Captain applies verdict-rules.md, surfaces verdict
```

**Cost:** ~3× the spawn count vs Claude's single-team approach. **Fidelity:** preserved — every cross-agent finding flows through the orchestrator's next-round prompt instead of through SendMessage.

**Persona embedding:** before each `spawn_agent`, Captain reads `agents/<member>.md` and pastes the full persona text (omitting the "REFERENCE ONLY" header for `captain-america`) into the spawn prompt. This keeps personas a single source of truth across platforms — no duplication.

## `--quick` mode (single round)

Both platforms collapse to a single fan-out:

- Claude: `TeamCreate` → parallel `Agent({...})` for 3-member quorum → each returns assessment → Captain aggregates.
- Codex: parallel `spawn_agent` × 3 → `wait_agent` × 3 → Captain aggregates.

No debate rounds. Same UX on both platforms.

## Codex feature flags

```toml
[features]
hooks = true
plugin_hooks = true
multi_agent = true   # REQUIRED — spawn_agent/wait_agent/close_agent
```

Without `multi_agent`, the skill must fall back to single-orchestrator-perspective review (no fan-out). Detect the capability and warn the user.

## Read-only environment (Codex App sandbox)

If commits / branch creation are blocked, the council can still produce its verdict and write the artifact under `.artifacts/avengers-council/`. Direct the user to use Codex App's "Create branch" / "Hand off to local" controls for any follow-through actions.

## What stays identical across platforms

- All persona files in `agents/`
- `references/verdict-rules.md`, `shared-principles.md`, `red-lines.md`, `member-registry.md`, `standards-protocol.md`, `verdict-template.md`
- Domain-scoring math (1-10 per member, aggregate < 5.0 → NEEDS REVISION)
- Black Widow's veto on unmitigated CRITICAL security findings
- Optional-member auto-join based on topic-tag matching (decided pre-spawn by the orchestrator)
- Captain America always played by the orchestrating model — never spawned

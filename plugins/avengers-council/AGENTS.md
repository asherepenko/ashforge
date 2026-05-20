# Avengers Council Plugin

## Routing

- **Skills** (Skill tool / natural-language invocation): `council-code-review`, `council-plan-review` — orchestrate council sessions on both Claude Code and Codex.
- **Agents** (Agent tool on Claude / `spawn_agent` on Codex): `hulk`, `iron-man`, `thor`, `scarlet-witch`, `black-widow`, `hawkeye`, `vision`, `doctor-strange` — spawned by the skills during orchestration.
- `captain-america` — reference only, never spawned. The orchestrating session plays this role on both platforms.
- Never spawn a skill as an agent `subagent_type`.

The slash-command form (`/avengers-council:plan-review`, `/avengers-council:code-review`) was retired in version 3.0.0. Skills are now the only entry point — same as android-expert-toolkit.

## Structure

```
.claude-plugin/plugin.json — Claude Code manifest
.codex-plugin/plugin.json  — Codex CLI / Codex App manifest (points at skills/)
agents/                    — 8 core members + captain-america (ref only) + optional members
skills/                    — council-plan-review, council-code-review (each with SKILL.md + scripts/preflight.sh)
references/                — Protocols, templates, shared docs (incl. codex-tools.md)
hooks/                     — PreToolUse:ExitPlanMode hook (Claude-only — no Codex equivalent)
docs/                      — Detailed documentation
tests/                     — Hook integration tests
```

## Sources of Truth

| What | File |
|------|------|
| Consensus rules | `references/verdict-rules.md` |
| Shared principles & tiebreakers | `references/shared-principles.md` |
| Red lines (non-negotiables) | `references/red-lines.md` |
| Member roster & extensibility | `references/member-registry.md` |
| Orchestration flow | `references/orchestration-protocol.md` |
| Debate transport (Claude SendMessage / Codex hub-mediated) | `references/debate-protocol.md` |
| Cross-platform tool mapping | `references/codex-tools.md` |

## Cross-Platform Tool Mapping

The council was built around Claude Code's agent-team primitives (`TeamCreate`, parallel `Agent`, peer-to-peer `SendMessage`). The Claude execution path is unchanged in 3.0.0. For Codex CLI / Codex App, the dual-annotated `references/orchestration-protocol.md` and `references/debate-protocol.md` describe the substitutions:

- `TeamCreate` → skip (no team primitive)
- `Agent({subagent_type, team_name})` → `spawn_agent(prompt)` with persona inlined from `agents/<name>.md`
- `SendMessage` (broadcast + DM) → hub-mediated context propagation (Captain consolidates each round's verdicts and re-spawns members for the next round with the consolidated context inlined)
- `TaskCreate` / `TaskUpdate` → `update_plan`
- `AskUserQuestion` → plain prompt with numbered options + free-form reply parsing
- `PreToolUse:ExitPlanMode` hook → no Codex equivalent (Claude-only feature)

Codex full-mode cost: ~3× the spawns of Claude (3 rounds × N members vs N stay-alive). `--quick` mode collapses to a single fan-out on both platforms. Debate fidelity is preserved because every cross-agent finding flows through the orchestrator's next-round prompt.

Codex requires `[features] multi_agent = true` in `~/.codex/config.toml` for parallel `spawn_agent` dispatch. Without it, fall back to single-orchestrator-perspective review and warn the user.

## Key Conventions

- Skills use explicit `Read @references/...` — not bare `@references/` lines.
- Agents include domain scores (1-10) in every assessment. Aggregate average < 5.0 overrides to NEEDS REVISION.
- Optional members auto-join based on topic matching. Add new ones via `member-registry.md`. The roster decision happens before any spawn — platform-agnostic.
- Black Widow retains VETO power on unmitigated CRITICAL security issues — platform-agnostic.

## Hooks (Claude-only)

`hooks/hooks.json` registers `PreToolUse:ExitPlanMode` → `hooks/council-plan-hook.sh`. The hook fires when the user exits Claude plan mode and offers a council review based on the `AVENGERS_COUNCIL_ON_PLAN` env var (off | prompt | auto).

There is no `.codex-plugin/hooks.json` — Codex has no `ExitPlanMode` tool to hook into. On Codex, users invoke the `council-plan-review` skill explicitly when they want a council review.

## Tests

Python tests for the `PreToolUse:ExitPlanMode` hook under `tests/`. Run:

```bash
pytest tests/
```

All 6 tests must pass.

## Versioning

Semantic versioning in `.claude-plugin/plugin.json` (mirrored in `.codex-plugin/plugin.json`):
- **Major**: breaking changes to skill/agent contracts, removed primitives, removed entry points
- **Minor**: new optional members, new flags, new skills
- **Patch**: docs, references, hook fixes, agent prompt tuning

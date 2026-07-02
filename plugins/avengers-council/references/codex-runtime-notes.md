# Codex Runtime Notes — Shared Scaffolding for Council Skills

Canonical version of the cross-runtime scaffolding shared by `council-plan-review` and `council-code-review`. The skill bodies reference this file instead of duplicating it.

## Contents

- [Platform Notes](#platform-notes) — Claude tool names vs Codex substitutions
- [Multi-Agent Capability Check (Codex only)](#multi-agent-capability-check-codex-only) — interpreting the preflight probe
- [Fallback Verdict Cap](#fallback-verdict-cap) — why the fallback caps at APPROVED WITH CONDITIONS
- [Codex App Sandbox](#codex-app-sandbox) — what still works when git ops are blocked

## Platform Notes

Tool names in the skill bodies use Claude Code primitives (`Agent`, `TeamCreate`, `SendMessage`, `TaskCreate`, `AskUserQuestion`). The Claude execution path is unchanged from earlier versions. For Codex CLI / Codex App, substitute per `${CLAUDE_PLUGIN_ROOT}/references/codex-tools.md`:

- `TeamCreate` is skipped (no team primitive).
- `SendMessage` is replaced by hub-mediated context propagation — Captain consolidates each round's verdicts and re-spawns members for the next round.
- Codex requires `multi_agent = true` in `~/.codex/config.toml` for parallel `spawn_agent` dispatch.

## Multi-Agent Capability Check (Codex only)

The preflight's `== Codex multi_agent capability ==` section emits one of:

| Value | Action |
|---|---|
| `NOT_CODEX` | Ignore — Claude `TeamCreate`/`Agent` not gated by a flag. Proceed with full debate. |
| `ENABLED` | Proceed with full hub-mediated debate (3 rounds × N members). |
| `DISABLED` or `NO_CONFIG` | **Read `${CLAUDE_PLUGIN_ROOT}/references/codex-fallback.md`** and run single-orchestrator persona walk instead. Do NOT attempt `spawn_agent` — it will fail at the tool layer. |

## Fallback Verdict Cap

The fallback skips debate rounds and caps the verdict at APPROVED WITH CONDITIONS (lower-fidelity than the full debate). The cap exists because there is no independent-instance challenge dynamic and no Black Widow security veto from a separate agent — both are mitigations the cap replaces.

## Codex App Sandbox

If running inside a Codex App managed worktree where branch creation, commits, or pushes are blocked (sandbox permission denial), the review still produces its verdict and writes the artifact under `.artifacts/reviews/{plans|code}/council/YYYY-MM-DD/HHMMSS-review-{verdict}.md` — verdict writes work in any sandbox because they're scoped to `.artifacts/`.

What's NOT available in a sandboxed run:

- Post-verdict actions that commit or push — "Apply suggested fixes" (code review; Edit calls may succeed but commit/push won't) and "Address findings now" when it would commit fixes (plan review)
- Re-review after changes that need branch creation
- `gh pr view` / `gh pr diff` may also fail without authenticated `gh` and network access (code review)

If the user picks an action that requires git ops the sandbox blocks, surface the limit explicitly and direct them to use the App's native "Create branch" / "Hand off to local" controls. The verdict and any TODOs created via the `/todo` skill survive the handoff.

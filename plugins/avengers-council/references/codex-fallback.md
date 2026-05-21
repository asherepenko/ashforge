## When to use

Read this when the `council-plan-review` or `council-code-review` skill's preflight reports `== Codex multi_agent capability ==` value of `DISABLED` or `NO_CONFIG`. The Codex `multi_agent` feature flag is off, so `spawn_agent` / `wait_agent` / `close_agent` are unavailable. Do NOT attempt parallel agent dispatch — the tool calls will fail at the runtime layer.

This file documents the single-orchestrator fallback. Claude users never hit this path (Claude's `TeamCreate` / `Agent` are not gated). Codex users with `multi_agent = true` use the normal hub-mediated flow in `references/orchestration-protocol.md`.

## Capability Decision Matrix

| Preflight value | Mode | Source |
|---|---|---|
| `NOT_CODEX` | Full flow (Claude path — agent team + SendMessage) | Claude Code; primitives always available |
| `ENABLED` | Full flow (Codex hub-mediated path — 3-round spawn_agent fan-out) | `multi_agent = true` in `~/.codex/config.toml` |
| `DISABLED` | This fallback | `multi_agent` set false or unset |
| `NO_CONFIG` | This fallback + warning | `~/.codex/config.toml` not found |

## Fallback Behavior

### Step 1 — Announce the mode

Tell the user explicitly before any review work begins:

```
⚠ Codex `multi_agent` feature is disabled. Falling back to single-orchestrator review.
  The full council is unavailable — there is no parallel `spawn_agent` to dispatch
  members in parallel, and no debate rounds are possible without peer instances.
  This run produces a sequential persona-walk review instead.

  Fidelity trade-off: lower than the full 3-round debate. Cross-member challenges,
  groupthink-detection, and security-veto-by-independent-instance are NOT available.

  To enable the full council, add to ~/.codex/config.toml:
      [features]
      multi_agent = true
  Then restart Codex.
```

### Step 2 — Sequential persona walk

Replace every `spawn_agent` callsite from `references/orchestration-protocol.md` Phase 1 with an inline persona walk by the orchestrating model (Captain America):

1. **Build the active roster** the same way (read `references/member-registry.md`). Optional members still auto-join based on topic.

2. **For each member in the roster:**
   - Read `agents/<member>.md` persona file
   - Adopt the persona's specialty lens and checklist
   - Apply against the REVIEW CONTEXT (same gathering logic — standards detection, codebase audit, domain artifacts)
   - Produce a single-member assessment block in that persona's voice with the same Round-1 schema:
     ```
     VERDICT: APPROVE / CONCERNS / REJECT
     DOMAIN SCORE: X/10 ([domain])
     KEY FINDINGS: max 5, each with severity
     CONSIDERED BUT NOT FLAGGED: 1-3 near-misses
     RECOMMENDATION: 1-2 sentences
     ```
   - Move to the next member

3. **Skip Rounds 2 and 3.** Without parallel instances, there is no debate dynamic — Captain America cannot challenge themselves while wearing a different persona hat and produce trustworthy disagreement. Document this explicitly in the verdict header.

4. **Aggregate the per-member blocks** using the same logic as the full mode (`references/verdict-rules.md`):
   - Tally votes
   - Compute aggregate domain score (average < 5.0 → NEEDS REVISION)
   - Check red lines (per `references/red-lines.md`)
   - Apply Black Widow veto on unmitigated CRITICAL security findings

### Step 3 — Verdict downgrade cap

**Cap the final verdict at APPROVED WITH CONDITIONS** in fallback mode. The cap reflects:

- No cross-member challenges → blind spots that the debate normally catches are still latent
- Same model played all personas → systematic-bias risk is concentrated, not diversified
- No Black Widow independent-instance veto → security flagging is best-effort, not authoritative

If the aggregate would otherwise be APPROVED, downgrade to APPROVED WITH CONDITIONS with the condition: *"Re-run the review with `multi_agent = true` enabled before considering this change fully approved."*

NEEDS REVISION and BLOCKED verdicts are NOT capped — those downward signals are still trustworthy because they reflect findings the orchestrator produced, not an absence of debate.

### Step 4 — Verdict header

Mark the saved verdict (`.artifacts/reviews/{plans,code}/council/YYYY-MM-DD/HHMMSS-review-{verdict}.md`) with:

```
> Run mode: Single-orchestrator fallback (Codex multi_agent disabled)
> Debate rounds skipped — verdict reflects sequential persona review by Captain America.
> Aggregate verdict capped at APPROVED WITH CONDITIONS regardless of tally; see codex-fallback.md.
```

### Step 5 — Post-verdict actions

Follow `references/post-verdict-actions.md` normally. The action menu (Address now / Save TODOs / Re-review / etc.) works identically — it doesn't depend on parallel dispatch. For "Re-review after changes," recommend the user enable `multi_agent` before re-running for a higher-fidelity verdict.

## What does NOT change

- Roster decision (`references/member-registry.md`)
- Standards detection and domain-artifact loading (Step 1 in the skill bodies)
- Codebase audit
- Verdict schema (`references/verdict-template.md`)
- Red-lines list (`references/red-lines.md`)
- Black Widow's veto **logic** — but it operates on Captain's own security-persona pass, not an independent agent's findings (this is the fidelity loss the cap exists to mitigate)
- Save path under `.artifacts/reviews/`

## Detection failure cases

- **`NO_CONFIG`** (no `~/.codex/config.toml`) — typically a fresh Codex install. Treat as `DISABLED` and mention the missing config in the announcement.
- **Probe reports `ENABLED` but `spawn_agent` still fails mid-round** — feature flag is on but runtime hasn't enabled it. Do NOT silently fall back mid-review (that mixes high- and low-fidelity rounds). Surface the tool error and let the user decide whether to restart.

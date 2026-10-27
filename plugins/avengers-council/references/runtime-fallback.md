## When to use

Read this after exposed tool discovery confirms no spawn capability and the `council-plan-review` or `council-code-review` skill's preflight reports `SPAWN=none` in the `== Runtime capability ==` section. No subagent dispatch is available on this runtime — `Agent` / `spawn_agent` / `wait_agent` / `close_agent` calls would fail at the tool layer. Do NOT attempt any spawn.

Typical causes: session restrictions remove spawn tools, or pi lacks a subagent extension. Modern Codex `[agents] enabled` defaults true; legacy `features.multi_agent` and preflight config are hints, not proof. Exposed working spawn tools use the normal flow even if a stale hint reports none.

## Contents

- [Capability Decision Matrix](#capability-decision-matrix) — profile → mode
- [Fallback Behavior](#fallback-behavior) — announce, sequential persona walk, verdict cap, header, post-verdict
- [What does NOT change](#what-does-not-change) — roster, standards, audit, schema, red lines
- [Detection failure cases](#detection-failure-cases) — unknown profiles, mid-round spawn failure

## Capability Decision Matrix

| Profile | Mode | Source |
|---------|------|--------|
| `SPAWN=registry` + `TRANSPORT=stay-alive` | Full flow (stay-alive path — agent team + SendMessage) | Claude Code with enabled teams in a verified interactive session |
| `SPAWN=prompt-embed` + `TRANSPORT=hub` | Full flow (hub-mediated path — 3-round spawn fan-out) | Codex with exposed spawn tools; subagent-equipped pi |
| `SPAWN=registry` + `TRANSPORT=hub` | Full flow (hub-mediated dispatch via `Agent(subagent_type)` — see runtime-adapters.md) | Zcode |
| `SPAWN=none` | This fallback | runtime with no exposed spawn tools; pi without a subagent skill |
| `SPAWN=unknown` | Resolve conversationally first (see runtime-adapters.md SPAWN axis) — only fall back if no subagent tool exists | undetected runtimes |

## Fallback Behavior

### Step 1 — Announce the mode

Tell the user explicitly before any review work begins:

```
⚠ No subagent spawning available on this runtime (SPAWN=none). Falling back to
  single-orchestrator review. The full council is unavailable — members cannot be
  dispatched in parallel, and no debate rounds are possible without peer instances.
  This run produces a sequential persona-walk review instead.

  Fidelity trade-off: lower than the full 3-round debate. Cross-member challenges,
  groupthink-detection, and security-veto-by-independent-instance are NOT available.

  Remediation depends on the runtime — e.g. on Codex, add to ~/.codex/config.toml:
      [agents]
      enabled = true  # defaults true; confirm tools are exposed after restart
  then restart. On pi, install a subagent skill/extension.
```

### Step 2 — Sequential persona walk

Replace every spawn callsite from `references/orchestration-protocol.md` Phase 1 with an inline persona walk by the orchestrating model (Captain America):

1. **Build the active roster** the same way (read `references/member-registry.md`). Optional members still auto-join based on topic. Select researchers by the same rule (`references/research-protocol.md`): `black-widow` plus the owner of each changed dependency manifest, only when `WEB=available`. Walk each selected persona's `## Research Focus` searches before its assessment, within that member's budget, and put the status in the verdict's Run Mode line. With `WEB=none`, write `Research: skipped — no web tools`.

2. **For each member in the roster:**
   - Read `agents/<member>.md` persona file
   - Adopt the persona's specialty lens and checklist
   - Apply against the REVIEW CONTEXT (same gathering logic — standards detection, codebase audit, domain artifacts)
   - Produce a single-member assessment block in that persona's voice with the same Round-1 schema:
     ```
     RESEARCH BRIEF (selected researchers only): date — findings with URLs | Nothing material
     VERDICT: APPROVE / CONCERNS / REJECT
     DOMAIN SCORE: X/10 ([domain]) — basis: <own finding numbers | weak: <slugs> | none>
     KEY FINDINGS: max 5, each with severity (code review: plus Introduced here: yes | pre-existing)
     VOTE BASIS (code review, CONCERNS or REJECT only): the findings the verdict rests on
     ARCHITECTURE DIAGRAM (plan review, iron-man only): mermaid or ASCII
     FLOW DIAGRAM + PATH → TEST (plan review, hulk only): mermaid or ASCII; <path> → <planned test | unmapped>
     CONSIDERED BUT NOT FLAGGED: 1-3 near-misses
     RECOMMENDATION: 1-2 sentences
     ```
   - The diagram fields apply when the member is present in the roster; skip them for any other persona.
   - Move to the next member

3. **Skip Rounds 2 and 3.** Without parallel instances, there is no debate dynamic — Captain America cannot challenge themselves while wearing a different persona hat and produce trustworthy disagreement. Document this explicitly in the verdict header.

4. **Aggregate the per-member blocks** using the same logic as the full mode (`references/verdict-rules.md`):
   - Tally votes
   - Compute the average domain score (informational; never changes the verdict)
   - Run `score-check.sh` per member and note any FLAG in the verdict (no Round 3 in fallback)
   - Run `review-grade.sh --ladder severity` on `yes` finding counts (plans: all findings; on a script error the Quality row reads `not scored ({reason})`) and set Risk from the tier table (`references/verdict-rules.md#quality-and-risk`); both go in the Consensus table's **Quality** and **Risk** rows. For **Quality**, strip the leading `Quality: ` from the script output, start the row with the grade's emoji (🟢 A/B, 🟡 C, 🟠 D, 🔴 F, ⚪ not scored) and append the weak-slug suffix per `references/verdict-rules.md#quality` (none on `not scored`). For **Risk**, write `<emoji> <level> — <basis>`
   - Check red lines (per `references/red-lines.md`)
   - Apply Black Widow veto on unmitigated CRITICAL security findings

### Step 3 — Verdict downgrade cap

**Cap the final verdict at APPROVED WITH CONDITIONS** in fallback mode. The cap reflects:

- No cross-member challenges → blind spots that the debate normally catches are still latent
- Same model played all personas → systematic-bias risk is concentrated, not diversified
- No Black Widow independent-instance veto → security flagging is best-effort, not authoritative

If the aggregate would otherwise be APPROVED, downgrade to APPROVED WITH CONDITIONS with the condition: *"Re-run the review with subagent spawning available before considering this change fully approved."*

NEEDS REVISION and BLOCKED verdicts are NOT capped — those downward signals are still trustworthy because they reflect findings the orchestrator produced, not an absence of debate.

### Step 4 — Verdict header

Mark the saved verdict (`.artifacts/reviews/{plans,code}/council/YYYY-MM-DD/HHMMSS-review-{verdict}.md`) with:

```
> Run mode: Single-orchestrator fallback (no subagent spawning available)
> Debate rounds skipped — verdict reflects sequential persona review by Captain America.
> Aggregate verdict capped at APPROVED WITH CONDITIONS regardless of tally; see runtime-fallback.md.
```

**Chat output:** show the verdict in the chat as the template's `## Chat Output` section sets out: the `## Consensus` block as it is (emoji headline plus the Quality, Risk, Vote and Score table), one line per condition or blocking finding with its severity emoji, then the saved path. Never a one-line prose recap of the grade and the verdict.

### Step 5 — Post-verdict actions

Follow `references/post-verdict-actions.md` normally. The action menu (Address now / Save TODOs / Re-review / etc.) works identically — it doesn't depend on parallel dispatch. For "Re-review after changes," recommend restoring subagent spawning before re-running for a higher-fidelity verdict.

If the user is unavailable (unattended run), take the non-blocking action — save the verdict and write follow-up TODOs — and say so, per orchestration-protocol.md → Mode Selection.

## What does NOT change

- Roster decision (`references/member-registry.md`)
- Standards detection and domain-artifact loading (Step 1 in the skill bodies)
- Codebase audit
- Verdict schema (`assets/verdict-template.md`)
- Red-lines list (`references/red-lines.md`)
- Black Widow's veto **logic** — but it operates on Captain's own security-persona pass, not an independent agent's findings (this is the fidelity loss the cap exists to mitigate)
- Save path under `.artifacts/reviews/`

## Detection failure cases

- **Fresh installs with no runtime config** (e.g. no `~/.codex/config.toml`) — typically a first run. Treat as `SPAWN=none` and mention the missing config in the announcement.
- **Profile reports spawns available but the first spawn still fails mid-round** — flag on, runtime lagging (version mismatch, registry not loaded). Do NOT silently fall back mid-review (that mixes high- and low-fidelity rounds). Surface the tool error and let the user decide whether to restart.

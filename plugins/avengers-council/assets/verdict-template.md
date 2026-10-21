# Verdict Output Template

Use this exact structure for the final council verdict output.

For full consensus rules and severity guidelines, see @references/verdict-rules.md

```markdown
# Avengers Council Verdict

## Topic
[What was reviewed]

## Run Mode
[Full Council | Quick Mode (--quick) | Quick Mode — cost-controlled degradation from Full Council | Single-orchestrator fallback]

Research: <member> (<status>), … | skipped — no web tools
[Status is completed, partial, failed (<reason>), or unavailable, per research-protocol.md. A member outside the Quick roster reads `<member> not in roster`. Disclosure only: it never changes the verdict.]

[When not Full Council: one line stating why + the fidelity trade — e.g. "verified fresh-worker schedule (four passes, 32 spawns for eight members) disproportionate; facts adversarially verified in triage; user unavailable. No cross-member debate rounds."]

## Consensus

### [✅ | ⚠️ | ⛔] [APPROVED | APPROVED WITH CONDITIONS | NEEDS REVISION | BLOCKED]

| | |
|---|---|
| **Quality** | [X — N critical, N high, N medium, N low · weak: slugs, or not scored ({reason})] |
| **Risk** | [🟢 low / 🟡 medium / 🔴 high] — [basis: what the change touches that sets the level] |
| **Vote** | [N approve · N concerns · N reject (N voters)] |
| **Score** | [X.X/10 avg] |

Vote adjustments (code reviews only): [none | one line per adjusted vote, e.g. `Thor: REJECT → APPROVE — basis thor#2, thor#4 are pre-existing`; see verdict-rules.md#votes-that-rest-on-pre-existing-findings]

Headline emoji: ✅ APPROVED and APPROVED WITH CONDITIONS, ⚠️ NEEDS REVISION, ⛔ BLOCKED. Quality and Risk are info rows computed after the debate; neither changes the verdict. See @references/verdict-rules.md#quality-and-risk

## Risk Tier

[Include this section for plan reviews and code reviews.]

**Risk tier**: [low | medium | high]
**Recommended human review of the resulting code**: [automated checks only | one person | two people]
**Basis**: [what the change touches that sets the tier — e.g. "adds a billing webhook handler"]

Set the tier by what the change touches, never by who writes it. See @references/verdict-rules.md#quality-and-risk for the tier table.

## Executive Summary
[2-3 sentences from Captain America]

## Council Positions

> Each position uses this shape:
> ```
> ### [Member] ([Domain]) — [VERDICT] | Score: X/10 — basis: …
> **Findings:**
> - [Finding 1 with file:line]
> - [Finding 2 with file:line]
>
> - Research: (only for a member who researched) [date — findings with URLs | Nothing material | failed (<reason>)]
>
> **Score flag:** (only when a score-check FLAG was not resolved in Round 3: the flag text)
>
> **Considered but not flagged:** (1–3 near-misses with reasoning, or "Nothing material — diff too narrow for near-misses")
> - [Pattern that looked wrong + why it's actually fine]
> ```

### Iron Man (Architecture & Scalability) — [VERDICT] | Score: X/10 — basis: …
**Findings:**
- [Finding 1]
- [Finding 2]

**Considered but not flagged:**
- [Near-miss with reasoning]

### Thor (Backend & API) — [VERDICT] | Score: X/10 — basis: …
**Findings:**
- [Finding 1]

**Considered but not flagged:**
- [Near-miss with reasoning]

### Scarlet Witch (Frontend & UX) — [VERDICT] | Score: X/10 — basis: …
**Findings:**
- [Finding 1]

**Considered but not flagged:**
- [Near-miss with reasoning]

### Hulk (Testing & QA) — [VERDICT] | Score: X/10 — basis: …
**Findings:**
- [Finding 1]

**Considered but not flagged:**
- [Near-miss with reasoning]

### Black Widow (Security & Privacy) — [VERDICT] | Score: X/10 — basis: …
**Findings:**
- [Finding 1]

**Considered but not flagged:**
- [Near-miss with reasoning]

### Hawkeye (Mobile Platforms) — [VERDICT] | Score: X/10 — basis: …
**Findings:**
- [Finding 1]

**Considered but not flagged:**
- [Near-miss with reasoning]

### Vision (Data & Observability) — [VERDICT] | Score: X/10 — basis: …
**Findings:**
- [Finding 1]

**Considered but not flagged:**
- [Near-miss with reasoning]

### Doctor Strange (DevOps & Cross-platform) — [VERDICT] | Score: X/10 — basis: …
**Findings:**
- [Finding 1]

**Considered but not flagged:**
- [Near-miss with reasoning]

### Captain America (Standards & Delivery) — [VERDICT]
**Findings:**
- [Finding 1]

**Considered but not flagged:**
- [Near-miss with reasoning]

<!-- If optional members participated, add their positions here using the same shape -->
### Ant-Man (Reuse & Placement) — [VERDICT] | Score: X/10 — basis: …
**Findings:**
- [Finding 1]

**Considered but not flagged:**
- [Near-miss with reasoning]
<!-- End optional members -->

## Domain Scores

| Member | Domain | Score |
|--------|--------|-------|
| Iron Man | Architecture & Scalability | X/10 |
| Thor | Backend & API | X/10 |
| Scarlet Witch | Frontend & UX | X/10 |
| Hulk | Testing & QA | X/10 |
| Black Widow | Security & Privacy | X/10 |
| Hawkeye | Mobile Platforms | X/10 |
| Vision | Data & Observability | X/10 |
| Doctor Strange | DevOps & Infrastructure | X/10 |
| Ant-Man (optional) | Reuse & Placement | X/10 |
| *[Other optional members — add rows if active]* | | |

**Average: X.X/10** | **Voters: N** | (info — never changes the verdict)

## Disagreements
[Specific points where members disagree, with reasoning]

## Tiebreaker (if applicable)
[Captain America's deciding rationale]

## Domain Alignment

[Include this section ONLY when the spawn brief carried a `DOMAIN MODEL` block. Otherwise omit entirely.]

- **Glossary contradictions**: terms used in the plan that conflict with `DOMAIN.md` (cite term + glossary line)
- **ADR contradictions**: plan claims that contradict accepted ADRs (cite ADR-NNNN + contradicting plan line)
- **Acknowledged supersession**: ADRs the plan explicitly proposes to supersede (with rationale)

If any unacknowledged ADR contradiction exists → automatic verdict downgrade to minimum NEEDS REVISION per `standards-protocol.md#phase-5-determine-verdict-based-on-standards`. Note the trigger here.

## Scope Check

[Include this section ONLY for plan reviews.]

Requested items come from the plan's linked source (PRD, design doc, or the stated requirement in its Source section) and from its Goal and acceptance criteria. Each item is tagged `[PRD]`, `[source]`, `[goal]` or `[AC]`.

Legend: ✅ covered · ⚠️ partial · ❌ missing · ⏸ deferred

| # | Requested item | Covered | Where |
|---|----------------|---------|-------|
| 1 | [item] `[PRD]` | ✅ | [plan section] |
| 2 | [item] `[AC]` | ❌ | Finding: [the shared finding] |

- ❌ = one HIGH finding, ⚠️ = one MEDIUM finding, ⏸ = no finding. Count them before grading.
- ⏸ applies only when the source itself defers the item or puts it out of scope. A plan that defers a source requirement on its own is ⚠️ partial.
- One underlying gap counts once across Scope Check, AC Validation and member findings; the highest severity wins. The Scope Check row cites the finding it shares.
- If a linked source cannot be read, say `Source not readable: <path>` and build the list from the Goal and acceptance criteria only.

## Acceptance Criteria Validation

[Include this section ONLY for plan reviews.]

- [x] [Criterion that is testable and measurable]
- [ ] [Criterion that is missing or vague] — **[finding or member that flagged it]**

**Result:** [N/M criteria satisfied. Remaining ones are council conditions.]

## Standards Compliance

**CLAUDE.md standards detected:** [N mandatory, M strong guidance]

| Standard | Category | Status |
|----------|----------|--------|
| [standard] | Mandatory or Strong Guidance | ✅ Met, ⚠️ Partial or ❌ Violated — [note] |

**Result:** [one line: mandatory standards met or violated; guidance items flagged as conditions]

## Diagrams

[Include this section ONLY for plan reviews.]

**Architecture** (Iron Man):
[mermaid or ASCII diagram, or `not drawn — iron-man not in Quick roster`]

**Flow** (Hulk):
[mermaid or ASCII diagram, or `not drawn — hulk not in Quick roster`]

**Path → test:** [one line per path: `<path> → <planned test | unmapped>`; each `unmapped` path is a Hulk finding]

When a member is not in the Quick roster, its slot reads `not drawn — <member> not in Quick roster`.

## Conditions for Approval
[Items that must be addressed]

## Concerns for the User

[Include this section ONLY when a member raised a concern. Otherwise omit entirely.]

Advisory. A concern is a risk the change knowingly takes on, or a judgment call for the user. It is never a condition, is not counted in Quality, and never changes the verdict. A concern that meets a severity definition or a red line is a finding, not a concern.

- [Member] [Concern and the trade-off behind it]

## Pre-existing

[Include this section ONLY for code reviews. Omit it for plan reviews. When no finding is pre-existing, write "None".]

Findings marked `Introduced here: pre-existing`. They did not count toward the consensus, the unmitigated-CRITICAL rules, or Black Widow's VETO (see @references/verdict-rules.md#pre-existing-findings). Track them as follow-ups.

- [SEVERITY] [Member] [Issue] (file:line) — suggested follow-up

## Action Items
1. [Actionable item with owner suggestion]
2. [...]

---
> **Verdict saved to:** `[absolute file path]`
```

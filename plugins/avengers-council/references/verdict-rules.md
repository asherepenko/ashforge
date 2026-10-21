# Verdict Consensus Rules & Severity Guidelines

Canonical rules for determining council verdict outcomes. Referenced by assets/verdict-template.md and references/captain-america-orchestrator.md.

## Contents

- [Consensus Rules (N voters)](#consensus-rules-n-voters) — vote thresholds + severity-weighted consensus
- [Domain Scoring](#domain-scoring) — informational per-member scores, anchored bands, basis line, score-check.sh
- [Quality and Risk](#quality-and-risk) — Quality grade ladder, risk tier table, verdict wins
- [Pre-existing Findings](#pre-existing-findings) — code-review findings this change did not introduce; excluded from every rule below
- [Severity Guidelines](#severity-guidelines) — CRITICAL / HIGH / MEDIUM / LOW definitions
- [Quick Mode Consensus Rules (3 voters)](#quick-mode-consensus-rules-3-voters) — abbreviated quorum rules

## Consensus Rules (N voters)

Let **N** = total active voters (core members + optional members + Captain America). Thresholds adjust automatically when optional members join. See @references/member-registry.md for roster determination.

| N | Majority (floor(N/2)+1) | BLOCKED threshold (floor(N*0.45)) | Default (8 core + Cap) |
|---|------------------------|-----------------------------------|----------------------|
| 9 | 5 | 4 | Yes |
| 10 | 6 | 4 | 9 + 1 optional |
| 11 | 6 | 4 | 9 + 2 optional |

### Severity-Weighted Consensus

In code reviews, every finding count and every "unmitigated CRITICAL" rule below counts only findings marked `Introduced here: yes`. See [Pre-existing Findings](#pre-existing-findings).

**APPROVED:**
- Majority APPROVE votes
- 0 CRITICAL issues
- 0 REJECT votes

**APPROVED WITH CONDITIONS:**
- (Majority - 1) or more APPROVE votes
- No CRITICAL issues
- Every HIGH issue is a condition
- Merge only after every condition is fixed
- MEDIUM/LOW issues can be addressed post-merge

**NEEDS REVISION:**
- 2+ REJECT votes
- OR any unmitigated CRITICAL issue
- OR any unmitigated red line violation (per @references/red-lines.md)
- Must fix before proceeding

**BLOCKED:**
- BLOCKED threshold or more REJECT votes
- OR Black Widow VETO (unmitigated CRITICAL security issue introduced by this change -- cannot be overridden)
- OR multiple mandatory standard violations
- Cannot proceed until blocking issues resolved

**Tiebreaker / Escalation Hierarchy:**

When votes are split and no clear consensus emerges, Captain America applies these steps in order. Stop at the first step that resolves the split:

1. **Review challenges**: Did Round 2-3 debates resolve any disagreements? Check if positions shifted but final votes weren't updated accordingly.
2. **Domain authority**: If the split centers on one domain (e.g., security debate), the primary domain expert's position carries weighted voice. A 4-4 split where Black Widow is the REJECT on a security matter tips toward her position.
3. **Red lines check**: Does either option violate a red line from @references/red-lines.md? If so, the option that avoids the violation wins.
4. **Tiebreaker principles** (from @references/shared-principles.md): Apply in order -- Simpler? Deletable? Composable? Deferrable? Reversible? Safer? First filter that differentiates wins.
5. **Risk assessment**: If principles don't differentiate, the higher-risk option loses. Prefer the conservative choice.
6. **Captain America decides**: Cap casts the deciding vote with explicit reasoning referencing the steps above. Documented in "Tiebreaker" section of verdict.

## Domain Scoring

The domain score is informational — never changes the verdict. The verdict comes from votes and findings alone. A low average is not a reason to downgrade it, and a high one is not a reason to upgrade it.

### Per-Member Scores

Each council member gives a domain score from 1-10 for how the proposal performs in their area. Scores are independent of the vote: a member can APPROVE with 6/10 or have CONCERNS with 7/10.

Pick the band that matches your own findings and WEAK criteria, then a score inside it.

| Band | Defined by the member's own findings and WEAK criteria |
|------|-------------------------------------------------------|
| 9–10 | No finding above LOW, and no WEAK criterion |
| 7–8 | No CRITICAL or HIGH. At most 2 MEDIUM or WEAK criteria combined (none is also fine) |
| 5–6 | A HIGH, or 3+ MEDIUM and WEAK combined. No CRITICAL |
| 3–4 | A CRITICAL that is contained or has a clear fix |
| 1–2 | A CRITICAL that is fundamental, or several CRITICAL findings |

WEAK criteria come from the member's rubric: correctness, simplicity, consistency, robustness, maintainability. A criterion is WEAK when the member found it clearly below acceptable, even without a numbered finding.

LOW findings never lower a score.

### Basis Line

Every score carries a `basis:`.

```
DOMAIN SCORE: X/10 ([domain]) — basis: <own finding numbers | weak: <slugs> | none>
```

Examples: `basis: 1, 3`, `basis: weak: robustness, simplicity`, `basis: none`. Findings count only if they are the member's own and, in code reviews, `Introduced here: yes`.

A bare score is missing. Captain America asks the member for the basis once. If it is still missing, the score is reported as `n/a` and left out of the average.

### Checking the Score

Captain America runs `scripts/score-check.sh` once per score, passing the member's own counts:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/score-check.sh" --score X --critical N --high N --medium N --low N --weak N
```

Exit 0 is ok. Exit 1 is FLAG: the score is above the cap its findings allow, or a clean-domain score is below 7. Full mode checks Round-1 scores and sends a FLAG back once in the Round 3 trigger, to fix the score or the labels; a bare score is asked for its basis in the same slot. Final scores are checked again in synthesis. Whatever the member answers, the verdict is unaffected; an unresolved FLAG (or any FLAG in Quick/fallback modes, which have no Round 3) becomes `Score flag:` in the verdict.

### Aggregate Score

- **Average Score**: sum of scored members / number of scored members. Reported for information only.
- **Quick Mode**: the same applies to the 2 specialist scores (Captain America does not score).

### Score Interpretation

| Average | Interpretation |
|---------|---------------|
| 8.0-10 | Excellent |
| 6.0-7.9 | Good |
| 5.0-5.9 | Marginal |
| Under 5.0 | Weak |

## Quality and Risk

Two lines in every verdict, computed from labels after the debate. Neither changes the verdict.

### Quality

Assign every severity label first, then grade. Never move a label to move the grade. Count `yes` findings only — pre-existing findings are excluded (see [Pre-existing Findings](#pre-existing-findings)). Plan reviews have no attribution, so every finding counts.

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/review-grade.sh" --ladder severity \
  --critical N --high N --medium N --low N
```

Ladder, first match wins:

| Grade | Rule |
|-------|------|
| F | 1+ CRITICAL |
| D | 1+ HIGH |
| C | 3+ MEDIUM |
| B | 1-2 MEDIUM, or more than 3 LOW |
| A | otherwise |

Count each underlying issue once across members; the highest severity wins. On a script error, print `Quality: not scored ({reason})`, never a guessed letter.

After the script's line, append ` · weak: <slugs>`: the union of every member's reported WEAK rubric criteria (`weak: <slug>`), deduplicated, in rubric order (correctness, simplicity, consistency, robustness, maintainability). Omit the suffix when no member reported a WEAK criterion. The letter comes only from the script; WEAK criteria never change it. On `not scored`, add no suffix. Plan reviews often have no rubric, so the suffix is usually omitted.

### Risk

Set the tier by what the change touches, never by who writes it. For plans and for code, the highest tier wins when the change touches several.

| Tier | The change touches | Recommended human review of the resulting code |
|------|--------------------|------------------------------------------------|
| `low` | Docs, copy, internal-only tooling, or additive behavior behind a flag | Automated checks only |
| `medium` | An ordinary product change | One person |
| `high` | Auth, permissions, billing or payments, data migrations, CI/deploy/release, auto-update, secrets, or any other path that always needs two people | Two people |

State the basis: name what the change touches that sets the tier.

### Verdict wins

The verdict is decided by votes and findings. Quality and Risk are info only. A grade or tier that could block would be a second verdict.

## Pre-existing Findings

Applies to code reviews. Each Round 1 finding carries `Introduced here: yes | pre-existing`.

- **yes**: the change under review introduced the defect. This also covers a defect that already existed in unchanged code when the diff makes it reachable or makes it worse.
- **pre-existing**: the defect is in code the diff does not change, and the diff does not make it reachable or worse.

Pre-existing findings never count toward:

- NEEDS REVISION
- BLOCKED
- the "unmitigated CRITICAL" rules in this file, in `standards-protocol.md#phase-5-determine-verdict-based-on-standards`, and in Phase 4 of `orchestration-protocol.md`
- Black Widow's VETO

They still keep their severity. Captain America lists them in the verdict's Pre-existing section as follow-ups, separate from Conditions for Approval.

### Votes that rest on pre-existing findings

Members base their vote and domain score on `yes` findings only. Captain America enforces this with the steps below, and changes a vote for no other reason. Domain scores are never changed.

1. **Basis.** In a code review, every CONCERNS or REJECT vote states its `VOTE BASIS`: the findings it rests on. A member cites their own findings by number (`2`), a teammate's as `<member>#<n>` (`thor#2`), and a red line by name. APPROVE needs no basis.
2. **Attribution.** Each basis finding is judged by its attribution after the debate. A finding still contested at synthesis counts as `yes` (see below).
3. **The test.** A vote rests only on pre-existing findings when its basis names at least one finding and every finding it names is `pre-existing`. A basis with any `yes` finding, or with a red line the change introduces, leaves the vote as cast.
4. **Missing basis.** Full Council: Captain America asks for it in that member's Round 3 trigger. Quick Mode and fallback runs: the member's own Round 1 findings are the basis.
5. **Full Council.** For a vote that passes the test, Captain America's Round 3 trigger to that member names the pre-existing findings and asks the member to restate the vote on `yes` findings only. If the `FINAL VOTE BASIS` still passes the test, the vote is adjusted (step 7).
6. **Quick Mode and fallback runs** have no Round 3, so a vote that passes the test is adjusted directly.
7. **Adjusting.** An adjusted vote counts as APPROVE in the tally. The verdict's **Vote adjustments** line lists each one, for example `Thor: REJECT → APPROVE — basis thor#2, thor#4 are pre-existing`. The member's original vote, findings and domain score stay in the record unchanged.

When members disagree on attribution, the debate rounds settle it. If it is still contested at synthesis, Captain America treats the finding as `yes` and records the disagreement.

## Severity Guidelines

**CRITICAL** (must fix before merge):
- Security vulnerabilities (injection, XSS, auth bypass)
- Data loss risks (destructive operations, missing transactions)
- Architectural flaws (wrong pattern, violates constraints)
- Production-breaking bugs (crashes, deadlocks, ANRs)

**HIGH** (must fix before merge):
- Significant bugs (incorrect behavior, data corruption potential)
- Performance issues (N+1 queries, memory leaks, blocking operations)
- Missing error handling (silent failures, uncaught exceptions)
- Accessibility violations (screen reader issues, keyboard navigation)

**MEDIUM** (should fix, can track post-merge):
- Code quality (readability, maintainability, duplication)
- Minor performance optimizations
- Non-critical missing tests
- Documentation gaps

**LOW** (nice to have):
- Style consistency
- Minor refactoring opportunities
- Documentation improvements
- Non-blocking suggestions

## Quick Mode Consensus Rules (3 voters)

**APPROVED:**
- 3 APPROVE votes
- 0 CRITICAL issues

**APPROVED WITH CONDITIONS:**
- 2 APPROVE + 1 CONCERNS
- No CRITICAL issues
- Every HIGH issue is a condition
- Merge only after every condition is fixed
- MEDIUM/LOW issues can be addressed post-merge

**NEEDS REVISION:**
- 2+ CONCERNS
- OR any unmitigated CRITICAL issue

**BLOCKED:**
- Any REJECT vote
- OR Black Widow VETO (unmitigated CRITICAL security issue introduced by this change — cannot be overridden)

Pre-existing findings are excluded here too, per [Pre-existing Findings](#pre-existing-findings).

No ties possible with 3 voters.

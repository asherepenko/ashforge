# Verdict Consensus Rules & Severity Guidelines

Canonical rules for determining council verdict outcomes. Referenced by assets/verdict-template.md and references/captain-america-orchestrator.md.

## Contents

- [Consensus Rules (N voters)](#consensus-rules-n-voters) — vote thresholds + severity-weighted consensus
- [Domain Scoring](#domain-scoring) — informational per-member scores, first-match table, domain-score.py
- [Quality and Risk](#quality-and-risk) — Quality grade ladder, risk tag table (risk-tier.py), verdict wins
- [Pre-existing Findings](#pre-existing-findings) — code-review findings this change did not introduce; excluded from every rule below
- [Severity Guidelines](#severity-guidelines) — CRITICAL / HIGH / MEDIUM / LOW definitions
- [Quick Mode Consensus Rules (3 voters)](#quick-mode-consensus-rules-3-voters) — abbreviated quorum rules

## Consensus Rules (N voters)

Let **N** = total active voters (core members + optional members + Captain America). Thresholds adjust automatically when optional members join. See @references/member-registry.md for roster determination.

| N | Majority (floor(N/2)+1) | BLOCKED threshold (floor(N*0.45)) | Default (8 core + Cap) |
|---|-------------------------|-----------------------------------|------------------------|
| 9 | 5 | 4 | Yes |
| 10 | 6 | 4 | 9 + 1 optional |
| 11 | 6 | 4 | 9 + 2 optional |

### Severity-Weighted Consensus

In code reviews, every finding count and every "unmitigated CRITICAL" rule below counts only findings marked `Introduced here: yes`. See [Pre-existing Findings](#pre-existing-findings).

Compute it — never apply these rules by hand:

```bash
python3 "<plugin root from preflight>/scripts/verdict.py" --mode full|quick --approve N --concerns N --reject N --critical N --high N --red-lines N --standards N [--missing-ac N] [--veto]
```

Counts: the final Round-3 votes; code reviews count `Introduced here: yes` findings only; `--critical` is unmitigated CRITICAL; `--red-lines` is unmitigated red line violations (@references/red-lines.md); `--standards` is mandatory standard violations; `--missing-ac` (plan reviews) is major acceptance criteria missing. Add `--veto` only for a Black Widow veto. Paste the output line verbatim. Exit 2 is a usage error: fix the counts and run again; the verdict is never `n/a`.

Rules, first match wins, top to bottom (N = approve + concerns + reject; majority = floor(N/2)+1; block = max(1, floor(N*0.45)); timed-out members do not vote, so N can be below 9):

| Verdict | When |
|---------|------|
| BLOCKED | Black Widow VETO (unmitigated CRITICAL security issue introduced by this change, cannot be overridden), or reject >= block, or 2+ mandatory standard violations |
| NEEDS REVISION | reject >= 2, or any unmitigated CRITICAL, red line violation, mandatory standard violation (1 standard violation), or missing acceptance criteria |
| APPROVED | approve >= majority, 0 REJECT votes, 0 HIGH |
| APPROVED WITH CONDITIONS | approve >= majority - 1. HIGH present with a majority APPROVE lands here. Every HIGH issue is a condition. Merge only after every condition is fixed. MEDIUM/LOW can be addressed post-merge |
| NO CONSENSUS | anything else: apply the tiebreaker below |

**Tiebreaker / Escalation Hierarchy:**

Run only when the script prints `NO CONSENSUS`. Captain America applies these steps in order and stops at the first step that resolves the split. Record the tiebreak decision in the verdict's Tiebreaker section with the step that resolved it:

1. **Review challenges**: Did Round 2-3 debates resolve any disagreements? Check if positions shifted but final votes weren't updated accordingly.
2. **Domain authority**: If the split centers on one domain (e.g., security debate), the primary domain expert's position carries weighted voice. A 4-4 split where Black Widow is the REJECT on a security matter tips toward her position.
3. **Red lines check**: Does either option violate a red line from @references/red-lines.md? If so, the option that avoids the violation wins.
4. **Tiebreaker principles** (from @references/shared-principles.md): Apply in order -- Simpler? Deletable? Composable? Deferrable? Reversible? Safer? First filter that differentiates wins.
5. **Risk assessment**: If principles don't differentiate, the higher-risk option loses. Prefer the conservative choice.
6. **Captain America decides**: Cap casts the deciding vote with explicit reasoning referencing the steps above. Documented in "Tiebreaker" section of verdict.

## Domain Scoring

The domain score is informational — never changes the verdict. The verdict comes from votes and findings alone. A low average is not a reason to downgrade it, and a high one is not a reason to upgrade it.

### Per-Member Scores

Members do not pick a score. Captain America counts each member's own findings and WEAK criteria and runs `scripts/domain-score.py`, so the score is the same for every reviewer and every runtime. Scores are independent of the vote: a member can APPROVE with 6/10 or have CONCERNS with 7/10.

First match wins, top to bottom. MEDIUM and WEAK count together.

| Member's own findings and WEAK criteria | Score |
|------|-------|
| 2+ CRITICAL | 1 |
| 1 CRITICAL | 3 |
| 2+ HIGH, or 1 HIGH and 3+ MEDIUM/WEAK | 5 |
| 1 HIGH, or 3+ MEDIUM/WEAK | 6 |
| 2 MEDIUM/WEAK | 7 |
| 1 MEDIUM/WEAK | 8 |
| none of the above | 10 |

WEAK criteria come from the member's rubric: correctness, simplicity, consistency, robustness, maintainability. A criterion is WEAK when the member found it clearly below acceptable, even without a numbered finding. Members report each as a `weak: <slug>` line. In code reviews, a weakness that rests only on pre-existing findings (`Introduced here: pre-existing`) is not WEAK: it adds no weak slug to the Quality row and does not count toward the score.

LOW findings never lower a score.

### Computing the Score

Captain America runs `scripts/domain-score.py` once per member, passing that member's own counts (code reviews: `Introduced here: yes` only; plan reviews: all own findings), and pastes the output verbatim. Never write the score by hand.

```bash
python3 "<plugin root from preflight>/scripts/domain-score.py" --critical N --high N --medium N --low N --weak N
```

Exit 0 prints `N/10`. Exit 2 is a usage error: the cell reads `n/a (reason)` and the member is left out of the average. In Full mode the Round 1 counts give the Round 1 score; the final counts, after severity changes in debate, give the final score.

### Aggregate Score

- **Average Score**: `domain-score.py --average <each member's N/10 or n/a>`, pasted verbatim. Reported for information only.
- **Quick Mode**: the same applies to the 2 specialist scores (Captain America does not score).

### Score Interpretation

| Average | Interpretation |
|---------|----------------|
| 8.0-10 | Excellent |
| 6.0-7.9 | Good |
| 5.0-5.9 | Marginal |
| Under 5.0 | Weak |

## Quality and Risk

Quality and Risk are two rows of the Consensus table in every verdict, computed from labels after the debate. Neither changes the verdict.

### Quality

Assign every severity label first, then grade. Never move a label to move the grade. Count `yes` findings only — pre-existing findings are excluded (see [Pre-existing Findings](#pre-existing-findings)). Plan reviews have no attribution, so every finding counts.

```bash
python3 "<plugin root from preflight>/scripts/review-grade.py" --ladder severity \
  --critical N --high N --medium N --low N
```

Ladder, first match wins:

| Row starts | Grade | Rule |
|------------|-------|------|
| 🔴 F | F | 1+ CRITICAL |
| 🟠 D | D | 1+ HIGH |
| 🟡 C | C | 3+ MEDIUM |
| 🟢 B | B | 1-2 MEDIUM, or more than 3 LOW |
| 🟢 A | A | otherwise |

The Quality row starts with the grade's emoji, then the script's line: `🟠 D — 0 critical, 11 high, 14 medium, 3 low`. A row that reads `not scored` starts with `⚪ not scored`.

Count each underlying issue once across members; the highest severity wins. On a script error, put `not scored ({reason})` in the Quality row, never a guessed letter.

After the script's line, append ` · weak: <slugs>`: the union of every member's reported WEAK rubric criteria (`weak: <slug>`), deduplicated, in rubric order (correctness, simplicity, consistency, robustness, maintainability). Omit the suffix when no member reported a WEAK criterion. The letter comes only from the script; WEAK criteria never change it. On `not scored`, add no suffix. Plan reviews often have no rubric, so the suffix is usually omitted.

### Risk

Set the tier by what the change touches, never by who writes it. Captain America tags what the change touches from the fixed list below and runs the script. The highest tier wins. Never write the Risk row by hand.

```bash
python3 "<plugin root from preflight>/scripts/risk-tier.py" --touches TAG[,TAG...]
```

`risk-tier.py --list` prints the tags. An unknown or missing tag is exit 2: fix the tags and run again. The script's output line (`high — touches: auth, secrets`) goes in the Risk row; the Basis is the tag list it prints.

| Tier | Tags (the change touches) | Recommended human review of the resulting code |
|------|--------------------|------------------------------------------------|
| `low` | `docs`, `copy`, `internal-tooling` (internal-only tooling), `flagged-additive` (additive behavior behind a flag) | Automated checks only |
| `medium` | `product` (an ordinary product change) | One person |
| `high` | `auth`, `permissions`, `billing`, `payments`, `data-migration`, `ci-deploy`, `release`, `auto-update`, `secrets`, `two-person-path` (any other path that always needs two people) | Two people |

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
7. **Adjusting.** An adjusted vote counts as APPROVE in the tally. The verdict's `Vote adjustments` line lists each one, for example `Thor: REJECT → APPROVE — basis thor#2, thor#4 are pre-existing`. The member's original vote, findings and domain score stay in the record unchanged.

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

Run `verdict.py --mode quick` with the same counts. N must be 3 (approve + concerns + reject); any other total is a usage error. Red lines and mandatory standards apply in Quick Mode too.

| Verdict | When |
|---------|------|
| BLOCKED | Black Widow VETO, or any REJECT vote |
| NEEDS REVISION | 2+ CONCERNS, or any unmitigated CRITICAL, red line violation or mandatory standard violation |
| APPROVED | 3 APPROVE, 0 HIGH |
| APPROVED WITH CONDITIONS | otherwise (2 APPROVE + 1 CONCERNS, or a HIGH present). Every HIGH is a condition |

Pre-existing findings are excluded here too, per [Pre-existing Findings](#pre-existing-findings).

No ties possible with 3 voters.

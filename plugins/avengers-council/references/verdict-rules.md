# Verdict Consensus Rules & Severity Guidelines

Canonical rules for determining council verdict outcomes. Referenced by verdict-template.md and agents/captain-america.md.

## Consensus Rules (N voters)

Let **N** = total active voters (core members + optional members + Captain America). Thresholds adjust automatically when optional members join. See @references/member-registry.md for roster determination.

| N | Majority (floor(N/2)+1) | BLOCKED threshold (floor(N*0.45)) | Default (8 core + Cap) |
|---|------------------------|-----------------------------------|----------------------|
| 9 | 5 | 4 | Yes |
| 10 | 6 | 4 | 9 + 1 optional |
| 11 | 6 | 4 | 9 + 2 optional |

### Severity-Weighted Consensus

**APPROVED:**
- Majority APPROVE votes
- 0 CRITICAL issues
- 0 REJECT votes

**APPROVED WITH CONDITIONS:**
- (Majority - 1) or more APPROVE votes
- All issues <= HIGH severity
- Conditions documented for tracking
- MEDIUM/LOW issues can be addressed post-merge

**NEEDS REVISION:**
- 2+ REJECT votes
- OR any unmitigated CRITICAL issue
- OR any unmitigated red line violation (per @references/red-lines.md)
- Must fix before proceeding

**BLOCKED:**
- BLOCKED threshold or more REJECT votes
- OR Black Widow VETO (unmitigated CRITICAL security issue -- cannot be overridden)
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

### Per-Member Scores

Each council member provides a domain score from 1-10 reflecting how well the proposal performs in their area of expertise. Scores are independent of the vote -- a member can APPROVE with a 6/10 (acceptable but not great) or have CONCERNS with a 7/10 (good in their domain but worried about cross-cutting issues).

### Aggregate Score

- **Average Score**: Sum of all active member scores / number of active members
- **Minimum Threshold**: Average score below 5.0 triggers mandatory re-evaluation, regardless of vote tally
- **Quick Mode**: Same threshold applies to the 2 specialist scores (Captain America does not score)

### Score Interpretation

| Average | Interpretation |
|---------|---------------|
| 8.0-10 | Excellent -- proceed with confidence |
| 6.0-7.9 | Good -- proceed with noted improvements |
| 5.0-5.9 | Marginal -- address concerns before proceeding |
| < 5.0 | Insufficient -- requires re-evaluation even if votes pass |

### Score Override Rule

If the vote tally yields APPROVED but the average domain score is below 5.0, Captain America downgrades the verdict to NEEDS REVISION with an explanation citing which domains scored lowest.

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
- All issues <= HIGH severity
- Conditions documented

**NEEDS REVISION:**
- 2+ CONCERNS
- OR any unmitigated CRITICAL issue

**BLOCKED:**
- Any REJECT vote
- OR Black Widow VETO (unmitigated CRITICAL security issue — cannot be overridden)

No ties possible with 3 voters.

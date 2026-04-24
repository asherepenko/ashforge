# Avengers Council Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User's Request                          │
│     /avengers-council:plan-review @proposal.md                  │
│     OR                                                          │
│     /avengers-council:code-review --pr 123                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Captain America (Steve Rogers) — ORCHESTRATOR & ENFORCER       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PHASE 1: DETECT STANDARDS & AUDIT CODEBASE                     │
│  ├─ Read CLAUDE.md (project level)                              │
│  ├─ Read .claude/CLAUDE.md (local level)                        │
│  ├─ Read ~/.claude/CLAUDE.md (global level)                     │
│  ├─ Index applicable standards → STANDARDS INDEX                │
│  └─ Audit codebase: structure, naming, architecture patterns    │
│                                                                 │
│  PHASE 2: DETERMINE ROSTER & VALIDATE INPUT                     │
│  ├─ Read member-registry.md → core + matching optional members  │
│  ├─ Calculate thresholds (majority, quorum) for N voters        │
│  ├─ [Plans] Check: Does it include acceptance criteria?         │
│  ├─ [Code] Check: Commit message format correct?                │
│  ├─ [Code] Check: Test coverage meets baseline?                 │
│  └─ Flag obvious violations → PRE-FLIGHT CHECK                  │
│                                                                 │
│  PHASE 3: ASSEMBLE COUNCIL                                      │
│  ├─ TeamCreate("avengers-council")                              │
│  ├─ Spawn core + optional teammates with context                │
│  │   (standards, codebase audit, shared principles, red lines)  │
│  └─ Each agent self-starts Round 1 immediately                  │
│                                                                 │
│  PHASE 4: FACILITATE DEBATE (Rounds 1-3)                        │
│  ├─ Round 1: Initial Assessment (with standards context)        │
│  ├─ Round 2: Challenge & Peer Debate                            │
│  ├─ Round 3: Final Positions                                    │
│  └─ Collect all votes & findings                                │
│                                                                 │
│  PHASE 5: SYNTHESIZE VERDICT                                    │
│  ├─ Tally votes: APPROVE, CONCERNS, REJECT                      │
│  ├─ Compute aggregate domain score (avg of all member scores)   │
│  ├─ Check red lines (references/red-lines.md)                   │
│  ├─ Check standards compliance:                                 │
│  │   ├─ Mandatory standard violated? → min "NEEDS REVISION"     │
│  │   ├─ CRITICAL security finding? → min "NEEDS REVISION"       │
│  │   ├─ Missing AC (plans)? → min "NEEDS REVISION"              │
│  │   └─ Avg domain score < 5.0? → min "NEEDS REVISION"          │
│  ├─ Apply consensus rules (N-based thresholds)                  │
│  ├─ Apply tiebreaker hierarchy if contested (shared-principles) │
│  ├─ Document conditions & action items                          │
│  └─ Add Captain's own assessment                                │
│                                                                 │
│  PHASE 6: RECORD VERDICT                                        │
│  ├─ Create .artifacts/reviews/{plans|code}/council/YYYY-MM-DD/  │
│  ├─ Write verdict with:                                         │
│  │   ├─ Vote tally (APPROVE/CONCERNS/REJECT by member)          │
│  │   ├─ Standards Compliance section                            │
│  │   ├─ Key findings (grouped by severity)                      │
│  │   ├─ Conditions for approval                                 │
│  │   └─ Action items                                            │
│  └─ Notify user of saved verdict & next steps                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
        ┌──────────────────────┐  ┌──────────────────────┐
        │  Council Members     │  │  Verdict Record      │
        ├──────────────────────┤  ├──────────────────────┤
        │ 8 Core:              │  │ APPROVED             │
        │  Iron Man (Arch)     │  │ WITH CONDITIONS:     │
        │  Thor (APIs)         │  │ - Fix test coverage  │
        │  Scarlet Witch (FE)  │  │ - Add rollback plan  │
        │  Hulk (Testing)      │  │                      │
        │  Black Widow (Sec)   │  │ Avg Score: 7.2/10    │
        │  Hawkeye (Mobile)    │  │                      │
        │  Vision (Data)       │  │ Saved to:            │
        │  Dr Strange (DevOps) │  │ .artifacts/reviews/  │
        │ + Optional members   │  │ {plans|code}/council │
        └──────────────────────┘  └──────────────────────┘
```

## Standards Detection Flow

```
┌────────────────────────────────────────────┐
│         Search for CLAUDE.md files         │
└────────────────────────────────────────────┘
                      │
  ┌─────────────┬─────┴────────┬───────────────┐
  │             │              │               │
  ▼             ▼              ▼               ▼
Found         Found         Found            Not found
 ./CLAUDE.md  ./.claude/    ~/.claude/      (skip)
 ✓ Read       CLAUDE.md     CLAUDE.md
 ✓ Index      ✓ Read        ✓ Read (ref only)
              ✓ Index
              ✓ Apply local
                overrides

              │
              ▼
┌────────────────────────────────────────────┐
│  CREATE STANDARDS INDEX                    │
├────────────────────────────────────────────┤
│ MANDATORY (blocks approval if violated):   │
│  - Testing coverage >= 80%                 │
│  - Commit message: imperative mood         │
│  - Black Widow signs off on security code  │
│                                            │
│ STRONG GUIDANCE (conditions if violated):  │
│  - Naming: camelCase functions             │
│  - API versioning required                 │
│  - Documentation updated                   │
│                                            │
│ ASPIRATIONAL (noted, not blocking):        │
│  - Performance optimizations               │
│  - Code comment density                    │
│  - Architecture patterns                   │
└────────────────────────────────────────────┘

              │
              ▼
┌────────────────────────────────────────────┐
│  BROADCAST TO COUNCIL MEMBERS              │
├────────────────────────────────────────────┤
│ "STANDARDS IN EFFECT:                      │
│  - Testing baseline: 80%                   │
│  - Commit format: imperative               │
│  - Security review: Black Widow mandatory  │
│                                            │
│ Apply these to your assessment."           │
└────────────────────────────────────────────┘
```

## Consensus Rules with Standards

Consensus rules applied during verdict synthesis: see @references/verdict-rules.md

## Verdict Output Format

```
┌─────────────────────────────────────────────────────────────────┐
│                       COUNCIL VERDICT                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ STATUS: [APPROVED | APPROVED WITH CONDITIONS |                  │
│          NEEDS REVISION | BLOCKED]                              │
│                                                                 │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ STANDARDS COMPLIANCE                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                 │
│ Applicable Standards:                                           │
│ ✓ Line 42: Testing coverage >= 80%                              │
│ ✓ Line 92: Commit format imperative                             │
│ ✓ Line 156: Black Widow review (security)                       │
│                                                                 │
│ Compliance Status:                                              │
│ ✓ Testing: 85% coverage                                         │
│ ✓ Commit: Format correct                                        │
│ ✗ Security: Black Widow review pending                          │
│                                                                 │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ VOTE TALLY                                                      │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                 │
│ APPROVE (6):        Iron Man, Thor, Scarlet Witch,              │
│                     Hulk, Hawkeye, Vision                       │
│                                                                 │
│ CONCERNS (2):       Black Widow, Doctor Strange                 │
│                                                                 │
│ REJECT (0):         None                                        │
│                                                                 │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ KEY FINDINGS (by severity)                                      │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                 │
│ 🔴 CRITICAL                                                     │
│  • Black Widow: Code lacks crypto review                        │
│    → Mandatory standard #1 (line 156)                           │
│    → Must resolve before approval                               │
│                                                                 │
│ 🟡 HIGH                                                         │
│  • Hulk: Test coverage at 85%, target 90%                       │
│    → Strong guidance, not blocking                              │
│                                                                 │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ CONDITIONS FOR APPROVAL                                         │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                 │
│ 1. Schedule Black Widow crypto review (MANDATORY — line 156)    │
│ 2. Increase test coverage to 90% (Hulk's recommendation)        │
│                                                                 │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ ACTION ITEMS                                                    │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                 │
│ For the user:                                                   │
│ [ ] Schedule Black Widow review of crypto code                  │
│ [ ] Add tests to reach 90% coverage                             │
│ [ ] Resubmit for final spot-check                               │
│                                                                 │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ CAPTAIN AMERICA'S ASSESSMENT                                    │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                 │
│ This proposal aligns with our architecture standards and        │
│ design patterns. The testing baseline is nearly met. However,   │
│ the mandatory security review (CLAUDE.md line 156) must be      │
│ completed before we can ship. Black Widow's concerns are        │
│ legitimate — crypto code requires expert review.                │
│                                                                 │
│ Fix the conditions above and resubmit. I'm confident we'll      │
│ get to APPROVED WITH CONDITIONS (conditions satisfied).         │
│                                                                 │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ SAVED TO                                                        │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                 │
│ .artifacts/reviews/{plans|code}/council/2026-02-13/154230-...   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Command Flow Diagrams

### Plan Review Flow

```
START: /avengers-council:plan-review @proposal.md
  │
  ├─ Captain reads proposal
  ├─ Captain detects CLAUDE.md standards
  ├─ Captain audits codebase (structure, naming, architecture)
  ├─ Captain determines roster (core + matching optional members)
  ├─ Captain validates: Does plan include AC? (Yes/No)
  │
  ├─ TeamCreate("avengers-council")
  ├─ Spawn N teammates with context (standards, audit, principles, red lines)
  │
  ├─ ROUND 1: Agents self-start assessment
  │  └─ Collect N responses (verdict + domain score + findings)
  │
  ├─ ROUND 2: Challenge & peer debate
  │  └─ Members send direct challenges to teammates
  │
  ├─ ROUND 3: Final positions
  │  └─ Collect final verdicts + updated domain scores + confidence
  │
  ├─ Captain synthesizes:
  │  ├─ Tallies votes + computes avg domain score
  │  ├─ Checks: Red line violations?
  │  ├─ Checks: Standards violated?
  │  ├─ Checks: Avg score < 5.0?
  │  ├─ Checks: CRITICAL findings?
  │  ├─ Applies N-based consensus rules
  │  ├─ Applies tiebreaker hierarchy if contested
  │  └─ Adds conditions if needed
  │
  ├─ Captain records verdict:
  │  ├─ Create .artifacts/reviews/plans/council/YYYY-MM-DD/
  │  ├─ Write verdict with scores, standards, conditions
  │  └─ Notify user
  │
  └─ END: Verdict saved + action items listed
```

### Code Review Flow

```
START: /avengers-council:code-review --pr 123
  │
  ├─ Captain gets PR diff
  ├─ Captain detects CLAUDE.md standards
  ├─ Captain audits codebase (structure, naming, architecture)
  ├─ Captain determines roster (core + matching optional members)
  ├─ Captain validates:
  │  ├─ Commit message format (Yes/No)
  │  ├─ Test coverage baseline (Yes/No)
  │  └─ Security-sensitive code? (Yes → Black Widow mandatory)
  │
  ├─ TeamCreate("avengers-council")
  ├─ Spawn N teammates with context (diff, standards, audit, principles, red lines)
  │
  ├─ ROUND 1: Agents self-start assessment
  │  └─ Collect N responses (verdict + domain score + findings)
  │
  ├─ ROUND 2: Challenge specific findings
  │  └─ Members debate code issues directly
  │
  ├─ ROUND 3: Final positions
  │  └─ Collect final verdicts + updated domain scores + confidence
  │
  ├─ Captain synthesizes:
  │  ├─ Tallies votes + computes avg domain score
  │  ├─ Checks: Red line violations?
  │  ├─ Checks: Standards violated?
  │  ├─ Checks: Avg score < 5.0?
  │  ├─ Checks: CRITICAL findings?
  │  ├─ Applies N-based consensus rules
  │  ├─ Applies tiebreaker hierarchy if contested
  │  └─ Adds conditions if needed
  │
  ├─ Captain records verdict:
  │  ├─ Create .artifacts/reviews/code/council/YYYY-MM-DD/
  │  ├─ Write verdict with scores, standards, conditions,
  │  │   file:line references, suggested fixes
  │  └─ Notify user
  │
  └─ END: Verdict saved + action items listed
```

## Summary

Captain America enforces project standards, shared principles, and red lines in every council review:

1. **Detecting** standards (CLAUDE.md), auditing codebase structure
2. **Determining** roster — core members + topic-matched optional members
3. **Indexing** standards by impact (Mandatory, Strong, Aspirational)
4. **Validating** against red lines and shared principles
5. **Scoring** — each member provides a domain score; aggregate < 5.0 overrides approval
6. **Applying** N-based consensus rules with graduated escalation hierarchy
7. **Recording** verdicts with scores, standards compliance, and conditions

Key references: `member-registry.md` (roster), `shared-principles.md` (tiebreakers), `red-lines.md` (non-negotiables), `verdict-rules.md` (consensus).

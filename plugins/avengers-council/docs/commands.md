# Avengers Council Command Reference

Comprehensive reference for Avengers Council commands: `plan-review` and `code-review`.

---

## Command Comparison

| Feature | `/avengers-council:plan-review` | `/avengers-council:code-review` |
|---------|-------------------------|--------------------------------|
| **Purpose** | Review plans, design specs, PRDs, `.claude/plans/` files | Review code changes, diffs, PRs |
| **Input** | Topic, file path, or auto-detects `.claude/plans/` | Diff, PR number, or files |
| **Review Type** | Design, architecture & plan completeness | Code & implementation |
| **Auto-invoked** | Yes (via ExitPlanMode hook) or manual | No |
| **Typical Use** | Before implementation / after plan mode | Before merge |
| **Performance** | 30-60 min (full) / 5-10 min (quick) | 30-60 min (full) / 5-10 min (quick) |

---

## When to Use Each Command

### Use `/avengers-council:plan-review` when:
- Evaluating a design decision before implementation begins
- Reviewing architectural specs, PRDs, or technical proposals
- Discussing framework choices, system design, or patterns
- Planning major refactors or migrations
- Exiting plan mode (auto-invoked by hook, or run with no args to auto-detect)
- Manually reviewing a generated `.claude/plans/` file
- Need broader perspective on "should we build this?" or "is this plan complete?"

### Use `/avengers-council:code-review` when:
- Reviewing code changes before merging
- Auditing security-sensitive code
- Checking PRs for quality, correctness, and standards
- Validating implementation against plan
- Need feedback on "is this code ready to ship?"

---

## `/avengers-council:plan-review`

### Purpose

Review planning decisions, design specifications, PRDs, or architectural plans through structured debate with the Avengers Council. Get consensus feedback before implementation begins.

### Syntax

```bash
/avengers-council:plan-review [topic or @file] [--focus <area>] [--quick]
```

### Arguments

| Argument | Type | Description | Required |
|----------|------|-------------|----------|
| `topic or @file` | string | Free-text topic OR file path (e.g., `@docs/architecture.md`) | Yes |
| `--focus <area>` | string | Filter by specialty area (see options below) | No |
| `--quick` | flag | Run 3-member quorum instead of full council | No |

#### `--focus` Options

- `security` — Security & privacy concerns (Black Widow leads)
- `mobile` — Android, iOS, cross-platform (Hawkeye leads)
- `architecture` — System design & scalability (Iron Man leads)
- `testing` — Test strategy & quality (Hulk leads)
- `delivery` — DevOps, CI/CD, deployment (Doctor Strange leads)
- `frontend` — UI, UX, web components (Scarlet Witch leads)
- `backend` — APIs, databases, server logic (Thor leads)
- `devops` — Infrastructure, containers, orchestration (Doctor Strange leads)
- `data` — Data models, observability, analytics (Vision leads)

### Examples

#### Example 1: Review a Plan File

```bash
/avengers-council:plan-review @.claude/plans/phase-1-auth.md
```

**What happens:**
1. Captain America reads the plan file
2. Full council (full council) reviews through 3 debate rounds
3. Each member applies their specialty checklist
4. Consensus verdict delivered with findings and action items
5. Verdict saved to `.artifacts/reviews/plans/council/YYYY-MM-DD/HHMMSS-review-{verdict}.md`

**Typical output:**
```
# Avengers Council Verdict

## Topic
Phase 1: Authentication System Plan

## Consensus: APPROVED WITH CONDITIONS
Vote: 6 Approve / 2 Concerns / 0 Reject

## Executive Summary
The authentication plan is solid with industry-standard patterns (OAuth2, JWT, RBAC).
Two critical conditions: add rate limiting for login endpoints and define token rotation strategy.
```

**Performance:** 30-60 minutes (full council)

---

#### Example 2: Review a Topic

```bash
/avengers-council:plan-review "Migrate from REST to GraphQL for mobile API"
```

**What happens:**
1. Captain America scans codebase for relevant context
2. Reads existing API code, mobile client code, CLAUDE.md conventions
3. Council debates migration strategy
4. Hawkeye and Thor lead discussion (mobile + backend)
5. Verdict includes migration risks, prerequisites, and recommended approach

**Typical output includes:**
- Hawkeye: Offline-first concerns, payload size, caching strategy
- Thor: Schema design, resolver performance, N+1 query risks
- Black Widow: Authorization at field level, rate limiting, query complexity
- Vision: Observability, query tracing, monitoring strategy

**Performance:** 30-60 minutes (full council)

---

#### Example 3: Quick Security Review

```bash
/avengers-council:plan-review @docs/api-design.md --quick --focus security
```

**What happens:**
1. `--quick` mode activates 3-member quorum
2. `--focus security` selects Black Widow + Thor (security + backend)
3. Single-round assessment (no challenge round)
4. Faster verdict focused on security concerns

**Quorum:**
- Captain America (orchestrator)
- Black Widow (security lead)
- Thor (backend perspective)

**Typical output:**
```
## Consensus: NEEDS REVISION
Vote: 0 Approve / 1 Concerns / 2 Reject

## Key Findings (CRITICAL)
- API exposes internal database IDs (enumeration vulnerability)
- No rate limiting on auth endpoints (brute force risk)
- JWT tokens never expire (session hijacking risk)
```

**Performance:** 5-10 minutes (quick mode)

---

#### Example 4: Architecture-Focused Review

```bash
/avengers-council:plan-review "Event-driven architecture for order processing" --focus architecture
```

**What happens:**
1. Full council convenes
2. `--focus architecture` highlights architecture findings in output
3. Iron Man and Doctor Strange lead on system design and deployment
4. All members still participate, but architecture findings prioritized

**Typical Iron Man findings:**
- Event schema versioning strategy
- Message ordering guarantees
- Partition key design for scaling
- Error handling and dead letter queues

**Performance:** 30-60 minutes (full council)

---

#### Example 5: Mobile-First Plan Review

```bash
/avengers-council:plan-review @.planning/offline-mode-spec.md --focus mobile
```

**What happens:**
1. Full council reviews offline-mode specification
2. Hawkeye leads on mobile concerns
3. Vision adds data sync perspective
4. Doctor Strange considers deployment to app stores

**Typical Hawkeye findings:**
- Offline data storage limits (SQLite vs Realm vs custom)
- Sync conflict resolution strategy
- Battery impact of background sync
- Network detection and retry logic
- App size impact of bundled data

**Performance:** 30-60 minutes (full council)

---

### Output Format

All verdicts follow this structure:

```markdown
# Avengers Council Verdict

## Topic
[What was reviewed]

## Consensus: [APPROVED | APPROVED WITH CONDITIONS | NEEDS REVISION | BLOCKED]
Vote: X Approve / X Concerns / X Reject

## Executive Summary
[Captain America's 2-3 sentence overview]

## Council Positions

### Iron Man (Architecture & Scalability) — [VERDICT]
- [Finding 1 with severity]
- [Finding 2 with severity]

### Thor (Backend & API) — [VERDICT]
[...]

[... all council members ...]

## Disagreements
[Unresolved debates between members]

## Tiebreaker (if applicable)
[Captain America's deciding vote with reasoning]

## Conditions for Approval
[Must-fix items before proceeding]

## Action Items
1. [Specific action with owner suggestion]
2. [...]
```

### Consensus Rules

Full consensus rules and severity guidelines: see @references/verdict-rules.md

### Performance Notes

**Full Mode (full council):**
- **Duration:** 30-60 minutes
- **Model usage:** 1x Opus (Iron Man) + 7x Sonnet (other members) + 1x Captain America (session model)
- **Token cost:** High (full context shared with all agents across 3 rounds)
- **Best for:** Major decisions, security-critical plans, cross-team impact

**Quick Mode (3 members):**
- **Duration:** 5-10 minutes
- **Model usage:** 2x Sonnet (selected members) + 1x Captain America (session model)
- **Token cost:** Low (single round, focused review)
- **Best for:** Focused reviews, time-sensitive decisions, smaller scope

**Member Selection (Quick Mode):**
When `--quick` is specified, Captain America selects the 2 most relevant members based on `--focus` or topic analysis:

| Focus Area | Selected Members |
|------------|------------------|
| `security` | Black Widow + Thor |
| `mobile` | Hawkeye + Doctor Strange |
| `architecture` | Iron Man + Doctor Strange |
| `testing` | Hulk + Iron Man |
| `delivery` | Doctor Strange + Hulk |
| `frontend` | Scarlet Witch + Thor |
| `backend` | Thor + Vision |
| `devops` | Doctor Strange + Iron Man |
| `data` | Vision + Thor |
| No focus | Analyze topic and pick 2 most relevant |

---

## `/avengers-council:code-review`

### Purpose

Review code changes (diffs, pull requests, specific files) with the Avengers Council. Get consensus feedback on implementation quality, correctness, security, and standards compliance before merging.

### Syntax

```bash
/avengers-council:code-review [--pr <number>] [--diff] [--files <paths>] [--focus <area>] [--quick]
```

### Arguments

| Argument | Type | Description | Required |
|----------|------|-------------|----------|
| `--pr <number>` | number | Review a GitHub pull request by number | No |
| `--diff` | flag | Review unstaged changes (default if no args) | No |
| `--files <paths>` | string | Review specific files (comma-separated paths) | No |
| `--focus <area>` | string | Filter by specialty area (see `plan` command) | No |
| `--quick` | flag | Run 3-member quorum instead of full council | No |

**Default behavior:** If no arguments provided, defaults to `--diff` (reviews unstaged changes).

### Examples

#### Example 1: Review Unstaged Changes (Default)

```bash
/avengers-council:code-review
```

**What happens:**
1. Captain America runs `git diff` and `git diff --cached`
2. Combines unstaged and staged changes
3. Full council reviews the diff through their code review checklists
4. Each finding includes file:line reference and suggested fix

**Typical output includes:**
- Hulk: Missing test coverage for new LoginViewModel
- Black Widow: SQL injection risk in UserRepository.findByEmail() line 45
- Scarlet Witch: Accessibility issue - missing contentDescription on ImageButton
- Thor: N+1 query in getUserOrders() endpoint

**Performance:** 30-60 minutes (full council)

---

#### Example 2: Review Pull Request

```bash
/avengers-council:code-review --pr 789
```

**What happens:**
1. Captain America runs `gh pr view 789` and `gh pr diff 789`
2. Reads PR description for context
3. Full council reviews all changes in the PR
4. Verdict considers PR metadata (title, description, labels)

**Typical output:**
```
# Avengers Council Verdict

## Topic
PR #789: Add user authentication with OAuth2

## Consensus: APPROVED WITH CONDITIONS
Vote: 7 Approve / 2 Concerns / 0 Reject

## Key Findings

### CRITICAL
None

### HIGH
1. [Black Widow] Missing rate limiting on /auth/login endpoint (security.ts:23)
   - Suggested fix: Add rate limiter middleware (express-rate-limit)
2. [Vision] No observability for token refresh operations
   - Suggested fix: Add logging and metrics for auth events

### MEDIUM
1. [Hulk] AuthService lacks unit tests
   - Suggested fix: Add tests for token validation, refresh, revocation
```

**Performance:** 30-60 minutes (full council)

---

#### Example 3: Review Specific Files

```bash
/avengers-council:code-review --files src/auth/AuthService.ts,src/db/UserRepository.ts
```

**What happens:**
1. Captain America reads both files
2. Runs `git diff` on those specific files
3. Runs `git log -5` on those files for recent history context
4. Council reviews focused on those 2 files only

**Use case:** When specific files changed and you want focused review without full diff noise.

**Performance:** 30-60 minutes (full council)

---

#### Example 4: Quick Security Review of PR

```bash
/avengers-council:code-review --pr 123 --quick --focus security
```

**What happens:**
1. `--quick` activates 3-member quorum
2. `--focus security` selects Black Widow + Thor
3. Captain America fetches PR diff
4. Single-round code review focused on security

**Quorum:**
- Captain America (orchestrator)
- Black Widow (security lead)
- Thor (backend perspective)

**Typical Black Widow findings:**
- SQL injection vulnerabilities
- XSS risks in template rendering
- Auth/authorization bypass opportunities
- Exposed secrets or API keys
- Insecure crypto usage

**Performance:** 5-10 minutes (quick mode)

---

#### Example 5: Quick Mobile Code Review

```bash
/avengers-council:code-review --files app/ProfileViewModel.kt,app/SettingsScreen.kt --quick --focus mobile
```

**What happens:**
1. `--quick` + `--focus mobile` selects Hawkeye + Doctor Strange
2. Reviews 2 Kotlin files
3. Focused on mobile-specific concerns

**Quorum:**
- Captain America (orchestrator)
- Hawkeye (mobile lead)
- Doctor Strange (deployment/cross-platform)

**Typical Hawkeye findings:**
- Memory leaks (leaked Activity context)
- Lifecycle violations (launching coroutines in wrong scope)
- Threading issues (UI operations off main thread)
- Jetpack Compose best practices
- App size impact of dependencies

**Performance:** 5-10 minutes (quick mode)

---

### Output Format

Same structure as `/avengers-council:plan-review`, with additional code-specific details:

```markdown
## Key Findings

### CRITICAL
1. [Black Widow] SQL injection in UserRepository.findByEmail() (UserRepository.ts:45)
   - Issue: Unsanitized user input in SQL query
   - Suggested fix: Use parameterized queries or ORM
   - Reference: OWASP A03:2021 - Injection

### HIGH
[...]

### MEDIUM
[...]

### LOW
[...]
```

**Enhancements:**
- All findings include `file:line` references
- Suggested fixes provided where applicable
- Security findings reference OWASP or CVE standards
- Performance findings include profiler or benchmark suggestions
- Test findings include example test cases

### Consensus Rules

Same as `/avengers-council:plan-review` command (see above).

### Performance Notes

**Full Mode:**
- **Duration:** 30-60 minutes
- **Best for:** Pre-merge review, security audits, large PRs

**Quick Mode:**
- **Duration:** 5-10 minutes
- **Best for:** Iterative reviews, focused checks, time-sensitive merges

**Member Selection (Quick Mode):**
When `--quick` + code changes detected, Captain America selects members based on affected code areas:

| Code Area | Selected Members |
|-----------|------------------|
| API routes | Thor + Black Widow |
| UI components | Scarlet Witch + Hulk |
| Infra/CI/CD | Doctor Strange + Iron Man |
| Mobile code | Hawkeye + Doctor Strange |
| Data/models | Vision + Thor |
| Mixed | Iron Man + Hulk |

---

## Common Workflows

### Workflow 1: Plan → Review → Implement

```bash
# Step 1: Create plan
Enter plan mode, produce `.claude/plans/feature-x.md`

# Step 2: Review plan (auto or manual — auto-detects .claude/plans/)
/avengers-council:plan-review

# Step 3: Address findings
Update plan based on verdict conditions

# Step 4: Implement
Proceed with implementation

# Step 5: Pre-merge review
/avengers-council:code-review --pr 123
```

**Duration:** Plan review (30-60 min) + Code review (30-60 min) = 1-2 hours total council time

---

### Workflow 2: Quick Iteration with Focused Reviews

```bash
# Step 1: Quick plan check
/avengers-council:plan-review @docs/api-change.md --quick --focus backend

# Step 2: Implement based on feedback

# Step 3: Quick code review
/avengers-council:code-review --quick --focus backend

# Step 4: Merge after approval
```

**Duration:** Quick plan (5-10 min) + Quick code (5-10 min) = 10-20 minutes total

---

### Workflow 3: Security-Critical Feature

```bash
# Step 1: Full security-focused plan review
/avengers-council:plan-review @.planning/auth-redesign.md --focus security

# Step 2: Address Black Widow's findings

# Step 3: Implement with security measures

# Step 4: Full security-focused code review
/avengers-council:code-review --pr 456 --focus security

# Step 5: Re-review if BLOCKED or NEEDS REVISION
```

**Duration:** 2 full reviews (60-120 minutes total) - appropriate for security-critical changes

---

## Troubleshooting

### "No plan file found"

**Problem:** `/avengers-council:plan-review` can't auto-detect a plan file

**Solution:**
```bash
# Option 1: Specify file explicitly
/avengers-council:plan-review @path/to/plan.md

# Option 2: Check plan directory
ls .claude/plans/
```

---

### "Review taking too long"

**Problem:** Full council review is taking 60+ minutes

**Solution:**
```bash
# Use quick mode for faster reviews
/avengers-council:plan-review @file.md --quick

# Or focus on specific area
/avengers-council:plan-review @file.md --quick --focus security
```

**Expected performance:**
- Full mode: 30-60 minutes
- Quick mode: 5-10 minutes

---

### "Which command should I use?"

**Decision tree:**

1. **Reviewing a design/plan before coding?**
   - Use `/avengers-council:plan-review`

2. **Reviewing code changes?**
   - Use `/avengers-council:code-review`

3. **Just exited plan mode?**
   - Use `/avengers-council:plan-review` with no args (auto-detects `.claude/plans/` files, or auto-runs via hook)

4. **Not sure?**
   - Plans/specs/design/`.claude/plans/` → `plan`
   - Code/diff/PR → `code-review`

---

### "What if council is split or disagrees?"

**Tiebreaker Protocol:**

1. If votes don't meet consensus thresholds, Captain America casts deciding vote
2. Tiebreaker reasoning documented in verdict under "Tiebreaker" section
3. All member positions preserved in verdict for context
4. Disagreements documented in "Disagreements" section

**Example:**
```markdown
## Tiebreaker
Captain America casts deciding vote: APPROVED WITH CONDITIONS

Reasoning: While Iron Man and Doctor Strange raise valid scalability concerns,
the plan includes clear performance benchmarks and a scaling roadmap.
The conditions (adding load tests and defining SLOs) adequately mitigate the risks.
```

---

### "Can I override Black Widow's veto?"

**No.** Black Widow's veto power on CRITICAL security issues cannot be overridden.

**Rationale:** Shipping code with unmitigated CRITICAL security vulnerabilities is never acceptable.

**Workaround:** Address the security issue, then re-run the review:
```bash
# After fixing the vulnerability
/avengers-council:code-review --pr 123 --quick --focus security
```

---

## Best Practices

### When to Use Full Mode vs Quick Mode

**Use Full Mode (full council) when:**
- Major architectural decisions
- Security-critical changes
- Cross-team impact (API changes, breaking changes)
- Large multi-file PRs
- Unfamiliar territory (new frameworks, patterns)

**Use Quick Mode (3 members) when:**
- Time-sensitive reviews
- Small focused changes
- Iterative feedback loops
- Clear single-domain changes (e.g., pure frontend)
- Second-pass reviews after addressing findings

---

### Combining Flags Effectively

**Pattern 1: Focused Quick Review**
```bash
/avengers-council:code-review --pr 123 --quick --focus mobile
```
**Use case:** Fast mobile-specific review before merge

**Pattern 2: Security-First Full Review**
```bash
/avengers-council:plan-review @docs/payment-flow.md --focus security
```
**Use case:** Comprehensive security evaluation (still uses full council, security findings prioritized)

**Pattern 3: Specific Files with Focus**
```bash
/avengers-council:code-review --files AuthService.ts --quick --focus security
```
**Use case:** Laser-focused security audit of single file

---

### Interpreting Verdicts

**APPROVED:**
- Ship it. No blocking issues.
- Consider LOW/MEDIUM findings for future iterations

**APPROVED WITH CONDITIONS:**
- Ship after addressing conditions
- Conditions are typically HIGH severity issues
- Re-review not required unless specified

**NEEDS REVISION:**
- Do not ship. Address CRITICAL/HIGH issues first.
- Re-run review after fixes:
  ```bash
  /avengers-council:code-review --quick  # Faster re-review
  ```

**BLOCKED:**
- Stop. Significant problems found.
- Address all blocking issues
- Consider redesigning approach
- Full re-review required after fixes

---

### Verdict Archiving

All council verdicts are automatically saved to:
```
.artifacts/reviews/{plans|code}/council/YYYY-MM-DD/HHMMSS-review-{verdict}.md
```

**Benefits:**
- Permanent audit trail of decisions
- Reference past debates for similar issues
- Track architectural evolution over time
- Onboarding resource for new team members

**Example:**
```
.artifacts/reviews/
├── plans/council/
│   ├── 2026-02-13/
│   │   └── 103045-review-approved.md       # Approved plan review
│   └── 2026-02-14/
│       └── 091500-review-approved.md       # Quick review that passed
└── code/council/
    └── 2026-02-13/
        ├── 143020-review-concerns.md       # Code review with conditions
        └── 173000-review-blocked.md        # Blocked PR (security issues)
```

**Access later:**
```bash
# View past plan reviews
ls .artifacts/reviews/plans/council/2026-02-13/

# View past code reviews
ls .artifacts/reviews/code/council/2026-02-13/

# Read specific verdict
cat .artifacts/reviews/plans/council/2026-02-13/103045-review-approved.md
```

---

## Advanced Usage

### Custom Quorum Selection

While `--quick` automatically selects 2 relevant members, custom quorums can be suggested by modifying the command logic:

**Example:** "I need frontend + testing + security review"
```
Quorum: Scarlet Witch (frontend), Hulk (testing), Black Widow (security)
```

**Note:** This requires modifying the command implementation. Current version supports `--focus` for automated selection.

---

### Chaining Reviews

**Pattern:** Plan review → Address findings → Code review

```bash
# Step 1: Review plan
/avengers-council:plan-review @.planning/feature-x.md
# Output: APPROVED WITH CONDITIONS (add error handling, define test strategy)

# Step 2: Update plan to address conditions
Update plan file

# Step 3: Implement based on updated plan
Code the feature

# Step 4: Review implementation
/avengers-council:code-review
# Output: APPROVED (all plan conditions satisfied)
```

---

### Integrating with Git Hooks

**Use case:** Require council review before pushing to main

**Setup:**
```bash
# .git/hooks/pre-push
#!/bin/bash
if [ "$BRANCH" = "main" ]; then
  echo "Council review required for main branch"
  # Trigger council review workflow
fi
```

**Note:** This is an advanced integration example. Standard usage is manual invocation.

---

## Summary

### Command Quick Reference

```bash
# Review a plan, design, or auto-detect .claude/plans/ file
/avengers-council:plan-review [topic or @file] [--focus <area>] [--quick]

# Review code changes
/avengers-council:code-review [--pr <number>] [--diff] [--files <paths>] [--focus <area>] [--quick]
```

### Key Takeaways

1. **Use the right command:** Plans/specs/design → `plan`, Code → `code-review`
2. **Quick mode for speed:** 5-10 min instead of 30-60 min
3. **Focus for specificity:** `--focus security` prioritizes security findings
4. **Read the verdict:** APPROVED (ship), CONDITIONS (fix then ship), REVISION (fix then re-review), BLOCKED (stop)
5. **Black Widow veto:** Cannot be overridden on CRITICAL security issues
6. **Archive for history:** All verdicts saved to `.artifacts/reviews/{plans|code}/council/`


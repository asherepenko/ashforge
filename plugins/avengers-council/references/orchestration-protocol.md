# Avengers Council Orchestration Protocol

Shared flow for all council commands. Each command handles context gathering independently, then delegates to this protocol for team orchestration.

> **Cost note:** Full mode spawns 8 core teammates + any matching optional members (~8-10x single-session cost).
> Recommend Quick Mode (3 members) for non-critical reviews.
> Full mode is justified for: security-sensitive changes, architectural decisions, pre-release reviews.

## Table of Contents

- [Standards Detection](#standards-detection-shared-across-all-commands) — project conventions discovery
- [Codebase Audit](#codebase-audit-shared-across-all-commands) — project structure, naming, architecture grounding
- [Phase 1 — Assemble the Council](#phase-1--assemble-the-council-full-mode) — team creation, agent spawning, quorum rules
- [Phase 2 — Round 1](#phase-2--round-1-collect-initial-assessments) — initial assessments
- [Phase 3 — Rounds 2 & 3](#phase-3--rounds-2--3-challenge-and-final-position) — challenge and final position
- [Phase 4 — Synthesize Verdict](#phase-4--synthesize-verdict) — voting, consensus rules, Black Widow VETO
- [Phase 5 — Save Verdict](#phase-5--save-verdict) — write to `.artifacts/reviews/`
- [Phase 6 — Interactive Follow-up](#phase-6--interactive-follow-up) — post-verdict actions
- [Phase 7 — Cleanup](#phase-7--cleanup) — shutdown and team deletion
- [Quick Mode](#quick-mode-3-member-quorum) — 3-member quorum, member selection tables, abbreviated flow

## Standards Detection (shared across all commands)

Before assembling the council, perform standards detection per @references/standards-protocol.md (Phases 1 & 2: discover project standards and categorize by impact). Include the discovered standards — with their category (mandatory / strong guidance / aspirational) — in the review context distributed to agents.

The full standards lifecycle (detection → categorization → application → verdict impact) is owned by `standards-protocol.md`; this orchestration protocol only triggers it at the right moment.

## Codebase Audit (shared across all commands)

After standards detection, Captain America performs a codebase audit to ground the review in the actual project structure. Include the audit summary in the review context distributed to agents.

1. **Directory structure**: Run `ls` or Glob on the project root and key directories to map how the project organizes code (by feature, by layer, by domain)
2. **Naming conventions**: Sample existing files, functions, and modules to identify established patterns (casing, prefixes, suffixes, pluralization)
3. **Architecture patterns**: Read entry points, routers, configs, or barrel exports to identify the architecture style (MVC, hexagonal, feature-sliced, modular monolith, etc.)
4. **Summarize**: Include a brief audit summary in the review context:
   ```
   CODEBASE AUDIT:
   - Structure: [e.g., feature-sliced with src/{feature}/{layer}]
   - Naming: [e.g., camelCase files, PascalCase components, kebab-case routes]
   - Architecture: [e.g., hexagonal with ports/adapters, dependency injection via Hilt]
   - Key patterns: [e.g., Repository pattern, ViewModel + StateFlow, Room DAOs]
   ```

This audit ensures agents evaluate proposals against the codebase as it actually exists, not as they imagine it. Agents should flag any proposed changes that deviate from the established structure, naming, or patterns.

## Phase 1 — Assemble the Council (Full Mode)

YOU are Captain America — the session model running the command.

### Step 1: Determine Active Roster

Read @references/member-registry.md to build the active roster:

1. **Core members**: Always included — all 8 core members from the registry.
2. **Optional members**: Scan the review topic against each optional member's `Invoke When` criteria and focus tags. If the topic matches, include that member.
3. **Announce**: If any optional members are joining, state which ones and why.
4. **Calculate thresholds**:
   - Let **N** = total active voters (core + optional + Captain America)
   - **Majority** = floor(N / 2) + 1
   - **Minimum quorum** = floor(N * 0.625) (rounds down; e.g., 9→5, 10→6, 11→6)
   - **Timeout threshold** = floor(N * 0.75) (rounds down; e.g., 9→6, 10→7, 11→8)

### Step 2: Create Team

Call `TeamCreate` with:
- `team_name`: "avengers-council"
- `description`: "Reviewing: [topic summary from calling command]"

### Step 3: Spawn Teammates

Spawn all active roster members using the `Agent` tool. Launch ALL in a SINGLE message for parallel startup.

Each spawn call embeds the FULL review context and Round 1 instructions so agents self-start immediately (teammates only receive their spawn prompt + CLAUDE.md — they do NOT get the lead's conversation history):

```
Agent({
  name: "[agent-name]",
  subagent_type: "avengers-council:[agent-name]",
  team_name: "avengers-council",
  prompt: "You are [agent-name] on the Avengers Council reviewing: [topic summary]

REVIEW CONTEXT:
[full context OR 'Read the review context from .artifacts/tmp/council-context.md']

STANDARDS IN EFFECT:
[applicable standards list]

CODEBASE AUDIT:
[audit summary from Codebase Audit step]

SHARED PRINCIPLES:
Review proposals against the council's shared principles (references/shared-principles.md).
Check for red line violations (references/red-lines.md) in your domain.

ROUND 1 INSTRUCTIONS:
Review this from your specialty lens using your [planning|code review] checklist.
Send your assessment to captain-america with:
- Verdict: APPROVE / CONCERNS / REJECT
- Domain Score: X/10 (your domain)
- Key Findings: max 5, each with severity (CRITICAL/HIGH/MEDIUM/LOW)
- Red Line Violations: any from references/red-lines.md (or 'None')
- Recommendation: 1-2 sentences

Then broadcast your key findings to all teammates.

After Round 1, wait for captain-america to signal Round 2 (challenge) and Round 3 (final position).
Follow the debate protocol from your agent definition for all rounds.",
  description: "[Agent Name] reviewing [topic]"
})
```

**Core agent roster** (always spawned):

| Name | subagent_type |
|------|--------------|
| iron-man | avengers-council:iron-man |
| thor | avengers-council:thor |
| scarlet-witch | avengers-council:scarlet-witch |
| hulk | avengers-council:hulk |
| black-widow | avengers-council:black-widow |
| hawkeye | avengers-council:hawkeye |
| vision | avengers-council:vision |
| doctor-strange | avengers-council:doctor-strange |

**Optional members** are listed in @references/member-registry.md. Spawn any that matched in Step 1 using the same prompt template.

**Context optimization:** If the review context exceeds 200 lines (large diffs, multi-file PRs), write it to `.artifacts/tmp/council-context.md` and reference it in the spawn prompt rather than embedding in each prompt.

### Context Management

If the review target exceeds 500 lines (large PR, lengthy plan), summarize changes by file before distributing to agents. Provide full content path so agents can read sections on demand. Do not paste entire diffs into agent prompts — this wastes context and reduces analysis quality.

### Step 4: Timeout and Quorum

- Wait for teammate responses. Messages from teammates are delivered automatically.
- **Timeout policy:** If fewer than the timeout threshold (Step 1) respond, proceed with available responses. Note which members were silent in the verdict.
- **Minimum quorum:** At least the minimum quorum (Step 1) responses required. If fewer respond, report the issue to the user and ask whether to proceed with available responses or retry.

## Phase 2 — Round 1: Collect Initial Assessments

Agents self-start Round 1 immediately from their spawn prompt — no broadcast needed.

1. Create task: "Round 1 — Initial Assessment" via TaskCreate (optional — for progress tracking), mark in_progress
2. Collect responses (apply timeout policy from Phase 1 Step 3)
3. Mark Round 1 task as completed

## Phase 3 — Rounds 2 & 3: Challenge and Final Position

After collecting Round 1 responses, send ONE broadcast to trigger both remaining rounds (1 broadcast = 8 messages):

1. Create task: "Rounds 2 & 3 — Challenge and Final Position" via TaskCreate (optional — for progress tracking), mark in_progress
2. Broadcast to all members via SendMessage (type: broadcast):

   ```
   ROUND 1 COMPLETE.

   Summary of Round 1 findings:
   [Brief summary of each member's verdict and key findings]

   ROUND 2 — CHALLENGE:
   Review your teammates' findings above. DM teammates you disagree with to challenge their position. Support findings you agree with.

   ROUND 3 — FINAL POSITION:
   After your challenges, send your final position to captain-america with:
   - Verdict: APPROVE / CONCERNS / REJECT
   - Final Domain Score: X/10 (your domain)
   - Confidence: HIGH / MEDIUM / LOW
   - Unresolved Disagreements: reference specific teammate exchanges
   - Key Condition: what must change for CONCERNS to become APPROVE
   ```

3. **Completion gate:** Wait until all active members send their final position to captain-america. Apply same timeout policy — if members don't signal completion, proceed after receiving signals from the quorum.
4. Mark task as completed

## Phase 4 — Synthesize Verdict

1. **Validate standards compliance** (per @references/standards-protocol.md):
   - Check if plan/code violates mandatory project standards
   - If CRITICAL standard violation → automatic "NEEDS REVISION" minimum

2. **Check red lines** (per @references/red-lines.md):
   - Collect all red line violations flagged by agents
   - Any unmitigated red line violation → minimum "NEEDS REVISION"

3. **Tally votes:** count APPROVE, CONCERNS, REJECT from all responding members

4. **Compute aggregate domain score:**
   - Collect final domain scores from all responding members
   - Calculate average per @references/verdict-rules.md#domain-scoring
   - If average < 5.0 and vote tally yields APPROVED → downgrade to NEEDS REVISION

5. **Apply consensus rules** per @references/verdict-rules.md (single source of truth — do not restate here)
   - For contested votes, apply the escalation hierarchy from verdict-rules.md

6. **Check Black Widow VETO** — if CRITICAL security finding is unmitigated → override to BLOCKED

7. **Add Captain America's assessment:** standards compliance, acceptance criteria, codebase audit alignment, conditions

8. **Format verdict** using @references/verdict-template.md (includes domain scores table and aggregate)

## Phase 5 — Save Verdict

Write verdict to permanent record:

1. Determine verdict slug: approved/revision/blocked
2. Determine review type directory: plans or code (passed by calling command)
3. Create directory and save:
   ```bash
   mkdir -p .artifacts/reviews/{review_type}/council/$(date +%Y-%m-%d)
   ```
4. Write formatted verdict to: `.artifacts/reviews/{review_type}/council/YYYY-MM-DD/HHMMSS-review-{verdict}.md`
5. **Always display the saved file path** — append to the verdict output:
   ```
   > **Verdict saved to:** `<absolute path>`
   ```
   This line MUST appear after the verdict markdown, before presenting interactive follow-up options.

## Phase 6 — Interactive Follow-up

Follow @references/post-verdict-actions.md:
1. Present AskUserQuestion based on verdict and review type
2. Execute chosen action
3. Only proceed to cleanup after action completes

## Phase 7 — Cleanup

1. Send `shutdown_request` (type: "shutdown_request") to each teammate by name
2. Wait for shutdown confirmations
3. Call `TeamDelete` to remove team and task list

---

## Quick Mode (3-member quorum)

For `--quick` flag, use abbreviated flow:

### Member Selection

Based on `--focus` or topic analysis, pick 2 most relevant members + yourself (Captain America) = 3. Use the routing tables in @references/member-registry.md#quick-mode-member-selection to determine which members to pick. Optional members are NOT included in Quick Mode (cost control).

### Quick Flow

1. TeamCreate + spawn only the 2 selected members
2. Single assessment round (no challenge/final rounds):
   ```
   QUICK REVIEW — Single Round

   [Review context]

   Review from your specialty lens. Send assessment with:
   - Verdict: APPROVE / CONCERNS / REJECT
   - Key Findings: max 3
   - Recommendation: 1-2 sentences
   ```
3. Collect 2 positions + add your own = 3 votes
4. Quick consensus per @references/verdict-rules.md Quick Mode section
5. Format abbreviated verdict (3 positions only)
6. Save verdict (same Phase 5)
7. Interactive follow-up (Phase 6)
8. Cleanup (Phase 7)

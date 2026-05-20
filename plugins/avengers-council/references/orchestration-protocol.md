# Avengers Council Orchestration Protocol

Shared flow for all council skills. Each skill handles context gathering independently, then delegates to this protocol for team orchestration.

> **Cost note:** Full mode spawns 8 core teammates + any matching optional members (~8-10x single-session cost on Claude; ~24-30x on Codex because each of the 3 rounds is a separate parallel fan-out).
> Recommend Quick Mode (3 members) for non-critical reviews.
> Full mode is justified for: security-sensitive changes, architectural decisions, pre-release reviews.

> **Platform branch:** Steps below are written for Claude Code's agent-team primitives (`TeamCreate`, parallel `Agent`, peer-to-peer `SendMessage`). The Claude execution path is unchanged. For Codex CLI / Codex App, follow the `Codex:` annotation at each tool callsite — debate becomes hub-mediated context propagation through the orchestrator. See @references/codex-tools.md for the full mapping and the cost/fidelity trade-off.

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

**Claude:** Call `TeamCreate` with:
- `team_name`: "avengers-council"
- `description`: "Reviewing: [topic summary from calling skill]"

**Codex:** Skip this step entirely — no team primitive exists. Concurrency is just parallel `spawn_agent` calls in one turn. Track the active roster in a local variable instead.

### Step 3: Spawn Teammates

Spawn all active roster members in parallel. Launch ALL in a SINGLE turn for parallel startup.

Each spawn call embeds the FULL review context and Round 1 instructions so agents self-start immediately (teammates only receive their spawn prompt + CLAUDE.md — they do NOT get the lead's conversation history):

**Claude:**

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

DOMAIN MODEL:
[Include this block ONLY when standards-protocol.md#locate-domain-artifacts found CONTEXT.md or docs/adr/. Otherwise omit entirely — do not insert empty or placeholder text.]
- Glossary: <CONTEXT-MAP.md path | CONTEXT.md path>
  <inline excerpt, capped at 60 lines>
- ADRs (most recent 20): cite ADR-NNNN by path; titles only — agents Read on demand
  - docs/adr/0001-...md — <title>
  - docs/adr/0002-...md — <title>
  ...

Reviewers MUST flag any plan claim that contradicts an accepted ADR (cite ADR-NNNN and quote the contradicting line) or drifts from CONTEXT.md vocabulary (cite the conflicting term). An unacknowledged ADR contradiction triggers automatic verdict downgrade per standards-protocol.md#phase-5-determine-verdict-based-on-standards.

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

**Codex:** Same prompt template, but use `spawn_agent(prompt)` per member with the persona text from `agents/<name>.md` pasted verbatim above the `REVIEW CONTEXT` block (Codex has no `subagent_type` registry). Drop the trailing line about "wait for captain-america to signal Round 2 and Round 3" — Codex workers terminate after returning; Captain re-spawns them for each round with the next round's context inlined. Update the `ROUND 1 INSTRUCTIONS` block to end with: *"Return your assessment as the result of this spawn. Do not broadcast — Captain America will distribute consolidated findings into the Round 2 spawn prompt."*

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

- **Claude:** Wait for teammate responses. Messages from teammates are delivered automatically via the team channel.
- **Codex:** Call `wait_agent(agent_id)` on each spawned worker; collect the returned verdicts. `close_agent(agent_id)` after each to free slots.
- **Timeout policy:** If fewer than the timeout threshold (Step 1) respond, proceed with available responses. Note which members were silent in the verdict.
- **Minimum quorum:** At least the minimum quorum (Step 1) responses required. If fewer respond, report the issue to the user and ask whether to proceed with available responses or retry.

## Phase 2 — Round 1: Collect Initial Assessments

Agents self-start Round 1 immediately from their spawn prompt — no broadcast needed.

1. **Claude:** Create task: "Round 1 — Initial Assessment" via `TaskCreate` (optional — for progress tracking), mark in_progress.
   **Codex:** Use `update_plan` with the same step name for visibility.
2. Collect responses (apply timeout policy from Phase 1 Step 4)
3. Mark Round 1 task as completed

## Phase 3 — Rounds 2 & 3: Challenge and Final Position

After collecting Round 1 responses:

1. **Claude:** Create task "Rounds 2 & 3 — Challenge and Final Position" via `TaskCreate`, mark in_progress.
   **Codex:** Use `update_plan` with the same step name.

2. **Trigger Round 2 + Round 3.**

   **Claude:** Send ONE broadcast via `SendMessage` (type: broadcast) to all stay-alive teammates. Agents DM each other to challenge in Round 2, then send final position to captain-america.

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

   **Codex:** Workers from Round 1 are terminated. Fan out Round 2 as a fresh parallel `spawn_agent` × N call. Each prompt embeds the persona + REVIEW CONTEXT + the consolidated Round-1 findings block + a Round-2 instruction block:

   ```
   ROUND 2 — CHALLENGE (you are [agent-name]):

   Round 1 produced these verdicts and findings from your fellow council members:
   [Per-member verdict + key findings + considered-but-not-flagged, ordered by domain score]

   Identify positions you disagree with. For each disagreement, write a CHALLENGE block addressed to that member:
   - Target: [agent-name]
   - Their position: [quoted]
   - Your challenge: [your counterargument]
   - Evidence: [reference]

   Identify positions you agree with — write a SUPPORT block for each:
   - Target: [agent-name]
   - Their finding: [quoted]
   - Why it strengthens your own assessment: [reasoning]

   Return CHALLENGES and SUPPORTS as the result of this spawn. Do not request your final verdict yet — that's Round 3.
   ```

   After `wait_agent` collects all Round-2 results, consolidate the cross-member challenges/supports into a Round-3 context block. Fan out again as a fresh parallel `spawn_agent` × N for Round 3:

   ```
   ROUND 3 — FINAL POSITION (you are [agent-name]):

   Round 2 produced these challenges and supports involving you:
   [Per-member challenges directed AT you + your own challenges + supports you received]

   Reach your final position. Return:
   - Verdict: APPROVE / CONCERNS / REJECT
   - Final Domain Score: X/10 (your domain)
   - Confidence: HIGH / MEDIUM / LOW
   - Unresolved Disagreements: reference the specific Round-2 exchanges that did not converge
   - Key Condition: what must change for CONCERNS to become APPROVE
   ```

   Cost: 2 additional `spawn_agent` fan-outs for full debate (3 rounds × N members = 3N total spawns vs Claude's N stay-alive). Fidelity is preserved — every cross-agent finding flows through the orchestrator's prompt instead of through SendMessage.

3. **Completion gate:**
   - **Claude:** Wait until all active members send their final position to captain-america.
   - **Codex:** Wait for all Round-3 `spawn_agent` calls to return via `wait_agent`.
   Apply same timeout policy — if members don't return, proceed after receiving results from the quorum.
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
1. **Claude:** Present `AskUserQuestion` based on verdict and review type.
   **Codex:** Print the question with numbered options as plain text; wait for and parse the user's free-form reply.
2. Execute chosen action
3. Only proceed to cleanup after action completes

## Phase 7 — Cleanup

**Claude:**
1. Send `shutdown_request` (type: "shutdown_request") to each teammate by name
2. Wait for shutdown confirmations
3. Call `TeamDelete` to remove team and task list

**Codex:**
1. Workers are already terminated after their final `wait_agent`. If any are still in-flight at the timeout boundary, call `close_agent` on each to free slots.
2. No team to delete.

---

## Quick Mode (3-member quorum)

For `--quick` flag, use abbreviated flow:

### Member Selection

Based on `--focus` or topic analysis, pick 2 most relevant members + yourself (Captain America) = 3. Use the routing tables in @references/member-registry.md#quick-mode-member-selection to determine which members to pick. Optional members are NOT included in Quick Mode (cost control).

### Quick Flow

1. **Claude:** `TeamCreate` + spawn the 2 selected members via `Agent`.
   **Codex:** Skip `TeamCreate`; spawn the 2 selected members via parallel `spawn_agent`.
2. Single assessment round (no challenge/final rounds):
   ```
   QUICK REVIEW — Single Round

   [Review context]

   Review from your specialty lens. Send assessment with:
   - Verdict: APPROVE / CONCERNS / REJECT
   - Key Findings: max 3
   - Recommendation: 1-2 sentences
   ```
3. Collect 2 positions + add your own = 3 votes (Claude: messages arrive automatically; Codex: `wait_agent` on each)
4. Quick consensus per @references/verdict-rules.md Quick Mode section
5. Format abbreviated verdict (3 positions only)
6. Save verdict (same Phase 5)
7. Interactive follow-up (Phase 6)
8. Cleanup (Phase 7)

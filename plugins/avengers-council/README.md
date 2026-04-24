# Avengers Council Plugin

**Extensible engineering advisory board (8 core + optional domain specialists) for reviewing planning decisions, code changes, and architectural designs through structured multi-round debate with domain scoring.**

---

## 🎯 What Is This?

The Avengers Council is a Claude Code plugin that assembles an extensible team of principal-engineer personas to review your work through structured multi-round debate. 8 core members bring deep expertise across key domains, optional specialists join based on topic relevance, and all contribute domain scores to a consensus verdict.

**The Council:**
- **Captain America** (You/Orchestrator) — Engineering standards & delivery
- **Iron Man** (Opus) — System architecture & scalability
- **Thor** (Sonnet) — Backend systems & APIs
- **Scarlet Witch** (Sonnet) — Frontend & UX
- **Hulk** (Sonnet) — Testing & QA
- **Black Widow** (Sonnet) — Security & privacy (VETO power)
- **Hawkeye** (Sonnet) — Mobile platforms (Android, iOS, Flutter, RN, KMP)
- **Vision** (Sonnet) — Data architecture & observability
- **Doctor Strange** (Sonnet) — DevOps & CI/CD

---

## 🚀 Quick Start

### Review a Plan

```bash
/avengers-council:plan-review @.claude/plans/my-plan.md
```

Council reviews your plan through 3 debate rounds and delivers consensus verdict.

### Review Code Changes

```bash
# Review unstaged changes (default)
/avengers-council:code-review

# Review a pull request
/avengers-council:code-review --pr 123

# Review specific files
/avengers-council:code-review --files src/auth.ts,src/db.ts
```

### Quick Review (3 members instead of 9)

```bash
# Fast review with focused expertise
/avengers-council:plan-review --quick --focus security
/avengers-council:code-review --pr 123 --quick --focus mobile
```

---

## 📖 Available Commands

### `/avengers-council:plan-review [topic or @file]`

**Purpose:** Review planning decisions, design specs, PRDs, or architectural plans

**Arguments:**
- `topic or @file` — Free-text topic OR file path (e.g., `@docs/architecture.md`)
- `--focus <area>` — Optional filter: `security|mobile|architecture|testing|delivery|frontend|backend|devops|data`
- `--quick` — Run 3-member quorum (fast mode)

**Examples:**
```bash
# Review plan file
/avengers-council:plan-review @.claude/plans/phase-1.md

# Review topic
/avengers-council:plan-review "Migrate from REST to GraphQL"

# Quick security-focused review
/avengers-council:plan-review @docs/api-design.md --quick --focus security
```

**Output:** Consensus verdict with findings from all relevant council members

---

### `/avengers-council:code-review [options]`

**Purpose:** Review code changes (diffs, PRs, or specific files)

**Arguments:**
- `--pr <number>` — Review GitHub pull request
- `--diff` — Review unstaged changes (default if no args)
- `--files <paths>` — Review specific files (comma-separated)
- `--focus <area>` — Optional filter: `security|mobile|architecture|testing|delivery|frontend|backend|devops|data`
- `--quick` — Run 3-member quorum (fast mode)

**Examples:**
```bash
# Review unstaged changes
/avengers-council:code-review

# Review PR
/avengers-council:code-review --pr 456

# Review specific files
/avengers-council:code-review --files src/auth/login.ts,src/db/users.ts

# Quick mobile-focused review
/avengers-council:code-review --pr 456 --quick --focus mobile
```

**Output:** Consensus verdict with file-specific findings and severity levels

---

## 🎭 How It Works

### 7-Phase Orchestration Protocol

| Phase | Name | What Happens |
|-------|------|-------------|
| 1 | **Standards Detection** | Read CLAUDE.md, CONTRIBUTING.md, project conventions. Audit codebase structure and patterns. |
| 2 | **Assemble the Council** | TeamCreate spawns the team. All 8 core agents launch in parallel with full review context. |
| 3 | **Round 1 — Assessment** | Each member reviews through their specialty lens. Delivers verdict (APPROVE/CONCERNS/REJECT), domain score (1-10), and max 5 findings with severity. |
| 4 | **Round 2 — Challenge** | Members DM challenges to specific teammates. "Your auth cache has a 60s revocation window." Positions evolve through debate. |
| 5 | **Round 3 — Final Position** | Final verdict, updated domain score, confidence level, unresolved disagreements, and conditions for changing verdict. |
| 6 | **Verdict Synthesis** | Captain America tallies votes, computes aggregate domain score, checks red lines, applies Black Widow veto if needed, runs tiebreaker hierarchy. |
| 7 | **Save & Follow-up** | Verdict saved to `.artifacts/reviews/{plans|code}/council/`. Interactive menu to address findings or save as TODOs. |

---

## Consensus Rules

Four verdict levels: **APPROVED**, **APPROVED WITH CONDITIONS**, **NEEDS REVISION**, **BLOCKED**.

**Black Widow VETO:** Unmitigated CRITICAL security issues trigger automatic BLOCKED verdict (cannot be overridden).

**Tiebreaker:** Captain America casts deciding vote with documented reasoning.

Full consensus rules and severity guidelines: see [references/verdict-rules.md](references/verdict-rules.md)

---

## ⚙️ Hook Configuration

The council includes a `PreToolUse:ExitPlanMode` hook that suggests or requires plan reviews.

**Configure via environment variable:**

```bash
# No intervention (default)
export AVENGERS_COUNCIL_ON_PLAN=off

# Suggest council review when exiting plan mode
export AVENGERS_COUNCIL_ON_PLAN=prompt

# Require council review before proceeding
export AVENGERS_COUNCIL_ON_PLAN=auto
```

**Add to your shell profile** (`~/.zshrc` or `~/.bashrc`):
```bash
export AVENGERS_COUNCIL_ON_PLAN=prompt  # or auto
```

---

## 💡 When to Use Council Reviews

### **Use Council For:**
✅ Major architectural decisions (framework choices, system design)
✅ Security-sensitive changes (auth, permissions, data handling)
✅ Cross-team impact (API changes, schema migrations, breaking changes)
✅ Large refactors (multi-file changes, pattern migrations)
✅ Plan review before multi-week projects
✅ Pre-merge review of critical PRs

### **Skip Council For:**
❌ Trivial changes (typos, formatting, docs)
❌ Single-line bug fixes
❌ Well-established patterns (following existing code)
❌ Time-critical hotfixes (use fast review, not full council)

**Rule of thumb:** If the change could cause production issues, security risks, or architectural debt → use council.

---

## 🔍 Council Member Specialties

| Member | Specialty | What They Review |
|--------|-----------|------------------|
| **Iron Man** | Architecture & Scalability | System design, performance bottlenecks, infrastructure costs, Big-O complexity |
| **Thor** | Backend & APIs | API design, databases, microservices, server-side performance, caching |
| **Scarlet Witch** | Frontend & UX | React, component architecture, accessibility, responsive design, state management |
| **Hulk** | Testing & QA | Test coverage, edge cases, race conditions, failure modes, reliability |
| **Black Widow** | Security & Privacy | Auth, authorization, data exposure, vulnerabilities, compliance (VETO power) |
| **Hawkeye** | Mobile Platforms | Android, iOS, Flutter, React Native, lifecycle, memory, threading, app size |
| **Vision** | Data & Observability | Database design, monitoring, logging, metrics, performance analytics |
| **Doctor Strange** | DevOps & CI/CD | Deployment, infrastructure-as-code, containerization, build systems |

**Captain America** (you) orchestrates the debate and serves as tiebreaker.

---

## 📁 Verdict Archive

All council verdicts are automatically saved to:

```
.artifacts/reviews/
├── plans/council/
│   ├── 2026-02-13/
│   │   └── 103045-review-approved.md
│   └── 2026-02-14/
│       └── 091500-review-revision.md
└── code/council/
    └── 2026-02-13/
        └── 153020-review-blocked.md
```

**Naming format:** `HHMMSS-review-{verdict}.md` where verdict is `approved|concerns|revision|blocked`

**Benefits:**
- Permanent audit trail of council decisions
- Can reference past debates when similar issues arise
- Track how architectural decisions evolved over time

---

## 🎯 Examples

### Example 1: Review Architecture Plan

```bash
/avengers-council:plan-review "Migrate from monolith to microservices"
```

**Council Process:**
1. Captain America gathers context (current architecture, migration goals)
2. Council members review through their lenses:
   - Iron Man: Scalability implications, service boundaries
   - Thor: API contracts, data consistency
   - Black Widow: Security boundaries, auth propagation
   - Vision: Observability strategy, distributed tracing
   - Doctor Strange: Deployment complexity, rollback strategy
3. Round 2: Members challenge each other
   - Iron Man: "That service split creates too much network overhead"
   - Thor: "Agreed, but we need it for scaling the write path"
4. Round 3: Final consensus
5. Verdict: APPROVED WITH CONDITIONS
   - Must: Add circuit breakers, define SLOs, implement distributed tracing
   - Nice to have: Consider event sourcing for audit trail

**Saved to:** `.artifacts/reviews/plans/council/2026-02-13/103045-review-concerns.md`

---

### Example 2: Review Security-Sensitive PR

```bash
/avengers-council:code-review --pr 789 --focus security
```

**Council Process:**
1. Captain America fetches PR diff and description
2. Full council review (Black Widow leads on security):
   - Black Widow: SQL injection in query builder (CRITICAL)
   - Vision: No audit logging of permission changes (HIGH)
   - Thor: API exposes internal user IDs (MEDIUM)
3. Black Widow exercises VETO on unmitigated SQL injection
4. Verdict: **BLOCKED**
   - Must fix: SQL injection vulnerability
   - Must add: Parameterized queries, audit logging
   - Then: Re-review after fixes

**Saved to:** `.artifacts/reviews/code/council/2026-02-13/153020-review-blocked.md`

---

### Example 3: Quick Mobile Review

```bash
/avengers-council:code-review --files app/ProfileViewModel.kt --quick --focus mobile
```

**3-Member Quorum:**
- Captain America (orchestrator)
- Hawkeye (mobile expert - primary)
- Hulk (testing perspective)

**Faster verdict** (30 minutes instead of 1-2 hours), focused on mobile-specific concerns.

---

## 📚 Additional Resources

- **[docs/commands.md](docs/commands.md)** — Detailed command reference
- **[docs/hooks.md](docs/hooks.md)** — Hook configuration guide
- **[docs/architecture.md](docs/architecture.md)** — System architecture diagrams
- **[references/debate-protocol.md](references/debate-protocol.md)** — How council debate works
- **[references/verdict-template.md](references/verdict-template.md)** — Verdict output format


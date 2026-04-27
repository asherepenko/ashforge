# Avengers Council

Engineering advisory board (8 core members + Captain America orchestrator) for reviewing plans, code, and architecture through structured 3-round debate with domain scoring and security veto.

## What It Does

- **8 Core Members** — Principal-engineer personas across architecture, backend, frontend, testing, security, mobile, data, and DevOps. Optional specialists join based on topic relevance.
- **3-Round Debate** — Assessment → Challenge → Final Position. Members critique each other's findings before consensus.
- **Domain Scoring** — Each member scores 1–10 in their specialty. Aggregate average < 5.0 forces NEEDS REVISION.
- **Black Widow VETO** — Unmitigated CRITICAL security issues trigger automatic BLOCKED verdict (cannot be overridden).
- **Verdict Archive** — Every review saved to `.artifacts/reviews/{plans,code}/council/YYYY-MM-DD/HHMMSS-review-{verdict}.md`.
- **Quick Mode** — 3-member quorum with `--quick --focus <area>` when full council is overkill.

## Installation

Install via the [ashforge](https://github.com/asherepenko/ashforge) marketplace:

```
/plugin marketplace add asherepenko/ashforge
/plugin install avengers-council@ashforge
/reload-plugins
```

## Usage

```bash
/avengers-council:plan-review @.claude/plans/my-plan.md     # Review a plan file
/avengers-council:plan-review "Migrate REST to GraphQL"     # Review a topic
/avengers-council:code-review                               # Review unstaged diff
/avengers-council:code-review --pr 123                      # Review a GitHub PR
/avengers-council:code-review --files src/auth.ts,src/db.ts # Review specific files
/avengers-council:code-review --pr 456 --quick --focus mobile # 3-member quick review
```

**Shared flags** (both commands):
- `--focus <area>` — `security|mobile|architecture|testing|delivery|frontend|backend|devops|data`
- `--quick` — 3-member quorum instead of full council

## Council Members

| Member | Model | Specialty |
|--------|-------|-----------|
| Captain America | (you) | Orchestrator, engineering standards, tiebreaker |
| Iron Man | Opus | Architecture, scalability, performance, infra cost |
| Thor | Sonnet | Backend, APIs, databases, microservices, caching |
| Scarlet Witch | Sonnet | Frontend, UX, accessibility, state management |
| Hulk | Sonnet | Testing, edge cases, race conditions, reliability |
| Black Widow | Sonnet | Security, privacy, auth, compliance (VETO power) |
| Hawkeye | Sonnet | Mobile (Android, iOS, Flutter, RN, KMP) |
| Vision | Sonnet | Data, observability, logging, metrics |
| Doctor Strange | Sonnet | DevOps, CI/CD, IaC, containerization |

Captain America never spawns as a subagent — the orchestrating session plays this role.

## Orchestration

Seven phases per review:

1. **Standards Detection** — Read `CLAUDE.md`, `CONTRIBUTING.md`, audit codebase.
2. **Assemble** — `TeamCreate` spawns the 8 core agents (plus topic-matched specialists) in parallel.
3. **Round 1 — Assessment** — Each member delivers verdict (APPROVE/CONCERNS/REJECT), domain score, and up to 5 findings with severity.
4. **Round 2 — Challenge** — Members DM challenges to each other. Positions evolve.
5. **Round 3 — Final Position** — Final verdict, updated score, confidence, unresolved disagreements.
6. **Verdict Synthesis** — Captain America tallies, checks red lines, applies veto, runs tiebreakers.
7. **Save & Follow-up** — Verdict written to disk; interactive menu to address findings or save TODOs.

Verdicts: **APPROVED**, **APPROVED WITH CONDITIONS**, **NEEDS REVISION**, **BLOCKED**.

## Hook Configuration

The plugin registers a `PreToolUse:ExitPlanMode` hook controlled by an env var:

```bash
export AVENGERS_COUNCIL_ON_PLAN=off      # No intervention (default)
export AVENGERS_COUNCIL_ON_PLAN=prompt   # Suggest review when exiting plan mode
export AVENGERS_COUNCIL_ON_PLAN=auto     # Require review before proceeding
```

Add to `~/.zshrc` / `~/.bashrc` to persist.

## When to Use

**Reach for the council** when the change carries production, security, or architectural-debt risk:
- Major architectural decisions (framework choice, system design)
- Security-sensitive changes (auth, permissions, data handling)
- Cross-team impact (API breaks, schema migrations)
- Large refactors and multi-week project plans
- Pre-merge review of critical PRs

**Skip the council** for trivial changes, single-line bug fixes, established patterns, and time-critical hotfixes (use `--quick` instead).

## Plugin Structure

```
avengers-council/
├── .claude-plugin/plugin.json    # Plugin manifest
├── agents/                       # 8 core members + captain-america (ref) + optional members
├── commands/                     # plan-review, code-review
├── references/                   # Verdict rules, red lines, debate protocol, member registry
├── hooks/                        # PreToolUse:ExitPlanMode hook
├── docs/                         # Detailed command + hook + architecture docs
└── tests/                        # Hook integration tests
```

## Documentation

| Doc | Purpose |
|-----|---------|
| [docs/commands.md](docs/commands.md) | Full command reference with all flags |
| [docs/examples.md](docs/examples.md) | End-to-end walkthroughs (architecture plan, security PR, quick mobile) |
| [docs/hooks.md](docs/hooks.md) | Hook configuration deep-dive |
| [docs/architecture.md](docs/architecture.md) | System architecture and data flow |
| [references/debate-protocol.md](references/debate-protocol.md) | How rounds, challenges, and consensus work |
| [references/verdict-rules.md](references/verdict-rules.md) | Severity guidelines and verdict thresholds |
| [references/verdict-template.md](references/verdict-template.md) | Output format for saved verdicts |
| [CLAUDE.md](CLAUDE.md) | Plugin internals (for maintainers) |

## License

[MIT](./LICENSE)

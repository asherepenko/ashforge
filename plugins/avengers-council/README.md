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

The plugin ships in the [ashforge](https://github.com/asherepenko/ashforge) marketplace and works on both Claude Code and Codex (CLI / App).

### Claude Code

```
/plugin marketplace add asherepenko/ashforge
/plugin install avengers-council@ashforge
/reload-plugins
```

The `PreToolUse:ExitPlanMode` hook activates automatically.

### Codex (CLI / App)

```bash
codex plugin marketplace add asherepenko/ashforge
```

Then enable the plugin in `~/.codex/config.toml`:

```toml
[plugins."avengers-council@ashforge"]
enabled = true

[features]
multi_agent = true      # REQUIRED — spawn_agent/wait_agent/close_agent for the debate
```

**Sandbox mode**: Codex must run with `sandbox_mode = "workspace-write"` (or `danger-full-access`) so the council can write verdicts under `.artifacts/reviews/`. `read-only` mode blocks the verdict save (Phase 5) and any post-verdict actions that edit files. Check your `~/.codex/config.toml`:

```toml
sandbox_mode = "workspace-write"
```

The council uses `spawn_agent` for each debate round; `multi_agent = true` is required. Without it, skills detect the gap via preflight and fall back to single-orchestrator mode per `references/codex-fallback.md`.

The plugin does not ship Codex-side hooks (the `ExitPlanMode` hook is Claude-only — Codex has no equivalent tool). See [`references/codex-tools.md`](references/codex-tools.md) for the full Claude → Codex primitive mapping including the hub-mediated debate trade-off.

### Project-Level Setup (both runtimes)

The council writes verdict files under `.artifacts/reviews/`. By default these are worth keeping in version control (they form an audit trail). If you'd rather treat them as transient, add to `.gitignore`:

```gitignore
.artifacts/reviews/
```

If you keep verdicts versioned but want to exclude any cached / temporary council state, ignore just:

```gitignore
.artifacts/cassandra/cache/
.artifacts/tmp/
```

## Usage

The toolkit ships as **skills** — invoke by intent on Claude Code or Codex CLI/App. The slash-command form (`/avengers-council:plan-review`) was retired in version 3.0.0.

```
council-plan-review @.claude/plans/my-plan.md     # Review a plan file
council-plan-review "Migrate REST to GraphQL"     # Review a topic
council-code-review                               # Review unstaged diff
council-code-review --pr 123                      # Review a GitHub PR
council-code-review --files src/auth.ts,src/db.ts # Review specific files
council-code-review --pr 456 --quick --focus mobile # 3-member quick review
```

Claude: the Skill tool auto-triggers on description match, or invoke explicitly with `Skill(skill="council-plan-review", args="@my-plan.md")`. Codex: state the intent in natural language.

**Shared flags** (both skills):
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
2. **Assemble** — Claude: `TeamCreate` + parallel `Agent` spawns the 8 core members (plus topic-matched specialists). Codex: parallel `spawn_agent` (no team primitive).
3. **Round 1 — Assessment** — Each member delivers verdict (APPROVE/CONCERNS/REJECT), domain score, and up to 5 findings with severity.
4. **Round 2 — Challenge** — Claude: members DM challenges to each other via `SendMessage`. Codex: Captain consolidates Round-1 findings and re-spawns each member with a per-recipient challenge prompt.
5. **Round 3 — Final Position** — Final verdict, updated score, confidence, unresolved disagreements. Claude: same agents stay alive. Codex: fresh `spawn_agent` fan-out with the consolidated Round-2 context.
6. **Verdict Synthesis** — Captain America tallies, checks red lines, applies veto, runs tiebreakers.
7. **Save & Follow-up** — Verdict written to disk; interactive menu to address findings or save TODOs.

Verdicts: **APPROVED**, **APPROVED WITH CONDITIONS**, **NEEDS REVISION**, **BLOCKED**.

Debate fidelity is preserved on both platforms — every cross-member finding flows either through `SendMessage` (Claude) or through the orchestrator's next-round spawn prompt (Codex). Codex full mode costs ~3× the spawns of Claude (3 rounds × N members vs N stay-alive agents); `--quick` mode collapses to a single fan-out on both platforms.

## Hook Configuration

The plugin registers a `PreToolUse:ExitPlanMode` hook (**Claude-only** — Codex has no `ExitPlanMode` tool) controlled by an env var:

```bash
export AVENGERS_COUNCIL_ON_PLAN=off      # No intervention (default)
export AVENGERS_COUNCIL_ON_PLAN=prompt   # Suggest review when exiting plan mode
export AVENGERS_COUNCIL_ON_PLAN=auto     # Require review before proceeding
```

Add to `~/.zshrc` / `~/.bashrc` to persist. On Codex, invoke the `council-plan-review` skill explicitly when needed.

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
├── .claude-plugin/plugin.json    # Claude Code manifest
├── .codex-plugin/plugin.json     # Codex CLI / Codex App manifest (points at skills/)
├── agents/                       # 8 core members + captain-america (ref) + optional members
├── skills/                       # council-plan-review, council-code-review (replaces the retired commands/)
├── references/                   # Verdict rules, red lines, debate protocol, member registry, codex-tools
├── hooks/                        # PreToolUse:ExitPlanMode hook (Claude-only)
├── docs/                         # Detailed skill + hook + architecture docs
└── tests/                        # Hook integration tests
```

## Documentation

| Doc | Purpose |
|-----|---------|
| [docs/skills.md](docs/skills.md) | Full skill reference with all flags |
| [references/codex-tools.md](references/codex-tools.md) | Claude → Codex tool mapping and hub-mediated debate notes |
| [docs/examples.md](docs/examples.md) | End-to-end walkthroughs (architecture plan, security PR, quick mobile) |
| [docs/hooks.md](docs/hooks.md) | Hook configuration deep-dive |
| [docs/architecture.md](docs/architecture.md) | System architecture and data flow |
| [references/debate-protocol.md](references/debate-protocol.md) | How rounds, challenges, and consensus work |
| [references/verdict-rules.md](references/verdict-rules.md) | Severity guidelines and verdict thresholds |
| [references/verdict-template.md](references/verdict-template.md) | Output format for saved verdicts |
| [CLAUDE.md](CLAUDE.md) | Plugin internals (for maintainers) |

## License

[MIT](./LICENSE)

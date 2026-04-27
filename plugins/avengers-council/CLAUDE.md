# Avengers Council Plugin

## Routing

- **Commands** (Skill tool): `code-review`, `plan-review` — orchestrate council sessions.
- **Agents** (Agent tool): `hulk`, `iron-man`, `thor`, `scarlet-witch`, `black-widow`, `hawkeye`, `vision`, `doctor-strange` — spawned by commands during orchestration.
- `captain-america` — reference only, never spawned. The orchestrating session plays this role.
- Never spawn a command as an agent subagent_type.

## Structure

```
agents/          — 8 core members + captain-america (ref only) + optional members
commands/        — plan, code-review
references/      — Protocols, templates, shared docs
hooks/           — PreToolUse:ExitPlanMode hook
docs/            — Detailed documentation
tests/           — Hook integration tests
```

## Sources of Truth

| What | File |
|------|------|
| Consensus rules | `references/verdict-rules.md` |
| Shared principles & tiebreakers | `references/shared-principles.md` |
| Red lines (non-negotiables) | `references/red-lines.md` |
| Member roster & extensibility | `references/member-registry.md` |
| Orchestration flow | `references/orchestration-protocol.md` |

## Key Conventions

- Commands use explicit `Read @references/...` — not bare `@references/` lines.
- Agents include domain scores (1-10) in every assessment. Aggregate average < 5.0 overrides to NEEDS REVISION.
- Optional members auto-join based on topic matching. Add new ones via `member-registry.md`.
- Black Widow retains VETO power on unmitigated CRITICAL security issues.

## Tests

Python tests for the `PreToolUse:ExitPlanMode` hook under `tests/`. Run:

```bash
pytest tests/
```

All 6 tests must pass.

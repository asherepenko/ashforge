# Avengers Council — Worked Examples

Three end-to-end walkthroughs covering the most common review shapes.

## Example 1 — Architecture plan review

```bash
/avengers-council:plan-review "Migrate from monolith to microservices"
```

**Council process:**

1. Captain America gathers context (current architecture, migration goals).
2. Members review through their lenses:
   - Iron Man — scalability implications, service boundaries
   - Thor — API contracts, data consistency
   - Black Widow — security boundaries, auth propagation
   - Vision — observability strategy, distributed tracing
   - Doctor Strange — deployment complexity, rollback strategy
3. Round 2 — members challenge each other:
   - Iron Man: "That service split creates too much network overhead"
   - Thor: "Agreed, but we need it for scaling the write path"
4. Round 3 — final consensus.
5. **Verdict: APPROVED WITH CONDITIONS**
   - Must: add circuit breakers, define SLOs, implement distributed tracing
   - Nice to have: consider event sourcing for audit trail

Saved to `.artifacts/reviews/plans/council/2026-02-13/103045-review-concerns.md`.

---

## Example 2 — Security-sensitive PR review

```bash
/avengers-council:code-review --pr 789 --focus security
```

**Council process:**

1. Captain America fetches PR diff and description.
2. Full council review, Black Widow leads on security:
   - Black Widow — SQL injection in query builder (CRITICAL)
   - Vision — no audit logging of permission changes (HIGH)
   - Thor — API exposes internal user IDs (MEDIUM)
3. Black Widow exercises VETO on unmitigated SQL injection.
4. **Verdict: BLOCKED**
   - Must fix: SQL injection vulnerability
   - Must add: parameterized queries, audit logging
   - Then: re-review after fixes

Saved to `.artifacts/reviews/code/council/2026-02-13/153020-review-blocked.md`.

---

## Example 3 — Quick mobile review

```bash
/avengers-council:code-review --files app/ProfileViewModel.kt --quick --focus mobile
```

**3-member quorum:**

- Captain America (orchestrator)
- Hawkeye (mobile expert — primary)
- Hulk (testing perspective)

Faster verdict (~30 minutes vs. 1–2 hours), focused on mobile-specific concerns: lifecycle, memory, threading, app size, platform idioms.

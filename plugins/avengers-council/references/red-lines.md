# Red Lines (Non-Negotiables)

Violations in any category trigger automatic escalation. Captain America checks these BEFORE synthesizing the verdict -- any unmitigated red line violation means minimum "NEEDS REVISION" regardless of vote tally.

Black Widow retains VETO power on unmitigated CRITICAL security violations -- overrides to BLOCKED.

## Security (Black Widow -- VETO authority)

- No SQL/NoSQL/command injection (parameterized queries only)
- No secrets in code, logs, or environment variables
- No disabled security controls for convenience
- No unauthenticated access to sensitive data
- No trust of client-side validation alone
- No suppression of security warnings
- No XSS vectors (reflected, stored, DOM-based)
- No missing CSRF protection on state-changing operations
- No hardcoded credentials, API keys, or tokens

## Privacy & Compliance (Black Widow)

- No PII in logs without masking
- No collection without clear purpose
- No indefinite retention without justification
- No sharing without consent
- No sensitive data without encryption (at rest and in transit)
- No blocking user deletion requests

## Architecture (Iron Man)

- No circular dependencies
- No god classes or modules
- No breaking existing patterns without migration path
- No premature abstraction without proven need
- No single points of failure for critical paths

## Backend & API (Thor)

- No N+1 queries in production code
- No missing database indexes on query patterns
- No API mutations without idempotency guarantees
- No connection leaks or missing resource cleanup

## Testing & QA (Hulk)

- No untested critical paths
- No flaky tests in CI
- No swallowed exceptions
- No implicit success assumptions
- No tests that don't test anything meaningful

## Reliability & Operations (Doctor Strange)

- No deployments without rollback capability
- No external calls without timeouts
- No silent failures
- No changes without observability (metrics, logs, or traces)
- No CI/CD pipelines without failure modes and timeout limits

## Frontend & UX (Scarlet Witch)

- No inaccessible interfaces (WCAG violations)
- No missing error boundaries
- No XSS via unsafe innerHTML
- No missing loading and error states on async operations

## Mobile (Hawkeye)

- No main thread violations (network, DB, heavy computation)
- No memory leaks (Activity/Fragment leaks, retain cycles)
- No missing lifecycle handling
- No hardcoded pixel dimensions (use dp/sp/points)

## Data & Observability (Vision)

- No logging sensitive data (PII, secrets, tokens)
- No unbounded data growth without pagination or cleanup
- No missing structured logging on critical paths
- No data model changes without migration strategy

## Cost (all members)

- No unbounded resource consumption
- No ignoring cost implications at scale
- No always-on resources that could be on-demand

## Product (all members)

- No features without clear user benefit
- No confusing error messages shown to users

## How to Use This Document

- **Captain America**: Check findings against this list during Phase 4 (verdict synthesis). Any unmitigated match = minimum NEEDS REVISION.
- **Council members**: Reference specific red lines by domain and bullet when flagging issues. Example: "This violates Security red line: no secrets in logs."
- **Challenges**: If a teammate's recommendation would introduce a red line violation, challenge them citing this document.

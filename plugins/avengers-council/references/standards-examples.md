# Standards Protocol Examples — Read on demand for reference

These examples illustrate how the Standards Detection & Validation Protocol (see @references/standards-protocol.md) works in practice.

## Standards Index Example

After scanning for project conventions, Captain America builds an index:

```
STANDARDS INDEX:

FILE: ./CLAUDE.md
|- Writing Convention: Use "the user" and "the assistant" instead of pronouns
|- Naming Convention: kebab-case for files, camelCase for functions
|- Testing Standard: All public APIs must have unit tests (coverage >= 80%)
|- Commit Format: imperative mood, max 70 chars title, scope prefix
|- Security Review: All auth/crypto changes require Black Widow review
|- Documentation: Every public function needs JSDoc
|- Performance: All queries must complete in <100ms
\- Deprecated Tech: No CoffeeScript (sunset 2025-Q2)

FILE: ./.claude/CLAUDE.md
|- Gradle Convention: Always use --no-daemon flag
\- Android Testing: All Activity changes need espresso tests

FILE: ~/.claude/CLAUDE.md
\- [Global user preferences -- reference only, project standards override]
```

## Phase 3 Examples: Applying Standards During Review

### Plan Review Finding

```
!! HIGH: Introduces CoffeeScript in deployment script
CLAUDE.md line 87: "All new code must be TypeScript (CoffeeScript sunset 2025-Q2)"
Current situation: deploy.coffee added to git
Recommendation: Rewrite deploy.coffee as deploy.ts

Severity: HIGH (strong guidance)
Impact: Tech debt, incompatible with team skill set
Action: Resubmit with TypeScript version
```

### Code Review Finding

```
!! CRITICAL: Security-sensitive code without required review
CLAUDE.md line 92: "All auth/crypto changes require Black Widow (security) review"
Current situation: Password reset token generation added (lines 145-167, user-service.ts)
Status: Black Widow has not reviewed yet
Action: Resubmit only after Black Widow signals approval
```

## Phase 4 Example: Standards Compliance Report

```markdown
# Standards Compliance Report

## Applicable Standards (from project CLAUDE.md)
- Standard A: Testing (coverage >= 80%)
- Standard B: Naming (camelCase functions)
- Standard C: Security (no plaintext passwords)
- Standard D: Documentation (JSDoc required)

## Compliance Status

### Met
- Standard A: Test coverage 85%
- Standard D: All functions documented with JSDoc

### Violated
- Standard B: Function 'getUserProfileById' uses underscores (violates camelCase)
  - Severity: HIGH
  - Location: user-service.ts line 42
  - Recommendation: Rename to getUserProfileById()

- Standard C: Config loads DB password from env without validation
  - Severity: CRITICAL
  - Location: config.ts line 18
  - Recommendation: Validate password length/complexity, consider secrets manager

### Conditional (if changes made)
- Standard [X]: Will be met after team approves [condition]
```

## Example 1: Plan Review with Standards

**Topic:** Add user authentication system

**Applicable Standards:**
1. (Mandatory) All auth/crypto changes require Black Widow review
2. (Mandatory) Testing coverage >= 80%
3. (Strong) API versioning required for new endpoints
4. (Strong) Documentation must include migration path for existing users

**Plan Assessment:**

```
Round 1 Findings:

Iron Man:
- CONCERNS: Doesn't describe scalability to 1M users
- Recommendation: Add load testing plan

Black Widow:
- CONCERNS: Auth plan missing code review checkpoint
- Recommendation: Schedule security review before implementation
- NOTE: Mandatory standard #1 requires Black Widow sign-off!

Scarlet Witch:
- APPROVE: API design is clean
- NOTE: API versioning standard met

Vision:
- CONCERNS: No database schema for user credentials documented
```

**Captain America Synthesis:**

Vote tally:
- APPROVE: Scarlet Witch (1)
- CONCERNS: Iron Man, Black Widow, Vision (3)
- REJECT: (0)

Standards check:
- Mandatory #1 (Black Widow review): NOT MET YET -- design lacks review checkpoint
- Mandatory #2 (80% testing): AC documents goal
- Strong #3 (API versioning): Documented
- Strong #4 (migration path): NOT DOCUMENTED -- high risk to existing users

**Verdict:** NEEDS REVISION
- Reason: Mandatory standard #1 requires Black Widow checkpoint (missing from plan)
- Reason: Migration path not documented (strong standard #4)
- Reason: Too many CONCERNS (3) relative to APPROVE (1)
- Conditions: Add Black Widow review checkpoint to phase 2, document migration strategy
- Action: Resubmit plan with these additions

## Example 2: Code Review with Standards

**Changes:** Refactor user password reset logic

**Standards Check Before Council:**
- Commit message: "Refactor user password reset" -- violates imperative mood
  - Severity: MEDIUM (strong guidance)
- Test coverage: No new tests added
  - Severity: HIGH (mandatory -- coverage >= 80%, this is auth code)
- Security-sensitive code (password reset): No review recorded
  - Severity: CRITICAL (mandatory -- Black Widow must review)

**Council Assessment:**

```
Round 1 Findings:

Black Widow:
- REJECT: Code lacks cryptographic strength validation
- CRITICAL: Token generation uses Math.random() instead of secure RNG
- Evidence: line 156, password-reset.ts
- Recommendation: Use crypto.randomBytes(), increase entropy

Hulk:
- REJECT: No unit tests for password reset logic
- HIGH: Auth code must have >90% test coverage (CLAUDE.md)
- Evidence: 0/8 new functions have tests
- Recommendation: Add unit tests, minimum 100 assertions

Iron Man:
- CONCERNS: Algorithm complexity not documented
- Evidence: lines 145-200 use nested loops for token validation
- Recommendation: Use O(1) lookup with hash table
```

**Captain America Synthesis:**

Vote tally:
- APPROVE: (0)
- CONCERNS: Iron Man (1)
- REJECT: Black Widow, Hulk (2)

Standards check:
- Mandatory: "Auth code >= 90% test coverage" -- 0% today
- Mandatory: "Crypto requires Black Widow review" -- REJECTED
- Strong: "Commit message imperative mood" -- violated

**Verdict:** BLOCKED
- Reason: 2 REJECT votes (Black Widow, Hulk)
- Reason: CRITICAL findings unmitigated (crypto weakness)
- Reason: Mandatory standard violated (testing baseline)
- Reason: Mandatory security review rejected
- Conditions: None can unblock except major rework -- discuss with team
- Action: Do not merge; consult with Black Widow on secure token generation

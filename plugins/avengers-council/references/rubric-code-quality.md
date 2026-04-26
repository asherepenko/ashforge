# Code Quality Grading Rubric

Evaluation criteria for code review. Each Council member grades through their specialty lens, but these five criteria provide shared grading language. Score each relevant criterion as STRONG / ADEQUATE / WEAK. Report WEAK findings; do not report STRONG or ADEQUATE unless asked.

**Anti-leniency reminder**: If you identify an issue then find yourself explaining why it's probably fine, that is a signal to report it, not dismiss it. The decision about acceptability belongs to the user.

## 1. Correctness

Does the code do what the spec/plan says? Every requirement should map to verifiable implementation. Untested edge cases (null, empty, error, concurrent) count as correctness risks even if the happy path works.

**STRONG**: All spec requirements have corresponding implementation. Edge cases are handled explicitly. Error paths are tested.
**WEAK**: Happy path works but edge cases are unaddressed. Requirements are partially implemented or subtly misinterpreted. "It works on my machine" correctness.

## 2. Simplicity

Is this the simplest approach that meets requirements? Over-engineering (premature abstraction, unnecessary indirection, speculative generalization) is as much a defect as under-engineering. Three similar lines of code is better than a premature abstraction.

**STRONG**: Implementation is straightforward. Abstractions exist because they solve a current problem, not a hypothetical future one. A new reader can follow the control flow without jumping through layers.
**WEAK**: Wrapper classes that add no behavior. Strategy/factory patterns for a single implementation. Configuration for values that never change. Indirection that makes debugging harder without providing current value.

## 3. Consistency

Does the code follow existing codebase patterns? New patterns must be justified by concrete limitations of existing ones, not by "better in theory." Consistency across a codebase is more valuable than local perfection.

**STRONG**: Follows naming conventions, directory structure, error handling patterns, and architectural layers already established. When it deviates, there's a comment or ADR explaining why.
**WEAK**: Introduces a new pattern alongside the existing one without migrating. Uses a different naming convention than surrounding code. Mixes paradigms (reactive + imperative) without justification.

## 4. Robustness

How does the code behave at boundaries? Network failures, empty inputs, concurrent access, lifecycle transitions, permission denials. Silent failures are worse than crashes — at least crashes get reported.

**STRONG**: Boundary conditions are handled explicitly. Errors surface as user-visible state (not swallowed). Concurrent access is either prevented by design or handled with synchronization. Timeout and retry strategies exist for external calls.
**WEAK**: Catch-all exception handlers that log and continue. No timeout on network calls. Race conditions possible but unlikely enough to ignore. Empty/null inputs cause undefined behavior.

## 5. Maintainability

Can another developer modify this code in 6 months without understanding the entire codebase? Clear naming, obvious control flow, minimal coupling. The test suite serves as documentation of intended behavior.

**STRONG**: Names reveal intent. Functions are short enough to fit in working memory. Dependencies are injected and mockable. Changes to one module don't cascade through others. Tests document behavior and catch regressions.
**WEAK**: Abbreviated names that require context to understand. God classes/functions that do too much. Tight coupling where changing one file requires changing five others. No tests, or tests that test implementation details rather than behavior.

---

## Forcing function: "Considered but not flagged"

The anti-leniency rule above guards against silently dismissing real issues. This rule guards the inverse failure: **silently dismissing the calls you almost made**.

For each review, surface 1–3 things in your domain that **looked wrong but you chose not to flag**, with the reasoning. Examples:

- "The deeply nested callback chain in `webhooks.kt:120` looked like a refactor target — left it because it preserves event ordering that a coroutine-based rewrite would break."
- "Considered flagging the `runBlocking { … }` in `migration.kt:45` — kept it because the call site is a one-shot CLI entry point, not a coroutine context."
- "Force-unwrap `try!` in `KeychainStore.swift:88` looked dangerous — left it because the preceding `guard` makes the failure path unreachable; would still annotate."

This is **not** a list of LOW-severity findings — those go in the findings table. This is the audit trail of judgment calls: things a reviewer would notice and ask about, with the rationale for why the council chose silence. An empty section signals shallow review unless the diff is genuinely small enough that no near-misses exist.

**Why this matters**: LLM reviewers tend to either flag everything (noise) or pattern-match to "looks fine" without recording the dismissal (opacity). Forcing the dismissal to be explicit makes the review auditable — the user can override a judgment call only if they can see it was made.

**When to skip**: very small diffs (< 50 LOC, single-purpose change) where no patterns triggered consideration. Say "Nothing material — diff was too narrow for near-misses" rather than padding.

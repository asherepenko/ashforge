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

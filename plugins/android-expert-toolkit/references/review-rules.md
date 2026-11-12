# Review Mode

A fixed procedure and output for reviewing Android code, so two reviews of the same code have the same shape.

## When to use

Any review request: "review this Android code", "review this screen", "audit this composable", "is this ViewModel right", a PR or diff review, or an agent brief that asks for review findings. Not for test review (`android-testing` skill) or writing new code (use the rubrics as generation targets instead).

## Pick the rows

Build the row list before reading the code closely. Include a row only when its lens applies; never drop a row because it would fail.

| Lens | Applies when the code touches | Rows |
|------|-------------------------------|------|
| Compose | any `@Composable` | C1–C5 from [rubric-compose-ui](rubric-compose-ui.md) |
| Architecture | ViewModels, repositories, modules, DI, data flow | A1–A5 from [rubric-android-architecture](rubric-android-architecture.md) |
| Checklist | a topic whose reference ends with `## Review checklist` | one row per checklist item, id `<reference>.<n>` (e.g. `coroutines.2`); references in alphabetical order |

Rubric rows, in order:

- C1 Design Cohesion · C2 State Completeness · C3 Accessibility · C4 Performance · C5 Adaptive Layout
- A1 Module Independence · A2 Data Flow Integrity · A3 Offline-First Fidelity · A4 State Predictability · A5 Dependency Hygiene

A lens that applies but cannot be judged from the code given (e.g. A1 on a single file) is `N/A` with the reason, not omitted.

## Grade each row

- ✅ **PASS** — the code matches the rubric's Strong column or the checklist item holds.
- ❌ **FAIL** — at least one concrete instance of the Weak column or a broken checklist item. Every FAIL cites `file:line`.
- ⏩ **N/A** — the row cannot apply to this code; give the reason in Evidence.

On a diff or PR, a row FAILs only for problems the change introduces or makes worse. A problem already present in untouched code is listed under 📋 Pre-existing and does not affect the verdict.

Grade against the project's own patterns first ([pragmatics](pragmatics.md)): code that follows an established project convention is not a FAIL because the rubric prefers another style. List the divergence under 🔔 Notes.

Write one finding per distinct issue, listing every row it fails (`C1, compose-ui.2`); two rows that fail on the same line are one finding. Give each finding a severity for sorting only: 🔴 CRITICAL (crash, data loss, security), 🟠 HIGH (broken behavior or state a user hits), 🟡 MEDIUM (degraded UX, performance, or maintainability), 🟢 LOW (polish).

## Verdict

- Any ❌ FAIL → ⚠️ **Changes needed**.
- No ❌ FAIL → ✅ **Approve**.

No other verdicts. No scores. Severity never changes the verdict.

## Output

Print the block in [review-template](../assets/review-template.md) exactly: its headings, table columns, group headings and finding shape. Then at most one line of prose. Before printing, check that each count in the summary table equals the items listed under it.

# Working in Existing Codebases

## When to use

Read when a best practice conflicts with what the codebase already does, when tempted to refactor beyond the task, or when recording a deliberate shortcut.

## Priority order

1. **User instructions** — the task, the project's `AGENTS.md`/`CLAUDE.md`. "Use LiveData" means LiveData.
2. **Codebase consistency** — match the pattern the module already uses (`aet-check`; ≥80% prevalence decides, see `pattern-detection.md`).
3. **Constraints** — API contracts, legacy dependencies, deadlines, team expertise.
4. **Best practice** — the patterns in this plugin and the official skills.

Codebase uses manual DI → don't introduce Hilt in a feature PR. Legacy API is callback-based → wrap it in a `Flow` at the boundary, don't rewrite the caller. Nothing decides it → apply best practice.

## Scope discipline

- Fix what blocks the task. Note other debt (`TODO(tech-debt): … TICKET-123`) or file it; don't fix it in the same change.
- Boy Scout changes stay small and safe: a named constant, a missing nullability annotation, a clearer name.
- Don't refactor working code without tests around it; write characterization tests first.
- Big migrations go module by module behind an adapter, with the app working at every step.

## Examples

```kotlin
// Codebase uses LiveData everywhere: match it in the new ViewModel.
class NewFeatureViewModel : ViewModel() {
    private val _items = MutableLiveData<List<Item>>()
    val items: LiveData<List<Item>> = _items
}
// Proposing StateFlow is a separate, approved migration — not a side effect of this feature.
```

```kotlin
// Deliberate shortcut, recorded where the next reader will see it.
// TODO(tech-debt): uses deprecated API; migration blocked by TICKET-123.
@Suppress("DEPRECATION")
fun legacyApproach() { /* … */ }
```

## When not to refactor

- Stable code with no task touching it.
- Changes that alter a public API or persisted data without a migration plan (`persisted-state-review.md`).
- High deadline pressure with no test coverage.
- The "better" approach is unfamiliar to the team that maintains it.

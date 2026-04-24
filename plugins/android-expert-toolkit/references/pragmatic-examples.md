# Pragmatic Development Examples

Code examples demonstrating the pragmatic development principles from SKILL.md.

## When to use

Read this reference when applying pragmatic principles to real code — tagging technical debt, making simplicity trade-offs, or justifying a deliberate shortcut. Used across all implementation agents when a decision needs to be documented inline rather than solved fully.

## Document Technical Debt

```kotlin
// TODO(tech-debt): This uses deprecated API. Migration blocked by JIRA-123.
// See design doc: [link] for proposed solution.
@Suppress("DEPRECATION")
fun legacyApproach() { ... }
```

## Good: Respect Existing Pattern

```kotlin
// Existing codebase uses LiveData everywhere
class NewFeatureViewModel : ViewModel() {
    // Match the pattern, don't introduce StateFlow yet
    private val _items = MutableLiveData<List<Item>>()
    val items: LiveData<List<Item>> = _items
}
```

## Bad: Force Best Practice

```kotlin
// Existing codebase uses LiveData everywhere
class NewFeatureViewModel : ViewModel() {
    // Don't do this - introduces inconsistency
    val items: StateFlow<List<Item>> = ...
}
```

## Good: Boy Scout Rule

```kotlin
// Found magic number, quick fix
- if (count > 10) { ... }
+ if (count > MAX_ITEMS) { ... }
```

## Bad: Over-Refactoring

```kotlin
// Task was to fix a bug, but you refactor entire file
// Original: 200 lines, 1 bug
// After: 500 lines, 3 new abstractions, 1 bug fixed, 2 new bugs
```

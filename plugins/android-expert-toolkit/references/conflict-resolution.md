# Conflict Resolution Hierarchy

When pragmatic principles conflict with each other or with best practices, use this priority hierarchy to make clear, justified decisions.

## When to use

Read this reference when two principles pull in opposite directions (e.g., "ship fast" vs "test coverage", "match existing patterns" vs "use modern API") and you need a defensible tiebreaker. Used by any agent facing a trade-off decision that affects safety, correctness, or maintainability.

## Priority Order

```
P0: Safety (Never Compromise)
|
|- Null safety
|- Error handling
|- Security vulnerabilities
'- Data integrity

P1: Boy Scout Rule (Within Task Scope)
|
|- Magic numbers -> constants
|- Unclear names -> descriptive names
|- Missing docs -> add comments
'- Simple refactors that improve maintainability

P2: Consistency (Match Existing)
|
|- Architecture patterns (MVVM, MVI)
|- State management (LiveData, StateFlow)
|- DI framework (Hilt, Koin, Dagger)
'- Code style and conventions

P3: Modernization (Long-term Value)
|
|- Deprecated APIs -> modern alternatives
|- Legacy patterns -> current best practices
|- Technical debt reduction
'- Future-proofing
```

## Conflict Resolution Matrix

| Higher Priority | vs | Lower Priority | Resolution |
|----------------|-------|----------------|------------|
| Safety | vs | Consistency | Always fix safety issues, even if it breaks consistency |
| Safety | vs | Modernization | Fix safety first, modernize later |
| Boy Scout | vs | Consistency | Improve code you're touching, don't expand scope |
| Boy Scout | vs | Modernization | Quick wins now, big changes later |
| Consistency | vs | Modernization | Match existing unless mandate to modernize |

## Detailed Conflict Scenarios

### Scenario 1: Safety vs. Consistency
**Conflict:** Codebase uses `!!` operator in 50+ places. Should new code match this pattern?

**Analysis:**
- **Consistency principle** says: Match existing pattern (use `!!`)
- **Safety principle** says: Never use `!!` (use safe calls or explicit null checks)

**Resolution:** Safety wins (P0 > P2)

**Action:**
```kotlin
// Matching existing pattern (unsafe)
val name = user.name!!  // NPE risk

// Safe approach (breaks consistency for safety)
val name = user.name ?: run {
    Timber.e("User name is null for id=${user.id}")
    "Unknown User"
}

// Document the deviation
// TODO(safety): JIRA-456 - Replace !! operator across codebase
// See ADR-089: "Zero Tolerance for !! Operator"
```

**Rationale:**
- NPEs cause production crashes
- User experience degradation
- Safety cannot be compromised for consistency

---

### Scenario 2: Boy Scout vs. Consistency
**Conflict:** Feature implementation requires editing a file with magic numbers everywhere. Should they be extracted?

**Analysis:**
- **Consistency principle** says: Don't change unrelated code
- **Boy Scout Rule** says: Leave it better than you found it

**Resolution:** Boy Scout wins IF within task scope (P1 > P2 when bounded)

**Action:**
```kotlin
// File: ItemsViewModel.kt (editing for new feature)

// GOOD: Fix magic numbers in file you're already touching
class ItemsViewModel {
    private val MAX_ITEMS = 50  // Was: if (count > 50)
    private val MIN_ITEMS = 5   // Was: if (count < 5)

    // Your new feature code here
    fun addNewFeature() { ... }
}

// BAD: Don't expand scope to other files
// Don't go fix magic numbers in ProfileViewModel, SettingsViewModel, etc.
```

**Rationale:**
- Small improvements are low-risk
- Bounded to files already being modified
- Doesn't expand PR scope significantly

**Boundary:**
- Fix magic numbers: YES (within file)
- Rename variables: YES (within file)
- Extract shared constants to util: NO (scope expansion)
- Refactor entire class: NO (scope expansion)

---

### Scenario 3: Consistency vs. Modernization
**Conflict:** Codebase has 47 ViewModels using LiveData. New feature could use StateFlow (modern). What to use?

**Analysis:**
- **Consistency principle** says: Match LiveData (94% of codebase)
- **Modernization principle** says: Use StateFlow (Kotlin-first, better performance)

**Resolution:** Consistency wins UNLESS explicitly mandated (P2 > P3 by default)

**Action:**
```kotlin
// GOOD: Match existing pattern
class ProfileViewModel : ViewModel() {
    private val _profile = MutableLiveData<Profile>()
    val profile: LiveData<Profile> = _profile
}

// Document for future
// TODO(tech-debt): JIRA-789 - StateFlow migration
// See migration plan: docs/stateflow_migration_plan.md
// Decision: Match LiveData for consistency (ADR-042)
```

**When Modernization Wins:**
If architect has issued explicit modernization directive:
```kotlin
// Architect decision: "All new features use StateFlow"
class ProfileViewModel : ViewModel() {
    val profile: StateFlow<Profile> = repository.profileFlow
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), Profile.Empty)
}

// Reference ADR-042: "StateFlow for New Features"
// Team guide: docs/stateflow_guide.md
// Rollback plan: Can revert to LiveData if issues
```

**Rationale:**
- Consistency reduces cognitive load
- Consistent patterns easier to review
- Migration should be planned, not ad-hoc

---

### Scenario 4: Boy Scout vs. Safety
**Conflict:** File has unclear variable names AND a potential NPE. Limited time. What to fix?

**Analysis:**
- **Safety principle** says: Fix NPE first
- **Boy Scout Rule** says: Improve variable names too

**Resolution:** Safety first, then Boy Scout if time permits (P0 > P1)

**Action:**
```kotlin
// Priority 1: Fix safety issue (MUST DO)
val user = repository.getUser(userId)
    ?: throw IllegalStateException("User $userId not found")

// Priority 2: Boy Scout improvements (if time permits)
- val x = user.data  // Unclear
+ val userName = user.data  // Better
```

**Rationale:**
- Safety issues can crash production
- Boy Scout improvements are nice-to-have
- If deadline is tight, safety only

---

### Scenario 5: All Principles Clash
**Conflict:** Legacy Java code with `null` returns (unsafe), inconsistent with Kotlin codebase (consistency issue), uses deprecated API (modernization), and has magic numbers (Boy Scout opportunity). What to prioritize?

**Analysis:**
```
P0: Safety - Fix null handling
P1: Boy Scout - Extract magic numbers (if in scope)
P2: Consistency - Wrap in Kotlin-friendly API
P3: Modernization - Replace deprecated API (future work)
```

**Resolution:** Address by priority order

**Action:**
```kotlin
// P0: Safety first - Add null safety
@Nullable
public User getUser(String id) {
    // Add @Nullable annotation for Kotlin interop
}

// P2: Consistency - Wrap in Kotlin API
class UserManagerWrapper @Inject constructor(
    private val javaManager: UserManager,
) {
    fun getUser(id: String): User? {
        return javaManager.getUser(id)  // Platform type -> explicit nullable
    }
}

// P1: Boy Scout (if time) - Extract magic numbers
- if (users.size() > 100) { ... }
+ private static final int MAX_USERS = 100;
+ if (users.size() > MAX_USERS) { ... }

// P3: Modernization (document for later)
// TODO(tech-debt): JIRA-901 - Migrate from deprecated API
// Current: getUserDeprecated() (works, but deprecated in API 29)
// Target: getUser(context) (modern, but requires refactor)
```

**Time Allocation:**
- Safety: 80% of effort (non-negotiable)
- Boy Scout: 15% of effort (quick wins)
- Consistency: 5% of effort (wrapper)
- Modernization: 0% now, 100% later (track in ticket)

---

## Conflict Resolution Template

Use this template when conflicts arise:

```markdown
## Conflict: [Brief Description]

**Date:** [Date]
**Author:** [Who made decision]
**Context:** [Feature, deadline, constraints]

### Principles in Conflict

1. **[Principle 1]** (Priority: P[0-3])
   - Suggests: [Approach A]
   - Rationale: [Why this principle applies]

2. **[Principle 2]** (Priority: P[0-3])
   - Suggests: [Approach B]
   - Rationale: [Why this principle applies]

### Constraint Analysis

- **Deadline:** [Date] ([X] weeks remaining)
- **Team Familiarity:** [High/Medium/Low] with [approach]
- **Risk Tolerance:** [High/Medium/Low] for this feature
- **Business Priority:** [Critical/Important/Nice-to-have]
- **Test Coverage:** [Adequate/Inadequate] for safe refactoring

### Resolution

**Winner:** [Higher Priority Principle] (P[X] > P[Y])

**Decision:** [Chosen approach with brief rationale]

**Immediate Action:**
- [What to do now]

**Follow-up Actions:**
- [What to document]
- [What to track for later]
- [Who to inform]

**ADR Reference:** [ADR-XXX if architectural decision]

### Code Example

\```kotlin
// Chosen approach
[code showing resolution]

// Alternative considered
[code showing rejected approach]

// Documentation
// TODO([priority]): [tracking ticket] - [what to fix later]
\```

### Lessons Learned

[What this conflict taught us about our codebase/process]
```

## Quick Reference Card

**When principles clash, ask:**

1. **Is there a safety issue?** -> Safety wins (fix immediately)
2. **Can I make a small improvement?** -> Boy Scout Rule (within scope only)
3. **Is there a dominant pattern?** -> Consistency wins (match existing)
4. **Is modernization mandated?** -> Modernization wins (if explicit directive)
5. **Still unsure?** -> Invoke Decision Council Protocol (android-architect.md)

**Golden Rules:**
- Never compromise safety for any other principle
- Don't expand scope beyond your task (even for improvements)
- Match existing patterns unless you have architectural approval
- Document technical debt you can't fix now

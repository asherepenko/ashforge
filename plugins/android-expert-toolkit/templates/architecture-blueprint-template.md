---
agent: android-architect
feature: "{feature_slug}"
timestamp: "{run_timestamp}"
files_created: []
files_modified: []
dependencies_added: []
interfaces_exposed: []
---

# Architecture Blueprint: [FEATURE NAME]

```yaml
Written by: android-architect
Timestamp: [ISO 8601 - e.g., 2026-02-13T10:30:00Z]
```

## Pipeline Context

<!-- Carry-forward block — downstream agents copy this section verbatim into their handoffs -->

**Original Prompt:** [The user's original 1-4 sentence request that started the pipeline]

**Business Purpose:** [1-2 sentences: what problem this feature solves for users, not how it's built]

**UX Intent:** [What the user experience should feel like — screen flow, key interactions, visual character. Enough for compose-expert to design screens without guessing.]

## Summary

<!-- High-level overview of the architectural design for this feature -->

**Feature:** [Brief description of what this feature does]

**Scope:** [What's included and what's out of scope]

**Impact:** [What systems/modules this affects]

## Decisions

<!-- Key architectural decisions made during design -->

### Decision 1: [Decision Title]

**Context:** [Why this decision was needed]

**Options Considered:**
1. [Option A] - [Brief description]
2. [Option B] - [Brief description]
3. [Option C - CHOSEN] - [Brief description]

**Decision:** We chose [Option C] because [reasoning].

**Trade-offs:**
- ✅ Benefit 1
- ✅ Benefit 2
- ⚠️ Trade-off 1
- ⚠️ Trade-off 2

### Decision 2: [Another Decision]

**Context:** [Context]
**Decision:** [What was decided]
**Rationale:** [Why]

## Artifacts Created

<!-- Concrete deliverables and their locations -->

### Module Structure

**Feature Modules:**
```
feature/
├── [feature-name]/
│   ├── api/              # Public navigation, interfaces
│   └── impl/             # Screens, ViewModels, internal logic
```

**Core Modules Used:**
- `core:data` - [Repositories being used]
- `core:database` - [Room entities and DAOs]
- `core:network` - [API clients]
- `core:model` - [Data models]
- `core:designsystem` - [UI components]

### Architecture Patterns

**State Management Pattern:**
```kotlin
// UI State sealed interface
sealed interface [Feature]UiState {
    data object Loading : [Feature]UiState
    data class Error(val message: String) : [Feature]UiState
    data class Success(val data: [DataType]) : [Feature]UiState
}
```

**ViewModel Pattern:**
```kotlin
@HiltViewModel
class [Feature]ViewModel @Inject constructor(
    private val repository: [Repository],
) : ViewModel() {
    val uiState: StateFlow<[Feature]UiState> =
        repository.dataFlow
            .map { [Feature]UiState.Success(it) }
            .catch { emit([Feature]UiState.Error(it.message ?: "Unknown")) }
            .stateIn(
                scope = viewModelScope,
                started = SharingStarted.WhileSubscribed(5_000),
                initialValue = [Feature]UiState.Loading
            )
}
```

**Repository Pattern:**
```kotlin
interface [Feature]Repository {
    val dataFlow: Flow<[DataType]>
    suspend fun performAction(action: [ActionType])
}
```

### Data Flow

```
User Action → Composable → ViewModel → Repository → DataSource → Room/Retrofit
                                                                       ↓
User sees ← Composable ← ViewModel ← StateFlow ← Repository ← Flow ← Room/Retrofit
```

**Flow Steps:**
1. [User action] triggers [event]
2. [Component] calls [method]
3. [State update] propagates via [mechanism]

## Next Steps

<!-- What downstream agents should do with this blueprint -->

### For gradle-build-engineer

**Action Required:**
- [ ] Create module structure in `feature/[feature-name]/`
- [ ] Set up `api` and `impl` submodules
- [ ] Configure dependencies in version catalog
- [ ] Add convention plugins for feature modules

**Reference:** This architecture blueprint (.artifacts/aet/handoffs/{feature_slug}/{run_timestamp}-architecture-blueprint.md)

### For android-developer

**Action Required:**
- [ ] Implement ViewModels using patterns defined above
- [ ] Create Repository implementations
- [ ] Implement Room entities and DAOs
- [ ] Write data layer with offline-first pattern

**Reference:** Module structure and architecture patterns sections above

### For compose-expert

**Action Required:**
- [ ] Implement Composable screens consuming StateFlow
- [ ] Create UI components following designsystem patterns
- [ ] Implement navigation routes in `api` module

**Reference:** UI State definitions and ViewModel contracts

### For android-testing-specialist

**Action Required:**
- [ ] Create test doubles for repositories
- [ ] Write ViewModel tests using Turbine for Flow testing
- [ ] Verify offline-first behavior with fakes

**Reference:** Repository interfaces and state definitions

## Constraints

<!-- Technical constraints and requirements -->

### Architectural Constraints

**Must Follow:**
- StateFlow for UI state (not LiveData)
- Flow-based data access (no suspend fun snapshots)
- Constructor injection only (no field injection)
- Offline-first: local database is source of truth
- Sealed interfaces for all UI states

**Must Not:**
- Feature-to-feature implementation dependencies
- Direct network access from ViewModels
- Nullable state types (use Loading/Error/Success sealed types)
- Mutable state exposed to UI

### Performance Constraints

- StateFlow with WhileSubscribed(5000ms) for lifecycle awareness
- Database queries optimized with indexes
- No blocking operations on main thread

### Testing Constraints

- All business logic must be testable with fakes (no mocks)
- Repositories must have test doubles
- ViewModels testable in isolation

### Build Constraints

- Max method count per module: 65k
- Use R8 shrinking for release builds
- ProGuard rules for serialization

---

## Validation Checklist

<!-- Used by validation hooks - do not remove -->

- [ ] Summary section complete
- [ ] All architectural decisions documented with rationale
- [ ] Module structure and patterns defined
- [ ] Next steps for all downstream agents specified
- [ ] All constraints documented

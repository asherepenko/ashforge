# Android Architecture Quality Rubric

Grading criteria for architecture and data layer work. Use both as **generation targets** (what to aim for when building) and **evaluation criteria** (what to check when reviewing). Each criterion describes what strong and weak work looks like.

## When to use

Read this reference when authoring an `architecture-blueprint.md` (to aim at the "Strong" column) or when reviewing architecture and data-layer work (to grade against the rubric). Used by android-architect for generation and by any reviewer for evaluation.

## 1. Module Independence

**Strong**: Features can be developed, tested, and deployed independently. Zero cross-feature implementation dependencies. Core modules never reference features. Adding a new feature requires no changes to existing feature modules.

**Weak**: Features import each other's implementation classes. Removing one feature breaks compilation of another. Shared state lives in feature modules instead of core. "Just this one import" shortcuts accumulate into a dependency web.

## 2. Data Flow Integrity

**Strong**: Unidirectional data flow — User Action -> ViewModel -> Repository -> DataSource -> Room/Network, with reactive Flow carrying data back up. Repositories expose only Flow (never snapshot methods). ViewModels expose StateFlow with WhileSubscribed(5_000). No layer skipping.

**Weak**: UI calls network directly. Repositories return suspend functions that give point-in-time snapshots instead of reactive streams. ViewModel exposes mutable state. Data flows sideways between repositories.

## 3. Offline-First Fidelity

**Strong**: Room is the single source of truth. Network operations write to Room; UI observes Room. The app works meaningfully without network. Sync failures are recoverable. Conflict resolution strategy is explicit and documented.

**Weak**: UI observes network responses directly and caches as an afterthought. Going offline breaks core features. Network errors surface as crashes rather than degraded-but-functional states. "Works offline" means showing cached data from last successful fetch with no indication of staleness.

## 4. State Predictability

**Strong**: UI state modeled with sealed interfaces (Loading, Error, Success). State transitions are explicit and traceable from user action to UI update. Error is state, not an exception thrown to the caller. A single StateFlow per screen carries all UI-relevant state.

**Weak**: Multiple independent boolean flags (isLoading, isError, hasData) that can enter impossible combinations. Error handling via try-catch in the UI layer. State scattered across multiple LiveData/StateFlow properties that can go out of sync.

## 5. Dependency Hygiene

**Strong**: All injection via constructor (Hilt @Inject). Every dependency has an interface boundary. Any dependency can be replaced with a test double by providing an alternative implementation. No service locators, no static singletons, no ambient state.

**Weak**: Field injection, service locators, or companion object singletons for convenience. Classes that cannot be instantiated in tests without the full DI graph. Dependencies on concrete implementations rather than interfaces.

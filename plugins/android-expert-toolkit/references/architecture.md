# Android App Architecture

## When to use

Read when deciding layers, module boundaries, or data flow for a feature, or when reviewing a change for architectural fit. ViewModel/state details → `presentation.md`. Repositories and persistence → `data-layer.md`. DI → `dependency-injection.md`. Run `android-conventions architecture` first and match what the project already does.

## Layers

| Layer | Holds | Rules |
|-------|-------|-------|
| UI | Composables, ViewModels | ViewModel exposes one `StateFlow<State>`; composables are stateless below the Route/Root. |
| Domain (optional) | Use cases | Add only for logic reused across ViewModels or combining several repositories. Plain CRUD goes straight to the repository. |
| Data | Repositories, data sources | Repository is the single source of truth. Expose `Flow` for observed data; one-shot operations are `suspend`. Map exceptions to a typed error here (`android-error-handling` skill). |

Data flows down as state, events flow up as actions (unidirectional data flow).

```
Composable ──action──▶ ViewModel ──call──▶ Repository ──▶ Local / Remote source
     ▲                     │                    │
     └──────state──────────┘◀───── Flow ────────┘
```

## Module structure

```
app/                      # Application, MainActivity, nav graph assembly
feature/<name>/api/       # Navigation keys, public contracts (no UI)
feature/<name>/impl/      # Screens, ViewModels, feature-private logic
core/model/               # Pure Kotlin models, no Android deps
core/data/                # Repositories
core/database/            # Room
core/network/             # HTTP client + DTOs
core/datastore/           # DataStore
core/designsystem/        # Theme, design-system components
core/ui/                  # Shared composables
core/testing/             # Fakes, test rules
sync/                     # WorkManager sync
```

Small apps don't need this split; propose it only when build times or ownership boundaries justify it.

### Dependency rules

- `feature:*:impl` may depend on other features' `api` modules, never on another `impl`.
- `core:*` never depends on `feature:*` or `:app`.
- `core:model` depends on nothing Android.
- `:app` is the only module that sees every `impl` and wires navigation.

Check for cycles with `./gradlew :app:dependencies` or the project's module-graph task.

## Coroutines and Flow

- `viewModelScope` for UI work; never `GlobalScope`.
- Convert cold flows to state with `stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), initial)`.
- Inject a `CoroutineDispatcher` only into classes that switch dispatchers **and** are unit-tested; ViewModels using `viewModelScope` are covered by `Dispatchers.setMain`.
- Every catch-all `catch` in a suspend function rethrows `CancellationException` — see `android-error-handling`.
- Prefer `combine` over nested `collect`; `distinctUntilChanged` before expensive mapping.
- Cancellation-safe cleanup goes in `finally` or `onCompletion`, not after the suspend call.

## Kotlin modelling

- Sealed interfaces for closed hierarchies (errors, actions, navigation keys); exhaustive `when` without `else`.
- `@JvmInline value class` for IDs and units (`UserId`, `Millis`) to stop argument mix-ups.
- Data classes for state; no mutable collections in state.
- Java interop or legacy Java modules → `kotlin-java-interop.md`.

## Offline-first

Local database is the source of truth. The UI observes the database; network refresh writes into it. Sync strategy (pull-to-refresh, WorkManager, conflict resolution) → `data-layer.md`.

## Decisions

Record significant decisions (new module, DI change, state-management change) as a short ADR: context, options, decision, consequences. For pattern choices, the 80/20 rule in `pattern-detection.md` decides between matching the codebase and proposing a change; `pragmatics.md` covers when not to refactor.

## Review checklist

- [ ] No `impl` → `impl` module dependency; no cycles.
- [ ] Repository exposes `Flow` for observed data; no snapshot getters used as streams.
- [ ] UI state holds no `Throwable`, raw exception message, `Context`, or lambdas.
- [ ] Errors are typed at the layer that catches them; `CancellationException` is rethrown.
- [ ] Persisted-state change on installed devices → `persisted-state-review.md`.
- [ ] Navigation keys live in `api` modules; Nav 3 work uses the `navigation-3` skill.

# Dependency Injection

## When to use

Read when adding bindings, scoping a dependency, or reviewing DI code. Run `aet-check di` first: use the framework the project already uses. Changing frameworks is a separate, approved migration.

## Framework-agnostic rules

1. Constructor injection everywhere you own the class. Field injection only where the framework creates the object (Activity, Service).
2. Inject interfaces at layer boundaries (repositories, data sources); inject concrete classes for pure helpers.
3. Scope to the consumer's lifetime. App singletons only for things that are expensive or hold shared state (HTTP client, database).
4. Never inject the container/graph itself into business code (service locator).
5. Tests construct classes directly with fakes; they don't need the DI graph.

## Hilt

```kotlin
@Module
@InstallIn(SingletonComponent::class)
internal abstract class DataModule {
    @Binds abstract fun bindItemsRepository(impl: OfflineFirstItemsRepository): ItemsRepository
}

@Module
@InstallIn(SingletonComponent::class)
internal object NetworkModule {
    @Provides @Singleton
    fun okHttp(): OkHttpClient = OkHttpClient.Builder().build()
}

@HiltViewModel
class ItemsViewModel @Inject constructor(
    private val savedStateHandle: SavedStateHandle,
    private val repository: ItemsRepository,
) : ViewModel()
```

- `@Binds` in abstract modules for interface → impl; `@Provides` for third-party types.
- Qualifiers (`@Dispatcher(IO)`) instead of named strings.
- AGP 9 requires Hilt ≥ 2.59.2 and KSP (no kapt) — `agp-9-upgrade` skill.
- Compose: `hiltViewModel()` in the Route/Root composable only.
- Nav 3 + Hilt → `navigation-3` skill (`recipes/modular-hilt.md`).

## Koin

```kotlin
val itemsModule = module {
    single<ItemsRepository> { OfflineFirstItemsRepository(get(), get()) }
    viewModelOf(::ItemsViewModel)
}
```

- One module per feature layer; assemble in `:app` with `startKoin { modules(...) }`.
- `single` for shared state, `factory` for cheap stateless objects, `viewModel`/`viewModelOf` for ViewModels.
- Koin resolves at runtime: add a `verify()` / `checkModules` test so a missing binding fails CI, not the user.
- Compose: `koinViewModel()` in the Root composable.

## Dagger (without Hilt)

Used in KMP-shared or legacy code. Components and subcomponents are explicit; keep component interfaces small and expose factories, not every binding. Same `@Binds`/`@Provides` rules as Hilt.

## Manual DI

An `AppContainer` holding `by lazy` singletons, created in `Application`. ViewModels via `viewModelFactory { initializer { ItemsViewModel(createSavedStateHandle(), container.itemsRepository) } }`. Fine for small apps; propose a framework only when wiring becomes the bottleneck.

## Comparison

| | Hilt | Dagger | Koin | Manual |
|-|------|--------|------|--------|
| Graph checked at | compile time | compile time | runtime (test with `verify`) | compile time (plain code) |
| Build cost | KSP | KSP | none | none |
| KMP | no | yes | yes | yes |
| ViewModel support | built in | manual | built in | `viewModelFactory` |

## Review checklist

- [ ] Same DI framework as the rest of the module.
- [ ] No field injection in classes you construct.
- [ ] Singletons justified; nothing holding an Activity `Context` in `SingletonComponent`.
- [ ] Koin graph covered by a verification test.

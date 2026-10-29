# Testing Patterns

## When to use

Read for test code mechanics: fakes, ViewModel and Flow tests, integration tests, Compose UI tests. **What** to test (break vectors, distinct angles, unit = behavior) is the `android-testing` skill — apply it first. Test infrastructure, instrumented runners, screenshot and E2E setup → `testing-setup` skill. Benchmarks → `performance.md`.

Use the project's libraries (`aet-check testing`). Samples use JUnit 4 + Truth + Turbine; swap for the module's equivalents.

## Test pyramid

| Kind | Runs | Covers | Default tool |
|------|------|--------|--------------|
| Unit | JVM, ms | ViewModels, validators, mappers, reducers, repositories with fakes | JUnit + coroutines-test |
| Integration | JVM (Robolectric) or device | Room DAOs + migrations, network mapping over `MockWebServer`, WorkManager | Room in-memory, `MigrationTestHelper`, `WorkManagerTestInitHelper` |
| UI | device/emulator or Robolectric | Screen behavior from state; navigation | Compose test rule |
| Screenshot | JVM | visual regressions per preview/state | per `testing-setup` |

Coverage targets are a signal, not a goal; a missing break vector matters more than a percentage.

## Fakes

```kotlin
class FakeItemsRepository : ItemsRepository {
    private val state = MutableStateFlow<List<Item>>(emptyList())
    var nextRefreshError: DataError? = null

    override val items: Flow<List<Item>> = state
    fun emit(list: List<Item>) { state.value = list }

    override suspend fun refresh(): EmptyResult<DataError> =
        nextRefreshError?.let { Result.Error(it) } ?: Result.Success(Unit)
}
```

Keep fakes in `core:testing` (or the feature's `testFixtures`) so every module shares them. Mocking libraries are for final framework/third-party classes only (see the skill).

## ViewModel tests

```kotlin
class ItemsViewModelTest {
    @get:Rule val mainDispatcherRule = MainDispatcherRule()   // sets Dispatchers.Main to a test dispatcher

    private val repository = FakeItemsRepository()
    private val viewModel = ItemsViewModel(repository)

    @Test fun `refresh failure with no cached items shows error resource`() = runTest {
        repository.nextRefreshError = DataError.Network.NO_INTERNET
        viewModel.uiState.test {
            assertThat(awaitItem()).isEqualTo(ItemsUiState.Loading)
            viewModel.onAction(ItemsAction.Refresh)
            assertThat(expectMostRecentItem())
                .isEqualTo(ItemsUiState.Error(UiText.StringResource(R.string.error_no_internet)))
        }
    }

    @Test fun `refresh failure keeps cached items`() = runTest { /* distinct angle */ }
}
```

- State built with `stateIn(WhileSubscribed)` only updates while collected: collect it (Turbine `test {}` or `backgroundScope.launch { viewModel.uiState.collect() }`) before acting.
- `StateFlow` conflates: assert the final state with `expectMostRecentItem()` instead of every intermediate emission, unless the intermediate state is the behavior under test.
- `UnconfinedTestDispatcher` runs launches eagerly; `StandardTestDispatcher` needs `advanceUntilIdle()`. Pick one per test class and be consistent.
- Virtual time: `advanceTimeBy(5_000)` for debounce/timeouts; inject a fake clock for wall-clock logic.

## Flow tests (Turbine)

```kotlin
flow.test {
    assertThat(awaitItem()).isEqualTo(first)
    assertThat(awaitItem()).isEqualTo(second)
    awaitComplete()            // or cancelAndIgnoreRemainingEvents()
}
```

`awaitError()` for flows that should fail; `expectNoEvents()` to prove nothing else was emitted (useful for double-tap and stale-response vectors).

## SavedStateHandle and routes

```kotlin
val handle = SavedStateHandle(mapOf("title" to "Draft"))
val restored = EditNoteViewModel(handle, FakeNoteRepository())
```

For Nav 2 type-safe routes, put the route's arguments in the handle under their property names (`SavedStateHandle(mapOf("itemId" to "42"))`) so `handle.toRoute<ItemDetailRoute>()` resolves. `toRoute` relies on Android `Bundle` support: run that test under Robolectric, or have the ViewModel receive the parsed id.

## Integration tests

- **Room:** `Room.inMemoryDatabaseBuilder(context, AppDatabase::class.java)`; assert through DAO flows with Turbine. Every migration gets a `MigrationTestHelper` test from the exported schema.
- **Network mapping:** `MockWebServer` returning real JSON fixtures, including malformed bodies, 401/409/500, and timeouts; assert the typed error.
- **WorkManager:** `WorkManagerTestInitHelper` + `TestListenableWorkerBuilder` for `CoroutineWorker`.

## Compose UI tests

Test the stateless Screen with fixed state; no ViewModel or DI needed.

```kotlin
@get:Rule val composeRule = createAndroidComposeRule<ComponentActivity>()

@Test fun errorState_retryDispatchesAction() {
    val actions = mutableListOf<ItemsAction>()
    composeRule.setContent {
        AppTheme {
            ItemsScreen(ItemsUiState.Error(UiText.StringResource(R.string.error_no_internet)), actions::add, onItemClick = {})
        }
    }
    composeRule.onNodeWithText(composeRule.activity.getString(R.string.retry)).performClick()
    assertThat(actions).containsExactly(ItemsAction.Retry)
}
```

- Find nodes the way users do: text, content description, role. Add `testTag` only when nothing else is stable.
- Resolve strings from resources, not literals, so tests pass in every locale.
- Use the preview matrix (`compose-ui.md`) as the list of states to cover.
- Full-app tests with Hilt: `@HiltAndroidTest` + `HiltAndroidRule(order = 0)` before the compose rule; swap modules with `@TestInstallIn`.
- Accessibility checks in UI tests → `accessibility.md`.

## Screenshot tests

Tool choice depends on the project and AGP version (Compose Preview Screenshot Testing, Roborazzi, Paparazzi). Follow the `testing-setup` skill: it detects what the project uses, prefers AGP test suites on new enough AGP, and notes Paparazzi issues on AGP 9. Don't add a second screenshot tool next to an existing one.

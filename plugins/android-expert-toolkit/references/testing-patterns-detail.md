# Testing Patterns Detail Reference

Code examples and implementation patterns extracted from android-testing-specialist agent prompt.

## When to use

Read this reference when implementing specific test infrastructure: test doubles, Turbine Flow tests, Compose UI tests, or parameterized test cases. Used by android-testing-specialist during test implementation. For high-level testing strategy, see `testing-patterns.md`.

## Test Double Pattern

```kotlin
// Production interface (core:data)
interface ItemRepository {
    val items: Flow<List<Item>>
    suspend fun refresh()
    suspend fun createItem(item: Item)
    suspend fun deleteItem(id: String)
}

// Test double (core:testing)
class TestItemRepository : ItemRepository {
    private val _items = MutableStateFlow<List<Item>>(emptyList())
    override val items: Flow<List<Item>> = _items

    // Test control methods
    fun setItems(items: List<Item>) {
        _items.value = items
    }

    fun emitError() {
        // Simulate error scenario
    }

    // Interface implementations
    override suspend fun refresh() {
        refreshCallCount++
    }

    override suspend fun createItem(item: Item) {
        _items.value = _items.value + item
    }

    override suspend fun deleteItem(id: String) {
        _items.value = _items.value.filterNot { it.id == id }
    }

    // Test verification helpers
    var refreshCallCount = 0
        private set

    fun reset() {
        _items.value = emptyList()
        refreshCallCount = 0
    }
}
```

## ViewModel Unit Tests

```kotlin
class ItemsViewModelTest {
    // MainDispatcherRule sets test dispatcher for coroutines
    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()

    private lateinit var repository: TestItemRepository
    private lateinit var viewModel: ItemsViewModel

    @Before
    fun setup() {
        repository = TestItemRepository()
        viewModel = ItemsViewModel(repository)
    }

    @After
    fun tearDown() {
        repository.reset()
    }

    @Test
    fun `uiState starts with Loading`() = runTest {
        val initialState = viewModel.uiState.value
        assertThat(initialState).isInstanceOf(ItemsUiState.Loading::class.java)
    }

    @Test
    fun `uiState emits Success when items available`() = runTest {
        val testItems = listOf(
            Item("1", "Item 1", "Description 1"),
            Item("2", "Item 2", "Description 2"),
        )
        repository.setItems(testItems)

        viewModel.uiState.test {
            val state = awaitItem() as ItemsUiState.Success
            assertThat(state.items).isEqualTo(testItems)
            assertThat(state.items).hasSize(2)
        }
    }

    @Test
    fun `uiState emits Error when repository fails`() = runTest {
        repository.emitError()

        viewModel.uiState.test {
            val state = awaitItem()
            assertThat(state).isInstanceOf(ItemsUiState.Error::class.java)
        }
    }

    @Test
    fun `refresh calls repository refresh`() = runTest {
        viewModel.refresh()
        assertThat(repository.refreshCallCount).isEqualTo(1)
    }

    @Test
    fun `createItem adds item to repository`() = runTest {
        viewModel.createItem("New Item", "New Description")

        repository.items.test {
            val items = awaitItem()
            assertThat(items).hasSize(1)
            assertThat(items[0].name).isEqualTo("New Item")
            assertThat(items[0].description).isEqualTo("New Description")
        }
    }

    @Test
    fun `deleteItem removes item from repository`() = runTest {
        val item = Item("1", "Item 1", "Description 1")
        repository.setItems(listOf(item))

        viewModel.deleteItem("1")

        repository.items.test {
            assertThat(awaitItem()).isEmpty()
        }
    }

    @Test
    fun `multiple rapid refreshes handled correctly`() = runTest {
        repeat(5) { viewModel.refresh() }
        assertThat(repository.refreshCallCount).isEqualTo(5)
    }
}
```

## Repository Unit Tests

```kotlin
class OfflineFirstItemRepositoryTest {
    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()

    private lateinit var localDataSource: TestItemDao
    private lateinit var remoteDataSource: TestItemApiService
    private lateinit var networkMonitor: TestNetworkMonitor
    private lateinit var repository: OfflineFirstItemRepository

    @Before
    fun setup() {
        localDataSource = TestItemDao()
        remoteDataSource = TestItemApiService()
        networkMonitor = TestNetworkMonitor()
        repository = OfflineFirstItemRepository(
            itemDao = localDataSource,
            apiService = remoteDataSource,
            networkMonitor = networkMonitor,
            ioDispatcher = StandardTestDispatcher(),
        )
    }

    @Test
    fun `items flow emits data from local data source`() = runTest {
        val testItems = listOf(
            ItemEntity("1", "Item 1", "Description 1"),
        )
        localDataSource.setItems(testItems)

        repository.items.test {
            val items = awaitItem()
            assertThat(items).hasSize(1)
            assertThat(items[0].id).isEqualTo("1")
        }
    }

    @Test
    fun `refresh updates local from remote when online`() = runTest {
        networkMonitor.setOnline(true)
        val remoteItems = listOf(
            ItemDto("1", "Remote Item", "Remote Description"),
        )
        remoteDataSource.setItems(remoteItems)

        repository.refresh()
        advanceUntilIdle()

        localDataSource.items.test {
            val items = awaitItem()
            assertThat(items).hasSize(1)
            assertThat(items[0].name).isEqualTo("Remote Item")
        }
    }

    @Test
    fun `refresh skips remote when offline`() = runTest {
        networkMonitor.setOnline(false)

        repository.refresh()
        advanceUntilIdle()

        assertThat(remoteDataSource.getItemsCallCount).isEqualTo(0)
    }

    @Test
    fun `createItem saves locally and syncs when online`() = runTest {
        networkMonitor.setOnline(true)
        val newItem = Item("1", "New", "Description")

        repository.createItem(newItem)
        advanceUntilIdle()

        localDataSource.items.test {
            assertThat(awaitItem()).contains(newItem.toEntity())
        }
        assertThat(remoteDataSource.createItemCallCount).isEqualTo(1)
    }

    @Test
    fun `createItem saves locally but not remote when offline`() = runTest {
        networkMonitor.setOnline(false)
        val newItem = Item("1", "New", "Description")

        repository.createItem(newItem)
        advanceUntilIdle()

        localDataSource.items.test {
            assertThat(awaitItem()).contains(newItem.toEntity())
        }
        assertThat(remoteDataSource.createItemCallCount).isEqualTo(0)
    }
}
```

## Compose UI Tests

```kotlin
@HiltAndroidTest
class ItemsScreenTest {
    @get:Rule(order = 0)
    val hiltRule = HiltAndroidRule(this)

    @get:Rule(order = 1)
    val composeTestRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun itemsScreen_loading_showsLoadingIndicator() {
        composeTestRule.setContent {
            ItemsScreen(
                uiState = ItemsUiState.Loading,
                onRefresh = {},
                onCreateItem = { _, _ -> },
                onDeleteItem = {},
                onItemClick = {},
            )
        }

        composeTestRule
            .onNodeWithContentDescription("Loading")
            .assertIsDisplayed()
    }

    @Test
    fun itemsScreen_error_showsErrorMessage() {
        composeTestRule.setContent {
            ItemsScreen(
                uiState = ItemsUiState.Error("Network error"),
                onRefresh = {},
                onCreateItem = { _, _ -> },
                onDeleteItem = {},
                onItemClick = {},
            )
        }

        composeTestRule
            .onNodeWithText("Network error")
            .assertIsDisplayed()
    }

    @Test
    fun itemsScreen_success_displaysItems() {
        val items = listOf(
            Item("1", "Item 1", "Description 1"),
            Item("2", "Item 2", "Description 2"),
        )

        composeTestRule.setContent {
            ItemsScreen(
                uiState = ItemsUiState.Success(items),
                onRefresh = {},
                onCreateItem = { _, _ -> },
                onDeleteItem = {},
                onItemClick = {},
            )
        }

        composeTestRule.onNodeWithText("Item 1").assertIsDisplayed()
        composeTestRule.onNodeWithText("Item 2").assertIsDisplayed()
        composeTestRule.onNodeWithText("Description 1").assertIsDisplayed()
    }

    @Test
    fun itemsScreen_clickItem_invokesCallback() {
        var clickedItemId: String? = null
        val items = listOf(Item("1", "Item 1", "Description 1"))

        composeTestRule.setContent {
            ItemsScreen(
                uiState = ItemsUiState.Success(items),
                onRefresh = {},
                onCreateItem = { _, _ -> },
                onDeleteItem = {},
                onItemClick = { clickedItemId = it },
            )
        }

        composeTestRule.onNodeWithText("Item 1").performClick()

        assertThat(clickedItemId).isEqualTo("1")
    }

    @Test
    fun itemsScreen_deleteItem_invokesCallback() {
        var deletedItemId: String? = null
        val items = listOf(Item("1", "Item 1", "Description 1"))

        composeTestRule.setContent {
            ItemsScreen(
                uiState = ItemsUiState.Success(items),
                onRefresh = {},
                onCreateItem = { _, _ -> },
                onDeleteItem = { deletedItemId = it },
                onItemClick = {},
            )
        }

        composeTestRule
            .onNodeWithContentDescription("Delete")
            .performClick()

        assertThat(deletedItemId).isEqualTo("1")
    }
}
```

## Flow Testing with Turbine

```kotlin
@Test
fun `combined flow emits when any source updates`() = runTest {
    val flow1 = MutableStateFlow("A")
    val flow2 = MutableStateFlow(1)

    val combined = combine(flow1, flow2) { s, i -> "$s$i" }

    combined.test {
        assertThat(awaitItem()).isEqualTo("A1")

        flow1.value = "B"
        assertThat(awaitItem()).isEqualTo("B1")

        flow2.value = 2
        assertThat(awaitItem()).isEqualTo("B2")
    }
}

@Test
fun `debounced flow emits only after delay`() = runTest {
    val flow = MutableSharedFlow<String>()
    val debounced = flow.debounce(300)

    debounced.test {
        flow.emit("A")
        flow.emit("B")
        flow.emit("C")

        // Only last value after delay
        assertThat(awaitItem()).isEqualTo("C")
    }
}
```

## Testing Coroutines with Virtual Time

```kotlin
@Test
fun `delayed action completes after timeout`() = runTest {
    val viewModel = MyViewModel(repository)

    // Advance time without real delay
    advanceTimeBy(5000)

    // Verify delayed action completed
    assertThat(viewModel.actionCompleted).isTrue()
}
```

## Testing State Updates

```kotlin
@Test
fun `state updates in correct sequence`() = runTest {
    repository.setItems(emptyList())

    viewModel.uiState.test {
        // Initial loading
        assertThat(awaitItem()).isInstanceOf(Loading::class.java)

        // Items loaded
        repository.setItems(testItems)
        val success = awaitItem() as Success
        assertThat(success.items).isEqualTo(testItems)

        // Refresh triggered
        viewModel.refresh()
        // Should not emit loading again (keep showing data)

        cancelAndIgnoreRemainingEvents()
    }
}
```

## Screenshot Testing with Roborazzi

```kotlin
@RunWith(RobolectricTestRunner::class)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class ScreenshotTests {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun itemCard_lightTheme() {
        composeTestRule.setContent {
            AppTheme(darkTheme = false) {
                ItemCard(
                    item = Item("1", "Item", "Description"),
                    onClick = {},
                    onDelete = {},
                )
            }
        }

        composeTestRule.onRoot().captureRoboImage()
    }

    @Test
    fun itemCard_darkTheme() {
        composeTestRule.setContent {
            AppTheme(darkTheme = true) {
                ItemCard(
                    item = Item("1", "Item", "Description"),
                    onClick = {},
                    onDelete = {},
                )
            }
        }

        composeTestRule.onRoot().captureRoboImage()
    }
}
```

## Performance Testing

### Macrobenchmark Testing

```kotlin
@RunWith(AndroidJUnit4::class)
class StartupBenchmark {
    @get:Rule
    val benchmarkRule = MacrobenchmarkRule()

    @Test
    fun startup() = benchmarkRule.measureRepeated(
        packageName = "com.example.app",
        metrics = listOf(StartupTimingMetric()),
        iterations = 5,
        startupMode = StartupMode.COLD,
        setupBlock = {
            pressHome()
        }
    ) {
        startActivityAndWait()
    }
}
```

### Baseline Profile Generation

```kotlin
@RunWith(AndroidJUnit4::class)
class BaselineProfileGenerator {
    @get:Rule
    val baselineProfileRule = BaselineProfileRule()

    @Test
    fun generate() = baselineProfileRule.collect(
        packageName = "com.example.app",
        maxIterations = 15,
        includeInStartupProfile = true,
    ) {
        startActivityAndWait()

        device.wait(Until.hasObject(By.res("feed_list")), 10_000)

        val feedList = device.findObject(By.res("feed_list"))
        feedList.scroll(Direction.DOWN, 0.8f)
        Thread.sleep(1000)

        device.findObject(By.text("First Item")).click()
        device.waitForIdle()

        device.pressBack()
        device.waitForIdle()
    }
}
```

### Frame Timing Benchmark

```kotlin
@RunWith(AndroidJUnit4::class)
class ScrollBenchmark {
    @get:Rule
    val benchmarkRule = MacrobenchmarkRule()

    @Test
    fun scrollFeed() = benchmarkRule.measureRepeated(
        packageName = "com.example.app",
        metrics = listOf(FrameTimingMetric()),
        iterations = 5,
        setupBlock = {
            startActivityAndWait()
        }
    ) {
        val feedList = device.findObject(By.res("feed_list"))
        feedList.setGestureMargin(device.displayWidth / 5)
        feedList.fling(Direction.DOWN)
        device.waitForIdle()
    }
}
```

### Performance Testing Checklist

```
STARTUP PERFORMANCE
- Cold startup <2 seconds
- Warm startup <1 second
- Baseline profile generated
- Startup path optimized
- Lazy initialization used

UI PERFORMANCE
- Scroll jank-free (60fps)
- Touch response <100ms
- Animations smooth (60fps)
- No dropped frames in critical paths
- Compose recomposition optimized

MEMORY PERFORMANCE
- No memory leaks detected
- Memory usage <100MB typical
- Heap size reasonable
- Large objects recycled

DATABASE PERFORMANCE
- Queries <100ms (simple)
- Indexes on frequently queried columns
- Batch inserts used
- Flow-based reactive queries

NETWORK PERFORMANCE
- API calls <1 second (p50)
- Connection pooling enabled
- Caching strategy implemented
```

## Decision Council Protocol - Testing Example

```markdown
## Decision: Testing Framework for New Feature Module

### Status Quo Advocate's Position:
"The codebase uses Mockito in 230 test files with JUnit 4.
Team has 3 years of Mockito expertise and established patterns.

Current test infrastructure:
- 230 test files using Mockito
- JUnit 4 throughout (15 modules)
- 75% average coverage
- Test suite executes in 45 seconds
- <2% flake rate

If we match existing pattern:
- Zero learning curve
- Consistent test code reviews
- No migration documentation needed
- Fast feature development"

### Best Practices Advocate's Position:
"Test doubles (real implementations) are superior to mocking for stability
and clarity. Turbine provides better Flow testing than manual collection.

Technical benefits of test doubles:
- No brittle verify() calls on implementation details
- Real behavior vs mock setup complexity
- Better refactoring safety (no verify() to update)
- Self-documenting (test double shows actual logic)
- Easier debugging (step into real code)

Turbine benefits:
- Declarative Flow assertions
- Better error messages
- Handles backpressure correctly
- Industry standard for Flow testing

Long-term value:
- More maintainable test suite
- Aligns with Google recommendations (2021+)
- Better coverage of edge cases
- This is greenfield - ideal opportunity"

### Pragmatic Synthesis:
Both perspectives valid. Constraint analysis:

Timeline: 4 weeks (moderate pressure)
Team: 5 developers, 1 senior familiar with test doubles
Risk: Low visibility feature (internal tool)
Current gaps: No Flow testing patterns established

Recommendation: Adopt test doubles + Turbine with guardrails
1. Feature is isolated (new module, no test dependencies)
2. Provides learning without disrupting existing tests
3. Low risk (internal feature)
4. Create test double examples for team reference

Incremental path:
- Phase 1: Use test doubles for this feature only
- Document patterns in core:testing module
- Schedule team demo (30 min)
- Monitor test stability and execution time
- Phase 2: Evaluate expansion to new features in Q3

Success criteria:
- Test suite executes in <10 seconds
- <1% flake rate
- Team comfort level increases
- Positive code review feedback
- Coverage >=80% for business logic

### Decision:
Use test doubles and Turbine for new feature module
Document in ADR-043: "Test Doubles for New Features"
Create test double guide with examples in core:testing
Schedule test doubles workshop (1 hour)
Q3 planning: Evaluate broader Mockito->test doubles migration
Rollback plan: Mockito still available if team struggles
```

### Testing Strategy Consultation Matrix

| Decision | Consult If |
|----------|-----------|
| Coverage targets | Unsure about 60% vs 80% vs 90% per layer |
| Test doubles vs mocks | Codebase uses mocks, considering test doubles |
| Framework migration | JUnit 4->5, Mockito->test doubles, adding Turbine |
| Integration test scope | Unclear where to draw boundary (unit vs integration) |
| UI test strategy | Balancing Compose UI tests vs screenshot tests |
| Performance testing | Adding macrobenchmark suite, need guidance |

**Example consultation:**
```
Status: "Current codebase has 45% ViewModel coverage using Mockito"
Question: "Should we target 80% with test doubles or 60% with existing mocks?"
Context: "New feature deadline in 2 weeks, team not familiar with test doubles"

Expected: android-architect applies Decision Council Protocol
- Status Quo: Mockito for speed, hit 60% quickly
- Best Practice: Test doubles for 80% quality coverage
- Pragmatic: Mockito for 60% now, document test double migration for Q3
```

---
agent: android-testing-specialist
feature: "{feature_slug}"
timestamp: "{run_timestamp}"
files_created: []
files_modified: []
dependencies_added: []
interfaces_exposed: []
---

# Test Report: [FEATURE NAME]

```yaml
Written by: [AGENT NAME]
Timestamp: [ISO 8601 - e.g., 2026-02-13T10:30:00Z]
```

## Pipeline Context

<!-- Copy verbatim from architecture-blueprint.md Pipeline Context section -->

**Original Prompt:** [Copy from blueprint]

**Business Purpose:** [Copy from blueprint]

## Summary

[Brief overview of testing work completed]

## Test Doubles Created

**Overall Coverage:**
- Unit Tests: [X% coverage]
- Integration Tests: [X tests]
- UI Tests: [X tests]
- Total Test Count: [X tests]

**Modules Tested:**
```
[List of modules with tests]
feature/[feature-name]/impl/src/test/
core/data/src/test/
core/database/src/androidTest/
```

## Test Doubles Created

**Repository Test Doubles:**
```kotlin
// Fake repository for testing
class Fake[Repository] : [Repository] {
    private val _data = MutableStateFlow<[DataType]>(/* initial state */)

    override val dataFlow: Flow<[DataType]> = _data.asStateFlow()

    override suspend fun performAction(action: [Action]) {
        // Controllable behavior for testing
    }

    // Test control methods
    fun emit(data: [DataType]) {
        _data.value = data
    }

    fun emitError(message: String) {
        // Error simulation
    }
}

// Location: [file path]
```

**Data Source Test Doubles:**
```kotlin
// Fake data source for testing
class Fake[DataSource] : [DataSource] {
    private val storage = mutableListOf<[Entity]>()

    override fun observeData(): Flow<List<[Entity]>> =
        flow { emit(storage.toList()) }

    override suspend fun save(entity: [Entity]) {
        storage.add(entity)
    }

    // Location: [file path]
}
```

**Additional Test Doubles:**
- [TestDouble1] - [Description] - `[file path]`
- [TestDouble2] - [Description] - `[file path]`

## Tests Implemented

**ViewModel Tests:**
```kotlin
@Test
fun `when repository emits data, ui state is success`() = runTest {
    // Given
    val repository = Fake[Repository]()
    val viewModel = [Feature]ViewModel(repository)

    // When
    repository.emit([testData])

    // Then
    val uiState = viewModel.uiState.value
    assertThat(uiState).isInstanceOf([Feature]UiState.Success::class.java)
    assertThat((uiState as Success).data).isEqualTo([testData])
}

@Test
fun `when action performed, repository receives action`() = runTest {
    // Given
    val repository = Fake[Repository]()
    val viewModel = [Feature]ViewModel(repository)

    // When
    viewModel.onAction([testAction])
    advanceUntilIdle()

    // Then
    assertThat(repository.receivedActions).contains([testAction])
}

// Location: [file path]
// Test count: [X tests]
```

**Repository Tests:**
```kotlin
@Test
fun `repository exposes flow from local data source`() = runTest {
    // Given
    val localDataSource = Fake[LocalDataSource]()
    val remoteDataSource = Fake[RemoteDataSource]()
    val repository = [Repository]Impl(localDataSource, remoteDataSource)

    // When
    localDataSource.emit([testData])

    // Then
    repository.dataFlow.test {
        assertThat(awaitItem()).isEqualTo([testData])
    }
}

@Test
fun `when action performed, writes to local then syncs remote`() = runTest {
    // Given
    val localDataSource = Fake[LocalDataSource]()
    val remoteDataSource = Fake[RemoteDataSource]()
    val repository = [Repository]Impl(localDataSource, remoteDataSource)

    // When
    repository.performAction([testAction])

    // Then
    assertThat(localDataSource.savedData).contains([expectedData])
    assertThat(remoteDataSource.syncedData).contains([expectedData])
}

// Location: [file path]
// Test count: [X tests]
```

**Flow Testing with Turbine:**
```kotlin
@Test
fun `data flow emits expected sequence`() = runTest {
    // Given
    val repository = Fake[Repository]()

    // When/Then
    repository.dataFlow.test {
        // Initial state
        assertThat(awaitItem()).isEqualTo([initialState])

        // After update
        repository.emit([updatedState])
        assertThat(awaitItem()).isEqualTo([updatedState])

        // No more emissions
        expectNoEvents()
    }
}

// Location: [file path]
```

## Integration Tests

**Database Tests:**
```kotlin
@Test
fun `dao saves and retrieves entity correctly`() = runTest {
    // Given
    val dao = database.[entity]Dao()
    val entity = [testEntity]

    // When
    dao.insert(entity)

    // Then
    dao.observeAll().test {
        val items = awaitItem()
        assertThat(items).contains(entity)
    }
}

// Location: [file path]
// Test count: [X tests]
```

**API Integration Tests:**
```kotlin
@Test
fun `api service returns expected response`() = runTest {
    // Given
    val mockWebServer = MockWebServer()
    mockWebServer.enqueue(MockResponse().setBody([jsonResponse]))
    val apiService = [createTestApiService](mockWebServer.url("/"))

    // When
    val response = apiService.getData()

    // Then
    assertThat(response.isSuccessful).isTrue()
    assertThat(response.body()).isEqualTo([expectedData])
}

// Location: [file path]
// Test count: [X tests]
```

## UI Tests

**Compose UI Tests:**
```kotlin
@Test
fun `displays loading state initially`() {
    composeTestRule.setContent {
        [Feature]Content(
            uiState = [Feature]UiState.Loading,
            onAction = {},
            onNavigateBack = {},
        )
    }

    composeTestRule
        .onNodeWithText("Loading")
        .assertIsDisplayed()
}

@Test
fun `displays data when state is success`() {
    composeTestRule.setContent {
        [Feature]Content(
            uiState = [Feature]UiState.Success([testData]),
            onAction = {},
            onNavigateBack = {},
        )
    }

    composeTestRule
        .onNodeWithText([expectedText])
        .assertIsDisplayed()
}

@Test
fun `click on item triggers action`() {
    val actions = mutableListOf<[Action]>()

    composeTestRule.setContent {
        [Feature]Content(
            uiState = [Feature]UiState.Success([testData]),
            onAction = { actions.add(it) },
            onNavigateBack = {},
        )
    }

    composeTestRule
        .onNodeWithText([itemText])
        .performClick()

    assertThat(actions).contains([expectedAction])
}

// Location: [file path]
// Test count: [X tests]
```

## Test Execution

**Running All Tests:**
```bash
# Unit tests
./gradlew :[module]:testDebugUnitTest

# Instrumented tests
./gradlew :[module]:connectedDebugAndroidTest

# All tests
./gradlew test connectedAndroidTest
```

**Test Results:**
```
[Module] Unit Tests: [X/X passed]
[Module] Integration Tests: [X/X passed]
[Module] UI Tests: [X/X passed]

Total: [X/X passed] (100%)
Duration: [X seconds]
```

## Coverage

**Coverage by Layer:**
```
ViewModels:     [X%] coverage
Repositories:   [X%] coverage
Data Sources:   [X%] coverage
DAOs:           [X%] coverage
UI Composables: [X%] coverage
```

**Untested Areas:**
- [List any untested code paths]
- [Rationale for not testing]
- [Plan to add coverage]

## Testing Strategy

**What Was Tested:**
1. **Business Logic** - All ViewModels and repositories have comprehensive tests
2. **Data Flow** - Flow emissions tested with Turbine
3. **State Management** - All UI states validated
4. **User Interactions** - UI tests cover critical user flows
5. **Edge Cases** - Error states, empty states, boundary conditions

**Testing Principles Applied:**
- ✅ Test doubles instead of mocking
- ✅ Fast unit tests (<5 seconds total)
- ✅ Isolated tests (no shared state)
- ✅ Tests use real implementations where possible
- ✅ Readable test names describing behavior

## Known Testing Gaps

**Current Limitations:**
- [List any testing gaps]
- [Tests not implemented and why]
- [Future testing improvements]

**Flaky Tests:**
- [List any flaky tests and status]
- [Steps taken to stabilize]

## Test Maintenance

**Test Doubles Location:**
```
core/testing/src/main/kotlin/
├── fake/
│   ├── Fake[Repository].kt
│   ├── Fake[DataSource].kt
│   └── [Additional test doubles]
```

**Test Utilities:**
```kotlin
// Shared test utilities created
object TestData {
    val sample[Entity] = [Entity](/* test data */)
}

fun create[TestDouble](
    initialState: [StateType] = [defaultState]
): [TestDouble] = [TestDouble](/* config */)

// Location: [file path]
```

## Next Steps

**For android-developer:**
1. [Review test failures if any]
2. [Address untested edge cases]
3. [Update implementation based on test feedback]

**For android-architect:**
1. [Validate test coverage meets standards]
2. [Review test architecture]
3. [Confirm testability requirements met]

**For compose-expert:**
1. [Review UI test coverage]
2. [Add additional interaction tests if needed]

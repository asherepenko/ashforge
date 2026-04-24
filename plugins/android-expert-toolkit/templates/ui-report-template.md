---
agent: compose-expert
feature: "{feature_slug}"
timestamp: "{run_timestamp}"
files_created: []
files_modified: []
dependencies_added: []
interfaces_exposed: []
---

# UI Implementation Report: [FEATURE NAME]

```yaml
Written by: [AGENT NAME]
Timestamp: [ISO 8601 - e.g., 2026-02-13T10:30:00Z]
```

## Pipeline Context

<!-- Copy verbatim from architecture-blueprint.md Pipeline Context section -->

**Original Prompt:** [Copy from blueprint]

**Business Purpose:** [Copy from blueprint]

**UX Intent:** [Copy from blueprint — this is your primary design brief]

## Summary

[Brief overview of UI implementation completed]

## Screens Implemented

**Feature Screens Implemented:**
- [Screen Name] - `[file path]`
- [Screen Name] - `[file path]`
- [Additional screens]

**Reusable Components Created:**
- [Component Name] - `[file path]`
- [Component Name] - `[file path]`

**Navigation Routes:**
```kotlin
// Navigation route definitions
@Serializable
data class [Feature]Route(val id: String)

// Location: [file path]
```

## Screen Implementations

**Main Screen:**
```kotlin
@Composable
fun [Feature]Screen(
    viewModel: [Feature]ViewModel = hiltViewModel(),
    onNavigateBack: () -> Unit,
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    [Feature]Content(
        uiState = uiState,
        onAction = viewModel::onAction,
        onNavigateBack = onNavigateBack,
    )
}

// Location: [file path]
```

**Content Composable:**
```kotlin
@Composable
private fun [Feature]Content(
    uiState: [Feature]UiState,
    onAction: ([Action]) -> Unit,
    onNavigateBack: () -> Unit,
) {
    when (uiState) {
        is [Feature]UiState.Loading -> LoadingState()
        is [Feature]UiState.Error -> ErrorState(message = uiState.message)
        is [Feature]UiState.Success -> SuccessState(
            data = uiState.data,
            onAction = onAction,
        )
    }
}

// Location: [file path]
```

## State Management

**UI State Handling:**
```kotlin
// State sealed interface from implementation-report.md
sealed interface [Feature]UiState {
    data object Loading : [Feature]UiState
    data class Error(val message: String) : [Feature]UiState
    data class Success(val data: [DataType]) : [Feature]UiState
}

// All states are handled in UI:
// ✅ Loading state displays progress indicator
// ✅ Error state displays error message
// ✅ Success state displays feature content
```

**User Actions:**
```kotlin
// User action sealed interface
sealed interface [Feature]Action {
    data class OnItemClick(val itemId: String) : [Feature]Action
    data object OnRefresh : [Feature]Action
    data class OnSearch(val query: String) : [Feature]Action
}

// Dispatched to ViewModel via: onAction(action)
```

## Components Created

**Custom Components Created:**
```kotlin
@Composable
fun [Component]Name(
    data: [DataType],
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    // Component implementation
}

// Location: [file path]
// Reusability: [Can be reused in other features? Yes/No]
```

**Material 3 Components Used:**
- `Scaffold` - App structure
- `TopAppBar` - Navigation bar
- `Button` / `IconButton` - Actions
- `LazyColumn` - Scrollable lists
- `Card` - Content containers
- [Additional Material components]

## Styling and Theming

**Theme Usage:**
```kotlin
// Using Material 3 theme tokens
MaterialTheme.colorScheme.primary
MaterialTheme.typography.titleLarge
MaterialTheme.shapes.medium
```

**Custom Styling:**
```kotlin
// Any custom modifiers or styles created
private val CustomPadding = 16.dp

@Composable
fun CustomStyledComponent() {
    // Custom styling implementation
}
```

## Navigation Integration

**Navigation Graph:**
```kotlin
fun NavGraphBuilder.[feature]Graph(
    onNavigateBack: () -> Unit,
    onNavigateToDetail: (String) -> Unit,
) {
    composable<[Feature]Route> { backStackEntry ->
        val route = backStackEntry.toRoute<[Feature]Route>()
        [Feature]Screen(
            onNavigateBack = onNavigateBack,
            onNavigateToDetail = onNavigateToDetail,
        )
    }
}

// Location: [file path]
```

**Deep Links:**
```kotlin
// Deep link configuration if applicable
deepLinks = listOf(
    navDeepLink<[Feature]Route>(
        basePath = "app://feature/[route]"
    )
)
```

## Accessibility

**Content Descriptions:**
```kotlin
// Accessibility semantics applied
Icon(
    imageVector = Icons.Default.[Icon],
    contentDescription = "[Meaningful description]",
)

Button(
    onClick = { /* ... */ },
    modifier = Modifier.semantics {
        contentDescription = "[Action description]"
    }
) {
    Text("[Button text]")
}
```

**Accessibility Checklist:**
- [ ] All icons have content descriptions
- [ ] Touch targets are at least 48dp
- [ ] Color is not the only indicator
- [ ] Text meets minimum contrast ratios
- [ ] Screen reader tested with TalkBack

## Performance Optimizations

**Compose Best Practices Applied:**
- [ ] `remember` used for expensive computations
- [ ] `derivedStateOf` for derived state
- [ ] `LaunchedEffect` for side effects
- [ ] Stable parameters and immutable data classes
- [ ] Lists use `key` parameter

**Performance Considerations:**
```kotlin
// Example optimization applied
@Composable
fun OptimizedList(items: List<Item>) {
    LazyColumn {
        items(
            items = items,
            key = { it.id }  // ✅ Stable key for recomposition
        ) { item ->
            ItemCard(item = item)
        }
    }
}
```

## Testing Support

**Preview Functions:**
```kotlin
@Preview(name = "Light Mode", showBackground = true)
@Preview(name = "Dark Mode", uiMode = Configuration.UI_MODE_NIGHT_YES)
@Composable
private fun [Feature]Preview() {
    AppTheme {
        [Feature]Content(
            uiState = [Feature]UiState.Success(/* mock data */),
            onAction = {},
            onNavigateBack = {},
        )
    }
}

// Location: [file path]
```

**UI Test Targets:**
```kotlin
// Composables ready for UI testing
@Composable
fun [Feature]Screen(
    viewModel: [Feature]ViewModel = hiltViewModel(),
    // ✅ All dependencies injectable for testing
) { /* ... */ }
```

## Known Issues and Limitations

**UI Limitations:**
- [List any UI limitations or edge cases]
- [Temporary UI workarounds]
- [Future UI enhancements]

**Browser/Device Compatibility:**
- Tested on: [API levels/devices tested]
- Known issues on: [Specific device/API issues]

## Next Steps

**For android-testing-specialist:**
1. [Review UI structure for test targets]
2. [Create Compose UI tests]
3. [Test user interaction flows]
4. [Validate accessibility with TalkBack]

**For android-developer:**
1. [Review ViewModel integration]
2. [Verify StateFlow collection patterns]
3. [Confirm error handling works]

**For android-architect:**
1. [Validate UI follows architecture blueprint]
2. [Verify separation of concerns]
3. [Confirm no business logic in UI layer]

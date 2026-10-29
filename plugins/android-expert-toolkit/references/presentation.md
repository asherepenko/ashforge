# Presentation Layer: ViewModel, State, Route/Screen

## When to use

Read when writing or reviewing a ViewModel, screen state, user actions, or the Route/Screen composable split. Error typing → `android-error-handling` skill. Composable components and previews → `compose-ui.md`. Testing → `android-testing` skill.

Match the project's existing style (`aet-check state`): sealed `UiState` (Loading/Error/Success) and single `data class State` + `Action` (MVI) are both fine; don't mix them in one feature.

## ViewModel

```kotlin
@HiltViewModel // or the project's DI
class ItemsViewModel @Inject constructor(
    private val repository: ItemsRepository,
) : ViewModel() {

    private val refreshError = MutableStateFlow<UiText?>(null)

    val uiState: StateFlow<ItemsUiState> =
        combine(repository.items, refreshError) { items, error ->
            if (error != null && items.isEmpty()) ItemsUiState.Error(error)
            else ItemsUiState.Success(items, transientError = error)
        }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), ItemsUiState.Loading)

    fun onAction(action: ItemsAction) {
        when (action) {
            ItemsAction.Retry, ItemsAction.Refresh -> refresh()
            ItemsAction.ErrorShown -> refreshError.value = null
        }
    }

    private fun refresh() = viewModelScope.launch {
        refreshError.value = null
        // refresh() returns the project's typed result; adapt to its Result/Either API.
        repository.refresh().onFailure { error -> refreshError.value = error.toUiText() }
    }
}
```

Rules:

- One public `StateFlow` of state; mutate private state with `.update { }`.
- User input arrives as one `onAction(Action)` (or a few named functions in non-MVI codebases) — never by exposing mutable state.
- **No `it.message ?: "Unknown error"` in state.** The data layer returns a typed error; the ViewModel maps it to a string resource reference (`UiText.StringResource(R.string.error_no_internet)`) that the UI resolves. Raw exception messages aren't localized, may leak internals, and break tests that compare state.
- `.catch { }` on a state flow is a last resort for programming errors; expected failures arrive as typed results.
- No `Context`, `Resources`, or Android views in the ViewModel.

## UI state

```kotlin
sealed interface ItemsUiState {
    data object Loading : ItemsUiState
    data class Error(val message: UiText) : ItemsUiState
    data class Success(val items: List<ItemUi>, val transientError: UiText? = null) : ItemsUiState
}

sealed interface ItemsAction {
    data object Refresh : ItemsAction
    data object Retry : ItemsAction
    data object ErrorShown : ItemsAction
}
```

- State is plain data: no `Throwable`, no lambdas, no `Flow`. **Retry is an action** (`ItemsAction.Retry`), not a `retry: () -> Unit` stored in an error state — a lambda in state breaks `equals`, can't be saved, and captures stale scope.
- Use UI models (`ItemUi`) with preformatted strings/dates when formatting is non-trivial.
- `UiText` is a small sealed type in the project (`StringResource(id, args)` / `DynamicString(value)`); reuse what exists.

## One-time events

Prefer state over events. Use an event channel only for effects the ViewModel alone decides (navigate after a successful save, show a snackbar for a failure):

```kotlin
private val _events = Channel<ItemsEvent>()
val events = _events.receiveAsFlow()
```

Collect with lifecycle awareness in the Root composable. Plain button-click navigation goes straight through composable callbacks, not through the ViewModel.

## Process death and SavedStateHandle

- **Form fields that must survive process death live in `SavedStateHandle`**, written on every change; state is initialized from it.

```kotlin
class EditItemViewModel(private val handle: SavedStateHandle, private val repo: ItemsRepository) : ViewModel() {
    private val _state = MutableStateFlow(
        EditItemState(title = handle[KEY_TITLE] ?: "", body = handle[KEY_BODY] ?: "")
    )
    val state = _state.asStateFlow()

    fun onAction(action: EditItemAction) = when (action) {
        is EditItemAction.TitleChanged -> {
            handle[KEY_TITLE] = action.title
            _state.update { it.copy(title = action.title) }
        }
        // …
    }
}
```

- Save only what the user would lose (typed text, selections), not data that reloads from the repository.
- Navigation arguments: `handle.toRoute<ItemDetailRoute>()` (Nav 2) or the Nav 3 key (`navigation-3` skill).
- Test restoration by constructing `SavedStateHandle(mapOf(...))` directly — see the `android-testing` skill.

## Route/Root and Screen

```kotlin
@Composable
fun ItemsRoot(onItemClick: (String) -> Unit, viewModel: ItemsViewModel = hiltViewModel()) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    ItemsScreen(state = state, onAction = viewModel::onAction, onItemClick = onItemClick)
}

@Composable
fun ItemsScreen(
    state: ItemsUiState,
    onAction: (ItemsAction) -> Unit,
    onItemClick: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    when (state) {
        ItemsUiState.Loading -> LoadingState(modifier)
        is ItemsUiState.Error -> ErrorState(
            message = state.message.asString(),
            onRetry = { onAction(ItemsAction.Retry) },
            modifier = modifier,
        )
        is ItemsUiState.Success -> ItemsList(state.items, onItemClick, modifier)
    }
}
```

- Root: obtains the ViewModel, collects state with `collectAsStateWithLifecycle()`, collects events, wires navigation callbacks. Not previewed.
- Screen: stateless, takes state + callbacks, fully previewable. Ship one preview per distinct state (Loading, Error, Success, empty, long content) — see `compose-ui.md`.

## Review checklist

- [ ] State has no `Throwable`, raw `message` string from an exception, lambda, or `Context`.
- [ ] Errors reach the UI as resource references.
- [ ] Retry, dismiss, and refresh are actions.
- [ ] Form input survives process death via `SavedStateHandle`.
- [ ] `collectAsStateWithLifecycle()` in the Root; Screen is preview-only-inputs.

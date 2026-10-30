# Presentation Layer: ViewModel, State, Route/Screen

## When to use

Read when writing or reviewing a ViewModel, screen state, user actions, or the Route/Screen composable split. Error typing → `android-error-handling` skill. Composable components and previews → `compose-ui.md`. Testing → `android-testing` skill.

Match the project's existing style (`android-conventions state`): sealed `UiState` (Loading/Error/Success) and single `data class State` + `Action` (MVI) are both fine; don't mix them in one feature.

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
- `UiText` is a small sealed type in the project (`StringResource(id, args)` / `DynamicString(value)`); reuse what exists. Make both cases `data class`es and hold `args` as a `List`, not an `Array`: an `Array` compares by identity, so equal states compare unequal, `StateFlow` re-emits, and state assertions fail.

## One-time events

ViewModel-originated "events" become state; the UI reacts and reports back with an action. A `Channel`/`SharedFlow` of events can lose an event when the ViewModel emits while no collector is active (rotation, background), so don't introduce one in new code; keep an existing one consistent rather than mixing both styles in a feature.

| Effect | Model as |
|--------|----------|
| Snackbar/toast after a failure | `userMessage: UiText?` in state + a `MessageShown` action that clears it (the `ErrorShown` pattern above) |
| Navigate after an async result (login, save) | a state flag (`isSaved = true`); the Root navigates from a `LaunchedEffect` |
| Navigate on a plain click | a composable callback; the ViewModel is not involved |

```kotlin
@Composable
fun EditItemRoot(onSaved: () -> Unit, viewModel: EditItemViewModel = hiltViewModel()) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val currentOnSaved by rememberUpdatedState(onSaved)
    LaunchedEffect(state.isSaved) { if (state.isSaved) currentOnSaved() }
    EditItemScreen(state, viewModel::onAction)
}
```

When the source screen stays on the back stack, reset the flag (or track "navigation pending" in the UI) so returning to it doesn't navigate again.

## Process death and SavedStateHandle

- **Text input** uses state-based fields: the ViewModel holds a `TextFieldState` per field and saves it through `SavedStateHandle`, so typed text survives process death. Read `titleState.text` when validating or submitting. Value-based `value`/`onValueChange` fields are deprecated (`compose-ui.md`).

```kotlin
class EditItemViewModel(handle: SavedStateHandle, private val repo: ItemsRepository) : ViewModel() {
    @OptIn(SavedStateHandleSaveableApi::class) // lifecycle-viewmodel-compose; opt-in as of Lifecycle 2.11
    val titleState: TextFieldState by handle.saveable(saver = TextFieldState.Saver) { TextFieldState() }
    // Screen: TextField(state = viewModel.titleState)
}
```

- **Other form fields that must survive process death** (selections, toggles, steps) live in `SavedStateHandle`, written on every change; state is initialized from it.

```kotlin
class EditItemViewModel(private val handle: SavedStateHandle, private val repo: ItemsRepository) : ViewModel() {
    private val _state = MutableStateFlow(
        EditItemState(category = handle[KEY_CATEGORY] ?: Category.DEFAULT)
    )
    val state = _state.asStateFlow()

    fun onAction(action: EditItemAction) = when (action) {
        is EditItemAction.CategorySelected -> {
            handle[KEY_CATEGORY] = action.category
            _state.update { it.copy(category = action.category) }
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

- Root: obtains the ViewModel, collects state with `collectAsStateWithLifecycle()`, turns state flags into navigation callbacks, wires navigation. Not previewed.
- Screen: stateless, takes state + callbacks, fully previewable. Ship one preview per distinct state (Loading, Error, Success, empty, long content) — see `compose-ui.md`.

## Review checklist

- [ ] State has no `Throwable`, raw `message` string from an exception, lambda, or `Context`.
- [ ] Errors reach the UI as resource references.
- [ ] Retry, dismiss, and refresh are actions.
- [ ] ViewModel-originated effects (messages, navigate-after-save) are state plus an action, not a new event channel.
- [ ] Text input is `TextFieldState`; form input survives process death via `SavedStateHandle`.
- [ ] `collectAsStateWithLifecycle()` in the Root; Screen is preview-only-inputs.

# Compose UI

## When to use

Read when building or reviewing composables below the Root/Screen level, theming, lists, or previews. Screen structure → `presentation.md`. Accessibility → `accessibility.md`. Hand off to official skills for:

| Topic | Skill |
|-------|-------|
| Window sizes, nav bar vs rail, list-detail, foldables, keyboard/mouse | `adaptive` |
| Insets, system bars, IME padding | `edge-to-edge` |
| Recomposition, stability, lazy-list jank, `remember` keys | `jetpack-compose-performance` |
| Effect API catalogue (`SideEffect`, `snapshotFlow`, `produceState`), `Modifier.Node` internals, animation phase deferral | `jetpack-compose-performance` (its effects, custom-modifier and animation references) |
| Porting an XML layout to Compose | `migrate-xml-views-to-jetpack-compose` |
| Screenshot test setup | `testing-setup` |

## Component rules

- Take only the parameters you render, not the whole screen state. `modifier: Modifier = Modifier` is the first optional parameter and is applied to the root element only.
- Callbacks describe what happened (`onDeleteClick`), not what the caller should do.
- Strings come from resources (`stringResource`); no hardcoded user-visible text.
- Colors, type and shapes from `MaterialTheme`; no literal `Color(0xFF…)` in feature code. Wrap Material 3 components in design-system components when the project has a design system — reuse those first.
- Size with constraints (`fillMaxWidth`, `weight`, `widthIn(max = …)`), not fixed dp for containers, so components fit any pane.
- Slot parameters (`content: @Composable () -> Unit`) instead of boolean flags that switch layouts.
- Animations that change every frame read state in `graphicsLayer { }` / lambda modifiers, not in composition (`jetpack-compose-performance`).

## State placement

Hoist state to the lowest common ancestor of everything that reads or writes it — no higher.

| State | Lives in |
|-------|----------|
| UI element state only this composable uses (expanded, animation, focus) | the composable (`remember`/`rememberSaveable`) |
| UI element state shared by several composables or with non-trivial UI logic | a plain state holder class (`LazyListState`-style), remembered |
| Anything business logic reads or changes, or that must reach the data layer | the ViewModel |

Don't push a purely visual `isExpanded` into the ViewModel just to make the component "stateless"; do hoist it when a parent, a test, or a sibling needs it. UI state that must survive recreation: `rememberSaveable` in UI, `SavedStateHandle` in the ViewModel (`presentation.md`).

## Side effects

- Every value an effect block reads goes in its keys, or is wrapped in `rememberUpdatedState` when a change must not restart it. Missing keys run stale work; extra keys restart it needlessly.
- `LaunchedEffect(Unit)`/`LaunchedEffect(true)` means "once per entry into composition"; treat it as suspicious and check it really should not restart.
- Long-running effect that calls a callback parameter (timeouts, tickers, flow collection): `val currentOnDone by rememberUpdatedState(onDone)`.
- Registration that needs teardown (listeners, observers, callbacks): `DisposableEffect(key) { …; onDispose { … } }`.
- Work started from a click or gesture: `rememberCoroutineScope()`, not a `LaunchedEffect` toggled by a flag.
- Business work (loading, saving) belongs in the ViewModel behind an action, not in an effect.

```kotlin
@Composable
fun SessionTimeout(timeoutMs: Long, onTimeout: () -> Unit) {
    val currentOnTimeout by rememberUpdatedState(onTimeout)
    LaunchedEffect(timeoutMs) {          // restart only when the duration changes
        delay(timeoutMs)
        currentOnTimeout()               // always the latest callback
    }
}
```

## Text input

Value-based text fields (`value` + `onValueChange`) are deprecated. New code uses the state-based `TextField(state = …)` / `BasicTextField(state = …)` with `TextFieldState`; filtering goes in an `InputTransformation`, formatting in an `OutputTransformation`, and passwords use `SecureTextField`.

- Local-only input (search box, dialog field): `rememberTextFieldState()` — saved across recreation for you.
- Input the ViewModel validates or submits: hold `TextFieldState` in the ViewModel and pass it to the field. It is a snapshot-state holder with no UI dependency, so this is allowed. Save it with the `SavedStateHandle.saveable` delegate and `TextFieldState.Saver` (see `presentation.md`).
- Can't restructure a `StateFlow` UI state yet: keep `rememberTextFieldState(initial)` in the composable and forward changes with `snapshotFlow { state.text.toString() }.collectLatest(onChange)` inside a `LaunchedEffect(state)`.
- Don't write a new `value`/`onValueChange` field that round-trips every keystroke through a `StateFlow`; async updates can desync the cursor and drop input.

## Custom modifiers

In order of preference: chain existing modifiers in a plain `fun Modifier.x() = this.then(…)`; a `@Composable` modifier factory only when it needs composition APIs (it is never skipped and resolves `CompositionLocal`s at the call site); `Modifier.Node` + `ModifierNodeElement` (a data class, for correct `equals`) for custom drawing, layout, input, or animation. Never `composed { }` — it is no longer recommended. Always build on `this`, or earlier modifiers in the chain are dropped.

## Previews: one per distinct state

Every component and every Screen ships a `@Preview` for **each state it can render differently**. Use separate preview functions — not `PreviewParameter` — so each state is visible on its own.

Enumerate states mechanically:

| Input | Previews |
|-------|----------|
| Each `Boolean`/enum that changes the look | each value (and meaningful combinations) |
| Content | empty, one item, many items; loading, error, success |
| Text | short and long (wrapping/truncation); RTL if the layout is directional |
| Size | `widthDp = 320` and `widthDp = 840` when the layout reflows; `fontScale = 2f` when large text could break it |
| Theme | light and dark (`uiMode = UI_MODE_NIGHT_YES`) |

```kotlin
@Preview(name = "Default")
@Preview(name = "Dark", uiMode = Configuration.UI_MODE_NIGHT_YES)
@Composable
private fun ItemCardPreview() = AppTheme { ItemCard(title = "Meeting notes", date = "Mar 15", isExpanded = false, onClick = {}) }

@Preview(name = "Expanded")
@Composable
private fun ItemCardExpandedPreview() = AppTheme { ItemCard(title = "Meeting notes", date = "Mar 15", isExpanded = true, onClick = {}) }

@Preview(name = "Long title", widthDp = 320)
@Composable
private fun ItemCardLongTitlePreview() = AppTheme {
    ItemCard(title = "Quarterly planning sync with the whole product and design org", date = "Mar 15", isExpanded = false, onClick = {})
}
```

Wrap previews in the app theme with realistic data. Previews double as screenshot-test inputs when the project uses Compose Preview Screenshot Testing (`testing-setup`). Render them from the CLI with `android` (`android-cli` skill, if installed).

## Lists

```kotlin
LazyColumn(contentPadding = PaddingValues(vertical = 8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
    items(items, key = { it.id }, contentType = { "item" }) { item ->
        ItemRow(item, onClick = { onItemClick(item.id) }, modifier = Modifier.animateItem())
    }
}
```

Stable `key` for every list whose items can move, insert, or delete. Paging → `data-layer.md`.

## Common Material 3 patterns

```kotlin
// Pull to refresh (Material 3 PullToRefreshBox)
PullToRefreshBox(isRefreshing = state.isRefreshing, onRefresh = { onAction(ItemsAction.Refresh) }) {
    ItemsList(state.items, onItemClick)
}

// Bottom sheet: the caller owns visibility; dismissal is a callback
if (showSheet) {
    ModalBottomSheet(onDismissRequest = onDismiss, sheetState = rememberModalBottomSheetState()) { SheetContent() }
}

// Size and visibility animation
Card(onClick = onToggle, modifier = Modifier.fillMaxWidth().animateContentSize()) { /* … */ }
AnimatedVisibility(visible, enter = fadeIn() + expandVertically(), exit = fadeOut() + shrinkVertically()) { /* … */ }
```

### Which animation API

| Animating | Use |
|-----------|-----|
| Content appearing/disappearing | `AnimatedVisibility` |
| Swapping between different content | `AnimatedContent` / `Crossfade`; destinations → the navigation library's transitions |
| Size change of one composable | `Modifier.animateContentSize()` |
| List item insert/move/remove | `Modifier.animateItem()` |
| One value with a known target | `animate*AsState`, read in `graphicsLayer { }` / `offset { }` |
| Several values that start together | `updateTransition` |
| Gesture-driven or sequenced values | `Animatable` (`animateTo`/`snapTo`) |
| Repeating forever | `rememberInfiniteTransition` |
| Vector icon micro-animation | `AnimatedVectorDrawable` |

Verify component APIs against the project's Compose BOM (`android docs search "<component> compose"`); Material 3 APIs change between releases.

## Theme

```kotlin
@Composable
fun AppTheme(darkTheme: Boolean = isSystemInDarkTheme(), dynamicColor: Boolean = true, content: @Composable () -> Unit) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }
        darkTheme -> DarkColors
        else -> LightColors
    }
    MaterialTheme(colorScheme = colorScheme, typography = AppTypography, shapes = AppShapes, content = content)
}
```

## Adaptive layouts

Don't hand-roll `when (windowSizeClass)` branches that swap a `NavigationBar` for a `NavigationRail`. Use the library components the `adaptive` skill describes:

- Top-level navigation chrome: `NavigationSuiteScaffold` (Material 3 adaptive) — it picks bar, rail, or drawer from the window size.
- List-detail and supporting panes: Navigation 3 scene strategies (`navigation-3` + `adaptive` skills), or `ListDetailPaneScaffold` in Nav 2 projects.
- Size queries inside components: the Compose MediaQuery API covered by the `adaptive` skill.

## Views interop

- Compose inside Views: `ComposeView` with `setViewCompositionStrategy(ViewCompositionStrategy.DisposeOnViewTreeLifecycleDestroyed)` in Fragments.
- Views inside Compose: `AndroidView(factory = { … }, update = { … })`; keep `factory` free of state reads, push state in `update`.
- Full screen migrations → `migrate-xml-views-to-jetpack-compose`.

## Review checklist

- [ ] Preview per distinct state, light and dark.
- [ ] No hardcoded strings, colors, or fixed container sizes.
- [ ] `key` on lazy items.
- [ ] Effect keys cover every value the block reads (or `rememberUpdatedState`); no `composed { }` modifiers.
- [ ] Text fields are state-based (`TextFieldState`), not new `value`/`onValueChange` code.
- [ ] Adaptive chrome via `NavigationSuiteScaffold`/scenes, not hand-rolled rails.
- [ ] Accessibility pass (`accessibility.md`).

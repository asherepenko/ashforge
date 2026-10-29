# Compose UI

## When to use

Read when building or reviewing composables below the Root/Screen level, theming, lists, or previews. Screen structure → `presentation.md`. Accessibility → `accessibility.md`. Hand off to official skills for:

| Topic | Skill |
|-------|-------|
| Window sizes, nav bar vs rail, list-detail, foldables, keyboard/mouse | `adaptive` |
| Insets, system bars, IME padding | `edge-to-edge` |
| Recomposition, stability, lazy-list jank, `remember` keys | `jetpack-compose-performance` |
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
- [ ] Adaptive chrome via `NavigationSuiteScaffold`/scenes, not hand-rolled rails.
- [ ] Accessibility pass (`accessibility.md`).

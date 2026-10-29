# Compose Accessibility

## When to use

Read when building or reviewing UI for TalkBack, Switch Access, keyboard, or large-font support. Run `android-conventions accessibility` to see the project's current coverage.

## Rules

- **Don't override what Material already says.** A `Button { Text("Save") }` is announced correctly; adding `contentDescription` to it replaces the visible label and usually makes things worse.
- **Icons and images:** `contentDescription = null` for decorative ones; a localized description (`stringResource`) for informative ones and for every icon-only button.
- **Grouping:** a clickable card reads as one element — put `Modifier.clickable` (or `Card(onClick)`) on the container, or `Modifier.semantics(mergeDescendants = true) {}` for non-clickable groups.
- **Click labels:** `Modifier.clickable(onClickLabel = stringResource(R.string.open_item)) { … }` so TalkBack says "Double-tap to open item".
- **Toggles:** `Modifier.toggleable(value, role = Role.Switch, onValueChange = …)` on the whole row, not just the `Switch`.
- **State:** `stateDescription` only for custom controls whose state isn't conveyed by a standard role.
- **Headings:** `Modifier.semantics { heading() }` on section titles so users can jump between them.
- **Live updates:** `liveRegion = LiveRegionMode.Polite` for status text that changes without focus (errors, counters). Use sparingly.
- **Custom actions:** swipe-to-delete and long-press menus need an accessible path — `customActions = listOf(CustomAccessibilityAction(label) { …; true })`.
- **Touch targets:** at least 48×48dp. Material components enforce this via `minimumInteractiveComponentSize()`; custom clickables need it too.
- **Text scaling:** never fixed heights on text containers; check at `fontScale = 2f` (`compose-ui.md` previews).
- **Color:** contrast ≥ 4.5:1 for body text, ≥ 3:1 for large text and UI components; never color as the only signal (add an icon or text).
- **Forms:** `OutlinedTextField(label = …, supportingText = …, isError = …)`; error text in `supportingText` so it's announced with the field.
- **Dialogs and sheets:** Material dialogs move focus correctly; custom overlays must too (`paneTitle`).
- **Lists:** `collectionInfo`/`collectionItemInfo` come free with `LazyColumn`; don't break them by flattening into a `Column` with many children.
- **Keyboard/focus:** focus order follows layout order; fix with `Modifier.focusProperties` only when layout order is wrong. Keyboard shortcuts and pointer support → `adaptive` skill.

## Example

```kotlin
@Composable
fun ItemRow(item: ItemUi, onOpen: () -> Unit, onDelete: () -> Unit, modifier: Modifier = Modifier) {
    val deleteLabel = stringResource(R.string.delete_item, item.title)
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClickLabel = stringResource(R.string.open_item), onClick = onOpen)
            .semantics { customActions = listOf(CustomAccessibilityAction(deleteLabel) { onDelete(); true }) }
            .padding(16.dp),
    ) {
        AsyncImage(model = item.imageUrl, contentDescription = null) // decorative: title follows
        Column(Modifier.weight(1f)) {
            Text(item.title, style = MaterialTheme.typography.titleMedium)
            Text(item.subtitle, style = MaterialTheme.typography.bodyMedium)
        }
        IconButton(onClick = onDelete) {
            Icon(Icons.Default.Delete, contentDescription = deleteLabel)
        }
    }
}
```

## Testing

- Compose tests find nodes the way TalkBack does: `onNodeWithContentDescription`, `onNodeWithText`, `assertHasClickAction()`, `assert(hasStateDescription(...))`.
- Instrumented Compose tests can run automated checks: add `ui-test-junit4-accessibility`, call `composeTestRule.enableAccessibilityChecks()`, then any action (or `onRoot().tryPerformAccessibilityChecks()`) validates the tree (developer.android.com, *Compose accessibility → Testing*).
- Manual pass: TalkBack swipe-through, Switch Access, 200% font, dark theme.

## Checklist

- [ ] Every icon-only control has a localized description; decorative images have `null`.
- [ ] Clickable groups read as one element with a click label.
- [ ] Touch targets ≥ 48dp.
- [ ] Section titles marked as headings.
- [ ] Errors announced (supporting text or polite live region).
- [ ] Gestures have an accessible alternative.
- [ ] Layout survives 200% font scale.

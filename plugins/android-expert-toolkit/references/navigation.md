# Navigation

## When to use

Read when adding a destination or deep link to a project on **Navigation 2** (Navigation Compose, `NavHost` + `NavController`). Check which one the project uses first:

| Project has | Load |
|-------------|------|
| `androidx.navigation:navigation-compose`, `NavHost`, `composable<T>` | this file (Navigation 2, type-safe routes, 2.8+) |
| `androidx.navigation3`, `NavDisplay`, `NavBackStack`, `entryProvider` | `navigation-3` skill |
| Migrating Nav 2 → Nav 3, or multi-pane scenes | `navigation-3` skill (its migration guide), plus `adaptive` for scenes |
| Predictive back, back-gesture interception | `navigation-event` skill |

Don't introduce Navigation 3 into a Nav 2 project as a side effect of a feature; it's a migration.

## Navigation 2 type-safe routes

Routes are `@Serializable` types in the feature's `api` module.

```kotlin
// feature/items/api
@Serializable data object ItemsRoute
@Serializable data class ItemDetailRoute(val itemId: String)
```

Each feature exposes a `NavGraphBuilder` extension from `impl`; navigation targets arrive as callbacks so features never import each other's `impl`.

```kotlin
// feature/items/impl
fun NavGraphBuilder.itemsGraph(
    onItemClick: (String) -> Unit,
    onBack: () -> Unit,
) {
    composable<ItemsRoute> { ItemsRoot(onItemClick = onItemClick) }
    composable<ItemDetailRoute>(
        deepLinks = listOf(navDeepLink<ItemDetailRoute>(basePath = "https://www.example.com/items")),
    ) { ItemDetailRoot(onBack = onBack) }
}

// app
NavHost(navController, startDestination = ItemsRoute) {
    itemsGraph(
        onItemClick = { id -> navController.navigate(ItemDetailRoute(id)) },
        onBack = navController::popBackStack,
    )
    profileGraph(/* … */)
}
```

- Read route arguments in the ViewModel with `savedStateHandle.toRoute<ItemDetailRoute>()`, not in the composable.
- Pass IDs, never whole objects; load the object from the repository.
- Nested graphs: `navigation<SettingsGraph>(startDestination = SettingsMain) { … }`.
- Plain click navigation goes through composable callbacks, not ViewModel events (see `presentation.md`).
- Single-top for bottom-level destinations: `navigate(route) { popUpTo(graph.findStartDestination().id) { saveState = true }; launchSingleTop = true; restoreState = true }`.

Adaptive navigation chrome (bar vs rail) is `NavigationSuiteScaffold` — see `compose-ui.md` and the `adaptive` skill.

## Deep links and App Links

```xml
<activity android:name=".MainActivity" android:exported="true">
    <intent-filter android:autoVerify="true">
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data android:scheme="https" android:host="www.example.com" android:pathPrefix="/items" />
    </intent-filter>
</activity>
```

- App Links need `/.well-known/assetlinks.json` on the host with the release signing SHA-256 (Play App Signing key when Play signs the app).
- Custom schemes (`myapp://`) aren't verified; any app can claim them. Never put auth tokens in a deep link.
- Validate every deep-link argument as untrusted input — exported entry points are covered by `android-intent-security`.
- `NavController` handles deep-link intents passed to `setContent`'s activity; with `launchMode="singleTop"`, forward `onNewIntent` to `navController.handleDeepLink(intent)`.
- Test with `adb shell am start -W -a android.intent.action.VIEW -d "https://www.example.com/items/42"`.

## Testing

- Use `TestNavHostController` + `ComposeNavigator` to assert `currentBackStackEntry?.destination?.hasRoute<ItemDetailRoute>()`.
- ViewModel route arguments: build `SavedStateHandle` from the route in tests (`testing-patterns.md`).

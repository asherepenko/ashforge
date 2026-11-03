# Navigation

## When to use

Read when choosing how screens connect, restoring navigation state, or handling links into the app. TCA navigation (`StackState`, `@Presents`) is in [tca](tca.md).

## In-app navigation

- Use `NavigationStack` with a path (`NavigationPath`, or a typed array of route values) owned by a state holder, so code can push, pop, and restore. `NavigationView` is deprecated.
- Register destinations with `.navigationDestination(for:)` on the stack content, one per route type.
- Route values are small `Hashable` value types holding identifiers, not models.
- Present sheets and alerts from optional or enum state (`.sheet(item:)`), not a boolean per sheet.
- Use `NavigationSplitView` for sidebar and list-detail layouts that must adapt to window size (`app-resizability`).

## Deep links and universal links

Custom URL schemes (`myapp://`) work for app-to-app links. Universal links are `https` URLs that open the app, and fall back to the website when the app is missing.

1. **Associate the domain.** Add the Associated Domains entitlement with `applinks:example.com`. Serve `/.well-known/apple-app-site-association` over HTTPS without redirects, as JSON with no file extension, listing the app ID (`TEAMID.bundle.id`) and the paths it handles.
2. **Receive the link.** In SwiftUI, attach `.onOpenURL { url in ... }` for custom schemes and universal links, and `.onContinueUserActivity(NSUserActivityTypeBrowsingWeb) { activity in ... }` when you need the `NSUserActivity`. In a UIKit app, handle `scene(_:continue:)` and `scene(_:openURLContexts:)`.
3. **Parse to a route.** One function turns a `URL` into a route value (or `nil`). Unit-test it with a table of URLs, including malformed and unknown ones.
4. **Apply the route to the path** from the state holder. If the user is signed out or the data isn't loaded yet, store the pending route and apply it after.
5. **Verify on a device or simulator**: `xcrun simctl openurl booted "https://example.com/item/42"`.

Treat every incoming URL as untrusted input: validate identifiers, never act on a destructive path without confirmation ([security](security.md)).

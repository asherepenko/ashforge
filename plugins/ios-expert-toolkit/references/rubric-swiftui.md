# SwiftUI Quality Rubric

Grading criteria for SwiftUI implementations. Use both as **generation targets** (what to aim for when building) and **evaluation criteria** (what to check when reviewing). Each criterion describes what strong and weak work looks like.

## When to use

Read this reference when building SwiftUI screens (to aim at the "Strong" column) or when reviewing SwiftUI code (to grade against the rubric). Used by swiftui-expert and by any UI reviewer. Rules for state wrappers and view structure live in [swiftui](swiftui.md); this page grades against them.

## 1. Design Cohesion

**Strong**: Colors are semantic (`.primary`, `.secondary`, `Color(.systemBackground)`, asset-catalog colors with light and dark variants). Text uses text styles (`.font(.body)`, `.headline`), so Dynamic Type scales it. Spacing and corner radii come from a small shared set, not per-view numbers. Standard controls and system materials are used where they fit. Dark mode and increased contrast work with no per-view overrides.

**Weak**: Hardcoded `Color(red:green:blue:)` or hex values next to semantic colors. Fixed `.font(.system(size: 17))` that ignores Dynamic Type. Padding values picked per view. Custom controls that copy a system control badly. Dark mode shows black text on a dark background because a color was hardcoded.

## 2. State Completeness

**Strong**: Every screen handles loading, error, empty, and success, plus refreshing where the screen supports pull-to-refresh. Each state has its own `#Preview` on the pure content view ([swiftui](swiftui.md)). Loading shows placeholder content (`.redacted(reason: .placeholder)`) or a labelled `ProgressView`. Error shows a readable message and a retry action. Empty uses `ContentUnavailableView` (iOS 17) or an equivalent with a next step. Success is previewed with one item and with many. State changes animate where it helps.

**Weak**: Only the success path has a preview. Loading is a bare spinner. An error looks the same as an empty list. Empty state is a blank screen. A `CancellationError` from leaving the screen shows as an error alert.

## 3. Accessibility

**Strong**: Follows [accessibility](accessibility.md). Icon-only buttons have `accessibilityLabel`. Decorative images are hidden from VoiceOver. Related elements are combined (`.accessibilityElement(children: .combine)`) into one logical unit. Custom controls expose traits, values, and actions. Tap targets are at least 44x44 points. Layout reflows at accessibility text sizes (`ViewThatFits`, a vertical stack at large sizes) instead of truncating. Animations respect Reduce Motion. Information is never carried by color alone.

**Weak**: Icon buttons read as "button" or as the SF Symbol name. Labels repeat visible text. Tap targets under 44 points. Text clips or overlaps at the largest Dynamic Type size. Custom controls are invisible to VoiceOver. Motion plays with Reduce Motion on.

## 4. Performance

**Strong**: Follows the `swiftui-pro` skill and [performance](performance.md). `body` does no sorting, filtering, or formatting. `ForEach` uses stable identity. Views read only the state they need, so a change redraws a small part of the tree. Hitch and slow-view claims are backed by a trace from the `xctrace` skill on a release build.

**Weak**: Expensive work in `body` on every update. `ForEach` over indices or with an `id` that changes. One large observed object read by every view, so any change redraws the screen. `AnyView` used to silence type errors. "Fixed" jank with no trace before or after.

## 5. Adaptive Layout

**Strong**: Layout works in compact and regular size classes, in portrait and landscape, and in resizable windows on iPad (see the `app-resizability` skill). Split views use `NavigationSplitView` where the content fits it. Content reflows rather than stretching. Selection and scroll position survive size changes. Keyboard and pointer input work on iPad.

**Weak**: An iPhone layout stretched across an iPad. Fixed frame widths. Hand-written size checks that duplicate screen code. Selection lost when the window resizes or the device rotates.

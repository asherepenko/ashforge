# Compose UI Quality Rubric

Grading criteria for Jetpack Compose implementations. Use both as **generation targets** (what to aim for when building) and **evaluation criteria** (what to check when reviewing). Each criterion describes what strong and weak work looks like.

## When to use

Read this reference when building Compose UI (to aim at the "Strong" column) or when reviewing Compose implementations (to grade against the rubric). Used by compose-expert and by any UI reviewer.

## 1. Design Cohesion

**Strong**: The UI feels like a coherent whole. All colors come from MaterialTheme.colorScheme, typography from MaterialTheme.typography, spacing from a consistent scale. Components use Material 3 tokens — no hardcoded dp/color values. Visual hierarchy is clear: primary actions are prominent, secondary content recedes. Dark mode works without manual overrides.

**Weak**: Hardcoded colors (`Color(0xFF...)`) mixed with theme colors. Typography sizes picked ad-hoc. Spacing inconsistent between similar components. Material 2 components mixed with Material 3. Dark mode is broken or has contrast issues because colors were hardcoded.

## 2. State Completeness

**Strong**: Every screen handles all state variations, each with its own `@Preview` (`compose-ui.md`) — Loading (skeleton or indicator), Error (resource-based message + retry action), Empty (actionable messaging, not just "No data"), Success (with 1 item and many items), Refreshing (pull-to-refresh indicator). Each state has a distinct, intentional visual representation. Transitions between states are smooth (AnimatedVisibility, crossfade).

**Weak**: Loading is a centered spinner with no context. Error shows a toast and otherwise looks like empty success. Empty state is a blank screen. Only the happy path (Success with data) received design attention. State transitions are jarring — content pops in without animation.

## 3. Accessibility

**Strong**: contentDescription on all icons and images. Touch targets minimum 48dp. Color contrast meets WCAG AA (4.5:1 for text, 3:1 for large text). Semantic grouping via mergeDescendants for logical units. Form fields have associated labels. Custom components expose semantics (role, stateDescription). Screen reader navigation order is logical.

**Weak**: Icons have no contentDescription (or worse, contentDescription repeats the visible text). Tap targets smaller than 48dp. Information conveyed only through color. Interactive elements not discoverable by TalkBack. Custom components are opaque to accessibility services.

## 4. Performance

**Strong**: Follows the `jetpack-compose-performance` skill: LazyLists use stable keys and contentType; frequently changing state is read in layout/draw lambdas (`graphicsLayer`, `offset { }`) rather than in composition; `remember` only for heavy allocations, with all inputs as keys; no backwards writes. Relies on strong skipping instead of blanket `@Stable`/`ImmutableList`. Jank claims are backed by frame timing from a release build.

**Weak**: LazyList items keyed by index. Expensive filtering/sorting runs in composition on every pass. Animated values read in composition. `@Immutable`/`ImmutableList` added everywhere to "fix" recomposition counts without a measured problem. Forgotten listeners leak.

## 5. Adaptive Layout

**Strong**: Follows the `adaptive` skill. Top-level navigation uses `NavigationSuiteScaffold`, so bar/rail/drawer follows the window size without hand-written branches. Multi-pane layouts use Navigation 3 scene strategies (or `ListDetailPaneScaffold` in Nav 2 projects). Content reflows rather than stretching; state survives fold/unfold, rotation, and window resizing. Keyboard and pointer input work on large screens.

**Weak**: Phone layout stretched to tablet. Hand-rolled `when (windowSizeClass)` branches that swap a `NavigationBar` for a `NavigationRail` and duplicate screen code. Landscape shows the same single column with empty space. Selection or scroll position lost on fold/unfold.

# Compose UI Quality Rubric

Grading criteria for Jetpack Compose implementations. Use both as **generation targets** (what to aim for when building) and **evaluation criteria** (what to check when reviewing). Each criterion describes what strong and weak work looks like.

## When to use

Read this reference when building Compose UI (to aim at the "Strong" column) or when reviewing Compose implementations (to grade against the rubric). Used by compose-expert for generation and by any UI reviewer for evaluation.

## 1. Design Cohesion

**Strong**: The UI feels like a coherent whole. All colors come from MaterialTheme.colorScheme, typography from MaterialTheme.typography, spacing from a consistent scale. Components use Material 3 tokens — no hardcoded dp/color values. Visual hierarchy is clear: primary actions are prominent, secondary content recedes. Dark mode works without manual overrides.

**Weak**: Hardcoded colors (`Color(0xFF...)`) mixed with theme colors. Typography sizes picked ad-hoc. Spacing inconsistent between similar components. Material 2 components mixed with Material 3. Dark mode is broken or has contrast issues because colors were hardcoded.

## 2. State Completeness

**Strong**: Every screen handles all state variations — Loading (skeleton or indicator), Error (message + retry action), Empty (actionable messaging, not just "No data"), Success (with 1 item and many items), Refreshing (pull-to-refresh indicator). Each state has a distinct, intentional visual representation. Transitions between states are smooth (AnimatedVisibility, crossfade).

**Weak**: Loading is a centered spinner with no context. Error shows a toast and otherwise looks like empty success. Empty state is a blank screen. Only the happy path (Success with data) received design attention. State transitions are jarring — content pops in without animation.

## 3. Accessibility

**Strong**: contentDescription on all icons and images. Touch targets minimum 48dp. Color contrast meets WCAG AA (4.5:1 for text, 3:1 for large text). Semantic grouping via mergeDescendants for logical units. Form fields have associated labels. Custom components expose semantics (role, stateDescription). Screen reader navigation order is logical.

**Weak**: Icons have no contentDescription (or worse, contentDescription repeats the visible text). Tap targets smaller than 48dp. Information conveyed only through color. Interactive elements not discoverable by TalkBack. Custom components are opaque to accessibility services.

## 4. Performance

**Strong**: LazyLists use stable keys and contentType. remember for expensive calculations. derivedStateOf for computed state. No lambdas capturing changing values in composable parameters. Images loaded with Coil and memory caching. DisposableEffect cleans up resources. Nesting depth is shallow. Recomposition scope is narrow — changing one field doesn't recompose the entire screen.

**Weak**: LazyList items keyed by index (breaks animations, causes recomposition). Expensive filtering/sorting runs on every recomposition. Large composables where a single state change triggers full recomposition. Images loaded without caching. Forgotten subscriptions or listeners leak.

## 5. Adaptive Layout

**Strong**: WindowSizeClass drives layout decisions. Compact shows single-pane, Medium shows navigation rail, Expanded shows dual-pane master-detail. Content reflows rather than simply stretching. Landscape orientation is handled. Foldable configurations are considered. Typography and spacing scale appropriately.

**Weak**: Phone layout stretched to tablet (huge margins, tiny content). No WindowSizeClass checks. Landscape shows the same single-column layout with empty space. Navigation doesn't adapt (bottom nav on tablets instead of navigation rail).

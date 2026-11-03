# Accessibility

## When to use

Read when building or reviewing UI for VoiceOver, Dynamic Type, and motion preferences. `swiftui-pro` carries an accessibility review section for SwiftUI code; this page is the short checklist.

## Checklist

- **Labels**: every control that isn't plain text has an `accessibilityLabel`. Decorative images use `Image(decorative:)` or `.accessibilityHidden(true)`.
- **Values and traits**: report state with `accessibilityValue`, and use `.accessibilityAddTraits(.isButton)` when a tap gesture stands in for a `Button`. Prefer a real `Button`.
- **Grouping**: combine a row into one element with `.accessibilityElement(children: .combine)` so VoiceOver reads it once.
- **Dynamic Type**: use text styles (`.font(.body)`) rather than fixed sizes; use `@ScaledMetric` for spacing and icon sizes that should grow. Test at the largest accessibility size and let layouts wrap or scroll (`ViewThatFits`).
- **Touch targets**: at least 44 × 44 points.
- **Color**: never convey meaning by color alone; check contrast in light, dark, and with Increase Contrast.
- **Motion**: honor `@Environment(\.accessibilityReduceMotion)` and skip large movement or parallax.
- **Custom actions**: `.accessibilityAction(named:)` for swipe actions and context menus.
- **Focus**: move VoiceOver focus after navigation or an error with `@AccessibilityFocusState`.

## Verifying

Run the Accessibility Inspector on the simulator and audit each screen. Then test with VoiceOver on a device. A passing audit does not replace listening to the screen read aloud.

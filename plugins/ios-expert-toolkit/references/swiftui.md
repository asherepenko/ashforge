# SwiftUI

## When to use

Read when structuring SwiftUI views, choosing state wrappers, or bridging UIKit. Reviews and new screens go to `swiftui-pro`; observation, environment, `ForEach` identity and deprecations go to `swiftui-specialist`; iOS 27 APIs go to `swiftui-whats-new-27`. This page keeps only the structure advice they share.

## View structure

- Small views over long `body` properties. Extract a `struct`, not a computed property that returns `some View`, when the piece has its own state or is reused.
- A screen is two parts: a container that reads state holders and sends actions, and a pure content view that takes plain values. The content view is what previews and snapshot tests use.
- Previews: one `#Preview` per meaningful state (loading, empty, error, loaded).
- Keep `body` free of work. Sort, filter and format outside it.

## State wrappers

| Need | Wrapper |
|------|---------|
| View-owned value | `@State` |
| Value owned by a parent | plain property, or `@Binding` if the child writes it |
| `@Observable` object the view creates | `@State` |
| `@Observable` object passed in | plain property; `@Bindable` when you need bindings into it |
| Shared value from the tree | `@Environment` |

`@Observable` needs iOS 17. For older targets use `@StateObject`, `@ObservedObject` and `@EnvironmentObject`.

## UIKit interop

- **UIKit inside SwiftUI**: wrap the view or controller in `UIViewRepresentable` or `UIViewControllerRepresentable`. Create it in `makeUIView`, apply state changes in `updateUIView`, and use a `Coordinator` for delegates and target-action. Never create new view instances in `updateUIView`.
- **SwiftUI inside UIKit**: host it in `UIHostingController` and add it as a child view controller (`addChild`, add the view, `didMove(toParent:)`). Pass data through the root view's initializer or an `@Observable` object.
- Keep the bridge thin: it translates values and events, and the logic stays on the SwiftUI side.

## Accessibility and navigation

See [accessibility](accessibility.md) and [navigation](navigation.md).

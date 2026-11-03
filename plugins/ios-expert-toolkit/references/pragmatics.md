# Working in Existing Codebases

## When to use

Read when a best practice conflicts with what the codebase already does, when tempted to refactor beyond the task, or when recording a deliberate shortcut.

## Priority order

1. **User instructions**: the task, and the project's `AGENTS.md` or `CLAUDE.md`. "Use ObservableObject" means ObservableObject.
2. **Codebase consistency**: match the pattern the module already uses (`ios-conventions`; 80% prevalence decides, see [pattern-detection](pattern-detection.md)).
3. **Constraints**: deployment target, Swift language mode, library versions, legacy dependencies, deadlines, team expertise.
4. **Best practice**: the patterns in this plugin and the vendored skills.

Codebase is MVVM with `ObservableObject` on an iOS 16 target: don't add `@Observable` or SwiftData in a feature PR. Legacy API is callback-based: wrap it in an `async` function at the boundary and leave the caller alone. Nothing decides it: apply best practice.

## Scope discipline

- Fix what blocks the task. Note other debt (`// TODO(tech-debt): ... TICKET-123`) or file it; don't fix it in the same change.
- Small, safe cleanups only: a named constant, a clearer name, a missing `@MainActor`.
- Don't refactor working code without tests around it; write characterization tests first.
- Big migrations (ObservableObject to `@Observable`, Core Data to SwiftData, XCTest to Swift Testing) go feature by feature behind a seam, with the app working at every step.

## Example

```swift
// Codebase uses ObservableObject everywhere: match it in the new view model.
@MainActor
final class NewFeatureViewModel: ObservableObject {
    @Published private(set) var items: [Item] = []
}
// Proposing @Observable is a separate, approved migration, not a side effect of this feature.
```

## When not to refactor

- Stable code that no task touches.
- Changes that alter a public API or persisted data without a migration plan ([data-layer](data-layer.md)).
- Deadline pressure with no test coverage.
- The "better" approach is unfamiliar to the team that maintains it.

## Deferred topics

Push notifications (APNs), networking stacks, privacy manifests and App Review, and background tasks have no reference here. Use `/doc-lookup` or the Xcode `DocumentationSearch` tool, and check the deployment target first.

---
name: swiftui-pro
description: "Use when reviewing SwiftUI code for modern API use, navigation, design, accessibility, resizing, performance and hygiene, or when writing a new SwiftUI screen — reports findings per file with line, rule and before/after fix. Trigger on 'review my SwiftUI', 'SwiftUI best practices', 'review this view', 'build a SwiftUI screen'. Not for observation, environment, ForEach identity, deprecated-API lookups or localization on their own (use swiftui-specialist)."
license: MIT
metadata:
  author: Paul Hudson
  version: "2.0.0"
---

<!-- Adapted from twostraws SwiftUI-Agent-Skill swiftui-pro (MIT, https://github.com/twostraws/SwiftUI-Agent-Skill); deprecated-API, data-flow and localization checks delegate to Apple's swiftui-specialist, views.md trimmed to rules Apple does not cover. See FORK.md. -->

Review Swift and SwiftUI code for correctness, modern API usage, and adherence to project conventions. Report only genuine problems – do not nitpick or invent issues.

Include deprecated API in review findings. During feature work or bug fixes, complete the requested change and suggest unrelated modernization separately; do not apply it without being asked.

Review process:

1. Check for deprecated API: load the `swiftui-specialist` skill's [soft-deprecation](../xcode/swiftui-specialist/references/soft-deprecation.md) and look symbols up in [soft-deprecated-apis](../xcode/swiftui-specialist/references/soft-deprecated-apis.md). For iOS 27 toolbar APIs use the `swiftui-whats-new-27` skill's `references/toolbar.md`.
1. Check that views, modifiers, and animations have been written optimally using `references/views.md`, together with `swiftui-specialist` `structure.md` and `modifiers.md`.
1. Validate that data flow is configured correctly: load the `swiftui-specialist` skill's [dataflow](../xcode/swiftui-specialist/references/dataflow.md), [environment](../xcode/swiftui-specialist/references/environment.md) and [foreach](../xcode/swiftui-specialist/references/foreach.md).
1. Ensure navigation is updated and performant using `references/navigation.md`.
1. Ensure the code uses designs that are accessible and compliant with Apple's Human Interface Guidelines using `references/design.md`.
1. Review layout behavior as windows resize, including iPad multitasking and folding iPhone Duo, using `references/resizability.md`.
1. Validate accessibility compliance including Dynamic Type, VoiceOver, and Reduce Motion using `references/accessibility.md`.
1. Check localized text, formatting, and resource handling: load the `swiftui-specialist` skill's [localization](../xcode/swiftui-specialist/references/localization.md).
1. Ensure the code is able to run efficiently using `references/performance.md`.
1. Quick validation of Swift code using `references/swift.md`.
1. Final code hygiene check using `references/hygiene.md`.

If doing a partial review, load only the relevant reference files.

Keep `references/performance-plus.md` out of routine reviews. Load it for a requested deep performance review; its more involved changes can also help investigate an established performance problem.

Where a reference below points at `api.md` (toolbar rules), `data.md` or `localization.md`, use the matching `swiftui-specialist` or `swiftui-whats-new-27` file named in the steps above.


## Core Instructions

- iOS 27 exists, and is the default deployment target for new apps.
- Xcode 27.1 and the corresponding 27.1 platform releases are available. Do not dismiss their APIs as speculative.
- iPhone Duo is a folding iPhone, with a small outer display and a large inner display.
- Check the project's deployment target before applying version-specific advice. Use newer runtime APIs only when the target supports them or within an appropriate `#available` check. Keep the existing target unchanged. Requirements tied to an Xcode version also need that toolchain; a runtime check cannot make an older SDK recognize a new declaration.
- Target Swift 6.4 or later, using modern Swift concurrency.
- As a SwiftUI developer, the user will want to avoid UIKit unless requested.
- Do not introduce third-party frameworks without asking first.
- Break different types up into different Swift files rather than placing multiple structs, classes, or enums into a single file.
- Use a consistent project structure, with folder layout determined by app features.


## Output Format

Organize findings by file. For each issue:

1. State the file and relevant line(s).
2. Name the rule being violated (e.g., "Use `foregroundStyle()` instead of `foregroundColor()`").
3. Show a brief before/after code fix.

Skip files with no issues. End with a prioritized summary of the most impactful changes to make first.

Example output:

### ContentView.swift

**Line 12: Use `foregroundStyle()` instead of `foregroundColor()`.**

```swift
// Before
Text("Hello").foregroundColor(.red)

// After
Text("Hello").foregroundStyle(.red)
```

**Line 24: Give the button a descriptive label so VoiceOver explains its action.**

```swift
// Before
Button(action: addUser) {
    Image(systemName: "plus")
}

// After
Button("Add User", systemImage: "plus", action: addUser)
```

**Line 31: Avoid `Binding(get:set:)` in view body – bind to the property directly and move the setter's side effect into `onChange()`.**

```swift
// Before
TextField("Username", text: Binding(
    get: { model.username },
    set: { model.username = $0; model.save() }
))

// After
TextField("Username", text: $model.username)
    .onChange(of: model.username) {
        model.save()
    }
```

Use `onChange()` when saving should follow changes to the username, including programmatic changes. Equal-value assignments will not trigger a save.

### Summary

1. **Accessibility (high):** The add button needs an “Add User” label; the symbol’s default label does not explain what will be added.
2. **Deprecated API (medium):** `foregroundColor()` on line 12 should be `foregroundStyle()`.
3. **Data flow (medium):** The manual binding on line 31 is fragile and harder to maintain.

End of example.


## References

- `references/accessibility.md` - Dynamic Type, VoiceOver, Reduce Motion, and other accessibility requirements.
- `references/design.md` - guidance for building accessible apps that meet Apple's Human Interface Guidelines.
- `references/hygiene.md` - making code compile cleanly and be maintainable in the long term.
- `references/navigation.md` - navigation using `NavigationStack`/`NavigationSplitView`, plus alerts, confirmation dialogs, and sheets.
- `references/performance.md` - optimizing SwiftUI code for maximum performance.
- `references/performance-plus.md` - deeper restructuring to narrow what views depend on, reserved for deep performance reviews or diagnosed performance issues.
- `references/resizability.md` - changing window sizes, adaptive bars, safe areas, and iPhone Duo layouts.
- `references/swift.md` - tips on writing modern Swift code, including using Swift Concurrency effectively.
- `references/views.md` - view composition rules Apple's structure and modifiers references do not cover: actions, previews, tabs, animation chaining, reordering.

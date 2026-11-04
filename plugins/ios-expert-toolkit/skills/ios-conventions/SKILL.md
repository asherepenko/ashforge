---
name: ios-conventions
description: "Use when analyzing pattern consistency in an iOS codebase or choosing the architecture for new iOS code — TCA vs MVVM vs UIKit, dependency injection, testing framework, persistence, concurrency, navigation. Runs detection sweeps and applies the TCA decision rule and 80/20 matrix. Trigger on 'check patterns', 'which architecture does this app use', 'should this feature use TCA', 'iOS conventions', 'iet check'."
argument-hint: "[architecture | di | testing | persistence | concurrency | navigation | version | all]"
---

# iOS Pattern Check

Detect what the codebase already does, then decide whether new code follows it or starts with TCA. Read-only: uses `rg`, `jq`, and file reads. Works the same on every runtime.

Sweep definitions (exact patterns, exclusions, counting rules) live in [pattern-detection](../../references/pattern-detection.md). Read it before running a sweep; do not improvise patterns from this page.

## Preflight

Run this first, from the project root. The script lives in this skill's folder (the folder holding this SKILL.md):

```bash
python3 <this skill's folder>/scripts/preflight.py
```

It is read-only and prints `NOT_FOUND` or `NONE` for anything missing. It reports: deployment targets (`IPHONEOS_DEPLOYMENT_TARGET`), `Package.swift` platforms, `swift-tools-version`, Swift language mode (`SWIFT_VERSION`, `swiftLanguageModes`), strict concurrency setting, TCA version from `Package.resolved`, all resolved packages, `import Testing` vs `import XCTest` file counts, and `@Observable` vs `ObservableObject` file counts. It skips `.build/`, `Pods/`, `Carthage/`, `SourcePackages/`, and `DerivedData/`.

Use the output to:
1. Answer the `version` area directly. Do not re-run that sweep by hand.
2. Pre-bias the `testing` and `concurrency` sweeps from the counts and settings.
3. Read the `@Observable` and `ObservableObject` counts as a first hint for the architecture sweep. The verdict still comes from the architecture sweep below.

## Sweeps

Count files, not matches. Exclude `Pods/`, `Carthage/`, `.build/`, `SourcePackages/`, `*Tests`, and `*Preview*` unless the sweep says otherwise.

| Area | Patterns compared |
|------|-------------------|
| `architecture` | TCA `@Reducer` vs MVVM (`@Observable` class or `ObservableObject` class) vs UIKit (`UIViewController` subclass) |
| `di` | `@Dependency` vs factories vs singletons (`static let shared`) |
| `testing` | `import Testing` vs `XCTestCase` |
| `persistence` | `@Model` (SwiftData) vs `NSManagedObject` (Core Data) |
| `concurrency` | Swift 6 language mode (`swiftLanguageModes`, `SWIFT_VERSION`), `@MainActor` coverage |
| `navigation` | `NavigationStack` vs coordinators (`Coordinator`, `UINavigationController`) |
| `version` | `Package.resolved` (TCA version), `IPHONEOS_DEPLOYMENT_TARGET`, `SWIFT_VERSION` / `swiftLanguageModes` |

For the architecture verdict, run the reference implementation when the plugin checkout includes `tests/`. Its path is relative to this skill's folder:

```bash
python3 <this skill's folder>/../../tests/fixtures/run-sweeps.py <project-dir>
```

It prints one of `NEW`, `TCA`, `MVVM`, `MIXED`. Without the script, apply the same counts by hand with the patterns from the reference.

## Decision rule

Run the architecture sweep first. The verdict sets what new feature code does.

| Verdict | Meaning | New feature code |
|---------|---------|------------------|
| `NEW` | No feature sources beyond the Xcode template (App struct and `ContentView`) | TCA required |
| `TCA` | TCA files are 80% or more of TCA + MVVM + UIKit | TCA for new features |
| `MVVM` | MVVM + UIKit files are 80% or more | Never force TCA; follow the existing pattern |
| `MIXED` | Neither side reaches 80% | Follow the dominant local pattern in the feature's folder; TCA only on request |

Why: matching the existing code keeps one pattern per codebase, and a fresh project has nothing to match, so the toolkit default applies. Exactly 80% counts as dominant. Legacy `ObservableObject` view models count as MVVM, so an app of old view models plus two new reducers is `MVVM`, not `MIXED`.

For `TCA` and `NEW`, hand new feature work to `/tca`. For SwiftUI view code, use `/swiftui-pro`.

## Other areas

Apply the 80/20 matrix to each remaining area, using the share of the dominant pattern:

- 80% or more: use the dominant pattern for new code.
- 50-79%: pattern conflict; propose standardizing on the modern choice.
- Below 50%: no dominant pattern; use the modern choice.

Modern choices: Swift Testing for new tests, SwiftData for new persistence on iOS 17+, `NavigationStack` over coordinators in SwiftUI code, `@Dependency` when TCA is in use.

## Version awareness

Use the preflight version facts before recommending an API. Check availability against the deployment target: `@Observable` and SwiftData need iOS 17, and the `*-whats-new-27` skills need iOS 27. Flag legacy TCA APIs only when the resolved TCA version deprecates them. Match the Swift language mode already in use.

## Report

State the architecture verdict and the rule it triggers first. Then one line per area: dominant pattern, share, recommendation. End with the version facts used.

## Done means

- The architecture verdict (`NEW`, `TCA`, `MVVM`, or `MIXED`) is stated with the three file counts behind it.
- Every requested area shows a dominant pattern and its share, or says the pattern is absent.
- The version facts (TCA version, deployment target, Swift mode) are listed, or marked not found.

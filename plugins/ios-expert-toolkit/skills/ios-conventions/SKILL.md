---
name: ios-conventions
description: "Use when checking pattern consistency in an iOS codebase or choosing the architecture for new iOS code — TCA vs MVVM vs UIKit, dependency injection, testing framework, persistence, concurrency, navigation. Trigger on 'check patterns', 'which architecture does this app use', 'should this feature use TCA', 'iOS conventions', 'iet check'."
argument-hint: "[architecture | di | testing | persistence | concurrency | navigation | version | all] [--fresh]"
---

# iOS Pattern Check

Detect what the codebase already does, then decide whether new code follows it or starts with TCA. Read-only apart from the cache file: uses a bundled Python script and file reads. Works the same on every runtime.

Sweep definitions (exact patterns, exclusions, counting rules) live in [pattern-detection](../../references/pattern-detection.md). Read it before running a sweep; do not improvise patterns from this page.

## Preflight

Run this first, from the project root. The script lives in this skill's folder (the folder holding this SKILL.md):

```bash
python3 <this skill's folder>/scripts/preflight.py
```

It is read-only and prints `NOT_FOUND` or `NONE` for anything missing. It reports: the project hash and any cached patterns, deployment targets (`IPHONEOS_DEPLOYMENT_TARGET`), `Package.swift` platforms, `swift-tools-version`, Swift language mode (`SWIFT_VERSION`, `swiftLanguageModes`), strict concurrency setting, TCA version from `Package.resolved`, all resolved packages, `import Testing` vs `import XCTest` file counts, and `@Observable` vs `ObservableObject` file counts. It skips `.build/`, `Pods/`, `Carthage/`, `SourcePackages/`, and `DerivedData/`.

Use the output to:
1. Check the cache: if `Project hash` equals the cached `project_hash` and the user did not ask for `--fresh`, use the cached `patterns` and skip to Report. The hash covers every Swift file, `Package.swift`, `Package.resolved`, `project.pbxproj` and `*.xcconfig` at any depth, so any edit to them forces a re-run. The cache is [documented here](../../references/pattern-detection.md) (section *Pattern Detection Cache*); its path and keys are a stable contract read by other tools and agents.
2. Answer the `version` area directly (the cache also holds a `version` entry).
3. Pre-bias the `testing` and `concurrency` sweeps from the counts and settings.
4. Read the `@Observable` and `ObservableObject` counts as a first hint for the architecture sweep. The verdict still comes from the architecture sweep below.

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

Run the counting script with the project root as `<project-dir>` and the requested areas (none = all). It also writes the cache, so a stale or missing cache is refreshed here:

```bash
python3 <this skill's folder>/scripts/detect-patterns.py <project-dir> [area ...] --write-cache
```

Do not recount by hand or improvise patterns. The script holds the sweeps from the reference and prints `== section ==` blocks:

- `files_scanned=` - Swift files under the project (`Pods/`, `Carthage/`, `.build/`, `SourcePackages/`, `DerivedData/` pruned).
- `architecture` - `count tca files=N` and likewise `mvvm_observable`, `mvvm_object`, `mvvm`, `uikit` and `feature_files`, then `verdict_architecture=NEW|TCA|MVVM|MIXED`.
- `decision <key>` - competing patterns in `di`, `testing`, `persistence` and `navigation`: one `<pattern> files=N share=P%` line each, then `dominant=... consistency=P% verdict=match|conflict|adopt|none`.
- `count <id> files=N` - sweeps that do not compete (`language_mode_settings` and `main_actor` in `concurrency`).
- `version` - `tca_version`, `deployment_target`, `swift_version`, `swift_language_modes` as `key=value`, `none` when absent. No verdict.

A count is Swift files with at least one match, not occurrences. Exit 2 means a usage error or a missing directory: fix the call, don't fall back to manual greps.

Judgment stays with you:

- `verdict=none` means no evidence of that pattern; say so, don't infer one.
- Overlaps in the reference regexes can inflate a count: `Factory` matches any type with that word in its name, and `Coordinator` matches non-navigation types. When a verdict hinges on one of these, open a few files before reporting.
- A project with several app targets or local packages mixes their counts; read the folder of the code you are about to change.

## Decision rule

Read `verdict_architecture` first. The verdict sets what new feature code does.

| Verdict | Meaning | New feature code |
|---------|---------|------------------|
| `NEW` | No feature sources beyond the Xcode template (App struct and `ContentView`) | TCA required |
| `TCA` | TCA files are 80% or more of TCA + MVVM + UIKit | TCA for new features |
| `MVVM` | MVVM + UIKit files are 80% or more | Never force TCA; follow the existing pattern |
| `MIXED` | Neither side reaches 80% | Follow the dominant local pattern in the feature's folder; TCA only on request |

Why: matching the existing code keeps one pattern per codebase, and a fresh project has nothing to match, so the toolkit default applies. Exactly 80% counts as dominant. Legacy `ObservableObject` view models count as MVVM, so an app of old view models plus two new reducers is `MVVM`, not `MIXED`.

For `TCA` and `NEW`, hand new feature work to `/tca`. For SwiftUI view code, use `/swiftui-pro`.

## Other areas

Apply the 80/20 matrix to each remaining area; the script prints the verdict, from the share of the dominant pattern:

- 80% or more (`match`): use the dominant pattern for new code.
- 50-79% (`conflict`): pattern conflict; propose standardizing on the modern choice.
- Below 50% (`adopt`): no dominant pattern; use the modern choice.

Modern choices: Swift Testing for new tests, SwiftData for new persistence on iOS 17+, `NavigationStack` over coordinators in SwiftUI code, `@Dependency` when TCA is in use.

## Version awareness

Use the `version` facts before recommending an API. Check availability against the deployment target: `@Observable` and SwiftData need iOS 17, and the `*-whats-new-27` skills need iOS 27. Flag legacy TCA APIs only when the resolved TCA version deprecates them. Match the Swift language mode already in use.

## Report

State the architecture verdict and the rule it triggers first. Then one rendered markdown table, never inside a code fence: `| Area | Dominant pattern | Share | Recommendation |`, one row per area. End with the version facts used.

## Done means

- `detect-patterns.py` ran with `--write-cache` (or the cache was a hit), so `.artifacts/iet/cache/detected-patterns.json` is current.
- The architecture verdict (`NEW`, `TCA`, `MVVM`, or `MIXED`) is stated with the three file counts behind it.
- Every requested area shows a dominant pattern and its share, or says the pattern is absent.
- The version facts (TCA version, deployment target, Swift mode) are listed, or marked not found.

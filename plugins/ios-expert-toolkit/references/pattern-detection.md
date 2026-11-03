# iOS Pattern Detection and Decision Framework

## When to use

Read this before deciding whether new iOS code should match the codebase's existing architecture or follow the toolkit default. The `ios-conventions` skill runs these sweeps. This file is the single source for the sweep patterns; `tests/fixtures/run-sweeps.py` implements the architecture sweep and a test keeps it identical to the table below.

## Architecture sweep (counts files)

Count files, not matches. Exclude `Pods/`, `Carthage/`, `.build/`, `SourcePackages/`, any `*Tests` directory, and any `*Preview*` path.

| Id | Meaning | Pattern (ERE) |
|----|---------|---------------|
| TCA | File declares a reducer | `@Reducer` |
| MVVM_OBSERVABLE | File has an `@Observable` class (view state). `@ObservableState` is TCA and does not match | `@Observable([^A-Za-z]\|$)` |
| MVVM_OBJECT | File has a class conforming to `ObservableObject` | `class[^{]*:[^{]*ObservableObject` |
| UIKIT | File subclasses a `UIViewController` | `class[[:space:]]+[A-Za-z0-9_]+[[:space:]]*:[[:space:]]*UI[A-Za-z]*ViewController` |

The `\|` in the MVVM_OBSERVABLE row is table escaping; the real pattern is `@Observable([^A-Za-z]|$)`.

MVVM = files matching MVVM_OBSERVABLE or MVVM_OBJECT (a file counts once). A class need not be named `*Model` or `*ViewModel`.

Reference run: `python3 tests/fixtures/run-sweeps.py <project-dir>` prints exactly one verdict.

```
total = TCA + MVVM + UIKit
NEW    no Swift file beyond the Xcode template (the @main App file and ContentView.swift)
TCA    TCA / total >= 0.8
MVVM   (MVVM + UIKit) / total >= 0.8
MIXED  everything else, including a project with code but zero signal
```

The 80% test is integer math (`TCA*10 >= 8*total`), so exactly 80% counts as dominant.

## Decision rule

| Verdict | What new feature code does |
|---------|----------------------------|
| NEW | TCA required |
| TCA | TCA for new features (share is 80% or more) |
| MVVM | Never force TCA; follow the existing MVVM/UIKit pattern |
| MIXED | Follow the dominant local pattern in the feature's folder; TCA only on request |

## Other sweeps

Run with `rg` from the project root, with the same exclusions as above unless noted.

### Dependency injection

```bash
rg -l '@Dependency\b|DependencyKey' --glob '*.swift'          # TCA dependencies
rg -l 'static let shared\b' --glob '*.swift'                   # singletons
rg -l 'Factory|func make[A-Z][A-Za-z]*\(' --glob '*.swift'     # factories
```

### Tests

```bash
rg -l 'import Testing' --glob '*.swift'      # Swift Testing
rg -l 'XCTestCase' --glob '*.swift'          # XCTest
```

This sweep scans test directories on purpose, so skip the `*Tests` exclusion.

### Persistence

```bash
rg -l '@Model\b' --glob '*.swift'            # SwiftData
rg -l 'NSManagedObject' --glob '*.swift'     # Core Data
```

### Concurrency

```bash
rg -n 'swiftLanguageModes|SWIFT_VERSION' Package.swift ./*.xcodeproj/project.pbxproj
rg -l '@MainActor' --glob '*.swift'
```

Swift 6 language mode means strict concurrency errors; match it in new code. Below 6, follow the project's current strictness.

### Navigation

```bash
rg -l 'NavigationStack|navigationDestination' --glob '*.swift'
rg -l 'Coordinator|UINavigationController' --glob '*.swift'
```

## Version sweep

```bash
jq -r '.pins[] | select(.identity=="swift-composable-architecture") | .state.version' Package.resolved
rg -o 'IPHONEOS_DEPLOYMENT_TARGET = [0-9.]+' --glob '*.pbxproj' | sort -u
rg -o 'SWIFT_VERSION = [0-9.]+|swiftLanguageModes: \[[^]]*\]' --glob '*.pbxproj' --glob 'Package.swift' | sort -u
```

Package.resolved may live under `*.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/`. Check availability against the deployment target before recommending an API: `@Observable` and SwiftData need iOS 17; the `*-whats-new-27` skills need iOS 27. Flag legacy TCA APIs only when the resolved TCA version deprecates them.

## Report format

One line per area: dominant pattern, share, verdict. State the architecture verdict first, then the rule it triggers.

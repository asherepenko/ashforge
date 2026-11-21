# iOS Pattern Detection and Decision Framework

## When to use

Read this before deciding whether new iOS code should match the codebase's existing architecture or follow the toolkit default. The `/ios-conventions` skill runs these sweeps. This file is the single source for the sweep patterns; `skills/ios-conventions/scripts/detect-patterns.py` implements every sweep below and a test keeps its patterns identical to this file.

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

Reference run: `python3 skills/ios-conventions/scripts/detect-patterns.py <project-dir> architecture` prints the file counts and one `verdict_architecture=` line.

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

Run with `rg` from the project root, with the same exclusions as above unless noted. `detect-patterns.py` runs the same patterns over `.swift` files.

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

## Decision matrix (80/20)

For every area except `architecture` (which has the verdict above), compare the files of the competing patterns. The dominant pattern's share of all matching files decides:

| Share | Verdict | Meaning |
|-------|---------|---------|
| 80% or more | `match` | Use the dominant pattern for new code |
| 50-79% | `conflict` | Propose standardizing on the modern choice |
| Below 50% | `adopt` | No dominant pattern; use the modern choice |
| no matches | `none` | The pattern is absent; say so |

Ties go to the first pattern listed in the sweep. Sweeps outside a comparison (`@MainActor`, the language-mode settings) are reported as counts.

## Version sweep

```bash
jq -r '.pins[] | select(.identity=="swift-composable-architecture") | .state.version' Package.resolved
rg -o 'IPHONEOS_DEPLOYMENT_TARGET = [0-9.]+' --glob '*.pbxproj' | sort -u
rg -o 'SWIFT_VERSION = [0-9.]+|swiftLanguageModes: \[[^]]*\]' --glob '*.pbxproj' --glob 'Package.swift' | sort -u
```

Package.resolved may live under `*.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/`. Check availability against the deployment target before recommending an API: `@Observable` and SwiftData need iOS 17; the `*-whats-new-27` skills need iOS 27. Flag legacy TCA APIs only when the resolved TCA version deprecates them.

## Pattern Detection Cache

### Cache Location

`.artifacts/iet/cache/detected-patterns.json`, under the project directory. `detect-patterns.py --write-cache` writes it.

### Cache Schema

```json
{
  "timestamp": "2026-11-21T17:00:00Z",
  "project_hash": "<sha256 of Package.swift + project.pbxproj files>",
  "patterns": {
    "architecture": { "detected": "TCA", "confidence": 0.9, "evidence": ["Sources/Features/CounterFeature.swift:tca"] },
    "di_style": { "detected": "tca_dependency", "confidence": 0.75, "evidence": ["Sources/Features/FeedFeature.swift:tca_dependency"] },
    "testing_framework": { "detected": "swift_testing", "confidence": 1.0, "evidence": ["Tests/CounterTests.swift:swift_testing"] }
  }
}
```

Keys: `architecture`, `di_style`, `testing_framework`, `persistence_framework`, `navigation_style`. For `architecture`, `detected` is the verdict (`NEW`, `TCA`, `MVVM` or `MIXED`) and `confidence` is the share of the side that decided it (`NEW` is 1.0; `MIXED` is the larger side's share, 0.0 with no signal). For the other keys, `detected` is the dominant pattern id (or `none`) and `confidence` its share. `evidence` lists up to three `path:pattern` entries. `version` and `concurrency` facts are not cached; read them from `preflight.py`.

### Freshness Rules

- The cache is valid while `project_hash` equals the current hash. A run for a subset of categories keeps the other entries while the hash is unchanged and drops them when it changes.
- An explicit user choice overrides a cached value; record it with `confidence: 1.0`.
- To force re-detection, delete the cache file or ask for `--fresh`.

### Computing `project_hash`

sha256 over the bytes of the root `Package.swift`, then each root-level `*.xcodeproj/project.pbxproj` in name order; `NO_PROJECT_FILES` when there are none. Only root-level files count; package manifests in subfolders change often without changing which patterns the app uses. `preflight.py` prints the same value under `== Project hash ==`.

The cache path is a stable contract: other tools read `.artifacts/iet/cache/detected-patterns.json`. Don't rename it or change existing keys.

## Report format

One line per area: dominant pattern, share, verdict. State the architecture verdict first, then the rule it triggers.

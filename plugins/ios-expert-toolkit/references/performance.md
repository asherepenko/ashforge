# Performance

## When to use

Read when setting performance goals or choosing a tool. Measure before and after every optimization; no "faster" without numbers.

| Problem | Load |
|---------|------|
| Recording and reading Instruments traces from the command line | `xctrace` skill |
| SwiftUI invalidation, animation cost, `ForEach` identity | `swiftui-specialist` skill |
| Main-actor hangs, actor contention | `swift-concurrency` skill |

## Tools

- **Instruments** (Time Profiler, Hangs, Allocations, SwiftUI): find the cause on a device with a Release build. The simulator's timings don't predict a device's.
- **MetricKit**: field data for launch time, hangs, memory, and disk writes. Ship a `MXMetricManagerSubscriber` in production builds.
- **Xcode Organizer**: crash, hang and launch trends per release. The Xcode MCP tools `GetTopFieldPerformanceIssues` and `GetFieldPerformanceIssueLogs` read the same data.
- **XCTest metrics** (`XCTClockMetric`, `XCTMemoryMetric`, `XCTApplicationLaunchMetric`): regression guards in CI. Set a baseline per device.

## Habits that pay off

- Keep the main thread free: no disk, network, or large parsing in `body`, `init`, or `@MainActor` code on the launch path.
- Defer work that isn't needed for the first screen. Launch is measured to the first frame the user can use.
- Lists: use `LazyVStack`/`List` for long content, stable identifiers in `ForEach`, and downsample images to display size.
- Cache derived values; don't recompute sorted or formatted data on every body evaluation.
- Watch memory growth on repeated navigation: retain cycles in closures and `Task`s that capture `self` are the usual cause.

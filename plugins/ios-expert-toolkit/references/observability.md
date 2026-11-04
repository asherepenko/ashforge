# Observability

## When to use

Read when adding logging, crash reporting, analytics events, or custom performance measurement. Match the project's existing logger and crash reporter. Tools for finding performance problems → [performance](performance.md).

## Logging

`Logger` (iOS 14+, `os` framework) writes to the unified log. It is cheap when a level is off.

```swift
import os

extension Logger {
    static let sync = Logger(subsystem: Bundle.main.bundleIdentifier!, category: "sync")
}

Logger.sync.info("Drained \(count) changes")
Logger.sync.error("Push failed for \(itemID, privacy: .private): \(error.localizedDescription, privacy: .public)")
```

- One subsystem per app, one category per feature. Filter by them in Console.app and `log stream`.
- Levels: `debug` is not kept in the log store, `info` is kept only briefly, `notice` (the default) and above are kept. Use `error` and `fault` for real failures.
- Privacy: dynamic strings and objects are redacted (`<private>`) by default outside a debugger; numbers and booleans are public. Mark a value `privacy: .public` only when it is safe. Use `privacy: .private(mask: .hash)` to correlate a value without showing it. Never log tokens, credentials, or personal data ([security](security.md)).
- Log once, where the error is caught and typed (`ios-error-handling`).
- `CancellationError` is not an error; don't log it at `error` level or report it.
- `print` goes to stdout only. Don't ship it.

## Signposts

`OSSignposter` (iOS 15+) marks intervals and events that show in the Instruments "os_signpost" and "Points of Interest" tracks.

```swift
let signposter = OSSignposter(logger: .sync)

func drain() async throws {
    let state = signposter.beginInterval("drain", id: signposter.makeSignpostID())
    defer { signposter.endInterval("drain", state) }
    // ...
}
```

- Use signposts to measure a span in a trace. They are not field metrics.
- Use `OSLog.pointsOfInterest` as the category to show marks in the Points of Interest track.
- Measure durations in code with `ContinuousClock` (iOS 16+) or `mach_continuous_time`. Never with `Date()`: wall time can jump.

## MetricKit

- `MXMetricManager` (iOS 13+) delivers daily `MXMetricPayload`s with launch time, hang rate, memory, disk writes, and battery use. Subscribe with an `MXMetricManagerSubscriber` early in launch and upload the JSON (`jsonRepresentation()`).
- `MXDiagnosticPayload` (iOS 14+) carries crash, hang, CPU and disk-write diagnostics with call stacks. On iOS 15+ diagnostics arrive immediately instead of once a day.
- Custom signpost intervals created with `mxSignpost` are summarized into `MXSignpostMetric` in the daily payload.
- Field data per release is also in Xcode Organizer ([performance](performance.md)).

## Crash reporting

- Use one crash reporter. Two reporters fight over signal handlers.
- Upload dSYMs for every release build, including from CI. Without them, stack traces are not symbolicated.
- Set custom keys that help triage (screen, feature flag variant, build configuration). No personal data.
- Record non-fatal errors only for unexpected failures. Expected ones (offline, 404 on a missing item) drown real problems; count them in analytics if the product needs them.
- Leave breadcrumbs with `Logger` too, so the device log shows the same story when a user sends a sysdiagnose.

## Analytics events

- One typed event API (an `enum AnalyticsEvent`) mapped to the vendor in one place. Features don't call the SDK directly.
- No personal data in event names or parameters: no emails, names, free text, precise location, or raw ids that link to a person. Use a random, resettable install id.
- Respect App Tracking Transparency and the user's analytics consent before sending. Declare the collected data in the privacy manifest ([security](security.md)).
- Event names and parameters are a contract with analysts. Version changes; don't rename silently.
- Fake the analytics interface in tests and assert the events a behavior emits when the event is the requirement.

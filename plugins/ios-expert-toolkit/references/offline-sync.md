# Offline Sync

## When to use

Read when local writes must reach a server later, or when local and remote copies can conflict. Repositories and storage choice → [data-layer](data-layer.md). Task ownership and cancellation → [concurrency](concurrency.md).

## Pending-change queue

Store each pending write in the same database as the local change, in the same save, so a crash can't lose one without the other.

```swift
@Model final class PendingChange {
    var entityID: UUID
    var kind: Kind              // create, update, delete
    var payload: Data
    var attempts: Int = 0
    var createdAt: Date
    var idempotencyKey: UUID
}

actor SyncEngine {
    private let store: PendingChangeStore
    private let api: ItemsAPI

    func drain() async throws -> SyncOutcome {
        for change in try await store.pending() {          // oldest first
            try Task.checkCancellation()
            do {
                try await api.push(change)
                try await store.remove(change)
            } catch let error as APIError where error.isRetryable {
                try await store.incrementAttempts(change)
                return .retryLater                         // keep order: stop here
            } catch let error as APIError {
                try await store.markFailed(change, error)
                return .failed
            }
        }
        return .done
    }
}
```

- Process oldest first. Stop at the first retryable failure so later changes don't overtake earlier ones.
- Collapse redundant changes (create then delete of the same id) before pushing.
- Send a client-generated id or idempotency key. A retry after a timeout may be a duplicate.
- `CancellationError` leaves the change in the queue. It is not a failure (`ios-error-handling`).
- One `actor` owns the drain so two triggers can't push the same change twice.

## Retries and backoff

- Use exponential backoff with jitter and a cap. Persist `attempts` so backoff survives relaunch.
- Retry on network loss, timeouts and 5xx. Do not retry 4xx other than 408 and 429. Honor `Retry-After`.
- Trigger a drain on launch, on return to foreground, on a path change to `.satisfied`, and from a background task. Do not run a polling loop.

## Background execution

- **`BGTaskScheduler`** (iOS 13+): register identifiers in `BGTaskSchedulerPermittedIdentifiers` and register handlers before launch finishes. Use `BGAppRefreshTaskRequest` for a short drain and `BGProcessingTaskRequest` with `requiresNetworkConnectivity = true` for large work. Set `expirationHandler` to cancel the drain, and call `setTaskCompleted(success:)` on every path. The system decides when, or if, a task runs.
- **Background `URLSession`** (`URLSessionConfiguration.background(withIdentifier:)`): uploads and downloads continue after the app is suspended or terminated. Uploads must come from a file, not `Data` in memory. Handle `application(_:handleEventsForBackgroundURLSession:completionHandler:)` and call the handler after `urlSessionDidFinishEvents`. Recreate the session with the same identifier on relaunch.
- Set `waitsForConnectivity = true` on foreground sessions so requests wait for a network instead of failing at once.

## Connectivity

- `NWPathMonitor` (iOS 12+, Network framework) reports `path.status` and `isExpensive` / `isConstrained`. Use it to trigger a drain and to defer large uploads on expensive or constrained paths.
- A `.satisfied` path does not mean the server is reachable. Always handle the request failing.
- Do not check reachability before every request. Send it and handle the error.

## Conflict resolution

| Strategy | Use when | Cost |
|----------|----------|------|
| Last-write-wins on server timestamp | single editor per record, or losing a concurrent edit is acceptable | simple; silently drops one edit |
| Version or ETag (optimistic concurrency) | server can reject stale writes (409 / 412) | client must refetch and re-apply or ask the user |
| Field-level merge | independent fields edited on several devices | more schema and merge code |
| CRDTs | true multi-writer offline editing | complex; only with a clear product need |

- Order by the **server's** timestamp or version. Device clocks drift and can go backwards.
- On a conflict, keep the local change in the queue, refresh the record, and surface the conflict if the merge isn't automatic.
- Deletions need tombstones so a stale device doesn't bring the record back.

## Delta sync

- Fetch with a server-issued cursor, not "my last sync time" from the device clock.
- Apply the page and store the new cursor in one save.
- If the server says the cursor expired, fall back to a full refresh.

## CloudKit and SwiftData sync

- SwiftData with CloudKit (iOS 17+) and `NSPersistentCloudKitContainer` (iOS 13+) sync to the user's private database. They give no conflict callback: the merge is last-writer-wins per record, done by the system.
- Sync timing is not under your control. Do not show "saved to server" based on a local save.
- Model limits (no unique constraints, optional or defaulted attributes, optional relationships) and schema rules are in `swiftdata-pro` and [persisted-state-review](persisted-state-review.md).
- The user can be signed out of iCloud or have iCloud off for the app. Check `CKContainer.accountStatus()` and keep the app usable without sync.
- For your own server, or for custom conflict handling in CloudKit, use `CKSyncEngine` (iOS 17+) or your own queue as above.

## Testing

Fake the API with scripted responses per call and drive the sync engine directly: success, retryable failure mid-queue (order kept), fatal failure, duplicate delivery, clock going backwards, cancellation mid-queue (nothing marked done), relaunch with a non-empty queue. The break vectors in the `ios-testing` skill apply.

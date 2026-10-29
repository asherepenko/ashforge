# Offline Sync

## When to use

Read when local writes must reach a server later, or when local and remote copies can conflict. Basic offline-first reads → `data-layer.md`.

## Sync queue

Persist each pending write in Room, in the same transaction as the local change, so a crash can't lose it.

```kotlin
@Entity(tableName = "sync_queue")
data class SyncOperation(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val entityId: String,
    val type: OperationType,          // CREATE, UPDATE, DELETE
    val payload: String,
    val attempts: Int = 0,
    val createdAt: Long,
)

class SyncManager @Inject constructor(
    private val queue: SyncQueueDao,
    private val api: ItemsApi,
) {
    suspend fun processQueue(): SyncOutcome {
        for (op in queue.pending()) {
            val result = safeCall { push(op) }          // typed result, rethrows CancellationException
            when (result) {
                is Result.Success -> queue.delete(op)
                is Result.Error -> return when (result.error) {
                    DataError.Network.NO_INTERNET, DataError.Network.SERVER_ERROR -> {
                        queue.update(op.copy(attempts = op.attempts + 1)); SyncOutcome.Retryable
                    }
                    else -> { queue.markFailed(op); SyncOutcome.Fatal }
                }
            }
        }
        return SyncOutcome.Done
    }
}
```

- Process in `createdAt` order; stop at the first retryable failure so later operations don't overtake earlier ones.
- Collapse redundant ops (create then delete of the same id) before pushing.
- Make server writes idempotent (client-generated ids or idempotency keys) — a retry after a timeout may be a duplicate.
- Retries and backoff belong to WorkManager (`Result.retry()` + `setBackoffCriteria`), not a hand-rolled `delay` loop.

## Conflict resolution

| Strategy | Use when | Cost |
|----------|----------|------|
| Last-write-wins on server timestamp | single editor per record, or loss of a concurrent edit is acceptable | simple; silently drops one edit |
| Version number / ETag (optimistic concurrency) | server can reject stale writes (409) | client must refetch and re-apply or ask the user |
| Field-level merge | records with independent fields edited on several devices | more schema and merge code |
| Vector clocks / CRDTs | true multi-writer offline editing | complex; only with a clear product need |

- Use the **server's** timestamp or version for ordering; device clocks drift and can go backwards.
- On a 409, keep the local edit in the queue, refresh the record, and surface the conflict if the merge isn't automatic.
- Deletions need tombstones (or a `deleted` flag) so a stale device doesn't resurrect the row.

## Delta sync

- Fetch with a server-issued cursor (`?since=<token>`), not "my last sync time" from the device clock.
- Apply the page and store the new cursor in one transaction.
- If the server says the cursor expired, fall back to a full refresh.

## Testing

Fake the API with scripted responses per call and drive `SyncManager` directly: success, retryable failure mid-queue (order preserved), fatal failure, duplicate delivery, clock going backwards, cancellation mid-queue (nothing marked done). The break-vector list in the `android-testing` skill applies.

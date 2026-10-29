# Data Layer

## When to use

Read when writing repositories, Room, DataStore, network clients, or background work. Error typing → `android-error-handling` skill. Sync queues and conflict resolution → `offline-sync.md`. Changing anything already stored on installed devices → `persisted-state-review.md`. Detect the project's stack first (`aet-check`): Retrofit vs Ktor, Moshi vs kotlinx.serialization, Room vs SQLDelight.

## Offline-first repository

The local database is the source of truth: reads observe it, writes land in it first, network refresh writes into it.

```kotlin
interface ItemsRepository {
    val items: Flow<List<Item>>
    suspend fun refresh(): EmptyResult<DataError>        // project's typed result
    suspend fun create(item: Item): EmptyResult<DataError>
}

internal class OfflineFirstItemsRepository @Inject constructor(
    private val dao: ItemDao,
    private val api: ItemsApi,
    private val syncQueue: SyncQueue,
) : ItemsRepository {

    override val items: Flow<List<Item>> = dao.observeAll().map { rows -> rows.map(ItemEntity::toModel) }

    override suspend fun refresh(): EmptyResult<DataError> =
        safeCall { api.getItems() }.map { remote -> dao.replaceAll(remote.map(ItemDto::toEntity)) }

    override suspend fun create(item: Item): EmptyResult<DataError> {
        dao.upsert(item.toEntity())
        syncQueue.enqueue(SyncOp.Create(item.id))   // WorkManager pushes it when online
        return Result.Success(Unit)
    }
}

// The one place network exceptions become typed errors.
internal suspend inline fun <T> safeCall(block: () -> T): Result<T, DataError.Network> =
    try {
        Result.Success(block())
    } catch (e: CancellationException) {
        throw e                                  // never swallow cancellation
    } catch (e: IOException) {
        Result.Error(DataError.Network.NO_INTERNET)
    } catch (e: HttpException) {
        Result.Error(e.code().toNetworkError())
    } catch (e: SerializationException) {
        Result.Error(DataError.Network.SERIALIZATION)
    }
```

- Expose `Flow` for anything the UI observes; `suspend` for one-shot commands.
- Map DTO ↔ entity ↔ model at the boundary; DTOs and entities never leave the data layer.
- Catch the specific exceptions the source throws. If a catch-all is unavoidable, rethrow `CancellationException` first.
- Don't decide "online" with a connectivity check before calling; call and handle the failure. Use a `NetworkMonitor` flow only for UI hints.

## Room

```kotlin
@Entity(tableName = "items")
data class ItemEntity(@PrimaryKey val id: String, val name: String, @ColumnInfo(name = "updated_at") val updatedAt: Long)

@Dao
interface ItemDao {
    @Query("SELECT * FROM items ORDER BY updated_at DESC") fun observeAll(): Flow<List<ItemEntity>>
    @Upsert suspend fun upsert(item: ItemEntity)
    @Query("DELETE FROM items") suspend fun clear()
    @Upsert suspend fun upsertAll(items: List<ItemEntity>)
    @Transaction suspend fun replaceAll(items: List<ItemEntity>) { clear(); upsertAll(items) }
}

@Database(entities = [ItemEntity::class], version = 2, exportSchema = true,
    autoMigrations = [AutoMigration(from = 1, to = 2)])
abstract class AppDatabase : RoomDatabase() { abstract fun itemDao(): ItemDao }
```

- `exportSchema = true` and commit the schema JSON; test every migration with `MigrationTestHelper`.
- Prefer `AutoMigration`; write a manual `Migration` for renames/splits. Never ship `fallbackToDestructiveMigration()` for user data.
- Observed queries return `Flow`; writes are `suspend`. Room runs them off the main thread.
- Room KSP processor (no kapt on AGP 9).

## DataStore

- Preferences DataStore for small key/value settings; Proto DataStore for typed settings objects.
- One instance per file per process (`by preferencesDataStore(name)` at top level, or a DI singleton).
- Read as `Flow`; catch `IOException` in `.catch { emit(emptyPreferences()) }` only — rethrow anything else.
- Migrating from SharedPreferences: `SharedPreferencesMigration`, and review it with `persisted-state-review.md`.

## Network client

```kotlin
@Provides @Singleton
fun okHttp(): OkHttpClient = OkHttpClient.Builder()
    .addInterceptor(HttpLoggingInterceptor().apply {
        level = if (BuildConfig.DEBUG) HttpLoggingInterceptor.Level.BODY else HttpLoggingInterceptor.Level.NONE
    })
    .build()

@Provides @Singleton
fun retrofit(client: OkHttpClient, json: Json): Retrofit = Retrofit.Builder()
    .baseUrl(BuildConfig.API_BASE_URL)
    .client(client)
    .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
    .build()
```

- `Json { ignoreUnknownKeys = true }` so new server fields don't crash old clients.
- No body logging in release (tokens, PII).
- Ktor projects: same rules — one client, a single `safeCall`-style mapper, typed errors.

## Background work (WorkManager)

```kotlin
@HiltWorker
class SyncWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val sync: SyncManager,
) : CoroutineWorker(context, params) {
    override suspend fun doWork(): Result = when (sync.processQueue()) {
        SyncOutcome.Done -> Result.success()
        SyncOutcome.Retryable -> if (runAttemptCount < MAX_ATTEMPTS) Result.retry() else Result.failure()
        SyncOutcome.Fatal -> Result.failure()
    }
}
```

- `SyncManager` returns an outcome instead of throwing; the worker doesn't wrap `doWork` in `catch (e: Exception)`. A cancelled worker must stay cancelled.
- `enqueueUniquePeriodicWork(…, ExistingPeriodicWorkPolicy.KEEP, …)` with `NetworkType.CONNECTED` and exponential backoff.
- Expedited/one-off work for user-triggered sync; periodic work minimum is 15 minutes.

## Paging and images

- Paging 3: `Pager(PagingConfig(pageSize = 20)) { dao.pagingSource() }.flow.cachedIn(viewModelScope)`; in Compose, `collectAsLazyPagingItems()` and `items(count = items.itemCount, key = items.itemKey { it.id })`.
- Images: Coil `AsyncImage` with `contentDescription` per `accessibility.md`.

## Third-party SDKs

Wrap each SDK behind an interface in the data layer, inject the wrapper, and fake it in tests. SDK types never reach ViewModels.

# Architecture Blueprint: Social Feed Feature

```yaml
Written by: android-architect
Timestamp: 2026-02-13T10:30:00Z
Pipeline: feature-build
```

## Summary

Social feed feature following offline-first architecture with infinite scroll, pull-to-refresh, and optimistic UI updates. Uses StateFlow for reactive state management, Hilt for DI, and follows established modular architecture with feature/core separation.

**Scope:**
- Display feed of posts with author info, timestamps, like counts
- Infinite scroll with pagination (20 posts per page)
- Pull-to-refresh for manual sync
- Like/unlike posts with optimistic updates
- Offline viewing of cached posts

**Out of Scope:**
- Post creation (separate feature)
- Comments (separate feature)
- Share functionality (future enhancement)

**Impact:** Adds new feature module, new Room entities, new API endpoints, new navigation route.

## Decisions

### Decision 1: State Management Pattern

**Context:** Feed requires reactive updates for likes, new posts, and pagination state.

**Options Considered:**
1. LiveData - Simple, team familiar, but not Kotlin-first
2. StateFlow - Modern, performant, better composition
3. Flow (raw) - Most flexible but requires manual state holding

**Decision:** StateFlow with sealed interface for UI state

**Rationale:**
- Codebase is transitioning to StateFlow (current split: 45% StateFlow, 55% LiveData)
- New features should use StateFlow per team guidelines
- Better composition with combiners and operators
- Type-safe state management

**Trade-offs:**
- ✅ Kotlin-first, better performance
- ✅ Easier testing with Turbine
- ⚠️ Team needs to learn StateFlow patterns (but already in progress)

### Decision 2: Pagination Strategy

**Context:** Feed could have thousands of posts, need efficient pagination.

**Decision:** Use Paging 3 library with RemoteMediator for offline-first pagination

**Rationale:**
- Paging 3 handles infinite scroll automatically
- RemoteMediator enables offline-first pattern
- Integrates with Room for local caching
- Standard Android best practice

### Decision 3: Module Placement

**Context:** Social feed is a major feature - should it be a separate module?

**Decision:** Yes - create `feature:feed` module with api/impl split

**Rationale:**
- Large feature with its own domain logic
- Independent development and testing
- Clear navigation boundary (FeedRoute in api module)
- Follows existing feature module convention

### Decision 4: Offline-First Sync

**Context:** Users must view feed offline with cached posts.

**Decision:** Room as source of truth, WorkManager for background sync every 15 minutes

**Rationale:**
- Consistent with existing repository pattern (100% of repos use offline-first)
- WorkManager handles constraints (network, battery)
- User sees immediate updates (optimistic UI)

## Artifacts Created

### Module Structure

```
feature/
└── feed/
    ├── api/
    │   └── FeedRoute.kt          # Navigation route
    └── impl/
        ├── FeedViewModel.kt      # State management
        ├── FeedScreen.kt         # Compose UI
        └── PostCard.kt           # Reusable post component

core/
├── data/
│   ├── FeedRepository.kt         # Repository interface
│   └── OfflineFirstFeedRepository.kt  # Implementation
├── database/
│   ├── PostEntity.kt             # Room entity
│   ├── PostRemoteKey.kt          # Paging 3 remote keys
│   └── FeedDao.kt                # Room DAO
├── network/
│   └── FeedApiService.kt         # Retrofit API
└── model/
    ├── Post.kt                   # Domain model
    └── Author.kt                 # Domain model (reused)
```

### Data Flow

```
User Action (scroll/refresh)
    ↓
FeedScreen (Compose)
    ↓
FeedViewModel
    ↓
FeedRepository
    ↓
Paging 3 + RemoteMediator
    ↓
Room (cache) ←→ Retrofit (network)
    ↓
Flow<PagingData<Post>>
    ↓
collectAsStateWithLifecycle()
    ↓
LazyColumn in FeedScreen
```

### State Management Pattern

```kotlin
// UI State
sealed interface FeedUiState {
    data object Loading : FeedUiState
    data class Error(val message: String) : FeedUiState
    data class Success(
        val posts: Flow<PagingData<Post>>,
        val isRefreshing: Boolean = false
    ) : FeedUiState
}

// ViewModel
@HiltViewModel
class FeedViewModel @Inject constructor(
    private val feedRepository: FeedRepository
) : ViewModel() {

    val uiState: StateFlow<FeedUiState> = feedRepository.posts
        .map { pagingData -> FeedUiState.Success(posts = flowOf(pagingData)) }
        .catch { emit(FeedUiState.Error(it.message ?: "Unknown error")) }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = FeedUiState.Loading
        )

    fun refresh() { /* Paging 3 handles this */ }

    fun likePost(postId: String) {
        viewModelScope.launch {
            feedRepository.likePost(postId)
        }
    }
}
```

### Repository Pattern

```kotlin
interface FeedRepository {
    val posts: Flow<PagingData<Post>>
    suspend fun likePost(postId: String)
    suspend fun refresh()
}

class OfflineFirstFeedRepository @Inject constructor(
    private val feedDao: FeedDao,
    private val feedApi: FeedApiService
) : FeedRepository {

    override val posts: Flow<PagingData<Post>> = Pager(
        config = PagingConfig(pageSize = 20, prefetchDistance = 5),
        remoteMediator = FeedRemoteMediator(feedDao, feedApi),
        pagingSourceFactory = { feedDao.getPosts() }
    ).flow

    override suspend fun likePost(postId: String) {
        // Optimistic update
        feedDao.updateLikeCount(postId, increment = 1)
        try {
            feedApi.likePost(postId)
        } catch (e: Exception) {
            // Rollback on failure
            feedDao.updateLikeCount(postId, increment = -1)
            throw e
        }
    }
}
```

## Next Steps

### For gradle-build-engineer
1. Create `feature:feed` module structure (api + impl)
2. Apply convention plugins:
   - `feature.api` for api module
   - `feature.impl` for impl module (includes Compose, Hilt, Room)
3. Add dependencies to version catalog:
   - Paging 3: `androidx.paging:paging-runtime-ktx:3.3.5`
   - Paging Compose: `androidx.paging:paging-compose:3.3.5`
   - WorkManager: `androidx.work:work-runtime-ktx:2.10.0`
4. Configure api module dependencies: navigation only
5. Configure impl module dependencies: Compose, Hilt, Paging, Room access

**Can run in parallel with android-developer** (developer doesn't need build files to start designing interfaces)

### For android-developer
1. Implement `FeedRepository` interface with offline-first pattern
2. Create `OfflineFirstFeedRepository` with Paging 3 RemoteMediator
3. Implement `FeedViewModel` with StateFlow<FeedUiState>
4. Create Room entities:
   - `PostEntity` (id, authorId, content, timestamp, likeCount, isLiked)
   - `PostRemoteKey` (postId, prevKey, nextKey) for Paging 3
5. Create `FeedDao` with:
   - `fun getPosts(): PagingSource<Int, PostEntity>`
   - `suspend fun updateLikeCount(postId: String, increment: Int)`
   - `suspend fun insertPosts(posts: List<PostEntity>)`
6. Create `FeedApiService` with:
   - `suspend fun getPosts(page: Int, pageSize: Int): FeedResponse`
   - `suspend fun likePost(postId: String): LikeResponse`
7. Document all interfaces in implementation-report.md

**Blocked by:** None (can start immediately with blueprint)

### For compose-expert
1. Wait for android-developer to complete FeedViewModel and provide state types
2. Read implementation-report.md for ViewModel interface and state types
3. Implement `FeedRoute` (stateful, ViewModel injection)
4. Implement `FeedScreen` (stateless, receives UiState)
5. Create `PostCard` composable for feed items
6. Add pull-to-refresh with Material 3 components
7. Add infinite scroll with Paging 3 Compose integration
8. Include accessibility semantics for screen readers
9. Document UI components and semantic properties in ui-report.md

**Blocked by:** android-developer (needs FeedViewModel and state types)

### For android-testing-specialist
1. Read implementation-report.md and ui-report.md
2. Create test doubles:
   - `TestFeedRepository` with MutableStateFlow for controllable state
   - Test PagingData factory utilities
3. Create ViewModel unit tests:
   - Test state transitions (Loading → Success → Error)
   - Test likePost optimistic updates
   - Test Paging 3 flow emissions with Turbine
   - Target 80%+ coverage
4. Create Compose UI tests:
   - Test PostCard renders correctly
   - Test pull-to-refresh interaction
   - Test infinite scroll loads more items
   - Test semantic properties for accessibility
5. Document test coverage and any testability issues in test-report.md

**Blocked by:** android-developer (unit tests), compose-expert (UI tests)

## Constraints

### Must Follow
- **StateFlow only** (not LiveData) - new feature, follow modern pattern
- **Offline-first** - Room as source of truth, network updates Room
- **Hilt DI** - matches 100% of existing codebase
- **Feature module independence** - no feature-to-feature dependencies
- **Paging 3** - for infinite scroll (don't implement manual pagination)
- **Material 3** - for UI components
- **Accessibility** - all UI must have semantic properties

### Must Not
- Do NOT use LiveData (StateFlow required)
- Do NOT introduce new DI frameworks (Hilt only)
- Do NOT create feature-to-feature dependencies (core modules only)
- Do NOT skip offline support (all features must work offline)
- Do NOT use deprecated APIs (no AsyncListDiffer, use Paging 3)
- Do NOT implement manual pagination (Paging 3 library handles this)

### Naming Conventions
- ViewModels: `*ViewModel` (e.g., `FeedViewModel`)
- Repositories: `*Repository` (e.g., `FeedRepository`)
- Screens: `*Screen` (e.g., `FeedScreen`)
- Routes: `*Route` (e.g., `FeedRoute`)
- Entities: `*Entity` (e.g., `PostEntity`)
- UI State: `*UiState` (e.g., `FeedUiState`)

## Pattern Detection Results

```
State Management:
- LiveData: 47 ViewModels (55%)
- StateFlow: 38 ViewModels (45%)
→ Decision: Use StateFlow (new features adopt modern pattern, migration in progress)

DI Framework:
- Hilt: 100% (all modules)
→ Decision: Use Hilt (unanimous)

Offline Strategy:
- Offline-first: 12 repositories (100%)
→ Decision: Use offline-first (established pattern)

UI Framework:
- Compose: 72% of screens
- XML: 28% of screens
→ Decision: Use Compose (majority pattern)
```

## Risk Assessment

### Risk 1: API Pagination Format
**Risk:** API might not return pagination metadata (total pages, has more, etc.)

**Mitigation:**
- Use Paging 3's "load until empty" strategy
- If empty page returned, assume end of feed
- Document API contract requirements in implementation-report.md

### Risk 2: Large Feed Performance
**Risk:** Feed with thousands of posts could cause memory issues

**Mitigation:**
- Paging 3 automatically manages memory (loads pages, drops old pages)
- Room only caches recent posts (configurable limit)
- LazyColumn in Compose recomposes efficiently

### Risk 3: Optimistic Like Updates
**Risk:** Like action could fail network call, leaving inconsistent state

**Mitigation:**
- Rollback logic in repository (increment +1, then -1 on failure)
- Error state shown to user on failure
- Retry queue for failed likes (WorkManager)

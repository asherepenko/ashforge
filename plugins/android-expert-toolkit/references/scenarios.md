# End-to-End Scenarios

Detailed walkthrough scenarios demonstrating multi-agent orchestration, pattern detection, Decision Council usage, and parallel execution for Android development with Claude Code.

Each scenario shows the exact user request, agent sequence, code produced at each step, and estimated timeline.

## When to use

Read this reference when learning how multi-agent orchestration works in practice, onboarding to the toolkit, or composing a custom pipeline. Demonstrates real agent sequences from greenfield feature through testing. Not needed for routine single-agent tasks.

---

## Scenario 1: Social Feed Feature (Greenfield)

Full agent orchestration from architecture design through testing for a new social feed feature with posts, likes, and infinite scrolling.

### User Request

```
"Build a social feed feature with posts, likes, and infinite scrolling.
Posts come from a REST API and should work offline. The feed should show
author avatar, post text, like count, and a like button. Use the standard
module structure with API/Impl split."
```

### Timeline Overview

```
Hour 0-1:    android-architect designs architecture
Hour 0-1:    gradle-build-engineer sets up modules (parallel after design)
Hour 1-3:    android-developer implements data layer
Hour 2-4:    compose-expert implements UI (parallel after models ready)
Hour 3-5:    android-testing-specialist writes tests (parallel after impl)
Hour 5:      Integration verification

Total: ~5 hours (with parallel execution: ~4 hours)
```

### Step 1: android-architect Designs Architecture

**Agent**: android-architect (opus model)
**Input**: User request + existing project structure
**Action**: Analyze requirements, design module structure, define data flow

The architect first scans the existing codebase to understand current patterns.

```
# Pattern detection: What modules exist already?
Glob: **/build.gradle.kts
Grep: pattern="plugins.*android" in build.gradle.kts files

# Check existing navigation patterns
Grep: pattern="@Serializable" glob="**/*.kt"
Grep: pattern="NavGraphBuilder" glob="**/*.kt"

# Check existing repository patterns
Grep: pattern="interface.*Repository" glob="**/*.kt"
```

**Output**: Architecture blueprint document.

```
## Social Feed Architecture Blueprint

### Module Structure
feature/
  feed/
    api/        -> FeedRoute, FeedNavigation (navigation contract)
    impl/       -> FeedViewModel, FeedScreen, internal logic

### New Core Additions
core/model     -> Post, Author, LikeStatus (add to existing module)
core/data      -> PostRepository interface (add to existing module)
core/database  -> PostEntity, PostDao (add to existing module)
core/network   -> FeedApiService (add to existing module)

### Data Flow
FeedApiService -> PostRepository (offline-first) -> FeedViewModel -> FeedScreen
                  PostDao (Room) <-/

### Data Models (core:model)
- Post(id, authorId, authorName, authorAvatarUrl, text, likeCount, isLikedByUser, createdAt)
- FeedPage(posts: List<Post>, nextCursor: String?, hasMore: Boolean)

### Repository Interface (core:data)
- PostRepository
  - val feedFlow: Flow<List<Post>>
  - suspend fun loadMore(cursor: String?)
  - suspend fun toggleLike(postId: String)
  - suspend fun refresh()

### UI State (feature:feed:impl)
- FeedUiState: Loading | Error(message) | Success(posts, isLoadingMore, hasMore)

### Dependency Graph
feature:feed:impl -> feature:feed:api
feature:feed:impl -> core:data, core:model, core:designsystem
core:data         -> core:model, core:database, core:network
```

**Handoff**: "The architecture is ready. I recommend having the gradle-build-engineer set up the feature:feed:api and feature:feed:impl modules, then having the android-developer implement the data layer starting with core:model additions."

### Step 2: gradle-build-engineer Sets Up Modules

**Agent**: gradle-build-engineer (sonnet model)
**Input**: Architecture blueprint with module dependency graph
**Action**: Create module directories, build.gradle.kts files, apply convention plugins

```kotlin
// feature/feed/api/build.gradle.kts
plugins {
    id("com.example.android.feature.api")
}

android {
    namespace = "com.example.feature.feed.api"
}

dependencies {
    implementation(projects.core.model)
}
```

```kotlin
// feature/feed/impl/build.gradle.kts
plugins {
    id("com.example.android.feature.impl")
    id("com.example.android.compose")
    id("com.example.hilt")
}

android {
    namespace = "com.example.feature.feed.impl"
}

dependencies {
    implementation(projects.feature.feed.api)
    implementation(projects.core.data)
    implementation(projects.core.model)
    implementation(projects.core.designsystem)
}
```

```kotlin
// settings.gradle.kts additions
include(":feature:feed:api")
include(":feature:feed:impl")
```

**Output**: Module build files created, settings.gradle.kts updated, Gradle sync verified.

**Handoff**: "Modules are configured. The android-developer can begin implementation."

### Step 3: android-developer Implements Data Layer

**Agent**: android-developer (sonnet model)
**Input**: Architecture blueprint, module structure
**Action**: Implement models, entities, DAOs, API service, repository

**Data Models (core:model):**

```kotlin
// core/model/src/main/kotlin/com/example/core/model/Post.kt
data class Post(
    val id: String,
    val authorId: String,
    val authorName: String,
    val authorAvatarUrl: String,
    val text: String,
    val likeCount: Int,
    val isLikedByUser: Boolean,
    val createdAt: Instant,
)
```

**Room Entity (core:database):**

```kotlin
// core/database/src/main/kotlin/com/example/core/database/model/PostEntity.kt
@Entity(tableName = "posts")
data class PostEntity(
    @PrimaryKey val id: String,
    val authorId: String,
    val authorName: String,
    val authorAvatarUrl: String,
    val text: String,
    val likeCount: Int,
    val isLikedByUser: Boolean,
    val createdAt: Long,
    val feedOrder: Int,
)

fun PostEntity.asExternalModel() = Post(
    id = id,
    authorId = authorId,
    authorName = authorName,
    authorAvatarUrl = authorAvatarUrl,
    text = text,
    likeCount = likeCount,
    isLikedByUser = isLikedByUser,
    createdAt = Instant.fromEpochMilliseconds(createdAt),
)
```

**Room DAO (core:database):**

```kotlin
// core/database/src/main/kotlin/com/example/core/database/dao/PostDao.kt
@Dao
interface PostDao {
    @Query("SELECT * FROM posts ORDER BY feedOrder ASC")
    fun observePosts(): Flow<List<PostEntity>>

    @Upsert
    suspend fun upsertPosts(posts: List<PostEntity>)

    @Query("UPDATE posts SET isLikedByUser = :liked, likeCount = likeCount + :delta WHERE id = :postId")
    suspend fun updateLikeStatus(postId: String, liked: Boolean, delta: Int)

    @Query("DELETE FROM posts")
    suspend fun clearAll()
}
```

**API Service (core:network):**

```kotlin
// core/network/src/main/kotlin/com/example/core/network/FeedApiService.kt
interface FeedApiService {
    @GET("feed")
    suspend fun getFeed(
        @Query("cursor") cursor: String? = null,
        @Query("limit") limit: Int = 20,
    ): NetworkFeedResponse

    @POST("posts/{postId}/like")
    suspend fun likePost(@Path("postId") postId: String): NetworkLikeResponse

    @DELETE("posts/{postId}/like")
    suspend fun unlikePost(@Path("postId") postId: String): NetworkLikeResponse
}

@Serializable
data class NetworkFeedResponse(
    val posts: List<NetworkPost>,
    val nextCursor: String?,
    val hasMore: Boolean,
)

@Serializable
data class NetworkPost(
    val id: String,
    val authorId: String,
    val authorName: String,
    val authorAvatarUrl: String,
    val text: String,
    val likeCount: Int,
    val isLikedByUser: Boolean,
    val createdAt: Long,
)
```

**Repository Interface (core:data):**

```kotlin
// core/data/src/main/kotlin/com/example/core/data/repository/PostRepository.kt
interface PostRepository {
    val feedFlow: Flow<List<Post>>
    suspend fun loadMore(cursor: String?)
    suspend fun toggleLike(postId: String)
    suspend fun refresh()
}
```

**Offline-First Repository Implementation (core:data):**

```kotlin
// core/data/src/main/kotlin/com/example/core/data/repository/OfflineFirstPostRepository.kt
internal class OfflineFirstPostRepository @Inject constructor(
    private val postDao: PostDao,
    private val feedApiService: FeedApiService,
    @Dispatcher(IO) private val ioDispatcher: CoroutineDispatcher,
) : PostRepository {

    private var nextCursor: String? = null
    private var hasMore: Boolean = true

    override val feedFlow: Flow<List<Post>> =
        postDao.observePosts().map { entities ->
            entities.map(PostEntity::asExternalModel)
        }

    override suspend fun refresh() = withContext(ioDispatcher) {
        val response = feedApiService.getFeed(cursor = null)
        nextCursor = response.nextCursor
        hasMore = response.hasMore
        postDao.clearAll()
        postDao.upsertPosts(response.posts.mapIndexed { index, post ->
            post.asEntity(feedOrder = index)
        })
    }

    override suspend fun loadMore(cursor: String?) = withContext(ioDispatcher) {
        if (!hasMore) return@withContext
        val effectiveCursor = cursor ?: nextCursor ?: return@withContext
        val response = feedApiService.getFeed(cursor = effectiveCursor)
        nextCursor = response.nextCursor
        hasMore = response.hasMore
        val currentCount = postDao.observePosts().first().size
        postDao.upsertPosts(response.posts.mapIndexed { index, post ->
            post.asEntity(feedOrder = currentCount + index)
        })
    }

    override suspend fun toggleLike(postId: String) = withContext(ioDispatcher) {
        val posts = postDao.observePosts().first()
        val post = posts.find { it.id == postId } ?: return@withContext
        val nowLiked = !post.isLikedByUser
        val delta = if (nowLiked) 1 else -1

        // Optimistic update
        postDao.updateLikeStatus(postId, nowLiked, delta)

        try {
            if (nowLiked) feedApiService.likePost(postId)
            else feedApiService.unlikePost(postId)
        } catch (e: Exception) {
            // Revert optimistic update
            postDao.updateLikeStatus(postId, !nowLiked, -delta)
        }
    }
}
```

**Hilt Module (core:data):**

```kotlin
@Module
@InstallIn(SingletonComponent::class)
internal abstract class PostRepositoryModule {
    @Binds
    abstract fun bindsPostRepository(
        impl: OfflineFirstPostRepository,
    ): PostRepository
}
```

**Handoff**: "Implementation complete for the data layer. Have the compose-expert implement the feed UI screens, and the android-testing-specialist create tests for the repository and ViewModel."

### Step 4: compose-expert Implements UI (Parallel with Step 5)

**Agent**: compose-expert (sonnet model)
**Input**: UI state definitions, ViewModel pattern, data models
**Action**: Implement FeedViewModel, FeedRoute, FeedScreen with infinite scroll

**ViewModel (feature:feed:impl):**

```kotlin
@HiltViewModel
class FeedViewModel @Inject constructor(
    private val postRepository: PostRepository,
) : ViewModel() {

    private val isLoadingMore = MutableStateFlow(false)
    private val hasMore = MutableStateFlow(true)

    val uiState: StateFlow<FeedUiState> = combine(
        postRepository.feedFlow,
        isLoadingMore,
        hasMore,
    ) { posts, loadingMore, more ->
        FeedUiState.Success(
            posts = posts,
            isLoadingMore = loadingMore,
            hasMore = more,
        )
    }.catch { emit(FeedUiState.Error(it.message ?: "Failed to load feed")) }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = FeedUiState.Loading,
        )

    init {
        viewModelScope.launch {
            try {
                postRepository.refresh()
            } catch (e: Exception) {
                // Initial load failure handled by uiState
            }
        }
    }

    fun onAction(action: FeedAction) {
        when (action) {
            is FeedAction.ToggleLike -> viewModelScope.launch {
                postRepository.toggleLike(action.postId)
            }
            FeedAction.LoadMore -> viewModelScope.launch {
                isLoadingMore.value = true
                try {
                    postRepository.loadMore(cursor = null)
                } finally {
                    isLoadingMore.value = false
                }
            }
            FeedAction.Refresh -> viewModelScope.launch {
                postRepository.refresh()
            }
        }
    }
}

sealed interface FeedUiState {
    data object Loading : FeedUiState
    data class Error(val message: String) : FeedUiState
    data class Success(
        val posts: List<Post>,
        val isLoadingMore: Boolean,
        val hasMore: Boolean,
    ) : FeedUiState
}

sealed interface FeedAction {
    data class ToggleLike(val postId: String) : FeedAction
    data object LoadMore : FeedAction
    data object Refresh : FeedAction
}
```

**Route and Screen (feature:feed:impl):**

```kotlin
@Composable
fun FeedRoute(
    modifier: Modifier = Modifier,
    viewModel: FeedViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    FeedScreen(
        uiState = uiState,
        onAction = viewModel::onAction,
        modifier = modifier,
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FeedScreen(
    uiState: FeedUiState,
    onAction: (FeedAction) -> Unit,
    modifier: Modifier = Modifier,
) {
    val pullRefreshState = rememberPullToRefreshState()

    PullToRefreshBox(
        isRefreshing = uiState is FeedUiState.Loading,
        onRefresh = { onAction(FeedAction.Refresh) },
        state = pullRefreshState,
        modifier = modifier.fillMaxSize(),
    ) {
        when (uiState) {
            FeedUiState.Loading -> LoadingIndicator()
            is FeedUiState.Error -> ErrorState(
                message = uiState.message,
                onRetry = { onAction(FeedAction.Refresh) },
            )
            is FeedUiState.Success -> FeedContent(
                posts = uiState.posts,
                isLoadingMore = uiState.isLoadingMore,
                hasMore = uiState.hasMore,
                onAction = onAction,
            )
        }
    }
}

@Composable
private fun FeedContent(
    posts: List<Post>,
    isLoadingMore: Boolean,
    hasMore: Boolean,
    onAction: (FeedAction) -> Unit,
    modifier: Modifier = Modifier,
) {
    val listState = rememberLazyListState()

    // Trigger load more when approaching end of list
    val shouldLoadMore by remember {
        derivedStateOf {
            val lastVisibleItem = listState.layoutInfo.visibleItemsInfo.lastOrNull()
                ?: return@derivedStateOf false
            lastVisibleItem.index >= listState.layoutInfo.totalItemsCount - 5
        }
    }

    LaunchedEffect(shouldLoadMore) {
        if (shouldLoadMore && hasMore && !isLoadingMore) {
            onAction(FeedAction.LoadMore)
        }
    }

    LazyColumn(
        state = listState,
        modifier = modifier.fillMaxSize(),
        contentPadding = PaddingValues(vertical = 8.dp),
    ) {
        items(
            items = posts,
            key = { it.id },
        ) { post ->
            PostCard(
                post = post,
                onLikeClick = { onAction(FeedAction.ToggleLike(post.id)) },
                modifier = Modifier.animateItem(),
            )
        }

        if (isLoadingMore) {
            item {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    contentAlignment = Alignment.Center,
                ) {
                    CircularProgressIndicator()
                }
            }
        }
    }
}

@Composable
private fun PostCard(
    post: Post,
    onLikeClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 4.dp),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            // Author row
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.fillMaxWidth(),
            ) {
                AsyncImage(
                    model = post.authorAvatarUrl,
                    contentDescription = "Avatar for ${post.authorName}",
                    modifier = Modifier
                        .size(40.dp)
                        .clip(CircleShape),
                    contentScale = ContentScale.Crop,
                )
                Spacer(modifier = Modifier.width(12.dp))
                Text(
                    text = post.authorName,
                    style = MaterialTheme.typography.titleSmall,
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Post text
            Text(
                text = post.text,
                style = MaterialTheme.typography.bodyLarge,
            )

            Spacer(modifier = Modifier.height(8.dp))

            // Like button row
            Row(verticalAlignment = Alignment.CenterVertically) {
                IconButton(onClick = onLikeClick) {
                    Icon(
                        imageVector = if (post.isLikedByUser) {
                            Icons.Filled.Favorite
                        } else {
                            Icons.Outlined.FavoriteBorder
                        },
                        contentDescription = if (post.isLikedByUser) "Unlike" else "Like",
                        tint = if (post.isLikedByUser) {
                            MaterialTheme.colorScheme.error
                        } else {
                            MaterialTheme.colorScheme.onSurfaceVariant
                        },
                    )
                }
                Text(
                    text = "${post.likeCount}",
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}
```

**Navigation (feature:feed:api):**

```kotlin
// feature/feed/api/src/main/kotlin/.../FeedNavigation.kt
@Serializable
object FeedRoute

fun NavGraphBuilder.feedGraph() {
    composable<FeedRoute> {
        FeedRoute()
    }
}
```

### Step 5: android-testing-specialist Writes Tests (Parallel with Step 4)

**Agent**: android-testing-specialist (sonnet model)
**Input**: Repository interface, ViewModel, data models
**Action**: Create test doubles, write ViewModel and repository tests

**Test Double (core:testing):**

```kotlin
class TestPostRepository : PostRepository {
    private val _posts = MutableStateFlow<List<Post>>(emptyList())
    override val feedFlow: Flow<List<Post>> = _posts

    // Test control methods
    fun setPosts(posts: List<Post>) {
        _posts.value = posts
    }

    fun addPost(post: Post) {
        _posts.value = _posts.value + post
    }

    // Tracking
    var refreshCallCount = 0; private set
    var loadMoreCallCount = 0; private set
    var lastToggledPostId: String? = null; private set

    private var shouldThrowOnRefresh = false
    fun setRefreshError(shouldThrow: Boolean) {
        shouldThrowOnRefresh = shouldThrow
    }

    override suspend fun refresh() {
        if (shouldThrowOnRefresh) throw IOException("Network error")
        refreshCallCount++
    }

    override suspend fun loadMore(cursor: String?) {
        loadMoreCallCount++
    }

    override suspend fun toggleLike(postId: String) {
        lastToggledPostId = postId
        _posts.value = _posts.value.map { post ->
            if (post.id == postId) {
                post.copy(
                    isLikedByUser = !post.isLikedByUser,
                    likeCount = post.likeCount + if (post.isLikedByUser) -1 else 1,
                )
            } else post
        }
    }

    fun reset() {
        _posts.value = emptyList()
        refreshCallCount = 0
        loadMoreCallCount = 0
        lastToggledPostId = null
        shouldThrowOnRefresh = false
    }
}
```

**ViewModel Tests:**

```kotlin
class FeedViewModelTest {
    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()

    private lateinit var repository: TestPostRepository
    private lateinit var viewModel: FeedViewModel

    private val testPosts = listOf(
        Post(
            id = "1",
            authorId = "a1",
            authorName = "Alice",
            authorAvatarUrl = "https://example.com/alice.jpg",
            text = "Hello world",
            likeCount = 5,
            isLikedByUser = false,
            createdAt = Clock.System.now(),
        ),
        Post(
            id = "2",
            authorId = "a2",
            authorName = "Bob",
            authorAvatarUrl = "https://example.com/bob.jpg",
            text = "Good morning",
            likeCount = 3,
            isLikedByUser = true,
            createdAt = Clock.System.now(),
        ),
    )

    @Before
    fun setup() {
        repository = TestPostRepository()
        viewModel = FeedViewModel(repository)
    }

    @Test
    fun `initial state is loading`() = runTest {
        viewModel.uiState.test {
            assertThat(awaitItem()).isEqualTo(FeedUiState.Loading)
            cancelAndIgnoreRemainingEvents()
        }
    }

    @Test
    fun `emits success when posts available`() = runTest {
        repository.setPosts(testPosts)

        viewModel.uiState.test {
            // Skip loading
            skipItems(1)

            val state = awaitItem() as FeedUiState.Success
            assertThat(state.posts).hasSize(2)
            assertThat(state.posts[0].authorName).isEqualTo("Alice")
        }
    }

    @Test
    fun `toggle like updates post state`() = runTest {
        repository.setPosts(testPosts)

        viewModel.uiState.test {
            skipItems(1)
            awaitItem() // Initial success

            viewModel.onAction(FeedAction.ToggleLike("1"))

            val updated = awaitItem() as FeedUiState.Success
            assertThat(updated.posts[0].isLikedByUser).isTrue()
            assertThat(updated.posts[0].likeCount).isEqualTo(6)
        }
    }

    @Test
    fun `refresh delegates to repository`() = runTest {
        viewModel.onAction(FeedAction.Refresh)
        advanceUntilIdle()

        assertThat(repository.refreshCallCount).isGreaterThan(0)
    }

    @Test
    fun `load more delegates to repository`() = runTest {
        viewModel.onAction(FeedAction.LoadMore)
        advanceUntilIdle()

        assertThat(repository.loadMoreCallCount).isEqualTo(1)
    }
}
```

**Compose UI Tests:**

```kotlin
class FeedScreenTest {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun feedScreen_loadingState_showsIndicator() {
        composeTestRule.setContent {
            FeedScreen(
                uiState = FeedUiState.Loading,
                onAction = {},
            )
        }

        composeTestRule.onNodeWithTag("loading").assertIsDisplayed()
    }

    @Test
    fun feedScreen_successState_showsPosts() {
        composeTestRule.setContent {
            FeedScreen(
                uiState = FeedUiState.Success(
                    posts = listOf(
                        Post(
                            id = "1",
                            authorId = "a1",
                            authorName = "Alice",
                            authorAvatarUrl = "",
                            text = "Hello world",
                            likeCount = 5,
                            isLikedByUser = false,
                            createdAt = Clock.System.now(),
                        ),
                    ),
                    isLoadingMore = false,
                    hasMore = true,
                ),
                onAction = {},
            )
        }

        composeTestRule.onNodeWithText("Alice").assertIsDisplayed()
        composeTestRule.onNodeWithText("Hello world").assertIsDisplayed()
        composeTestRule.onNodeWithText("5").assertIsDisplayed()
    }

    @Test
    fun feedScreen_errorState_showsRetryButton() {
        composeTestRule.setContent {
            FeedScreen(
                uiState = FeedUiState.Error("Network error"),
                onAction = {},
            )
        }

        composeTestRule.onNodeWithText("Network error").assertIsDisplayed()
        composeTestRule.onNodeWithText("Retry").assertIsDisplayed()
    }
}
```

### Step 6: Integration Verification

All agents verify their outputs work together:
- Gradle build succeeds with new modules
- ViewModel properly connects to repository
- UI renders all states correctly
- Tests pass with >80% coverage on business logic
- Navigation integrates with app-level nav graph

---

## Scenario 2: LiveData to StateFlow Migration

Pattern detection, 80/20 analysis, and Decision Council deliberation for migrating an existing codebase from LiveData to StateFlow.

### User Request

```
"Our app has grown to 30+ ViewModels and we want to modernize our state
management. Most ViewModels use LiveData but some newer ones already use
StateFlow. Should we migrate, and if so, what's the plan?"
```

### Step 1: Pattern Detection

**Agent**: android-architect (opus model)
**Action**: Scan codebase to quantify the current state

```
# Count LiveData usage across the codebase
Grep: pattern="LiveData" glob="**/*.kt" output_mode="count"
Grep: pattern="MutableLiveData" glob="**/*.kt" output_mode="count"
Grep: pattern="StateFlow" glob="**/*.kt" output_mode="count"
Grep: pattern="MutableStateFlow" glob="**/*.kt" output_mode="count"

# Find all ViewModels
Grep: pattern="class.*ViewModel.*:" glob="**/*.kt" output_mode="content"

# Check which ViewModels use which pattern
Grep: pattern="LiveData|StateFlow" glob="**/viewmodel/**/*.kt" output_mode="content"
Grep: pattern="LiveData|StateFlow" glob="**/ui/**/*.kt" output_mode="content"

# Check observation patterns in UI
Grep: pattern="observeAsState|collectAsStateWithLifecycle|observe\(" glob="**/*.kt" output_mode="content"

# Check for sealed UI state interfaces (modern pattern)
Grep: pattern="sealed interface.*UiState" glob="**/*.kt" output_mode="content"

# Check testing patterns
Grep: pattern="getOrAwaitValue|Turbine|\.test\s*\{" glob="**/*Test*.kt" output_mode="content"
```

**Pattern Detection Results:**

```
USAGE ANALYSIS
-------------------------------------------------
LiveData references:           247 across 34 files
MutableLiveData:               89 across 31 files
StateFlow references:          42 across 8 files
MutableStateFlow:              18 across 8 files

VIEWMODEL BREAKDOWN
-------------------------------------------------
Total ViewModels:              35
Using LiveData:                27 (77%)
Using StateFlow:               8 (23%)
Using sealed UiState:          6 (17%)

UI OBSERVATION
-------------------------------------------------
observeAsState:                14 calls (Compose + LiveData bridge)
collectAsStateWithLifecycle:   8 calls (Compose + StateFlow)
observe() in Fragments:        19 calls (View system)

TESTING
-------------------------------------------------
getOrAwaitValue (LiveData):    45 test assertions
Turbine (.test {}):            12 test assertions
```

### Step 2: 80/20 Analysis

The architect identifies the highest-impact, lowest-risk migration targets.

```
HIGH-IMPACT VIEWMODELS (Critical user paths)
- LoginViewModel          -> LiveData, 5 observers, 3 tests
- HomeViewModel           -> LiveData, 8 observers, 7 tests
- ProfileViewModel        -> LiveData, 6 observers, 4 tests
- CheckoutViewModel       -> LiveData, 9 observers, 8 tests
- SearchViewModel         -> LiveData, 4 observers, 2 tests

ALREADY MIGRATED (Reference implementations)
- SettingsViewModel       -> StateFlow + sealed UiState
- NotificationsViewModel  -> StateFlow + sealed UiState
- OnboardingViewModel     -> StateFlow + sealed UiState

LOW-RISK STARTING POINTS (Few observers, simple state)
- AboutViewModel          -> LiveData, 1 observer, 1 test
- FaqViewModel            -> LiveData, 1 observer, 0 tests
- TermsViewModel          -> LiveData, 2 observers, 0 tests
```

### Step 3: Decision Council

**Invoked because**: This is a significant migration affecting 27 ViewModels, multiple test files, and the entire team's patterns.

```markdown
## Decision: LiveData to StateFlow Migration Strategy

### Status Quo Advocate's Position:
"27 ViewModels use LiveData consistently. The pattern works and
has zero production issues.

Current usage:
- 77% of ViewModels use LiveData (27/35)
- 247 LiveData references across 34 files
- 45 test assertions use getOrAwaitValue
- 19 Fragment observers using traditional observe()
- Team has 3+ years LiveData experience

Risk assessment:
- Migration touches critical paths (login, checkout, home)
- Rewriting tests risks breaking test coverage
- Fragment-based screens need different observation patterns
- LiveData is NOT deprecated - just in maintenance mode
- Mixed patterns during migration create confusion

If we keep LiveData:
- Zero risk to production stability
- No migration effort (estimated 3-4 weeks)
- Team productivity unaffected
- LiveData is perfectly adequate for the use cases"

### Best Practices Advocate's Position:
"StateFlow is the modern Kotlin-first approach recommended by Google.
8 ViewModels already prove the pattern works in this codebase.

Technical benefits:
- Type-safe null handling (no LiveData null gotchas)
- Better coroutine integration (no asLiveData bridge)
- Cold stream semantics prevent subscription leaks
- Compose-native with collectAsStateWithLifecycle
- Superior testing with Turbine (12 tests already use it)
- Sealed interface UI states eliminate impossible states

Long-term value:
- Google recommends StateFlow for new code (2021+)
- Aligns with Kotlin-first Android direction
- 8 existing StateFlow ViewModels prove feasibility
- Compose migration makes LiveData observation awkward
- New hires expect StateFlow (industry standard)

The 23% already migrated creates an inconsistency
that should be resolved one way or the other."

### Pragmatic Synthesis:
Both perspectives are valid. The existing StateFlow ViewModels
already broke consistency, so pure status quo is not possible.

Constraint analysis:
- Timeline: No hard deadline (modernization initiative)
- Team: 6 developers, 3 senior (familiar with Flow)
- Risk: Must not break login, checkout, or home
- Business: Q2 feature work takes priority
- Testing: Must maintain 80%+ coverage throughout

Recommendation: Phased migration over 2 quarters

Phase 1 (Sprint 1-2): Low-risk ViewModels
- Migrate AboutViewModel, FaqViewModel, TermsViewModel
- Establish team patterns and documentation
- Create migration checklist and code review guide
- Total: 3 ViewModels, minimal test changes

Phase 2 (Sprint 3-4): Medium-risk ViewModels
- Migrate utility ViewModels (HistoryVM, BookmarksVM, etc.)
- Convert observeAsState to collectAsStateWithLifecycle
- Total: 8-10 ViewModels

Phase 3 (Q2): High-value ViewModels
- Migrate HomeViewModel, SearchViewModel, ProfileViewModel
- Requires comprehensive regression testing
- Total: 5-8 ViewModels

Phase 4 (Q3): Critical path ViewModels
- Migrate LoginViewModel, CheckoutViewModel
- Full QA regression cycle required
- Total: remaining ViewModels

Policy: All NEW ViewModels must use StateFlow immediately.

Success criteria:
- Zero production regressions per phase
- Test coverage stays above 80%
- Team velocity not impacted more than 10%
- Each phase has rollback plan

### Decision:
Proceed with phased migration. All new code uses StateFlow.
Existing code migrated incrementally over 2 quarters.

ADR: "ADR-015: StateFlow Migration Strategy"
Documentation: Create migration guide with before/after examples
Training: Schedule Flow/Turbine workshop for team
Follow-up: Review progress at end of each phase
```

### Step 4: Migration Implementation Guide

**Agent**: android-developer (sonnet model)
**Input**: Decision Council output, migration plan
**Action**: Create migration guide with before/after examples

**Before (LiveData):**

```kotlin
class AboutViewModel @Inject constructor(
    private val contentRepository: ContentRepository,
) : ViewModel() {

    private val _aboutContent = MutableLiveData<AboutContent>()
    val aboutContent: LiveData<AboutContent> = _aboutContent

    private val _isLoading = MutableLiveData(true)
    val isLoading: LiveData<Boolean> = _isLoading

    private val _error = MutableLiveData<String?>()
    val error: LiveData<String?> = _error

    fun loadContent() {
        viewModelScope.launch {
            _isLoading.value = true
            _error.value = null
            try {
                _aboutContent.value = contentRepository.getAboutContent()
            } catch (e: Exception) {
                _error.value = e.message
            } finally {
                _isLoading.value = false
            }
        }
    }
}

// Fragment observation
viewModel.aboutContent.observe(viewLifecycleOwner) { content ->
    binding.title.text = content.title
}
viewModel.isLoading.observe(viewLifecycleOwner) { loading ->
    binding.progressBar.isVisible = loading
}
viewModel.error.observe(viewLifecycleOwner) { error ->
    binding.errorText.isVisible = error != null
    binding.errorText.text = error
}
```

**After (StateFlow + Sealed Interface):**

```kotlin
sealed interface AboutUiState {
    data object Loading : AboutUiState
    data class Error(val message: String) : AboutUiState
    data class Success(val content: AboutContent) : AboutUiState
}

@HiltViewModel
class AboutViewModel @Inject constructor(
    private val contentRepository: ContentRepository,
) : ViewModel() {

    val uiState: StateFlow<AboutUiState> =
        contentRepository.aboutContentFlow
            .map<AboutContent, AboutUiState> { AboutUiState.Success(it) }
            .catch { emit(AboutUiState.Error(it.message ?: "Unknown error")) }
            .stateIn(
                scope = viewModelScope,
                started = SharingStarted.WhileSubscribed(5_000),
                initialValue = AboutUiState.Loading,
            )
}

// Compose observation
@Composable
fun AboutRoute(viewModel: AboutViewModel = hiltViewModel()) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    AboutScreen(uiState = uiState)
}
```

**Test Migration (Before):**

```kotlin
@Test
fun `loadContent sets content on success`() {
    viewModel.loadContent()
    val content = viewModel.aboutContent.getOrAwaitValue()
    assertThat(content.title).isEqualTo("About Us")
}
```

**Test Migration (After):**

```kotlin
@Test
fun `uiState emits success when content available`() = runTest {
    repository.setAboutContent(testContent)

    viewModel.uiState.test {
        val state = awaitItem() as AboutUiState.Success
        assertThat(state.content.title).isEqualTo("About Us")
    }
}
```

### Timeline

```
Week 1:   Pattern detection + Decision Council (architect)
Week 1:   Migration guide created (developer)
Week 2-3: Phase 1 - 3 low-risk ViewModels migrated
Week 4-5: Phase 2 - 8-10 medium-risk ViewModels migrated
Q2:       Phase 3 - High-value ViewModels
Q3:       Phase 4 - Critical path ViewModels
```

---

## Scenario 3: Legacy Java Interop

Working with existing Java code, wrapping it safely in Kotlin, and applying Boy Scout improvements.

### User Request

```
"We have a legacy Java UserManager class that handles authentication.
It has no nullability annotations and uses callbacks. We need to build
a new Kotlin profile feature that depends on it. Don't rewrite the
Java code - we need to wrap it safely."
```

### Step 1: Analyze Legacy Java Code

**Agent**: android-developer (sonnet model)
**Action**: Scan and understand the Java codebase

```
# Find the Java file
Glob: pattern="**/UserManager.java"

# Check for existing nullability annotations
Grep: pattern="@NonNull|@Nullable|@NullableDecl" glob="**/UserManager.java" output_mode="content"

# Check callback patterns
Grep: pattern="interface.*Callback|interface.*Listener" glob="**/UserManager.java" output_mode="content"

# Find all callers of UserManager
Grep: pattern="UserManager" glob="**/*.kt" output_mode="files_with_matches"
Grep: pattern="UserManager" glob="**/*.java" output_mode="files_with_matches"
```

**Discovery: Existing Java Code (No annotations, callback-based):**

```java
// legacy/src/main/java/com/example/legacy/UserManager.java
public class UserManager {
    private static UserManager instance;
    private User currentUser;

    public static UserManager getInstance() {
        if (instance == null) {
            instance = new UserManager();
        }
        return instance;
    }

    // No nullability annotation - dangerous platform type in Kotlin
    public User getCurrentUser() {
        return currentUser;
    }

    // Callback-based authentication
    public void authenticate(String email, String password, AuthCallback callback) {
        executor.execute(() -> {
            try {
                User user = apiClient.login(email, password);
                currentUser = user;
                mainHandler.post(() -> callback.onSuccess(user));
            } catch (Exception e) {
                mainHandler.post(() -> callback.onError(e.getMessage()));
            }
        });
    }

    public void fetchProfile(String userId, ProfileCallback callback) {
        executor.execute(() -> {
            try {
                UserProfile profile = apiClient.getProfile(userId);
                mainHandler.post(() -> callback.onSuccess(profile));
            } catch (Exception e) {
                mainHandler.post(() -> callback.onError(e.getMessage()));
            }
        });
    }

    public interface AuthCallback {
        void onSuccess(User user);
        void onError(String message);
    }

    public interface ProfileCallback {
        void onSuccess(UserProfile profile);
        void onError(String message);
    }
}
```

### Step 2: Conflict Resolution (Safety Priority)

The developer identifies the safety issues before wrapping.

```
SAFETY ANALYSIS
-------------------------------------------------
1. getCurrentUser() returns platform type (User!)
   Risk: NullPointerException in Kotlin code
   Fix: Wrap with explicit null check

2. Singleton pattern (not thread-safe)
   Risk: Race condition on initialization
   Fix: Wrap access through Hilt-scoped provider

3. Callback threading (mainHandler.post)
   Risk: Lifecycle mismatch, memory leaks
   Fix: Convert callbacks to suspend functions

4. No error typing (String message only)
   Risk: Lost error context
   Fix: Map to sealed error types in wrapper
```

### Step 3: Create Kotlin Wrapper

**Agent**: android-developer (sonnet model)
**Action**: Build a safe Kotlin wrapper that converts callbacks to coroutines

**Boy Scout Improvement: Add nullability annotations to Java code (minimal, safe):**

```java
// Boy Scout: Add annotations without changing behavior
// This is safe because it only adds compiler hints, no runtime changes
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

public class UserManager {
    // Added @Nullable - getCurrentUser can return null when not logged in
    @Nullable
    public User getCurrentUser() {
        return currentUser;
    }

    // Added @NonNull to parameters that must not be null
    public void authenticate(
            @NonNull String email,
            @NonNull String password,
            @NonNull AuthCallback callback) {
        // ... existing implementation unchanged
    }
}
```

**Kotlin Wrapper (core:data):**

```kotlin
// core/data/src/main/kotlin/com/example/core/data/user/UserManagerWrapper.kt

/**
 * Safe Kotlin wrapper around legacy [UserManager] Java class.
 *
 * Responsibilities:
 * - Converts callback-based APIs to suspend functions
 * - Handles platform type null safety
 * - Provides Flow-based observation for current user
 * - Maps Java exceptions to typed Kotlin errors
 *
 * TODO(tech-debt): Replace with pure Kotlin implementation when
 * UserManager is fully migrated. Tracked in JIRA-789.
 */
class UserManagerWrapper @Inject constructor(
    private val userManager: UserManager,
    @Dispatcher(IO) private val ioDispatcher: CoroutineDispatcher,
) {
    // Convert singleton state to reactive Flow
    private val _currentUser = MutableStateFlow<User?>(null)
    val currentUser: StateFlow<User?> = _currentUser.asStateFlow()

    init {
        // Sync initial state from legacy manager
        // Explicit null check for platform type safety
        _currentUser.value = userManager.currentUser  // @Nullable now annotated
    }

    /**
     * Converts callback-based authenticate to suspend function.
     * Wraps legacy [UserManager.authenticate] with coroutine support.
     */
    suspend fun authenticate(email: String, password: String): AuthResult =
        withContext(ioDispatcher) {
            suspendCancellableCoroutine { continuation ->
                userManager.authenticate(
                    email,
                    password,
                    object : UserManager.AuthCallback {
                        override fun onSuccess(user: User) {
                            _currentUser.value = user
                            continuation.resume(AuthResult.Success(user))
                        }

                        override fun onError(message: String?) {
                            continuation.resume(
                                AuthResult.Error(
                                    message ?: "Authentication failed"
                                )
                            )
                        }
                    },
                )
            }
        }

    /**
     * Converts callback-based fetchProfile to suspend function.
     */
    suspend fun fetchProfile(userId: String): ProfileResult =
        withContext(ioDispatcher) {
            suspendCancellableCoroutine { continuation ->
                userManager.fetchProfile(
                    userId,
                    object : UserManager.ProfileCallback {
                        override fun onSuccess(profile: UserProfile) {
                            continuation.resume(ProfileResult.Success(profile))
                        }

                        override fun onError(message: String?) {
                            continuation.resume(
                                ProfileResult.Error(
                                    message ?: "Failed to load profile"
                                )
                            )
                        }
                    },
                )
            }
        }
}

// Typed result wrappers (no more String-only errors)
sealed interface AuthResult {
    data class Success(val user: User) : AuthResult
    data class Error(val message: String) : AuthResult
}

sealed interface ProfileResult {
    data class Success(val profile: UserProfile) : ProfileResult
    data class Error(val message: String) : ProfileResult
}
```

**Hilt Provider (bridging legacy singleton to DI):**

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object LegacyModule {

    @Provides
    @Singleton
    fun provideUserManager(): UserManager {
        // Bridge legacy singleton into Hilt DI graph
        // TODO(tech-debt): Replace with proper constructor injection
        // when UserManager is converted to Kotlin. Tracked in JIRA-790.
        return UserManager.getInstance()
    }
}
```

### Step 4: Build Profile Feature Using Wrapper

**Agent**: android-developer (sonnet model)
**Action**: Build the profile feature using the safe wrapper

```kotlin
// Repository that uses the wrapper (not the raw Java class)
interface ProfileRepository {
    val currentUser: StateFlow<User?>
    val profileFlow: Flow<UserProfile>
    suspend fun refreshProfile()
}

internal class DefaultProfileRepository @Inject constructor(
    private val userManagerWrapper: UserManagerWrapper,
) : ProfileRepository {

    override val currentUser: StateFlow<User?> = userManagerWrapper.currentUser

    override val profileFlow: Flow<UserProfile> = currentUser
        .filterNotNull()
        .mapLatest { user ->
            when (val result = userManagerWrapper.fetchProfile(user.id)) {
                is ProfileResult.Success -> result.profile
                is ProfileResult.Error -> throw ProfileException(result.message)
            }
        }

    override suspend fun refreshProfile() {
        val user = currentUser.value ?: throw ProfileException("Not logged in")
        when (val result = userManagerWrapper.fetchProfile(user.id)) {
            is ProfileResult.Success -> { /* Flow will update automatically */ }
            is ProfileResult.Error -> throw ProfileException(result.message)
        }
    }
}
```

### Step 5: Test Double for the Wrapper

**Agent**: android-testing-specialist (sonnet model)
**Action**: Create test double that avoids touching Java code

```kotlin
// Test double wraps behavior, not the Java class
class TestUserManagerWrapper : UserManagerWrapper {
    private val _currentUser = MutableStateFlow<User?>(null)
    override val currentUser: StateFlow<User?> = _currentUser

    var authenticateResult: AuthResult = AuthResult.Error("Not configured")
    var fetchProfileResult: ProfileResult = ProfileResult.Error("Not configured")

    fun setCurrentUser(user: User?) {
        _currentUser.value = user
    }

    override suspend fun authenticate(email: String, password: String): AuthResult {
        val result = authenticateResult
        if (result is AuthResult.Success) {
            _currentUser.value = result.user
        }
        return result
    }

    override suspend fun fetchProfile(userId: String): ProfileResult {
        return fetchProfileResult
    }
}
```

### Timeline

```
Hour 0-1:   Analyze Java code, identify safety issues (developer)
Hour 1-2:   Boy Scout annotations on Java class (developer)
Hour 2-4:   Build Kotlin wrapper with coroutine bridging (developer)
Hour 4-5:   Build profile feature on top of wrapper (developer)
Hour 5-6:   Test doubles and tests (testing-specialist)

Total: ~6 hours
```

---

## Scenario 4: Architecture Refactoring

Multi-agent parallel review and synthesis for a codebase that has grown organically and needs structural improvements.

### User Request

```
"Our app started as a single-module project and now has 15 screens,
8 ViewModels, and everything in one module. Build times are 45 seconds
for any change. We need to modularize but can't stop feature development.
Design a refactoring plan."
```

### Step 1: Parallel Analysis (3 Agents Simultaneously)

Three agents analyze the codebase in parallel, each from their specialized perspective.

**Agent 1: android-architect - Structural Analysis**

```
# Module structure analysis
Glob: pattern="**/build.gradle.kts"
Grep: pattern="dependencies" glob="**/build.gradle.kts" output_mode="content"

# Package organization
Glob: pattern="**/*.kt" -> group by package

# Find all ViewModels, Repositories, DAOs
Grep: pattern="class.*ViewModel" glob="**/*.kt" output_mode="content"
Grep: pattern="interface.*Repository|class.*Repository" glob="**/*.kt" output_mode="content"
Grep: pattern="@Dao" glob="**/*.kt" output_mode="content"

# Check for circular dependencies (imports between packages)
Grep: pattern="^import com.example.app.feature" glob="**/feature/**/*.kt" output_mode="content"

# Navigation graph complexity
Grep: pattern="composable<|NavGraphBuilder" glob="**/*.kt" output_mode="content"
```

**Architect Output:**

```
STRUCTURAL ANALYSIS
-------------------------------------------------
Modules: 1 (monolith)
Packages: 23
Kotlin files: 89
Build time: 45s (any change recompiles everything)

DEPENDENCY ANALYSIS
- feature.home imports feature.profile (circular risk)
- feature.search imports feature.home (coupling)
- feature.settings imports 4 other feature packages
- data layer mixed into feature packages

PROPOSED MODULE EXTRACTION (Priority Order)
1. core:model      - 12 data classes, zero dependencies
2. core:database   - 1 Room database, 6 DAOs
3. core:network    - 3 Retrofit services
4. core:data       - 5 repositories
5. core:designsystem - Theme, common components
6. feature:home    - HomeViewModel + 2 screens
7. feature:profile - ProfileViewModel + 3 screens
8. feature:search  - SearchViewModel + 2 screens
9. feature:settings - SettingsViewModel + 2 screens
```

**Agent 2: android-developer - Code Quality Analysis**

```
# Check for anti-patterns
Grep: pattern="GlobalScope|runBlocking" glob="**/*.kt" output_mode="content"
Grep: pattern="\.value\s*=" glob="**/ui/**/*.kt" output_mode="content"  # Direct state mutation in UI
Grep: pattern="object\s+.*Repository" glob="**/*.kt" output_mode="content"  # Singleton repos

# Check DI patterns
Grep: pattern="@Inject|@HiltViewModel|@Module" glob="**/*.kt" output_mode="count"
Grep: pattern="getInstance\(\)|Singleton" glob="**/*.kt" output_mode="content"

# Check for internal visibility opportunities
Grep: pattern="^class |^fun |^val |^interface " glob="**/*.kt" output_mode="count"
```

**Developer Output:**

```
CODE QUALITY FINDINGS
-------------------------------------------------
GlobalScope usage:     3 instances (must fix before modularizing)
Singleton anti-pattern: 2 repositories use object instead of Hilt
ServiceLocator:        1 manual DI container (AppContainer.kt)
Missing internal:      67% of classes are public unnecessarily
Mixed concerns:        4 ViewModels directly call Retrofit

BLOCKING ISSUES FOR MODULARIZATION
1. AppContainer.kt - Manual DI must convert to Hilt first
2. GlobalScope in SyncManager - Must use viewModelScope or WorkManager
3. Direct Retrofit calls in ViewModels - Must extract to repositories
```

**Agent 3: android-testing-specialist - Testability Analysis**

```
# Current test coverage
Grep: pattern="@Test" glob="**/*Test*.kt" output_mode="count"
Grep: pattern="class.*Test" glob="**/*Test*.kt" output_mode="content"

# Check for testability blockers
Grep: pattern="object |companion object" glob="**/data/**/*.kt" output_mode="content"
Grep: pattern="interface.*Repository" glob="**/*.kt" output_mode="content"
```

**Testing Specialist Output:**

```
TESTABILITY ANALYSIS
-------------------------------------------------
Total tests:           23
ViewModel tests:       8 (of 8 ViewModels = 100% coverage)
Repository tests:      2 (of 5 repositories = 40% coverage)
UI tests:              0
Test doubles:          3 (of 8 needed interfaces)

TESTABILITY BLOCKERS
- 2 repositories are objects (not injectable, not testable)
- 3 ViewModels take repository implementations (not interfaces)
- No MainDispatcherRule in test utilities
- No test doubles for NetworkMonitor, SyncManager

RISKS DURING MODULARIZATION
- Moving files may break 23 existing tests
- Need characterization tests before extracting modules
- Test utilities must move to core:testing module first
```

### Step 2: Synthesis and Decision Council

**Agent**: android-architect (opus model)
**Action**: Synthesize all three analyses into a migration plan

```markdown
## Decision: Monolith to Multi-Module Migration Strategy

### Status Quo Advocate's Position:
"The monolith works. 15 screens, 8 ViewModels, 23 tests, zero
production issues. Build time is 45 seconds - annoying but not
blocking. The team ships features weekly.

Modularization risk:
- Every file move is a potential merge conflict
- Feature development pauses during migration
- Team must learn new module patterns
- Gradle configuration complexity increases
- Build time might not improve if done wrong"

### Best Practices Advocate's Position:
"45-second builds for ANY change is a 10x productivity tax.
With 15 screens, the codebase is already beyond comfortable
monolith size.

Benefits of modularization:
- Incremental builds: 5-10s per module vs 45s
- Parallel development: Features can't conflict
- Clear ownership: Each module has defined scope
- Better testing: Module boundaries enforce testability
- Enforced architecture: Gradle prevents layer violations"

### Pragmatic Synthesis:
Migration must not stop feature development. Use the
'strangler fig' pattern: extract modules incrementally
while the monolith continues to work.

Recommendation: 4-phase migration over 6 weeks

Phase 0 (Week 1): Preparation - Fix blocking issues
- Convert AppContainer to Hilt
- Replace GlobalScope with proper scoping
- Extract repository interfaces
- Add characterization tests
- NO MODULE CHANGES - just cleanup

Phase 1 (Week 2): Core modules extraction
- Extract core:model (zero-dependency, safest first)
- Extract core:database
- Extract core:network
- App module depends on new core modules

Phase 2 (Week 3-4): Data and design extraction
- Extract core:data (repositories)
- Extract core:designsystem (theme, components)
- Extract core:testing (test utilities)

Phase 3 (Week 5-6): Feature modules
- Extract features one at a time
- Start with most independent feature (settings)
- End with most coupled feature (home)

Rule: Feature development continues in app module.
Extracted modules are "done" and locked.

### Decision:
Proceed with 4-phase strangler fig migration.
Feature development continues in parallel.
```

### Step 3: Phase 0 Implementation

**Agent**: android-developer (sonnet model)
**Action**: Fix blocking issues before modularization begins

**Fix 1: Convert Manual DI to Hilt:**

```kotlin
// BEFORE: AppContainer.kt (manual DI)
object AppContainer {
    val userRepository: UserRepository by lazy {
        UserRepositoryImpl(database.userDao(), apiService)
    }
    val postRepository: PostRepository by lazy {
        PostRepositoryImpl(database.postDao(), apiService)
    }
}

// AFTER: Hilt modules
@Module
@InstallIn(SingletonComponent::class)
internal abstract class RepositoryModule {
    @Binds
    abstract fun bindsUserRepository(impl: UserRepositoryImpl): UserRepository

    @Binds
    abstract fun bindsPostRepository(impl: PostRepositoryImpl): PostRepository
}
```

**Fix 2: Replace GlobalScope:**

```kotlin
// BEFORE
object SyncManager {
    fun startSync() {
        GlobalScope.launch {
            repository.sync()
        }
    }
}

// AFTER
@Singleton
class SyncManager @Inject constructor(
    private val repository: PostRepository,
    @ApplicationScope private val scope: CoroutineScope,
) {
    fun startSync() {
        scope.launch {
            repository.sync()
        }
    }
}
```

**Fix 3: Extract Repository Interfaces:**

```kotlin
// BEFORE: ViewModel depends on implementation
class HomeViewModel(
    private val repository: PostRepositoryImpl,  // Concrete class
) : ViewModel()

// AFTER: ViewModel depends on interface
@HiltViewModel
class HomeViewModel @Inject constructor(
    private val repository: PostRepository,  // Interface
) : ViewModel()
```

### Step 4: Module Extraction (Phase 1 Example)

**Agent**: gradle-build-engineer (sonnet model)
**Action**: Create core:model module and move data classes

```kotlin
// core/model/build.gradle.kts
plugins {
    id("com.example.android.library")
}

android {
    namespace = "com.example.core.model"
}

// Zero dependencies - pure data models
```

```
# Files to move (identified by architect)
app/src/main/kotlin/com/example/app/data/model/User.kt
  -> core/model/src/main/kotlin/com/example/core/model/User.kt

app/src/main/kotlin/com/example/app/data/model/Post.kt
  -> core/model/src/main/kotlin/com/example/core/model/Post.kt

# ... 10 more data classes

# Update app/build.gradle.kts
dependencies {
    implementation(projects.core.model)
}
```

### Timeline

```
Week 0:     Parallel analysis by 3 agents (1-2 hours)
Week 0:     Synthesis and Decision Council (1 hour)
Week 1:     Phase 0 - Fix blocking issues (3-4 days)
Week 2:     Phase 1 - Core module extraction (3-4 days)
Week 3-4:   Phase 2 - Data and design extraction (5-6 days)
Week 5-6:   Phase 3 - Feature module extraction (5-6 days)

Total: 6 weeks (feature development continues throughout)
```

---

## Scenario 5: Performance Optimization

Parallel agent execution to identify and fix performance bottlenecks across architecture, UI, and build layers.

### User Request

```
"Our app has gotten slow. Cold start is 4 seconds, the main list
screen drops to 30fps when scrolling, and clean builds take 3.5
minutes. We need to get startup under 2 seconds, scrolling to 60fps,
and builds under 2 minutes."
```

### Step 1: Parallel Diagnosis (3 Agents Simultaneously)

**Agent 1: android-architect - Startup and Architecture Bottlenecks**

```
# Check Application class initialization
Grep: pattern="class.*Application.*:" glob="**/*.kt" output_mode="content"
Grep: pattern="onCreate\(\)" glob="**/*Application*.kt" output_mode="content" -A 20

# Check Hilt initialization
Grep: pattern="@EarlyEntryPoint|@EntryPoint" glob="**/*.kt" output_mode="content"
Grep: pattern="@Singleton|@InstallIn.SingletonComponent" glob="**/*.kt" output_mode="count"

# Check eager vs lazy initialization
Grep: pattern="@Provides" glob="**/*Module*.kt" output_mode="content"

# Check database initialization
Grep: pattern="Room.databaseBuilder" glob="**/*.kt" output_mode="content" -A 5

# Check ContentProvider-based init
Grep: pattern="ContentProvider|InitializationProvider" glob="**/*.kt" output_mode="content"
Grep: pattern="provider.*android:name" glob="**/AndroidManifest.xml" output_mode="content"
```

**Architect Diagnosis:**

```
STARTUP BOTTLENECKS
-------------------------------------------------
1. Application.onCreate() does 6 eager initializations
   - Firebase init: ~400ms
   - Room database creation: ~300ms
   - Retrofit client creation: ~200ms
   - Analytics setup: ~150ms
   - Crash reporting: ~100ms
   - Feature flags sync: ~500ms (BLOCKING network call!)

2. 47 @Singleton-scoped objects created at startup via Hilt
   - Many are unused on initial screen

3. Room database has no prepackaged schema
   - First query triggers schema creation: ~200ms

4. Splash screen → Home screen transition:
   - Home fetches 3 data sources sequentially (not parallel)
```

**Agent 2: compose-expert - UI Performance Bottlenecks**

```
# Check for unstable parameters in Composables
Grep: pattern="@Composable.*fun.*\(.*List<|Map<|Set<" glob="**/*.kt" output_mode="content"

# Check for missing keys in LazyColumn
Grep: pattern="items\(" glob="**/*.kt" output_mode="content" -A 3

# Check for heavy computations in composition
Grep: pattern="@Composable" glob="**/*.kt" output_mode="content" -B 2 -A 10

# Check image loading
Grep: pattern="AsyncImage|rememberAsyncImagePainter|Image\(" glob="**/*.kt" output_mode="content"

# Check for missing remember/derivedStateOf
Grep: pattern="\.filter\(|\.map\(|\.sorted" glob="**/*Screen*.kt" output_mode="content"
```

**Compose Expert Diagnosis:**

```
UI PERFORMANCE BOTTLENECKS
-------------------------------------------------
1. ItemCard composable takes List<Tag> parameter (unstable)
   - Causes full recomposition of every card on any list change
   - Fix: Use kotlinx.collections.immutable.ImmutableList

2. LazyColumn missing keys
   - items(posts) { post -> PostCard(post) }
   - Missing key causes full rebind on any list mutation
   - Fix: items(posts, key = { it.id }) { ... }

3. Heavy filtering in composition scope
   - val filtered = posts.filter { it.category == selected }
   - Runs on every recomposition
   - Fix: Use remember(posts, selected) { ... } or derivedStateOf

4. Image loading without size constraints
   - AsyncImage without Modifier.size() causes layout thrashing
   - 50 images load simultaneously (no prefetch limit)

5. Nested scrolling conflict
   - LazyColumn inside ScrollableColumn detected
```

**Agent 3: gradle-build-engineer - Build Performance Bottlenecks**

```
# Check build configuration
Grep: pattern="kapt|annotationProcessor" glob="**/build.gradle.kts" output_mode="content"
Grep: pattern="buildFeatures" glob="**/build.gradle.kts" output_mode="content" -A 5

# Check for configuration cache issues
Grep: pattern="org.gradle.configuration-cache" glob="**/gradle.properties" output_mode="content"

# Check dependency count
Grep: pattern="implementation|api\(" glob="**/build.gradle.kts" output_mode="count"

# Check for unnecessary build features
Grep: pattern="buildConfig = true|viewBinding = true" glob="**/build.gradle.kts" output_mode="content"
```

**Build Engineer Diagnosis:**

```
BUILD PERFORMANCE BOTTLENECKS
-------------------------------------------------
1. kapt used instead of KSP for Hilt and Room
   - kapt runs full Java stub generation: +30s per module
   - KSP is 2x faster for annotation processing

2. Configuration cache disabled
   - Every build reconfigures all modules: +15s

3. Parallel execution disabled
   - org.gradle.parallel=false in gradle.properties

4. Unnecessary build features enabled
   - buildConfig = true in all 12 modules (only app needs it)
   - viewBinding = true in 3 modules that use only Compose

5. No build cache
   - org.gradle.caching not enabled

6. Full clean rebuild on CI
   - CI script uses 'clean build' instead of incremental
```

### Step 2: Parallel Fixes (3 Agents Simultaneously)

**Agent 1: android-architect - Startup Optimization**

```kotlin
// BEFORE: Eager initialization in Application.onCreate()
@HiltAndroidApp
class MyApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        FirebaseApp.initializeApp(this)          // 400ms
        setupCrashReporting()                     // 100ms
        AnalyticsManager.initialize(this)         // 150ms
        FeatureFlags.syncBlocking(this)           // 500ms BLOCKING!
        setupDatabase()                           // 300ms
        setupRetrofit()                           // 200ms
    }
}

// AFTER: Deferred initialization with App Startup
@HiltAndroidApp
class MyApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        // Only critical-path initialization here
        // Everything else deferred via App Startup or lazy injection
    }
}

// App Startup initializers (ordered by priority)
class CrashReportingInitializer : Initializer<Unit> {
    override fun create(context: Context) {
        // Crash reporting first so we catch startup crashes
        setupCrashReporting()
    }
    override fun dependencies(): List<Class<out Initializer<*>>> = emptyList()
}

class FirebaseInitializer : Initializer<Unit> {
    override fun create(context: Context) {
        FirebaseApp.initializeApp(context)
    }
    override fun dependencies() = listOf(CrashReportingInitializer::class.java)
}

// Feature flags: async, not blocking
class FeatureFlagInitializer : Initializer<Unit> {
    override fun create(context: Context) {
        // Non-blocking: fetch in background, use cached values
        FeatureFlags.syncAsync(context)
    }
    override fun dependencies() = listOf(FirebaseInitializer::class.java)
}

// Database and Retrofit: lazy via Hilt (created on first use)
@Module
@InstallIn(SingletonComponent::class)
object LazyDataModule {
    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): AppDatabase {
        // Only created when first DAO is injected
        return Room.databaseBuilder(context, AppDatabase::class.java, "app.db")
            .createFromAsset("databases/prepopulated.db")  // Prepackaged schema
            .build()
    }
}

// Home screen: parallel data loading
@HiltViewModel
class HomeViewModel @Inject constructor(
    private val postsRepo: PostRepository,
    private val storiesRepo: StoryRepository,
    private val suggestionsRepo: SuggestionRepository,
) : ViewModel() {

    // BEFORE: Sequential loading
    // val posts = postsRepo.get()
    // val stories = storiesRepo.get()
    // val suggestions = suggestionsRepo.get()

    // AFTER: Parallel loading with combine
    val uiState: StateFlow<HomeUiState> = combine(
        postsRepo.feedFlow,
        storiesRepo.storiesFlow,
        suggestionsRepo.suggestionsFlow,
    ) { posts, stories, suggestions ->
        HomeUiState.Success(posts, stories, suggestions)
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = HomeUiState.Loading,
    )
}
```

**Expected improvement**: Cold start 4.0s down to 1.5s.

**Agent 2: compose-expert - UI Performance Fixes**

```kotlin
// FIX 1: Stable parameters with ImmutableList
// BEFORE
@Composable
fun PostCard(
    post: Post,
    tags: List<Tag>,  // Unstable - causes unnecessary recomposition
    onClick: () -> Unit,
)

// AFTER
@Composable
fun PostCard(
    post: Post,
    tags: ImmutableList<Tag>,  // Stable - skips recomposition when unchanged
    onClick: () -> Unit,
)

// FIX 2: LazyColumn with keys
// BEFORE
LazyColumn {
    items(posts) { post ->
        PostCard(post = post)
    }
}

// AFTER
LazyColumn {
    items(
        items = posts,
        key = { it.id },  // Enables item identity tracking
    ) { post ->
        PostCard(
            post = post,
            modifier = Modifier.animateItem(),  // Smooth animations
        )
    }
}

// FIX 3: Remember expensive computations
// BEFORE
@Composable
fun FilteredFeed(posts: List<Post>, selectedCategory: String) {
    // Runs on EVERY recomposition
    val filtered = posts.filter { it.category == selectedCategory }

// AFTER
@Composable
fun FilteredFeed(posts: ImmutableList<Post>, selectedCategory: String) {
    // Only recomputes when inputs change
    val filtered by remember(posts, selectedCategory) {
        derivedStateOf {
            posts.filter { it.category == selectedCategory }
        }
    }

// FIX 4: Image loading with proper constraints
// BEFORE
AsyncImage(
    model = post.imageUrl,
    contentDescription = null,
    // No size constraints - layout thrashing
)

// AFTER
AsyncImage(
    model = ImageRequest.Builder(LocalContext.current)
        .data(post.imageUrl)
        .crossfade(true)
        .size(Size.ORIGINAL)
        .build(),
    contentDescription = "Post image",
    modifier = Modifier
        .fillMaxWidth()
        .height(200.dp)  // Fixed height prevents layout thrashing
        .clip(RoundedCornerShape(8.dp)),
    contentScale = ContentScale.Crop,
)

// FIX 5: Remove nested scrolling conflict
// BEFORE
Column(Modifier.verticalScroll(rememberScrollState())) {
    // ... header content
    LazyColumn {  // Nested scrollable - performance disaster
        items(posts) { PostCard(it) }
    }
}

// AFTER
LazyColumn {
    item {
        // Header content as LazyColumn item
        HeaderContent()
    }
    items(posts, key = { it.id }) { post ->
        PostCard(post)
    }
}
```

**Expected improvement**: Scrolling 30fps up to 60fps.

**Agent 3: gradle-build-engineer - Build Performance Fixes**

```properties
# gradle.properties optimizations
org.gradle.configuration-cache=true
org.gradle.parallel=true
org.gradle.caching=true
org.gradle.jvmargs=-Xmx4g -XX:+UseParallelGC
kotlin.incremental=true
```

```kotlin
// Migrate kapt to KSP in build.gradle.kts
// BEFORE
plugins {
    id("kotlin-kapt")
}
dependencies {
    kapt(libs.hilt.compiler)
    kapt(libs.room.compiler)
}

// AFTER
plugins {
    alias(libs.plugins.ksp)
}
dependencies {
    ksp(libs.hilt.compiler)
    ksp(libs.room.compiler)
}
```

```kotlin
// Disable unnecessary build features across modules
// convention plugin update
class AndroidLibraryConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            extensions.configure<LibraryExtension> {
                buildFeatures {
                    buildConfig = false    // Disabled by default
                    viewBinding = false    // Disabled by default
                    resValues = false      // Disabled by default
                }
            }
        }
    }
}
```

**Expected improvement**: Clean build 3.5min down to 1.8min. Incremental build 45s down to 8-12s.

### Step 3: Testing Specialist Adds Benchmarks

**Agent**: android-testing-specialist (sonnet model)
**Action**: Add performance benchmarks to prevent regression

```kotlin
// Startup benchmark
@RunWith(AndroidJUnit4::class)
@LargeTest
class StartupBenchmark {
    @get:Rule
    val benchmarkRule = MacrobenchmarkRule()

    @Test
    fun coldStartup() = benchmarkRule.measureRepeated(
        packageName = "com.example.app",
        metrics = listOf(StartupTimingMetric()),
        iterations = 5,
        startupMode = StartupMode.COLD,
    ) {
        pressHome()
        startActivityAndWait()
    }

    @Test
    fun warmStartup() = benchmarkRule.measureRepeated(
        packageName = "com.example.app",
        metrics = listOf(StartupTimingMetric()),
        iterations = 5,
        startupMode = StartupMode.WARM,
    ) {
        pressHome()
        startActivityAndWait()
    }
}

// Scroll performance benchmark
@RunWith(AndroidJUnit4::class)
@LargeTest
class FeedScrollBenchmark {
    @get:Rule
    val benchmarkRule = MacrobenchmarkRule()

    @Test
    fun feedScroll_noJank() = benchmarkRule.measureRepeated(
        packageName = "com.example.app",
        metrics = listOf(FrameTimingMetric()),
        iterations = 5,
        startupMode = StartupMode.WARM,
    ) {
        startActivityAndWait()

        val feedList = device.findObject(By.res("feed_list"))
        feedList.setGestureMargin(device.displayWidth / 5)

        repeat(3) {
            feedList.fling(Direction.DOWN)
            device.waitForIdle()
        }
    }
}
```

### Results Summary

```
METRIC              BEFORE    AFTER     TARGET    STATUS
---------------------------------------------------------
Cold startup        4.0s      1.5s      <2.0s     PASS
Warm startup        2.5s      0.8s      <1.0s     PASS
Feed scrolling      30fps     60fps     60fps     PASS
Clean build         3.5min    1.8min    <2.0min   PASS
Incremental build   45s       10s       <10s      PASS
```

### Timeline

```
Hour 0-2:   Parallel diagnosis by 3 agents
Hour 2-4:   Parallel fix implementation by 3 agents
Hour 4-5:   Benchmark creation (testing-specialist)
Hour 5-6:   Integration and verification

Total: ~6 hours (parallel execution: ~4 hours)
```

---

## Scenario 6: Offline-First Feature with Sync Conflicts

Building a notes feature that works offline and handles sync conflicts when the user edits on multiple devices.

### User Request

```
"Build a notes feature where users can create and edit notes offline.
Notes sync to the server when connectivity returns. Handle the case
where the same note is edited on two devices simultaneously."
```

### Step 1: Architecture Design

**Agent**: android-architect (opus model)
**Action**: Design offline-first sync architecture with conflict resolution

```
SYNC STRATEGY: Last-Write-Wins with Conflict Detection
-------------------------------------------------
- Each note has a 'version' field (server-incremented)
- Each note has 'lastModifiedAt' timestamp
- Local edits marked as 'pendingSync = true'
- On sync: compare local version vs server version
- If server version > local version AND local has pending edits:
  -> Conflict detected, keep both versions for user resolution
- If no conflict: normal merge

DATA MODEL
-------------------------------------------------
Note:
  id: String (UUID, generated client-side)
  title: String
  content: String
  version: Int (server version)
  lastModifiedAt: Instant
  syncStatus: SYNCED | PENDING | CONFLICT

SYNC FLOW
-------------------------------------------------
1. User edits note -> Room update, syncStatus = PENDING
2. Connectivity restored -> WorkManager triggers sync
3. Upload pending notes to server
4. Server returns updated version or 409 Conflict
5. On success: update version, syncStatus = SYNCED
6. On conflict: store server version, syncStatus = CONFLICT
7. User resolves conflict in UI
```

### Step 2: Implementation

**Agent**: android-developer (sonnet model)

```kotlin
// core/model
data class Note(
    val id: String,
    val title: String,
    val content: String,
    val version: Int,
    val lastModifiedAt: Instant,
    val syncStatus: SyncStatus,
)

enum class SyncStatus {
    SYNCED,
    PENDING,
    CONFLICT,
}

data class NoteConflict(
    val localNote: Note,
    val serverNote: Note,
)

// core/database
@Entity(tableName = "notes")
data class NoteEntity(
    @PrimaryKey val id: String,
    val title: String,
    val content: String,
    val version: Int,
    val lastModifiedAt: Long,
    val syncStatus: String,
    // Conflict data stored alongside
    val conflictServerTitle: String? = null,
    val conflictServerContent: String? = null,
    val conflictServerVersion: Int? = null,
)

@Dao
interface NoteDao {
    @Query("SELECT * FROM notes ORDER BY lastModifiedAt DESC")
    fun observeNotes(): Flow<List<NoteEntity>>

    @Query("SELECT * FROM notes WHERE id = :id")
    fun observeNote(id: String): Flow<NoteEntity?>

    @Query("SELECT * FROM notes WHERE syncStatus = 'PENDING'")
    suspend fun getPendingNotes(): List<NoteEntity>

    @Query("SELECT * FROM notes WHERE syncStatus = 'CONFLICT'")
    fun observeConflicts(): Flow<List<NoteEntity>>

    @Upsert
    suspend fun upsert(note: NoteEntity)

    @Query("DELETE FROM notes WHERE id = :id")
    suspend fun delete(id: String)
}

// core/data - Offline-first repository with conflict handling
internal class OfflineFirstNoteRepository @Inject constructor(
    private val noteDao: NoteDao,
    private val noteApi: NoteApiService,
    @Dispatcher(IO) private val ioDispatcher: CoroutineDispatcher,
) : NoteRepository {

    override val notesFlow: Flow<List<Note>> =
        noteDao.observeNotes().map { entities ->
            entities.map(NoteEntity::asExternalModel)
        }

    override val conflictsFlow: Flow<List<NoteConflict>> =
        noteDao.observeConflicts().map { entities ->
            entities.mapNotNull { it.asConflict() }
        }

    override suspend fun createNote(title: String, content: String) =
        withContext(ioDispatcher) {
            val note = NoteEntity(
                id = UUID.randomUUID().toString(),
                title = title,
                content = content,
                version = 0,
                lastModifiedAt = Clock.System.now().toEpochMilliseconds(),
                syncStatus = SyncStatus.PENDING.name,
            )
            noteDao.upsert(note)
        }

    override suspend fun updateNote(id: String, title: String, content: String) =
        withContext(ioDispatcher) {
            val existing = noteDao.observeNote(id).first() ?: return@withContext
            noteDao.upsert(
                existing.copy(
                    title = title,
                    content = content,
                    lastModifiedAt = Clock.System.now().toEpochMilliseconds(),
                    syncStatus = SyncStatus.PENDING.name,
                ),
            )
        }

    override suspend fun sync() = withContext(ioDispatcher) {
        // 1. Upload pending changes
        val pending = noteDao.getPendingNotes()
        for (note in pending) {
            try {
                val response = noteApi.upsertNote(
                    NoteRequest(
                        id = note.id,
                        title = note.title,
                        content = note.content,
                        expectedVersion = note.version,
                    ),
                )
                noteDao.upsert(
                    note.copy(
                        version = response.version,
                        syncStatus = SyncStatus.SYNCED.name,
                    ),
                )
            } catch (e: HttpException) {
                if (e.code() == 409) {
                    // Conflict: fetch server version and store both
                    val serverNote = noteApi.getNote(note.id)
                    noteDao.upsert(
                        note.copy(
                            syncStatus = SyncStatus.CONFLICT.name,
                            conflictServerTitle = serverNote.title,
                            conflictServerContent = serverNote.content,
                            conflictServerVersion = serverNote.version,
                        ),
                    )
                }
            }
        }

        // 2. Pull remote changes
        val remoteNotes = noteApi.getAllNotes()
        for (remote in remoteNotes) {
            val local = noteDao.observeNote(remote.id).first()
            if (local == null || (local.syncStatus == SyncStatus.SYNCED.name
                    && remote.version > local.version)) {
                noteDao.upsert(remote.asEntity())
            }
        }
    }

    override suspend fun resolveConflict(
        noteId: String,
        resolution: ConflictResolution,
    ) = withContext(ioDispatcher) {
        val note = noteDao.observeNote(noteId).first() ?: return@withContext
        when (resolution) {
            ConflictResolution.KEEP_LOCAL -> {
                noteDao.upsert(
                    note.copy(
                        syncStatus = SyncStatus.PENDING.name,
                        version = note.conflictServerVersion ?: note.version,
                        conflictServerTitle = null,
                        conflictServerContent = null,
                        conflictServerVersion = null,
                    ),
                )
            }
            ConflictResolution.KEEP_SERVER -> {
                noteDao.upsert(
                    note.copy(
                        title = note.conflictServerTitle ?: note.title,
                        content = note.conflictServerContent ?: note.content,
                        version = note.conflictServerVersion ?: note.version,
                        syncStatus = SyncStatus.SYNCED.name,
                        conflictServerTitle = null,
                        conflictServerContent = null,
                        conflictServerVersion = null,
                    ),
                )
            }
            is ConflictResolution.Merge -> {
                noteDao.upsert(
                    note.copy(
                        title = resolution.title,
                        content = resolution.content,
                        version = note.conflictServerVersion ?: note.version,
                        syncStatus = SyncStatus.PENDING.name,
                        conflictServerTitle = null,
                        conflictServerContent = null,
                        conflictServerVersion = null,
                    ),
                )
            }
        }
    }
}

enum class ConflictResolution {
    KEEP_LOCAL,
    KEEP_SERVER;

    data class Merge(val title: String, val content: String) : Any()
}

// sync/ module - WorkManager sync worker
@HiltWorker
class NoteSyncWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val noteRepository: NoteRepository,
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result = try {
        noteRepository.sync()
        Result.success()
    } catch (e: Exception) {
        if (runAttemptCount < 3) Result.retry() else Result.failure()
    }

    companion object {
        fun enqueue(workManager: WorkManager) {
            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build()

            val request = OneTimeWorkRequestBuilder<NoteSyncWorker>()
                .setConstraints(constraints)
                .setBackoffCriteria(
                    BackoffPolicy.EXPONENTIAL,
                    Duration.ofSeconds(30),
                )
                .build()

            workManager.enqueueUniqueWork(
                "note_sync",
                ExistingWorkPolicy.REPLACE,
                request,
            )
        }
    }
}
```

### Timeline

```
Hour 0-1:   Architecture design with sync strategy (architect)
Hour 1-3:   Data layer implementation (developer)
Hour 3-4:   Sync worker implementation (developer)
Hour 4-5:   Conflict resolution UI (compose-expert)
Hour 5-6:   Tests for sync and conflict scenarios (testing-specialist)

Total: ~6 hours
```

---

## Scenario 7: Navigation 3 Migration

Migrating from Navigation 2 (Fragment-based or Compose NavHost) to Navigation 3 with type-safe routes.

### User Request

```
"We're using Navigation Compose with string-based routes. We want to
migrate to Navigation 3 with type-safe @Serializable routes. We have
12 screens across 4 feature modules."
```

### Step 1: Pattern Detection

**Agent**: android-architect (opus model)

```
# Current navigation patterns
Grep: pattern="NavHost|NavGraphBuilder|composable\(" glob="**/*.kt" output_mode="content"
Grep: pattern="navArgument|arguments\s*=" glob="**/*.kt" output_mode="content"
Grep: pattern="navigate\(" glob="**/*.kt" output_mode="content"

# Route definitions
Grep: pattern="const val.*route|object.*Route" glob="**/*.kt" output_mode="content"

# Deep link handling
Grep: pattern="deepLinks|navDeepLink" glob="**/*.kt" output_mode="content"
```

**Discovery:**

```
CURRENT NAVIGATION STATE
-------------------------------------------------
NavHost location:           app/MainNavHost.kt
Route definitions:          String constants in each feature:api module
Total routes:               12
Routes with arguments:      5 (string-based parsing)
Deep links:                 3
Navigation calls:           28 (navigate("route/$arg"))

RISK AREAS
- 5 routes parse arguments from strings (type-unsafe)
- 3 deep links need URI template updates
- 28 navigation calls need lambda updates
```

### Step 2: Migration

**Agent**: android-developer (sonnet model)

```kotlin
// BEFORE: String-based routes
// feature/profile/api
object ProfileNav {
    const val ROUTE = "profile/{userId}"
    fun createRoute(userId: String) = "profile/$userId"
}

// app/MainNavHost.kt
composable(
    route = ProfileNav.ROUTE,
    arguments = listOf(navArgument("userId") { type = NavType.StringType }),
) { backStackEntry ->
    val userId = backStackEntry.arguments?.getString("userId") ?: return@composable
    ProfileRoute(userId = userId)
}

// Calling code
navController.navigate(ProfileNav.createRoute("user-123"))


// AFTER: Type-safe @Serializable routes
// feature/profile/api
@Serializable
data class ProfileRoute(val userId: String)

// app/MainNavHost.kt
composable<ProfileRoute> { backStackEntry ->
    val route = backStackEntry.toRoute<ProfileRoute>()
    ProfileScreen(userId = route.userId)
}

// Calling code
navController.navigate(ProfileRoute(userId = "user-123"))
```

### Timeline

```
Hour 0-1:   Pattern detection and migration plan (architect)
Hour 1-2:   Update feature:api modules with @Serializable routes (developer)
Hour 2-3:   Update NavHost and navigation calls (developer)
Hour 3-4:   Update deep link handling (developer)
Hour 4-5:   Test all navigation paths (testing-specialist)

Total: ~5 hours
```

---

## Scenario 8: Adding CI/CD Pipeline

Setting up a complete CI/CD pipeline with lint, tests, and release automation.

### User Request

```
"Set up GitHub Actions CI for our Android project. We need lint checks,
unit tests, instrumented tests on Firebase Test Lab, and automated
release to Play Store internal track."
```

### Step 1: Build Configuration

**Agent**: gradle-build-engineer (sonnet model)
**Action**: Ensure build system supports CI requirements

```kotlin
// Ensure lint is configured across all modules
// Convention plugin addition
class AndroidLintConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            extensions.configure<CommonExtension<*, *, *, *, *, *>> {
                lint {
                    xmlReport = true
                    htmlReport = true
                    checkDependencies = true
                    warningsAsErrors = true
                    abortOnError = true
                    baseline = file("lint-baseline.xml")
                }
            }
        }
    }
}
```

### Step 2: CI Pipeline Configuration

**Agent**: android-developer (sonnet model)
**Action**: Create GitHub Actions workflow files

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: 17
      - uses: gradle/actions/setup-gradle@v4
      - run: ./gradlew lint
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: lint-reports
          path: "**/build/reports/lint-results-*.html"

  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: 17
      - uses: gradle/actions/setup-gradle@v4
      - run: ./gradlew testDebugUnitTest
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-reports
          path: "**/build/reports/tests/"

  instrumented-tests:
    runs-on: ubuntu-latest
    needs: [lint, unit-tests]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: 17
      - uses: gradle/actions/setup-gradle@v4
      - run: ./gradlew assembleDebug assembleDebugAndroidTest
      - uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      - uses: google-github-actions/setup-gcloud@v2
      - run: |
          gcloud firebase test android run \
            --type instrumentation \
            --app app/build/outputs/apk/debug/app-debug.apk \
            --test app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk \
            --device model=Pixel6,version=33 \
            --timeout 10m

  release:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    needs: [instrumented-tests]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: 17
      - uses: gradle/actions/setup-gradle@v4
      - run: ./gradlew bundleRelease
        env:
          SIGNING_KEY_ALIAS: ${{ secrets.SIGNING_KEY_ALIAS }}
          SIGNING_KEY_PASSWORD: ${{ secrets.SIGNING_KEY_PASSWORD }}
          SIGNING_STORE_PASSWORD: ${{ secrets.SIGNING_STORE_PASSWORD }}
      - uses: r0adkll/upload-google-play@v1
        with:
          serviceAccountJsonPlainText: ${{ secrets.PLAY_SERVICE_ACCOUNT }}
          packageName: com.example.app
          releaseFiles: app/build/outputs/bundle/release/app-release.aab
          track: internal
```

### Timeline

```
Hour 0-1:   Build configuration for CI (gradle-build-engineer)
Hour 1-3:   GitHub Actions workflow creation (developer)
Hour 3-4:   Secret configuration and first run verification
Hour 4-5:   Fix any CI-specific issues

Total: ~5 hours
```

---

## How to Use These Scenarios

Each scenario demonstrates the agent orchestration model. In practice, invoke agents as follows:

```
# Start with the architect for any new feature or refactoring
"Have the android-architect design the architecture for [feature]"

# Then the build engineer for module setup
"Have the gradle-build-engineer create the module structure"

# Then the developer for implementation
"Have the android-developer implement the data layer"

# The compose-expert for UI (can run parallel with testing)
"Have the compose-expert implement the screens"

# The testing specialist for test coverage (can run parallel with UI)
"Have the android-testing-specialist write comprehensive tests"
```

**Parallel execution opportunities:**
- compose-expert and android-testing-specialist can work simultaneously after the data layer is ready
- gradle-build-engineer and android-architect can work simultaneously on module setup and detailed design
- Multiple android-developer tasks can run in parallel if they target independent modules

**Decision Council is invoked when:**
- Choosing between competing patterns (LiveData vs StateFlow)
- Making breaking changes to existing codebase
- Selecting frameworks (Hilt vs Koin vs Dagger)
- Planning large migrations with risk
- Any decision affecting more than 5 files or 2 developers

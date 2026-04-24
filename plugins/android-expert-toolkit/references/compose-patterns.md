# Compose Patterns Reference

Code examples and implementation patterns extracted from compose-expert agent prompt.

## When to use

Read this reference when implementing Jetpack Compose UI, integrating Compose with the legacy View system (ComposeView, AndroidView), or migrating XML layouts to Compose. Used by compose-expert during UI implementation. For high-level UI organization, see `ui-patterns.md`.

## Compose + View System Interoperability

### ComposeView in XML Layouts

**XML Layout with ComposeView:**

```xml
<!-- fragment_items.xml -->
<LinearLayout
    xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical">

    <!-- Legacy View: Toolbar -->
    <com.google.android.material.appbar.MaterialToolbar
        android:id="@+id/toolbar"
        android:layout_width="match_parent"
        android:layout_height="?attr/actionBarSize"
        android:background="?attr/colorPrimary" />

    <!-- Compose UI: Content -->
    <androidx.compose.ui.platform.ComposeView
        android:id="@+id/compose_view"
        android:layout_width="match_parent"
        android:layout_height="0dp"
        android:layout_weight="1" />

</LinearLayout>
```

**Fragment Setup with Lifecycle-aware Compose:**

```kotlin
class ItemsFragment : Fragment() {

    private var _binding: FragmentItemsBinding? = null
    private val binding get() = _binding!!

    private val viewModel: ItemsViewModel by viewModels()

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentItemsBinding.inflate(inflater, container, false)

        binding.toolbar.title = "Items"

        binding.composeView.apply {
            setViewCompositionStrategy(
                ViewCompositionStrategy.DisposeOnViewTreeLifecycleDestroyed
            )

            setContent {
                AppTheme {
                    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

                    ItemsScreen(
                        uiState = uiState,
                        onItemClick = { itemId ->
                            findNavController().navigate(
                                ItemsFragmentDirections.actionToDetail(itemId)
                            )
                        },
                        onRefresh = viewModel::refresh,
                    )
                }
            }
        }

        return binding.root
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
```

**Theme Synchronization (Material 2 View -> Material 3 Compose):**

```kotlin
@Composable
fun AppTheme(
    content: @Composable () -> Unit
) {
    val context = LocalContext.current

    val colorScheme = when {
        Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            if (isSystemInDarkTheme()) {
                dynamicDarkColorScheme(context)
            } else {
                dynamicLightColorScheme(context)
            }
        }
        else -> {
            if (isSystemInDarkTheme()) {
                darkColorScheme(
                    primary = Color(context.getColorFromAttr(R.attr.colorPrimary)),
                    onPrimary = Color(context.getColorFromAttr(R.attr.colorOnPrimary)),
                )
            } else {
                lightColorScheme(
                    primary = Color(context.getColorFromAttr(R.attr.colorPrimary)),
                    onPrimary = Color(context.getColorFromAttr(R.attr.colorOnPrimary)),
                )
            }
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = AppTypography,
        content = content,
    )
}

private fun Context.getColorFromAttr(@AttrRes attrId: Int): Int {
    val typedValue = TypedValue()
    theme.resolveAttribute(attrId, typedValue, true)
    return typedValue.data
}
```

**ViewCompositionStrategy Options:**

```kotlin
binding.composeView.apply {
    // 1. Default: Dispose when ComposeView detaches from window
    //    Use for: Simple cases, Activity-based UI
    setViewCompositionStrategy(ViewCompositionStrategy.DisposeOnDetachedFromWindow)

    // 2. Dispose when ViewTreeLifecycleOwner is destroyed
    //    Use for: Fragments (recommended), ViewPager2 pages
    setViewCompositionStrategy(
        ViewCompositionStrategy.DisposeOnViewTreeLifecycleDestroyed
    )

    // 3. Dispose when specific Lifecycle is destroyed
    //    Use for: Custom lifecycle management
    setViewCompositionStrategy(
        ViewCompositionStrategy.DisposeOnLifecycleDestroyed(viewLifecycleOwner)
    )

    // 4. Never dispose automatically (manual control)
    //    Use for: Shared compositions, custom disposal logic
    setViewCompositionStrategy(ViewCompositionStrategy.DisposeOnDetachedFromWindowOrReleasedFromPool)

    setContent { /* ... */ }
}
```

### AndroidView in Compose

**Basic AndroidView Usage:**

```kotlin
@Composable
fun LegacyViewInCompose(
    modifier: Modifier = Modifier,
) {
    AndroidView(
        factory = { context ->
            CustomLegacyView(context).apply {
                layoutParams = ViewGroup.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.WRAP_CONTENT,
                )
            }
        },
        update = { view ->
            view.updateData(/* new data */)
        },
        modifier = modifier,
    )
}
```

**MapView Integration (Google Maps):**

```kotlin
@Composable
fun MapViewContainer(
    latitude: Double,
    longitude: Double,
    zoom: Float,
    modifier: Modifier = Modifier,
) {
    val mapView = rememberMapViewWithLifecycle()

    AndroidView(
        factory = { mapView },
        update = { view ->
            view.getMapAsync { googleMap ->
                val position = LatLng(latitude, longitude)
                googleMap.moveCamera(
                    CameraUpdateFactory.newLatLngZoom(position, zoom)
                )
            }
        },
        modifier = modifier,
    )
}

@Composable
fun rememberMapViewWithLifecycle(): MapView {
    val context = LocalContext.current
    val lifecycle = LocalLifecycleOwner.current.lifecycle

    val mapView = remember {
        MapView(context).apply {
            onCreate(Bundle())
        }
    }

    DisposableEffect(lifecycle, mapView) {
        val observer = LifecycleEventObserver { _, event ->
            when (event) {
                Lifecycle.Event.ON_CREATE -> mapView.onCreate(Bundle())
                Lifecycle.Event.ON_START -> mapView.onStart()
                Lifecycle.Event.ON_RESUME -> mapView.onResume()
                Lifecycle.Event.ON_PAUSE -> mapView.onPause()
                Lifecycle.Event.ON_STOP -> mapView.onStop()
                Lifecycle.Event.ON_DESTROY -> mapView.onDestroy()
                else -> {}
            }
        }

        lifecycle.addObserver(observer)

        onDispose {
            lifecycle.removeObserver(observer)
            mapView.onDestroy()
        }
    }

    return mapView
}
```

**WebView Integration:**

```kotlin
@Composable
fun WebViewContainer(
    url: String,
    onPageLoaded: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    var webView: WebView? by remember { mutableStateOf(null) }

    AndroidView(
        factory = { context ->
            WebView(context).apply {
                layoutParams = ViewGroup.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT,
                )

                settings.apply {
                    javaScriptEnabled = true
                    domStorageEnabled = true
                    loadWithOverviewMode = true
                    useWideViewPort = true
                }

                webViewClient = object : WebViewClient() {
                    override fun onPageFinished(view: WebView?, url: String?) {
                        url?.let { onPageLoaded(it) }
                    }
                }

                webView = this
            }
        },
        update = { view ->
            if (view.url != url) {
                view.loadUrl(url)
            }
        },
        modifier = modifier,
    )

    BackHandler(enabled = webView?.canGoBack() == true) {
        webView?.goBack()
    }
}
```

**Custom View Integration with State Updates:**

```kotlin
@Composable
fun ChartView(
    data: List<ChartDataPoint>,
    selectedIndex: Int?,
    onDataPointClick: (Int) -> Unit,
    modifier: Modifier = Modifier,
) {
    val currentOnClick by rememberUpdatedState(onDataPointClick)

    AndroidView(
        factory = { context ->
            CustomChartView(context).apply {
                setOnDataPointClickListener { index ->
                    currentOnClick(index)
                }
            }
        },
        update = { view ->
            view.setData(data)
            view.setSelectedIndex(selectedIndex)
        },
        modifier = modifier,
    )
}
```

### State Synchronization

**StateFlow -> Compose (Recommended):**

```kotlin
@Composable
fun ItemsRoute(
    viewModel: ItemsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val selectedItemId by viewModel.selectedItemId.collectAsStateWithLifecycle()

    ItemsScreen(
        uiState = uiState,
        selectedItemId = selectedItemId,
        onItemSelect = { id -> viewModel.selectItem(id) },
    )
}
```

**LiveData -> Compose (Legacy Support):**

```kotlin
@Composable
fun ItemsRoute(
    viewModel: ItemsViewModel = viewModel(),
) {
    val items by viewModel.items.observeAsState(initial = emptyList())
    ItemsList(items = items)
}
```

**StateFlow -> LiveData (for View components):**

```kotlin
class HybridViewModel : ViewModel() {
    private val _uiState = MutableStateFlow<UiState>(UiState.Loading)
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()
    val uiStateLiveData: LiveData<UiState> = uiState.asLiveData()
}
```

**Bidirectional State Flow:**

```kotlin
class SharedViewModel : ViewModel() {
    private val _searchQuery = MutableStateFlow("")
    val searchQuery: StateFlow<String> = _searchQuery.asStateFlow()
    val searchQueryLiveData: LiveData<String> = searchQuery.asLiveData()

    fun updateSearchQuery(query: String) {
        _searchQuery.value = query
    }
}
```

### Migration Strategies

**Migration Decision Matrix:**

```
PROJECT SIZE | TEAM CAPACITY | TIMELINE | RECOMMENDED STRATEGY
-------------|---------------|----------|---------------------
Small        | High          | Short    | Top-Down (new screens)
Small        | Low           | Long     | Bottom-Up (incremental)
Medium       | High          | Medium   | Feature-by-Feature
Medium       | Low           | Long     | Bottom-Up (incremental)
Large        | High          | Short    | Top-Down (new screens)
Large        | Medium        | Medium   | Feature-by-Feature
Large        | Low           | Long     | Hybrid Coexistence
Enterprise   | Any           | Any      | Hybrid Coexistence
```

## Route/Screen Separation Pattern

```kotlin
// Route Composable (Stateful Container)
@Composable
fun ItemsRoute(
    onNavigateToDetail: (String) -> Unit,
    modifier: Modifier = Modifier,
    viewModel: ItemsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val searchQuery by viewModel.searchQuery.collectAsStateWithLifecycle()

    ItemsScreen(
        uiState = uiState,
        searchQuery = searchQuery,
        onSearchQueryChange = viewModel::onSearchQueryChange,
        onItemClick = onNavigateToDetail,
        onRefresh = viewModel::refresh,
        modifier = modifier,
    )
}

// Screen Composable (Stateless, Pure)
@Composable
fun ItemsScreen(
    uiState: ItemsUiState,
    searchQuery: String,
    onSearchQueryChange: (String) -> Unit,
    onItemClick: (String) -> Unit,
    onRefresh: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Scaffold(
        topBar = {
            ItemsTopBar(
                searchQuery = searchQuery,
                onSearchQueryChange = onSearchQueryChange,
            )
        },
        modifier = modifier,
    ) { padding ->
        when (uiState) {
            ItemsUiState.Loading -> LoadingState(Modifier.padding(padding))
            is ItemsUiState.Error -> ErrorState(
                message = uiState.message,
                onRetry = onRefresh,
                modifier = Modifier.padding(padding),
            )
            is ItemsUiState.Success -> ItemsList(
                items = uiState.items,
                onItemClick = onItemClick,
                onRefresh = onRefresh,
                modifier = Modifier.padding(padding),
            )
        }
    }
}
```

## Material 3 Component Examples

### ItemCard

```kotlin
@Composable
fun ItemCard(
    item: Item,
    onClick: () -> Unit,
    onDelete: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Card(
        onClick = onClick,
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
    ) {
        Row(
            modifier = Modifier
                .padding(16.dp)
                .fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(4.dp),
            ) {
                Text(
                    text = item.name,
                    style = MaterialTheme.typography.titleMedium,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                Text(
                    text = item.description,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                )
            }
            IconButton(onClick = onDelete) {
                Icon(
                    Icons.Default.Delete,
                    contentDescription = "Delete ${item.name}",
                    tint = MaterialTheme.colorScheme.error,
                )
            }
        }
    }
}
```

### Adaptive UI with WindowSizeClass

```kotlin
@Composable
fun AdaptiveItemsScreen(
    uiState: ItemsUiState,
    selectedItemId: String?,
    onItemClick: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val windowSizeClass = currentWindowAdaptiveInfo().windowSizeClass

    when (windowSizeClass.windowWidthSizeClass) {
        WindowWidthSizeClass.COMPACT -> {
            ItemsList(
                items = (uiState as? ItemsUiState.Success)?.items.orEmpty(),
                onItemClick = onItemClick,
                modifier = modifier,
            )
        }
        WindowWidthSizeClass.MEDIUM -> {
            Row(modifier = modifier) {
                NavigationRail { /* Navigation items */ }
                ItemsList(
                    items = (uiState as? ItemsUiState.Success)?.items.orEmpty(),
                    onItemClick = onItemClick,
                    modifier = Modifier.weight(1f),
                )
            }
        }
        WindowWidthSizeClass.EXPANDED -> {
            Row(modifier = modifier) {
                ItemsList(
                    items = (uiState as? ItemsUiState.Success)?.items.orEmpty(),
                    selectedItemId = selectedItemId,
                    onItemClick = onItemClick,
                    modifier = Modifier.weight(0.4f),
                )
                VerticalDivider()
                if (selectedItemId != null) {
                    ItemDetailPane(
                        itemId = selectedItemId,
                        modifier = Modifier.weight(0.6f),
                    )
                } else {
                    EmptyDetailPane(Modifier.weight(0.6f))
                }
            }
        }
    }
}
```

### LazyList Performance Optimization

```kotlin
@Composable
fun ItemsList(
    items: List<Item>,
    onItemClick: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    LazyColumn(
        modifier = modifier,
        contentPadding = PaddingValues(vertical = 8.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        items(
            items = items,
            key = { it.id },
            contentType = { "item" },
        ) { item ->
            ItemCard(
                item = item,
                onClick = { onItemClick(item.id) },
                onDelete = { /* handle delete */ },
            )
        }
    }
}
```

### Pull-to-Refresh

```kotlin
@Composable
fun RefreshableItemsList(
    items: List<Item>,
    onRefresh: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val pullRefreshState = rememberPullToRefreshState()

    if (pullRefreshState.isRefreshing) {
        LaunchedEffect(true) {
            onRefresh()
        }
    }

    LaunchedEffect(items) {
        if (pullRefreshState.isRefreshing) {
            pullRefreshState.endRefresh()
        }
    }

    Box(modifier.nestedScroll(pullRefreshState.nestedScrollConnection)) {
        LazyColumn {
            items(items, key = { it.id }) { item ->
                ItemCard(item = item, onClick = {}, onDelete = {})
            }
        }

        PullToRefreshContainer(
            state = pullRefreshState,
            modifier = Modifier.align(Alignment.TopCenter),
        )
    }
}
```

### Modal Bottom Sheet

```kotlin
@Composable
fun ItemDetailsBottomSheet(
    item: Item,
    onDismiss: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val sheetState = rememberModalBottomSheetState()

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = sheetState,
        modifier = modifier,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Text(text = item.name, style = MaterialTheme.typography.headlineSmall)
            Text(text = item.description, style = MaterialTheme.typography.bodyLarge)
            Button(onClick = onDismiss, modifier = Modifier.align(Alignment.End)) {
                Text("Close")
            }
        }
    }
}
```

### SearchBar

```kotlin
@Composable
fun SearchBar(
    query: String,
    onQueryChange: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    OutlinedTextField(
        value = query,
        onValueChange = onQueryChange,
        modifier = modifier.fillMaxWidth(),
        placeholder = { Text("Search items...") },
        leadingIcon = { Icon(Icons.Default.Search, contentDescription = null) },
        trailingIcon = {
            if (query.isNotEmpty()) {
                IconButton(onClick = { onQueryChange("") }) {
                    Icon(Icons.Default.Clear, contentDescription = "Clear search")
                }
            }
        },
        singleLine = true,
        keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
    )
}
```

### Animation Patterns

```kotlin
@Composable
fun AnimatedItemCard(
    item: Item,
    visible: Boolean,
    modifier: Modifier = Modifier,
) {
    AnimatedVisibility(
        visible = visible,
        enter = fadeIn() + expandVertically(),
        exit = fadeOut() + shrinkVertically(),
        modifier = modifier,
    ) {
        ItemCard(item = item, onClick = {}, onDelete = {})
    }
}

@Composable
fun ExpandableCard(
    item: Item,
    expanded: Boolean,
    onToggleExpanded: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Card(
        onClick = onToggleExpanded,
        modifier = modifier
            .fillMaxWidth()
            .animateContentSize(),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(text = item.name, style = MaterialTheme.typography.titleMedium)

            if (expanded) {
                Spacer(modifier = Modifier.height(8.dp))
                Text(text = item.description, style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}
```

### Theme Implementation

```kotlin
@Composable
fun AppTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = true,
    content: @Composable () -> Unit,
) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context)
            else dynamicLightColorScheme(context)
        }
        darkTheme -> darkColorScheme(
            primary = Purple80,
            secondary = PurpleGrey80,
            tertiary = Pink80,
        )
        else -> lightColorScheme(
            primary = Purple40,
            secondary = PurpleGrey40,
            tertiary = Pink40,
        )
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = AppTypography,
        shapes = AppShapes,
        content = content,
    )
}
```

## Advanced Patterns

### Custom Layout

```kotlin
@Composable
fun StaggeredGrid(
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit,
) {
    Layout(
        content = content,
        modifier = modifier,
    ) { measurables, constraints ->
        val placeables = measurables.map { it.measure(constraints) }

        val columnHeights = IntArray(2)
        val positions = mutableListOf<Pair<Int, Int>>()

        placeables.forEach { placeable ->
            val column = if (columnHeights[0] <= columnHeights[1]) 0 else 1
            positions.add(column to columnHeights[column])
            columnHeights[column] += placeable.height
        }

        layout(
            width = constraints.maxWidth,
            height = columnHeights.maxOrNull() ?: 0,
        ) {
            placeables.forEachIndexed { index, placeable ->
                val (column, y) = positions[index]
                val x = column * constraints.maxWidth / 2
                placeable.placeRelative(x, y)
            }
        }
    }
}
```

### Complex State Management

```kotlin
@Composable
fun rememberItemListState(
    items: List<Item>,
): ItemListState {
    return remember(items) {
        ItemListState(items)
    }
}

@Stable
class ItemListState(
    items: List<Item>,
) {
    var selectedItems by mutableStateOf<Set<String>>(emptySet())
        private set

    val filteredItems by derivedStateOf {
        items.filter { it.isVisible }
    }

    fun toggleSelection(itemId: String) {
        selectedItems = if (itemId in selectedItems) {
            selectedItems - itemId
        } else {
            selectedItems + itemId
        }
    }

    fun clearSelection() {
        selectedItems = emptySet()
    }
}
```

## Accessibility Patterns

### Semantic Properties

```kotlin
@Composable
fun AccessibleButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
) {
    Button(
        onClick = onClick,
        enabled = enabled,
        modifier = modifier.semantics {
            contentDescription = text
            role = Role.Button
            stateDescription = if (enabled) "enabled" else "disabled"
            customActions = listOf(
                CustomAccessibilityAction("Long press for options") {
                    true
                }
            )
        }
    ) {
        Text(text)
    }
}
```

### Content Grouping

```kotlin
@Composable
fun AccessibleCard(
    title: String,
    subtitle: String,
    imageUrl: String?,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Card(
        onClick = onClick,
        modifier = modifier.semantics(mergeDescendants = true) {
            contentDescription = buildAnnotatedString {
                append(title)
                append(", ")
                append(subtitle)
                if (imageUrl != null) {
                    append(", has image")
                }
            }.text

            onClick(label = "Open $title") {
                onClick()
                true
            }
        }
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            if (imageUrl != null) {
                AsyncImage(
                    model = imageUrl,
                    contentDescription = null,
                    modifier = Modifier.size(64.dp),
                )
            }
            Column(
                modifier = Modifier
                    .weight(1f)
                    .padding(start = 16.dp)
            ) {
                Text(text = title)
                Text(text = subtitle)
            }
        }
    }
}
```

### Touch Target Size

```kotlin
fun Modifier.minimumTouchTarget(
    size: Dp = 48.dp,
): Modifier = composed {
    this.then(
        Modifier.sizeIn(minWidth = size, minHeight = size)
    )
}

@Composable
fun AccessibleIconButton(
    icon: ImageVector,
    contentDescription: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    IconButton(
        onClick = onClick,
        modifier = modifier.minimumTouchTarget(),
    ) {
        Icon(
            imageVector = icon,
            contentDescription = contentDescription,
        )
    }
}
```

### Live Region Announcements

```kotlin
@Composable
fun ItemsLoadedAnnouncement(itemCount: Int) {
    val announcement = remember(itemCount) {
        "$itemCount items loaded"
    }

    Text(
        text = announcement,
        modifier = Modifier
            .clearAndSetSemantics {
                liveRegion = AccessibilityLiveRegion.Polite
                contentDescription = announcement
            }
            .alpha(0f)
    )
}
```

### Form Accessibility

```kotlin
@Composable
fun AccessibleTextField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
    error: String? = null,
    modifier: Modifier = Modifier,
) {
    Column(modifier = modifier) {
        OutlinedTextField(
            value = value,
            onValueChange = onValueChange,
            label = { Text(label) },
            isError = error != null,
            modifier = Modifier
                .fillMaxWidth()
                .semantics {
                    if (error != null) {
                        error(error)
                    }
                    contentDescription = buildString {
                        append(label)
                        append(" text field")
                        if (error != null) {
                            append(", error: $error")
                        }
                    }
                }
        )

        if (error != null) {
            Text(
                text = error,
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.bodySmall,
                modifier = Modifier
                    .padding(start = 16.dp, top = 4.dp)
                    .semantics {
                        liveRegion = AccessibilityLiveRegion.Assertive
                    }
            )
        }
    }
}
```

### Navigation Accessibility

```kotlin
@Composable
fun AccessibleNavigationBar(
    items: List<NavigationItem>,
    selectedIndex: Int,
    onItemSelected: (Int) -> Unit,
) {
    NavigationBar {
        items.forEachIndexed { index, item ->
            NavigationBarItem(
                icon = { Icon(item.icon, contentDescription = null) },
                label = { Text(item.label) },
                selected = selectedIndex == index,
                onClick = { onItemSelected(index) },
                modifier = Modifier.semantics {
                    contentDescription = buildString {
                        append(item.label)
                        append(" tab")
                        if (selectedIndex == index) {
                            append(", selected")
                        }
                        append(", ${index + 1} of ${items.size}")
                    }
                }
            )
        }
    }
}
```

### Dialog Accessibility

```kotlin
@Composable
fun AccessibleDialog(
    title: String,
    message: String,
    onDismiss: () -> Unit,
    onConfirm: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text(
                text = title,
                modifier = Modifier.semantics { heading() }
            )
        },
        text = {
            Text(
                text = message,
                modifier = Modifier.semantics {
                    liveRegion = AccessibilityLiveRegion.Polite
                }
            )
        },
        confirmButton = {
            TextButton(
                onClick = onConfirm,
                modifier = Modifier.semantics {
                    contentDescription = "Confirm $title"
                }
            ) { Text("Confirm") }
        },
        dismissButton = {
            TextButton(
                onClick = onDismiss,
                modifier = Modifier.semantics {
                    contentDescription = "Cancel $title"
                }
            ) { Text("Cancel") }
        },
        modifier = Modifier.semantics { paneTitle = title }
    )
}
```

### List Accessibility

```kotlin
@Composable
fun AccessibleLazyColumn(
    items: List<String>,
    modifier: Modifier = Modifier,
) {
    LazyColumn(
        modifier = modifier.semantics {
            contentDescription = "${items.size} items"
            collectionInfo = CollectionInfo(rowCount = items.size, columnCount = 1)
        }
    ) {
        itemsIndexed(items, key = { _, item -> item }) { index, item ->
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(8.dp)
                    .semantics {
                        collectionItemInfo = CollectionItemInfo(
                            rowIndex = index, rowSpan = 1,
                            columnIndex = 0, columnSpan = 1
                        )
                        contentDescription = "$item, item ${index + 1} of ${items.size}"
                    }
            ) {
                Text(text = item, modifier = Modifier.padding(16.dp))
            }
        }
    }
}
```

### Custom Accessibility Actions

```kotlin
@Composable
fun AccessibleItemCard(
    item: Item,
    onEdit: () -> Unit,
    onDelete: () -> Unit,
    onShare: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Card(
        modifier = modifier.semantics {
            contentDescription = item.name
            customActions = listOf(
                CustomAccessibilityAction("Edit") { onEdit(); true },
                CustomAccessibilityAction("Delete") { onDelete(); true },
                CustomAccessibilityAction("Share") { onShare(); true },
            )
        }
    ) {
        Text(item.name)
    }
}
```

### Accessibility Testing

```kotlin
@Test
fun itemCard_hasCorrectSemantics() {
    composeTestRule.setContent {
        ItemCard(item = Item("Test Item"), onClick = {}, onDelete = {})
    }

    composeTestRule
        .onNodeWithContentDescription("Test Item")
        .assertExists()
        .assertHasClickAction()

    composeTestRule
        .onNodeWithText("Test Item")
        .assertHeightIsAtLeast(48.dp)
        .assertWidthIsAtLeast(48.dp)

    composeTestRule
        .onNodeWithContentDescription("Delete")
        .assertExists()
        .assertHasClickAction()
}
```

## Compose Navigation with Type-Safe Routes

### @Serializable Route Definitions

```kotlin
// Simple object route (no parameters)
@Serializable
data object HomeRoute

// Route with required parameter
@Serializable
data class ItemDetailRoute(val itemId: String)

// Route with optional parameters and defaults
@Serializable
data class SearchRoute(
    val query: String = "",
    val category: String? = null,
    val sortBy: SortOrder = SortOrder.DATE,
)

@Serializable
enum class SortOrder { DATE, NAME, RELEVANCE }
```

### NavHost with Type-Safe Composables

```kotlin
@Composable
fun AppNavHost(
    navController: NavHostController = rememberNavController(),
    modifier: Modifier = Modifier,
) {
    NavHost(
        navController = navController,
        startDestination = HomeRoute,
        modifier = modifier,
    ) {
        composable<HomeRoute> {
            HomeRoute(
                onNavigateToItem = { itemId ->
                    navController.navigate(ItemDetailRoute(itemId))
                },
                onNavigateToSearch = { query ->
                    navController.navigate(SearchRoute(query = query))
                },
            )
        }

        composable<ItemDetailRoute> { backStackEntry ->
            val route = backStackEntry.toRoute<ItemDetailRoute>()
            ItemDetailRoute(itemId = route.itemId)
        }

        composable<SearchRoute> { backStackEntry ->
            val route = backStackEntry.toRoute<SearchRoute>()
            SearchRoute(
                initialQuery = route.query,
                category = route.category,
                sortBy = route.sortBy,
            )
        }
    }
}
```

### Nested Navigation Graphs

```kotlin
// Define graph-level route markers
@Serializable
data object SettingsGraphRoute

@Serializable
data object SettingsMainRoute

@Serializable
data object SettingsNotificationsRoute

@Serializable
data object SettingsPrivacyRoute

// Nested graph in NavHost
NavHost(navController = navController, startDestination = HomeRoute) {
    composable<HomeRoute> { /* ... */ }

    navigation<SettingsGraphRoute>(startDestination = SettingsMainRoute) {
        composable<SettingsMainRoute> {
            SettingsMainScreen(
                onNavigateToNotifications = {
                    navController.navigate(SettingsNotificationsRoute)
                },
                onNavigateToPrivacy = {
                    navController.navigate(SettingsPrivacyRoute)
                },
            )
        }

        composable<SettingsNotificationsRoute> {
            NotificationsSettingsScreen(
                onBack = { navController.popBackStack() },
            )
        }

        composable<SettingsPrivacyRoute> {
            PrivacySettingsScreen(
                onBack = { navController.popBackStack() },
            )
        }
    }
}
```

### Multi-Module Feature Navigation

```kotlin
// feature/settings/api/SettingsNavigation.kt
@Serializable
data object SettingsGraphRoute

// feature/settings/impl/SettingsNavigation.kt
fun NavGraphBuilder.settingsGraph(
    onNavigateBack: () -> Unit,
) {
    navigation<SettingsGraphRoute>(startDestination = SettingsMainRoute) {
        composable<SettingsMainRoute> {
            SettingsRoute(onBack = onNavigateBack)
        }
        composable<SettingsNotificationsRoute> {
            NotificationsRoute(onBack = onNavigateBack)
        }
    }
}

// app/AppNavHost.kt — wire feature graphs
NavHost(navController = navController, startDestination = HomeRoute) {
    composable<HomeRoute> {
        HomeRoute(
            onNavigateToSettings = {
                navController.navigate(SettingsGraphRoute)
            },
        )
    }

    settingsGraph(
        onNavigateBack = { navController.popBackStack() },
    )
}
```

## Decision Council Protocol - UI Example

```markdown
## Decision: Material 3 Adoption for Redesigned Profile Feature

### Status Quo Advocate's Position:
"The app uses Material 2 components in 35 screens across all features.
Full Material 3 migration introduces visual inconsistency and design debt."

### Best Practices Advocate's Position:
"Material 3 is the modern design system recommended by Google since 2021.
Dynamic color, improved accessibility, modern component shapes, better dark mode."

### Pragmatic Synthesis:
Recommendation: Use Material 3 with visual bridge strategy
- Phase 1: Profile feature only (Material 3)
- Create visual bridge guide (M2->M3 mapping)
- A/B test with 10% users for 2 weeks
- Phase 2: New features use Material 3 (Q3)
- Phase 3: Migrate high-traffic screens (Q4)
```

## Accessibility Checklist

```
CONTENT DESCRIPTIONS
- All interactive elements have descriptions
- Decorative images have null descriptions
- Informational images have meaningful descriptions
- State changes announced

TOUCH TARGETS
- Minimum 48dp touch target size
- Sufficient spacing between targets (8dp+)
- Focus indicators visible

SCREEN READER SUPPORT
- Content properly grouped (mergeDescendants)
- Reading order logical
- Headings marked with heading()
- Live regions for dynamic content
- Custom actions for complex interactions

COLOR & CONTRAST
- Text contrast ratio >= 4.5:1 (normal)
- Text contrast ratio >= 3:1 (large)
- Interactive elements contrast >= 3:1
- Color not sole indicator
- Dark mode support

NAVIGATION
- Keyboard navigation supported
- Focus order logical
- Tab order correct

FORMS
- Labels associated with inputs
- Error messages clear
- Required fields indicated

TESTING
- TalkBack tested (Android)
- Switch Access tested
- Font scaling tested (200%)
- Dark/light mode tested
```

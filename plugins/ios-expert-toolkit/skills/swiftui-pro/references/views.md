# SwiftUI Views

View structure (separate `View` structs instead of computed properties, `Group` with one child, cheap `init`) is covered by Apple's `structure.md` in swiftui-specialist; follow it. Small private helper properties that belong to the same concern as `body` and would fit in `body` if inlined may stay.

- Flag `body` properties that are excessively long; extract subviews as described in `structure.md`.
- Button actions should be extracted from view bodies into separate methods, to avoid mixing layout and logic.
- Similarly, general business logic should not live inline in `task()`, `onAppear()` or elsewhere in `body`.
- Prefer to place view logic into view models or similar, so it can be tested. For more help with testing, suggest the `swift-testing-expert` skill.
- Each type (struct, class, enum) should be in its own Swift file. Flag files containing multiple type definitions.
- Unless a full-screen editing experience is required, prefer using `TextField` with `axis: .vertical` to using `TextEditor`, because it allows placeholder text. If a specific minimum height is required for `TextField`, use something like `lineLimit(5...)`.
- If a button action can be provided directly as an `action` parameter, do so. For example: `Button("Label", systemImage: "plus", action: myAction)` is preferred over `Button("Label", systemImage: "plus") { action() }`.
- When rendering SwiftUI views to images, strongly prefer `ImageRenderer` over `UIGraphicsImageRenderer`.
- `#Preview` should be used for previews, not the legacy `PreviewProvider` protocol.
- When using `TabView(selection:)`, use a binding to a property that stores an enum rather than an integer or string. For example, `Tab("Home", systemImage: "house", value: .home)` is better than `Tab("Home", systemImage: "house", value: 0)`.


## Animating views

Custom `Animatable` types and the `@Animatable` macro are covered by Apple's `animations.md` in swiftui-specialist; the deprecated `AnimatableModifier` is listed in its `soft-deprecated-apis.md`.

- Never use `animation(_ animation: Animation?)`; always provide a value to watch, such as `.animation(.bouncy, value: score)`.
- Chaining animations must be done using a `completion` closure passed to `withAnimation()`, rather than trying to execute multiple `withAnimation()` calls using delays.

For example:

```swift
Button("Animate Me") {
    withAnimation {
        scale = 2
    } completion: {
        withAnimation {
            scale = 1
        }
    }
}
```


## Reordering and swipe actions

Swipe actions in scroll views: see `swiftui-whats-new-27` `references/swipe-actions.md`.

Reordering requires iOS 27+ and is unavailable on tvOS.

- Enable drag reordering with `reorderable()` on the `ForEach` and `reorderContainer(for:)` on its enclosing container. Apply the callback's `ReorderDifference` to the source data yourself; SwiftUI does not mutate it. This works in lists, lazy stacks and grids, ordinary stacks, and custom layouts. Earlier versions require `List` with `onMove()` or a custom drag implementation. Elements must conform to `Identifiable`, or use the `itemID:` overload.

For example:

```swift
ScrollView {
    LazyVStack {
        ForEach(bookmarks) { bookmark in
            BookmarkRow(bookmark: bookmark)
        }
        .reorderable()
    }
    .reorderContainer(for: Bookmark.self) { change in
        change.apply(to: &bookmarks)
    }
}
```

SwiftUI has no built-in way to apply this difference. Add a helper like this one, adapted from an Apple example, in its own file:

```swift
extension ReorderDifference where CollectionID == ReorderableSingleCollectionIdentifier {
    func apply<Items>(to items: inout Items)
    where Items: RangeReplaceableCollection,
          Items.Element: Identifiable,
          Items.Element.ID == ItemID {
        let sourceIDs = Set(sources)
        var relocated: [Items.Element] = []

        items.removeAll { candidate in
            if sourceIDs.contains(candidate.id) {
                relocated.append(candidate)
                return true
            }
            return false
        }

        switch destination.position {
        case .before(let followingID):
            let insertionPoint = items.firstIndex { $0.id == followingID } ?? items.endIndex
            items.insert(contentsOf: relocated, at: insertionPoint)
        case .end:
            items.append(contentsOf: relocated)
        }
    }
}
```

- For moves across sections, identify each inner collection with `reorderable(collectionID:)`, and use `reorderContainer(for:in:)` on the enclosing container. Read `difference.destination.collectionID` to determine the receiving section.
- Reordering needs no drag-and-drop code; `reorderContainer(for:)` already acts as the drag container. Add `dragContainer(for:)` to the same container only when items should also take part in system drag and drop, such as dragging out to other views or apps, and make the item type `Transferable`. A `draggable()` on a row has no effect on reordering.

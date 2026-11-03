# swiftui-pro fork notes

Upstream: [twostraws/SwiftUI-Agent-Skill](https://github.com/twostraws/SwiftUI-Agent-Skill),
tag `2.0.0`, commit `f9800713b24580bc444931949aad4519128605e8` (see `ios-skills.lock`).
Check for upstream changes with `scripts/sync-ios-skills.sh --fork-ref <ref>`, which
prints a diff and writes nothing.

The review steps and the output format (file, line, rule, before/after, summary) are unchanged.
The sha256 of every reference kept byte for byte is in `ios-skills.lock` (`fork.swiftui-pro.sha256.*`).

## Removed, delegated to Apple's swiftui-specialist

| Upstream file | Review step now loads |
|---|---|
| `references/api.md` | `swiftui-specialist` `soft-deprecation.md` + `soft-deprecated-apis.md`; iOS 27 toolbar rules: `swiftui-whats-new-27` `references/toolbar.md` |
| `references/data.md` | `swiftui-specialist` `dataflow.md` + `environment.md` + `foreach.md` |
| `references/localization.md` | `swiftui-specialist` `localization.md` |

Kept references still mention `api.md` (`resizability.md`, toolbar rules) and `views.md`.
They stay unedited so the lock hashes hold; `SKILL.md` maps those names to the replacements.

## views.md versus Apple structure.md and modifiers.md

| Upstream `views.md` rule | Decision |
|---|---|
| Avoid `some View` computed properties or methods; extract `View` structs (stated twice) | Dropped. `structure.md` covers it, with the tiny-fragment exception. |
| Small private helpers may stay | Kept as one sentence, because `performance.md` points here for view-extraction exceptions. |
| Remove a `Group` wrapping one view | Dropped. `structure.md` "Single Child Group" covers it. |
| Flag excessively long `body` | Kept, pointing at `structure.md`. |
| Extract button actions and business logic out of `body`/`task()`/`onAppear()` | Kept. Apple does not cover it. |
| View logic in testable view models; one type per file | Kept. Apple does not cover it. |
| `TextField(axis: .vertical)` over `TextEditor`; `Button(action:)` direct; `ImageRenderer`; `#Preview`; enum `TabView` selection | Kept. Apple does not cover them. |
| `@Animatable` macro, `AnimatableModifier` deprecation | Dropped. `animations.md` and `soft-deprecated-apis.md` cover them. |
| `animation(_:)` needs `value:`; chain with `withAnimation` completion | Kept. Apple does not cover them. |
| Reordering (`reorderable`, `reorderContainer`) | Kept. Apple does not cover it. |
| Swipe actions in scroll views | Replaced with a pointer to `swiftui-whats-new-27` `swipe-actions.md`. |
| Conditional modifiers (not in upstream `views.md`) | Not needed here; `modifiers.md` owns it. |

## Known coverage loss

`data.md` and `api.md` held rules that Apple's files do not repeat verbatim, for example
numeric `TextField` formatting, scene-scoped state, and the `GeometryReader` alternatives.
The fork accepts that loss for the three delegated files, as specified. Restore any of them
in a new reference if reviews miss them.

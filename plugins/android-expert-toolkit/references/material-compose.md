# Material Design for Compose

Material 3 for Jetpack Compose (`androidx.compose.material3`): where the guidance lives, how to fetch it, and the rules that hold on every screen. Theme wiring and code patterns stay in [theme](compose-ui.md#theme); this file adds the design guidelines.

Material's new work lands in Compose first: the Views library is in maintenance mode ([status-maintenance-mode](material-views.md#status-maintenance-mode)).

## Fetching

Pages come from the Android Knowledge Base through the `android` CLI:

```bash
android docs fetch kb://android/develop/ui/compose/components/<page>
android docs search "compose <component>"
```

- Fetch from the page map below first. Search only for a page the map lacks.
- Keep only `kb://android/develop/ui/compose/` and `kb://android/design/ui/mobile/` hits. Search also returns Wear OS, TV, XR and Views pages for the same words, and ranks quick guides (`compose/quick-guides/`) above the component page.
- `android docs fetch` exits 1 when the page does not exist; search again instead of guessing a name.
- Without the `android` CLI, open the same path on `https://developer.android.com/` with the runtime's web tool; `kb://android/develop/ui/compose/components/button` is `https://developer.android.com/develop/ui/compose/components/button`.
- Cite the page URL for every rule, size or API the answer states.

## Design guides for both toolkits

`kb://android/design/ui/mobile/guides/` holds Android's own Material design guidance. It applies to Compose and Views alike.

| Topic | Page |
|-------|------|
| Material components overview, links to m3.material.io | `components/material-overview` |
| Color roles | `styles/color` |
| dp, sp, 8 dp grid, layout grids, size classes | `layout-and-content/grids-and-units` |
| App anatomy, common layouts, nav patterns, adapting layouts | `layout-and-content/app-anatomy`, `common-layouts`, `layout-and-nav-patterns`, `adapt-layout` |
| Edge-to-edge, immersive content, system bars | `layout-and-content/edge-to-edge`, `immersive-content`, `foundations/system-bars` |
| Accessibility | `foundations/accessibility` |
| Predictive back, settings screens | `patterns/predictive-back`, `patterns/settings` |
| Home screen widgets | `widgets/*` |

## Compose pages

Theming: `kb://android/develop/ui/compose/designsystems/material3` (color scheme, dynamic color, typography, shapes, experimental APIs).

Components, under `kb://android/develop/ui/compose/components/`:

| Group | Pages |
|-------|-------|
| Actions | `button`, `icon-button`, `fab`, `segmented-button` |
| Containment | `card`, `dialog`, `bottom-sheets`, `divider`, `carousel`, `tooltip` |
| Navigation | `app-bars`, `app-bars-dynamic`, `navigation-bar`, `navigation-rail`, `drawer`, `tabs`, `search-bar` |
| Selection | `checkbox`, `radio-button`, `switch`, `chip`, `slider`, `datepickers`, `time-pickers`, `menu` |
| Communication | `badges`, `progress`, `snackbar`, `pull-to-refresh` |
| Layout | `scaffold` |

Text fields are under `kb://android/develop/ui/compose/text/user-input`. Swipe to dismiss is under `kb://android/develop/ui/compose/touch-input/user-interactions/swipe-to-dismiss`.

The page list was checked on 2026-11-23; a new component may have a page that is not listed, so search before saying there is none. When a component has no Compose page (for example a newer M3 Expressive component), say so, take its design intent from the matching m3.material.io or Views doc, and check its API in the `androidx.compose.material3` reference or release notes, never from memory.

## Rules

1. **Theme tokens, not literals.** Color, type and shape come from `MaterialTheme`; see [theme](compose-ui.md#theme).
2. **Choose by emphasis.** Pick the component variant whose documented purpose matches the action's priority: filled for high-emphasis primary actions, outlined for important secondary actions, text for low-emphasis ones (`components/button`). Read the component page's purpose table before picking a variant.
3. **Dynamic color is Android 12+.** Use `dynamicLightColorScheme` / `dynamicDarkColorScheme` only when `Build.VERSION.SDK_INT >= Build.VERSION_CODES.S`, and fall back to the app's own scheme (`designsystems/material3`).
4. **Experimental APIs need an opt-in.** Annotate with `@OptIn(ExperimentalMaterial3Api::class)` at the narrowest scope, and check the project's Compose BOM before using one (`designsystems/material3`).
5. **Dimensions in dp, text in sp.** Layout, components and spacing follow the 8 dp grid; small elements such as icons align to a 4 dp grid (`grids-and-units`).
6. **Touch targets at least 48 dp,** even when the visual element is smaller (`foundations/accessibility`). Custom clickable composables need it as much as Material ones.
7. **Body text at least 12 sp** (`foundations/accessibility`), and test at large font scales.
8. **Prefer the Material component over a hand-built one.** A custom row with `clickable` and a `Text` loses the component's states, semantics and touch target; wrap or style the Material component instead.

# Material Design for Views (XML)

Material Components for Android (`com.google.android.material`, MDC-Android) on the View system: themes, widget styles and theme attributes. Docs are fetched with `/android-material-design`, which owns the fetch scripts and exit codes.

## Status: maintenance mode

Since Google I/O 2026 the Views library is in maintenance mode: no more planned feature releases, and Material's new work lands in Compose first ([getting-started](https://github.com/material-components/material-components-android/blob/master/docs/getting-started.md)).

- Fix and extend existing XML screens in place; match the project (`/android-conventions`).
- For a new screen in a project that already has Compose, recommend Compose ([material-compose](material-compose.md)). Migrating a screen → `/migrate-xml-views-to-jetpack-compose` skill.
- Don't promise a View-side version of a component that only ships in Compose.

## Rules

1. **Theme parent.** App themes inherit `Theme.Material3.*` (for example `Theme.Material3.DayNight.NoActionBar`). `Theme.Material3Expressive.*` is required for `Widget.Material3Expressive.*` styles and needs library `1.14.0-alpha01` or later. Apps that must stay on an `AppCompat` or `MaterialComponents` theme add the new theme attributes instead; the getting-started doc lists them.
2. **Activities extend `AppCompatActivity`** (or use `AppCompatDelegate`) so Material versions of widgets inflate.
3. **Colors from theme attributes.** Layouts and styles use `?attr/colorPrimary`, `?attr/colorSurface`, `?attr/colorOnSurface` and the other color roles, never a literal `#RRGGBB` or a raw `@color` in a widget. Dynamic color: `DynamicColors.applyToActivitiesIfAvailable(application)`, or a `Theme.Material3.DynamicColors.*` parent.
4. **Type from text appearances.** Text uses `?attr/textAppearanceBodyLarge`, `?attr/textAppearanceTitleMedium` and the other type-scale roles, not a raw `android:textSize`. Sizes are in `sp`.
5. **Component styles over per-view overrides.** Pick the documented `Widget.Material3.*` style (`?attr/materialButtonOutlinedStyle`, a `style="@style/Widget.Material3.Button.TonalButton"`), and theme a subtree with a `ThemeOverlay.Material3.*` rather than repeating attributes on every view.
6. **Version-check new attributes.** The docs track `master`, so an attribute may be newer than the project's pinned library. Read the version from the catalog and check the release notes before recommending it.

## Docs to fetch

`/android-material-design` resolves names to the `docs/` tree of `material-components-android`: `components/*` (one page per widget), `theming/*` (Color, Typography, Shape, Dark, Motion), `foundations/*` and `adaptive/*`. Run its catalog for the full list. `button` resolves to `CommonButton.md`; `Button.md` is only an index.

Design guidance that applies to both toolkits (layout grid, touch targets, system bars) is in [design-guides-for-both-toolkits](material-compose.md#design-guides-for-both-toolkits).

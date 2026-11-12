# Review Output Template

The exact block a review prints. Rules (rows, grading, verdict) live in [review-rules](../references/review-rules.md). Shape matches the avengers-council verdict block and the findings-block format: emoji headline, `| | |` summary, then grouped two-line findings.

## Rules

- Headline: `### ✅ Android review — Approve` or `### ⚠️ Android review — Changes needed`.
- The row table lists only ❌ FAIL rows, in row order. ✅ and ⏩ rows go on the two lines under it as IDs; ⏩ IDs carry their reason in parentheses.
- Groups, in this order, omitted when empty: `#### ❌ Fails ({n}) — counted in the verdict`, `#### 📋 Pre-existing ({n}) — not counted in the verdict` (diff reviews only), `#### 🔔 Notes ({n}) — project convention differs from the rubric`.
- Inside a group, sort by severity 🔴 🟠 🟡 🟢, then by first row ID; number across groups.
- Each finding is two lines: `{n}. {sev} **{issue}** — `file:line` · {row IDs}` then `    → {fix}`. No code blocks, diffs or prose between findings.
- No ❌ rows: print the summary table, then `No findings.`
- Counts: **Rows** counts rows; **Findings** counts listed findings per group. They must equal what is printed. A whole-file review prints `{n} fails · {n} notes`; only a diff review adds `· {n} pre-existing`.

## Template

```markdown
### ⚠️ Android review — Changes needed

| | |
|---|---|
| **Subject** | diff vs `main`: `FeedScreen.kt` |
| **Rows** | ✅ 6 pass · ❌ 3 fail · ⏩ 4 n/a |
| **Findings** | 2 fails · 1 pre-existing · 0 notes |

| ID | Criterion | Evidence |
|----|-----------|----------|
| C1 | Design Cohesion | `FeedScreen.kt:43` raw `Color(0xFF222222)`, `22.sp` |
| C4 | Performance | `FeedScreen.kt:42` LazyColumn inside `verticalScroll` |
| compose-ui.2 | No hardcoded strings, colors, sizes | `FeedScreen.kt:43` |

✅ C2, C3, A4, A5, coroutines.1, coroutines.2
⏩ C5 (no navigation chrome), A1 (single file), A3 (repository not in scope), coroutines.6 (no tests)

#### ❌ Fails (2) — counted in the verdict

1. 🔴 **LazyColumn inside a `verticalScroll` Column crashes on unbounded height** — `FeedScreen.kt:42` · C4
    → Drop `verticalScroll`; make the header an `item { }` in the LazyColumn
2. 🟡 **Hardcoded title color and size** — `FeedScreen.kt:43` · C1, compose-ui.2
    → Use `MaterialTheme.typography.titleLarge` and the theme's `onSurface`

#### 📋 Pre-existing (1) — not counted in the verdict

3. 🟡 **`runCatching` around a suspend call** — `SettingsRepository.kt:88` · coroutines.2
    → Rethrow `CancellationException` in a follow-up change
```

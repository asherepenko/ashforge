# Review Output Template

The exact block a review prints. Rules (rows, grading, verdict) live in [review-rules](../references/review-rules.md). Shape matches the avengers-council verdict block and the findings-block format: emoji headline, `| | |` summary, then grouped two-line findings.

## Rules

- Headline: `### ✅ iOS review — Approve` or `### ⚠️ iOS review — Changes needed`.
- The row table lists only ❌ FAIL rows, in row order. ✅ and ⏩ rows go on the two lines under it as IDs; ⏩ IDs carry their reason in parentheses.
- Groups, in this order, omitted when empty: `#### ❌ Fails ({n}) — counted in the verdict`, `#### 📋 Pre-existing ({n}) — not counted in the verdict` (diff reviews only), `#### 🔔 Notes ({n}) — project convention differs from the rubric`.
- Inside a group, sort by severity 🔴 🟠 🟡 🟢, then by first row ID; number across groups.
- Each finding is two lines: `{n}. {sev} **{issue}** — `file:line` · {row IDs}` then `    → {fix}`. No code blocks, diffs or prose between findings.
- No ❌ rows: print the summary table, then `No findings.`
- Counts: **Rows** counts rows; **Findings** counts listed findings per group. They must equal what is printed. A whole-file review prints `{n} fails · {n} notes`; only a diff review adds `· {n} pre-existing`.

## Template

```markdown
### ⚠️ iOS review — Changes needed

| | |
|---|---|
| **Subject** | diff vs `main`: `FeedView.swift` |
| **Rows** | ✅ 5 pass · ❌ 3 fail · ⏩ 3 n/a |
| **Findings** | 3 fails · 1 pre-existing · 0 notes |

| ID | Criterion | Evidence |
|----|-----------|----------|
| C1 | Design Cohesion | `FeedView.swift:31` raw `Color(red: 0.13, green: 0.13, blue: 0.13)`, `.font(.system(size: 22))` |
| C4 | Performance | `FeedView.swift:40` `ForEach(items.indices, id: \.self)` |
| A3 | State and Data Flow | `FeedView.swift:12` view loads data in `onAppear` |

✅ C2, C3, A4, A5, A6
⏩ C5 (no size classes in scope), A1 (single file), A2 (single file)

#### ❌ Fails (3) — counted in the verdict

1. 🟠 **`ForEach` over indices loses row identity on insert and delete** — `FeedView.swift:40` · C4
    → `ForEach(items)` with `Identifiable` items
2. 🟡 **Hardcoded title color and size** — `FeedView.swift:31` · C1
    → `.font(.title2)` and `.foregroundStyle(.primary)`
3. 🟡 **The view loads data in `onAppear`** — `FeedView.swift:12` · A3
    → Load in the model from `.task { await model.load() }`

#### 📋 Pre-existing (1) — not counted in the verdict

4. 🟡 **`try?` hides a decoding error** — `SettingsClient.swift:88` · A4
    → Catch and map the error in a follow-up change
```

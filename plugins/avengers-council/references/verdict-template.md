# Verdict Output Template

Use this exact structure for the final council verdict output.

For full consensus rules and severity guidelines, see @references/verdict-rules.md

```markdown
# Avengers Council Verdict

## Topic
[What was reviewed]

## Consensus: [APPROVED | APPROVED WITH CONDITIONS | NEEDS REVISION | BLOCKED]
**Vote**: X Approve / X Concerns / X Reject (N voters)
**Average Domain Score**: X.X/10

## Executive Summary
[2-3 sentences from Captain America]

## Council Positions

### Iron Man (Architecture & Scalability) — [VERDICT] | Score: X/10
- [Finding 1]
- [Finding 2]

### Thor (Backend & API) — [VERDICT] | Score: X/10
- [Finding 1]

### Scarlet Witch (Frontend & UX) — [VERDICT] | Score: X/10
- [Finding 1]

### Hulk (Testing & QA) — [VERDICT] | Score: X/10
- [Finding 1]

### Black Widow (Security & Privacy) — [VERDICT] | Score: X/10
- [Finding 1]

### Hawkeye (Mobile Platforms) — [VERDICT] | Score: X/10
- [Finding 1]

### Vision (Data & Observability) — [VERDICT] | Score: X/10
- [Finding 1]

### Doctor Strange (DevOps & Cross-platform) — [VERDICT] | Score: X/10
- [Finding 1]

### Captain America (Standards & Delivery) — [VERDICT]
- [Finding 1]

<!-- If optional members participated, add their positions here -->
### [Optional Member Name] ([Domain]) — [VERDICT] | Score: X/10
- [Finding 1]
<!-- End optional members -->

## Domain Scores

| Member | Domain | Score |
|--------|--------|-------|
| Iron Man | Architecture & Scalability | X/10 |
| Thor | Backend & API | X/10 |
| Scarlet Witch | Frontend & UX | X/10 |
| Hulk | Testing & QA | X/10 |
| Black Widow | Security & Privacy | X/10 |
| Hawkeye | Mobile Platforms | X/10 |
| Vision | Data & Observability | X/10 |
| Doctor Strange | DevOps & Infrastructure | X/10 |
| *[Optional members — add rows if active]* | | |

**Average: X.X/10** | **Voters: N** | [Interpretation per verdict-rules.md]

## Disagreements
[Specific points where members disagree, with reasoning]

## Tiebreaker (if applicable)
[Captain America's deciding rationale]

## Conditions for Approval
[Items that must be addressed]

## Action Items
1. [Actionable item with owner suggestion]
2. [...]

---
> **Verdict saved to:** `[absolute file path]`
```

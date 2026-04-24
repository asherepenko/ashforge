# Pipeline Summary Template

Use this template for Step 8 (Generate Summary) after pipeline completes.

## Report Format

```markdown
# Pipeline Summary: [Pipeline Type]

**Feature:** [Feature Name]
**Started:** [Timestamp]
**Completed:** [Timestamp]
**Total Duration:** [Duration]

## Stage Metrics
| Stage | Agent | Duration | Artifact Size | Validation |
|-------|-------|----------|---------------|------------|
| 1 | android-architect | 12m | 4.2 KB | Passed |
| 2 | gradle-build-engineer | 5m | 2.1 KB | Passed |
| 3 | android-developer | 18m | 6.8 KB | Passed |
| 4 | compose-expert | 15m | 5.4 KB | Passed |
| 5 | android-testing-specialist | 10m | 7.1 KB | Passed |

## Artifacts Created
- Module: feature/{feature_slug}/impl/
- Files: [N] Kotlin files, [N] test files
- Coverage: [N]%
- Total artifact size: [N] KB
- Validation passes: [N]/[N]

## Next Steps
- [Manual testing instructions]
- [Deployment checklist]
```

## Completion Metrics (aet/state.json)

After generating the report, store metrics in pipeline state:

```json
{
  "completed_at": "2026-02-18T16:30:00Z",
  "total_duration_seconds": 3600,
  "stage_durations": {
    "android-architect": 720,
    "gradle-build-engineer": 300,
    "android-developer": 1080,
    "compose-expert": 900,
    "android-testing-specialist": 600
  },
  "artifact_sizes": {
    "architecture-blueprint": 4200,
    "module-setup": 2100,
    "implementation-report": 6800,
    "ui-report": 5400,
    "test-report": 7100
  },
  "validation_counts": {
    "passed": 5,
    "failed": 0,
    "skipped": 0
  }
}
```

## Squash-Merge

After pipeline completes successfully, offer to squash-merge the pipeline branch:

```bash
git checkout <original-branch>
git merge --squash aet/{feature_slug}/{run_timestamp}
git commit -m "feat: {feature_name} via android-expert pipeline

Pipeline: {pipeline_type}
Stages: {comma-separated list of completed agents}
Artifacts: .artifacts/aet/handoffs/{feature_slug}/"
```

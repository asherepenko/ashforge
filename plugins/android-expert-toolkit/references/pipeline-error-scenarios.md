# Pipeline Error Scenarios

Common error scenarios encountered during pipeline execution, with detailed recovery walkthroughs.

Referenced from `commands/aet-pipeline.md`. See also: SKILL.md Error Recovery section.

## When to use

Read this reference when the pipeline command encounters an error (incomplete handoff artifact, failed build, missing validation input) and you need a documented recovery path. Used by the pipeline orchestrator when surfacing recovery options to the user.

---

### Common Error Scenarios

#### Scenario 1: Incomplete Handoff Artifact

**Error:**
```
✗ .artifacts/aet/handoffs/social-feed/2026-02-18-143022-architecture-blueprint.md validation failed
Missing required sections:
  - Decisions
  - Next Steps
```

**Recovery:**
1. Pipeline pauses after android-architect completes
2. Re-invoke android-architect with feedback:
   "The architecture-blueprint.md is missing 'Decisions' and 'Next Steps' sections. Please add these sections with: (1) Key architectural decisions made (pattern choices, framework selections), (2) Explicit next steps for gradle-build-engineer and android-developer."
3. android-architect updates the artifact
4. Validation re-runs (attempt 2/2)
5. If passes: Pipeline continues to next stage
6. If fails again: Pipeline pauses, notifies user

**User Action:** Review handoff artifact, manually add missing sections if needed, then resume pipeline.

---

#### Scenario 2: Build Failure After Implementation

**Error:**
```
> Task :feature:profile:impl:compileDebugKotlin FAILED

e: /src/feature/profile/impl/ProfileViewModel.kt: (15, 25): Unresolved reference: User
```

**Recovery:**
1. Pipeline pauses after android-developer completes
2. Build validation fails (compilation error)
3. Report to user:
   "Build failed after android-developer implementation. Error: Unresolved reference 'User' in ProfileViewModel.kt:15. The data model may not have been created or imported correctly."
4. User options:
   - **Fix manually:** Add missing `User` model or import, then resume pipeline
   - **Re-run agent:** Ask android-developer to fix the specific error
   - **Abort pipeline:** Cancel if error is blocking

**User Action:**
```bash
# Option 1: Fix manually
# Add import androidx.example.core.model.User to ProfileViewModel.kt
/aet-pipeline resume

# Option 2: Re-run android-developer
Use android-developer to fix the unresolved reference to 'User' in ProfileViewModel.kt line 15
```

---

#### Scenario 3: Test Failures After Implementation

**Error:**
```
ProfileViewModelTest > loadProfile updates state to Success FAILED
    Expected: Success(user=User(id=1, name=Andrew))
    Actual: Loading

    at ProfileViewModelTest.kt:45
```

**Recovery:**
1. Pipeline pauses after android-testing-specialist completes
2. Test execution fails
3. Report to user:
   "Tests failed after android-testing-specialist created test suite. ProfileViewModel test 'loadProfile updates state to Success' is failing. The ViewModel may not be properly updating state from the repository Flow."
4. User options:
   - **Fix ViewModel:** Ask android-developer to fix state update logic
   - **Fix Test:** Ask android-testing-specialist to correct test expectations
   - **Accept and continue:** (Not recommended) Note the failure in test-report.md and continue pipeline

**User Action:**
```bash
# Diagnose and fix
Use android-developer to debug ProfileViewModel.loadProfile() - the test expects state to update to Success but it remains Loading. Check if the repository Flow is being collected correctly.
```

---

#### Scenario 4: Pattern Conflict Detected

**Error:**
```
Pattern detection results:
- LiveData: 47 ViewModels (51%)
- StateFlow: 45 ViewModels (49%)

No clear winner (80% threshold not met). Decision Council required.
```

**Recovery:**
1. Pipeline pauses after android-architect pattern detection
2. android-architect invokes Decision Council Protocol:
   - Status Quo Advocate: Arguments for LiveData (team familiarity, existing tooling)
   - Best Practices Advocate: Arguments for StateFlow (Kotlin-first, performance)
   - Pragmatic Mediator: Balanced recommendation with migration path
3. User reviews Decision Council output
4. User chooses approach:
   - **LiveData:** Document tech debt, plan StateFlow migration for later
   - **StateFlow:** Accept migration work, phase in over time
   - **Hybrid:** New features use StateFlow, existing code stays LiveData
5. android-architect updates architecture-blueprint.md with decision
6. Pipeline continues

**User Action:**
```bash
# Review Decision Council output in architecture-blueprint.md
# Choose approach and confirm
Continue pipeline with [chosen approach] for state management
```

---

#### Scenario 5: User Constraint Violation

**Error:**
```
Architecture violation detected:
- User specified: "Must use Manual DI (no Hilt)"
- architecture-blueprint.md specifies: Hilt dependency injection

This violates user constraints.
```

**Recovery:**
1. Pipeline pauses after android-architect completes
2. Validation detects constraint violation
3. Report to user:
   "The architecture-blueprint.md violates your requirement to use Manual DI. The blueprint specifies Hilt for dependency injection."
4. User options:
   - **Correct constraint:** If Hilt is actually acceptable, clarify requirements and continue
   - **Re-run architect:** Ask android-architect to revise blueprint with Manual DI
   - **Abort pipeline:** If fundamental mismatch between requirements and approach

**User Action:**
```bash
# Option 1: Revise architecture
Use android-architect to revise the architecture-blueprint.md to use Manual DI with ViewModelProvider.Factory instead of Hilt. Keep all other architectural decisions the same.

# Then resume
/aet-pipeline resume
```

---

#### Scenario 6: Git Conflict Recovery

**When conflicts occur:**

Pipeline creates branches (`aet/{feature_slug}/{run_timestamp}`) with git checkpoints after each stage. Conflicts can happen when concurrent work modifies files the pipeline also touches. This is most common during parallel dispatch (gradle-build-engineer + android-developer running simultaneously).

**Error:**
```
error: could not apply abc1234... [checkpoint] android-developer stage complete
hint: Resolve all conflicts manually, mark them as resolved with
hint: "git add/rm <pathspec>", then run "git rebase --continue".

Unmerged paths:
  both modified:   .artifacts/aet/handoffs/social-feed/2026-02-18-143022-build-config.md
  both modified:   feature/profile/impl/src/main/kotlin/ProfileViewModel.kt
```

**Recovery:**

1. **Detect:** Pipeline checkpoint commit fails with merge conflict
2. **Assess scope:**
   ```bash
   # List conflicting files
   git diff --name-only --diff-filter=U
   ```
   - If conflicts are in handoff artifacts only (`.artifacts/aet/`) → safe to resolve automatically (accept current stage's version)
   - If conflicts are in source code → trigger DP4 (Error Recovery) for user decision
3. **Resolve handoff conflicts:** Handoff artifacts are stage-owned — the writing stage's version is always correct:
   ```bash
   # Accept current stage's version for handoff artifacts
   git checkout --theirs .artifacts/aet/handoffs/social-feed/2026-02-18-143022-build-config.md
   git add .artifacts/aet/handoffs/
   ```
4. **Resolve source conflicts:** Present conflicts to user via DP4 with options:
   - **Auto-merge:** Attempt `git merge --no-edit` (if conflicts are trivial)
   - **Manual resolve:** Pause pipeline, user resolves, then resume
   - **Rebase on main:** `git rebase main` the pipeline branch, re-run current stage
   - **Abort stage:** Discard current stage's changes, skip to next

**Prevention:**
- Use `git stash` before starting pipeline if working tree is dirty
- Consider using worktree isolation (`isolation: "worktree"`) for pipeline branches to avoid conflicts entirely
- Don't run multiple pipelines concurrently on the same feature

**Resuming after resolution:**

Pipeline state in `.artifacts/aet/state.json` tracks completed stages. After resolving conflicts, resume with:
```bash
/aet-pipeline resume
```
The resume command reads pipeline state and picks up from the last incomplete stage.

**User Action:**
```bash
# Quick path: handoff-only conflicts
git checkout --theirs .artifacts/aet/
git add .artifacts/aet/
/aet-pipeline resume

# Full path: source code conflicts
# 1. Resolve conflicts in editor
# 2. Stage resolved files
git add <resolved-files>
# 3. Resume pipeline
/aet-pipeline resume
```

---

**References**: See `android-expert-toolkit` SKILL.md for error recovery principles.

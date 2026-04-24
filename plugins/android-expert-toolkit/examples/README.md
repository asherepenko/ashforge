# Android Expert Toolkit - Example Pipelines

This directory contains complete example handoff artifacts showing real-world pipeline execution.

## social-feed-pipeline/

**Pipeline Type:** `feature-build`

**Feature:** Social feed with infinite scroll, pull-to-refresh, like functionality

**Complete Pipeline Execution Example:**

**Run timestamp:** `2026-02-13-021300` (all artifacts share the same pipeline run prefix)

1. **2026-02-13-021300-architecture-blueprint.md** (android-architect)
   - Architecture decisions (StateFlow, Paging 3, offline-first)
   - Module structure (feature:feed with api/impl split)
   - Data flow diagram
   - Repository and ViewModel patterns
   - Constraints for downstream agents

2. **2026-02-13-021300-module-setup.md** (gradle-build-engineer)
   - Module creation (feature:feed:api, feature:feed:impl)
   - Convention plugins applied
   - Version catalog entries added
   - Dependency configuration

3. **2026-02-13-021300-implementation-report.md** (android-developer)
   - ViewModel implementation (FeedViewModel with StateFlow)
   - Repository implementation (OfflineFirstFeedRepository with Paging 3)
   - Room entities and DAOs
   - API service definitions
   - Build verification results

4. **2026-02-13-021300-ui-report.md** (compose-expert)
   - Compose UI screens (FeedRoute, FeedScreen)
   - Reusable components (PostCard, EmptyFeedState)
   - Material 3 design tokens
   - Adaptive layout (phone/tablet)
   - Accessibility semantic properties

5. **2026-02-13-021300-test-report.md** (android-testing-specialist)
   - Test doubles (TestFeedRepository)
   - Unit tests for ViewModel (15 tests, 92% coverage)
   - Compose UI tests (8 tests, 85% coverage)
   - Coverage summary (87% overall)
   - Test execution results

**Timeline:** Simulates 2-day feature build with parallel work

**Total Handoff Artifacts:** 5

---

## How to Use These Examples

### Learning Pipeline Structure

Read the artifacts in sequence to understand the full pipeline flow:
```bash
1. 2026-02-13-021300-architecture-blueprint.md   # Start here - architecture decisions
2. 2026-02-13-021300-module-setup.md              # Build configuration
3. 2026-02-13-021300-implementation-report.md     # Data layer implementation
4. 2026-02-13-021300-ui-report.md                 # UI implementation
5. 2026-02-13-021300-test-report.md               # Testing and coverage
```

### Understanding Handoff Protocol

Each artifact demonstrates:
- **YAML metadata** (Written by, Timestamp, Pipeline, Reads)
- **Required sections** (Summary, Decisions, Next Steps, Constraints)
- **Downstream instructions** (explicit guidance for next agents)
- **Validation compatibility** (all artifacts validate with `validate-handoff.py`)

### Using as Templates

Copy artifacts and replace feature-specific content:

```bash
# Copy architecture blueprint
mkdir -p .artifacts/aet/handoffs/social-feed
cp examples/social-feed-pipeline/2026-02-13-021300-architecture-blueprint.md .artifacts/aet/handoffs/social-feed/2026-02-18-143022-architecture-blueprint.md

# Update for your feature
# - Change feature name
# - Update module structure
# - Adjust decisions for your context
# - Modify constraints as needed
```

**Note:** The `templates/` directory has cleaner templates without example content. Use those for production, use these examples for learning.

### Validating Your Handoffs

Test your handoff artifacts match the structure:

```bash
# Validate your architecture blueprint
python hooks/validate-handoff.py .artifacts/aet/handoffs/social-feed/2026-02-18-143022-architecture-blueprint.md

# Should output: ✓ .artifacts/aet/handoffs/social-feed/2026-02-18-143022-architecture-blueprint.md is valid
```

---

## Example Walkthrough

**Scenario:** The user wants to build a social feed feature

**Pipeline Execution:**

1. **User Request:**
   ```
   /aet-pipeline feature-build "Social Feed"
   ```

2. **Pipeline Triggered:**
   - Reads `references/agent-routing.md` pipeline definition
   - Creates `.artifacts/aet/state.json` to track progress
   - Dispatches android-architect

3. **android-architect Executes:**
   - Analyzes existing patterns (StateFlow 45%, LiveData 55%)
   - Runs Decision Council (chooses StateFlow for new feature)
   - Designs module structure, data flow, repository pattern
   - Writes `.artifacts/aet/handoffs/social-feed/2026-02-18-143022-architecture-blueprint.md`
   - (See example in `social-feed-pipeline/2026-02-13-021300-architecture-blueprint.md`)

4. **Validation:**
   - Runs `validate-handoff.py` on architecture-blueprint.md
   - ✓ All required sections present
   - ✓ Decisions documented
   - ✓ Next steps clear

5. **Parallel Agent Dispatch:**
   - gradle-build-engineer: Set up modules per blueprint
   - android-developer: Implement data layer per blueprint
   - (Both read architecture-blueprint.md, work independently)

6. **gradle-build-engineer Executes:**
   - Creates feature:feed modules (api + impl)
   - Configures dependencies, convention plugins
   - Writes `.artifacts/aet/handoffs/social-feed/2026-02-18-143022-module-setup.md`
   - (See example in `social-feed-pipeline/2026-02-13-021300-module-setup.md`)

7. **android-developer Executes:**
   - Implements FeedRepository, FeedViewModel
   - Creates Room entities, DAOs
   - Creates API service
   - Writes `.artifacts/aet/handoffs/social-feed/2026-02-18-143022-implementation-report.md`
   - (See example in `social-feed-pipeline/2026-02-13-021300-implementation-report.md`)

8. **Validation of Both:**
   - Both handoffs validated successfully
   - Dispatches compose-expert (reads both artifacts)

9. **compose-expert Executes:**
   - Implements FeedRoute, FeedScreen, PostCard
   - Material 3 components, accessibility
   - Writes `.artifacts/aet/handoffs/social-feed/2026-02-18-143022-ui-report.md`
   - (See example in `social-feed-pipeline/2026-02-13-021300-ui-report.md`)

10. **Final Agent Dispatch:**
    - android-testing-specialist (reads all artifacts)

11. **android-testing-specialist Executes:**
    - Creates TestFeedRepository
    - Writes ViewModel unit tests (92% coverage)
    - Writes Compose UI tests (85% coverage)
    - Writes `.artifacts/aet/handoffs/social-feed/2026-02-18-143022-test-report.md`
    - (See example in `social-feed-pipeline/2026-02-13-021300-test-report.md`)

12. **Pipeline Complete:**
    - Updates `.artifacts/aet/state.json` to "completed"
    - Reports summary:
      ```
      ✓ Social Feed feature pipeline complete

      Artifacts created:
      - .artifacts/aet/handoffs/social-feed/2026-02-18-143022-architecture-blueprint.md
      - .artifacts/aet/handoffs/social-feed/2026-02-18-143022-module-setup.md
      - .artifacts/aet/handoffs/social-feed/2026-02-18-143022-implementation-report.md
      - .artifacts/aet/handoffs/social-feed/2026-02-18-143022-ui-report.md
      - .artifacts/aet/handoffs/social-feed/2026-02-18-143022-test-report.md

      Coverage: 87% (exceeds 80% target)
      Build: Passing
      Tests: 23/23 passing

      Ready for: Integration testing, QA review
      ```

**Total Time:** ~2 days with parallel execution (vs ~4 days sequential)

---

## Key Takeaways from Examples

1. **Handoffs are detailed:** Each artifact provides complete context for downstream agents
2. **Decisions are documented:** Every choice explained with rationale
3. **Next steps are explicit:** No ambiguity about what comes next
4. **Constraints are enforced:** Downstream agents must respect architecture decisions
5. **Validation ensures quality:** Required sections prevent incomplete handoffs
6. **Parallel work is identified:** gradle-build-engineer + android-developer can run simultaneously

These examples demonstrate how the Android Expert Toolkit coordinates 5 specialized agents to deliver production-grade Android features efficiently.

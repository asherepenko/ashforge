# Post-Verdict Interactive Actions

After printing the verdict (including the `> **Verdict saved to:** ...` path line from Phase 5), Captain America presents an interactive menu so the user can act on findings immediately.

## Protocol

1. Determine which options to show based on the **consensus verdict**
2. Present options using `AskUserQuestion` with verdict-dependent choices
3. If the review type supports context-specific actions (code-review or plan), add a second question when verdict is NEEDS REVISION or BLOCKED
4. Execute the chosen action
5. Only proceed to cleanup **after** the action completes

## Verdict Options

### APPROVED

Present `AskUserQuestion` with:
- **"Proceed"** (default) — Acknowledge verdict, continue to cleanup
- **"Save action items as TODOs"** — Extract any minor suggestions from verdict, create via the `/todo` skill

### APPROVED WITH CONDITIONS

Present `AskUserQuestion` with:
- **"Address conditions now"** (default) — Captain summarizes the top-priority conditions and begins working through them interactively
- **"Save conditions as TODOs"** — Extract conditions from verdict as actionable items, create via the `/todo` skill
- **"Proceed without addressing"** — Acknowledge conditions, continue to cleanup

#### Conditions Tracking

When verdict is APPROVED WITH CONDITIONS:
1. Extract each condition into a numbered checklist in the verdict file
2. Before implementation proceeds, verify each condition is addressed
3. Mark conditions as met with evidence (file path, test output, or code reference)
4. If a condition cannot be met, escalate to the user — do not silently skip

### NEEDS REVISION

Present `AskUserQuestion` with:
- **"Address findings now"** (default) — Captain summarizes the highest-severity findings and begins working through them interactively
- **"Save action items as TODOs"** — Extract all findings as actionable items grouped by severity, create via the `/todo` skill
- **"Re-review after changes"** — User makes changes, then Captain re-invokes the same council command with the same arguments

### BLOCKED

Present `AskUserQuestion` with:
- **"Address blocking issues now"** (default) — Captain summarizes CRITICAL/blocking findings and begins working through them interactively
- **"Save action items as TODOs"** — Extract blocking issues and all findings as actionable items, create via the `/todo` skill
- **"Re-review after changes"** — User makes changes, then Captain re-invokes the same council command with the same arguments

## Context-Specific Actions

When the verdict is **NEEDS REVISION** or **BLOCKED**, present a second question based on review type:

### Code Review (`code-review`)

Second question: "Would you like to apply fixes automatically?"
- **"Apply suggested fixes"** — Apply file:line fixes from findings that include specific code suggestions. Only apply fixes where the finding includes both a file:line reference and a concrete suggested fix.
- **"No, I'll handle it manually"** — Skip automatic fixes

### Plan Review (`plan`)

Second question: "Would you like to update the plan based on findings?"
- **"Update plan based on findings"** — Edit the plan file incorporating council feedback. Address findings in severity order (CRITICAL first).
- **"No, I'll update it manually"** — Skip automatic plan update

## Action Implementations

### "Address [conditions/findings/blocking issues] now"
1. Extract top-priority items from the verdict (CRITICAL first, then HIGH, then MEDIUM)
2. Present a numbered summary to the user
3. Begin working through each item interactively — propose a fix, get user confirmation, apply it
4. **Partial completion**: If the user wants to stop before all items are addressed, use `AskUserQuestion` to offer: "Save remaining items as TODOs" or "Done for now" (remaining items stay in the saved verdict file for reference)
5. After all items addressed (or user chooses to stop), fall through to cleanup

### "Save as TODOs"
1. Parse the verdict for all actionable findings
2. Group by severity (CRITICAL → HIGH → MEDIUM → LOW)
3. Create TODO items via the `/todo` skill with severity prefix: `[CRITICAL]`, `[HIGH]`, etc.
4. Confirm to user how many TODOs were created
5. Fall through to cleanup

### "Proceed"
1. Acknowledge the verdict
2. Fall through to cleanup immediately

### "Re-review after changes"
1. **Clean up the current council first** — send `shutdown_request` to all teammates, then `TeamDelete`
2. Tell the user to make their changes
3. Wait for user confirmation that changes are ready
4. Re-invoke the same council command with the original arguments
5. The new review starts fresh (new council, new debate)

### "Apply suggested fixes" (code-review only)
1. Collect all findings that include both a `file:line` reference and a suggested fix
2. Present the list of fixes to the user for confirmation
3. Apply each fix using the Edit tool
4. Run any available linter/formatter to clean up
5. Fall through to cleanup

### "Update plan based on findings" (plan only)
1. Collect all findings that suggest plan changes, ordered by severity
2. Read the current plan file
3. Apply changes incorporating council feedback
4. Show the user a summary of what changed
5. Fall through to cleanup

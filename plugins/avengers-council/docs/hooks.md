# Avengers Council Hook Configuration

The Avengers Council plugin includes a `PreToolUse:ExitPlanMode` hook that can suggest or automatically invoke plan reviews when exiting plan mode.

---

## Hook Overview

**Hook Type:** `PreToolUse:ExitPlanMode`

**Purpose:** Catch plan completion and trigger council review before implementation begins

**Location:** `.claude/hooks/council-plan-hook.sh`

**Configuration:** Environment variable `AVENGERS_COUNCIL_ON_PLAN`

---

## Configuration Modes

### Mode 1: `off` (Default)

**Behavior:** Hook does nothing, no intervention

**Use when:**
- You don't want automatic council suggestions
- Plans are simple and don't need review
- You'll manually decide when to use council

**Setup:**
```bash
export AVENGERS_COUNCIL_ON_PLAN=off
```

Or just don't set the variable (off is default).

---

### Mode 2: `prompt` (Recommended)

**Behavior:** Hook suggests running council review, but doesn't require it

**User experience:**
```
You: [exit plan mode]
Assistant: "The Avengers Council plugin is active. Consider running
        `/avengers-council:plan-review` to get a multi-expert engineering
        advisory review of this plan before proceeding."
[You can choose to run it or skip]
```

**Use when:**
- You want reminders but not requirements
- You review some plans but not all
- You like flexibility

**Setup:**
```bash
# Add to ~/.zshrc or ~/.bashrc
export AVENGERS_COUNCIL_ON_PLAN=prompt
```

Then restart Claude Code or reload shell.

---

### Mode 3: `auto` (Strict)

**Behavior:** Hook requires council review before proceeding with implementation

**User experience:**
```
You: [exit plan mode]
Assistant: "The Avengers Council plugin is active with auto-review enabled.
        BEFORE proceeding with this plan, I'll invoke
        `/avengers-council:plan-review` to get the council's verdict."
[Assistant automatically runs council review]
[You see full council debate and verdict]
[Assistant waits for approval before implementing]
```

**Use when:**
- You want mandatory reviews for all plans
- Working on critical systems (production, security-sensitive)
- Team policy requires peer review before implementation
- You want maximum safety and oversight

**Setup:**
```bash
# Add to ~/.zshrc or ~/.bashrc
export AVENGERS_COUNCIL_ON_PLAN=auto
```

Then restart Claude Code or reload shell.

---

## Setup Instructions

### Step 1: Choose Your Mode

Decide which mode fits your workflow:
- **off** — No intervention (default)
- **prompt** — Gentle reminders (recommended for most users)
- **auto** — Required reviews (maximum safety)

### Step 2: Set Environment Variable

Add to your shell profile:

**For zsh** (`~/.zshrc`):
```bash
# Avengers Council — Plan review on exit
export AVENGERS_COUNCIL_ON_PLAN=prompt  # or: off, auto
```

**For bash** (`~/.bashrc`):
```bash
# Avengers Council — Plan review on exit
export AVENGERS_COUNCIL_ON_PLAN=prompt  # or: off, auto
```

### Step 3: Reload Shell

```bash
# Reload your shell config
source ~/.zshrc  # or ~/.bashrc
```

### Step 4: Restart Claude Code

The hook only activates when Claude Code starts with the environment variable set.

### Step 5: Verify

```bash
# Check variable is set
echo $AVENGERS_COUNCIL_ON_PLAN
# Should output: prompt (or off, auto)
```

Then test by entering and exiting plan mode in a Claude Code session.

---

## Hook Behavior Details

### When Hook Triggers

**Trigger:** The assistant calls `ExitPlanMode` tool

**Timing:** Right before the assistant would proceed with implementation

**Hook executes:** `hooks/council-plan-hook.sh` (source location; installed at `.claude/hooks/council-plan-hook.sh` when plugin is registered)

### What Hook Does

**Mode `off`:**
- Returns exit code 0 immediately
- No output, no side effects

**Mode `prompt`:**
- Returns JSON with `additionalContext`:
  ```json
  {
    "hookSpecificOutput": {
      "hookEventName": "PreToolUse",
      "additionalContext": "The Avengers Council plugin is active. Consider running `/avengers-council:plan-review` to get a multi-expert engineering advisory review of this plan before proceeding."
    }
  }
  ```
- The assistant sees this as a system message
- The assistant mentions the suggestion to the user
- User can choose to run `/avengers-council:plan-review` or skip

**Mode `auto`:**
- Returns JSON with `additionalContext`:
  ```json
  {
    "hookSpecificOutput": {
      "hookEventName": "PreToolUse",
      "additionalContext": "The Avengers Council plugin is active with auto-review enabled. BEFORE proceeding with this plan, invoke `/avengers-council:plan-review` to get the council's verdict on this plan. Do not continue until the council review is complete."
    }
  }
  ```
- The assistant is instructed to run `/avengers-council:plan-review` automatically
- Implementation waits until council review completes
- If verdict is BLOCKED → the assistant pauses for user decision

---

## Troubleshooting

### "Hook not working"

**Check:**
```bash
# 1. Verify variable is set
echo $AVENGERS_COUNCIL_ON_PLAN

# 2. Verify hook file exists and is executable
ls -la ~/.claude/plugins/*/avengers-council/*/hooks/council-plan-hook.sh

# 3. Check hook registration
cat ~/.claude/plugins/*/avengers-council/*/hooks/hooks.json
```

**Common issues:**
- Environment variable not exported (add `export` keyword)
- Shell profile not reloaded (run `source ~/.zshrc`)
- Claude Code not restarted (hooks only load on startup)
- Typo in variable name (must be exactly `AVENGERS_COUNCIL_ON_PLAN`)

### "Hook suggests review but I want to skip"

**Solution:** Just ignore the suggestion and proceed with your work. Mode `prompt` doesn't block you.

**Alternative:** Switch to `off` mode temporarily:
```bash
export AVENGERS_COUNCIL_ON_PLAN=off
```

### "Hook requires review but I want to skip this time"

**Solution:** You can't skip in `auto` mode — that's the point. Options:
1. Run the quick review: `/avengers-council:plan-review --quick`
2. Temporarily switch to `prompt` mode
3. Address the council's concerns

**Why auto mode exists:** Some teams require mandatory peer review. Auto mode enforces that policy.

### "Want different behavior for different projects"

**Solution:** Use project-specific shell configs or per-session variables:

```bash
# In specific project directory
cd ~/critical-project
export AVENGERS_COUNCIL_ON_PLAN=auto  # Strict for this project
claude

# In another project
cd ~/prototype-project
export AVENGERS_COUNCIL_ON_PLAN=off  # No reviews for prototypes
claude
```

---

## Advanced Configuration

### Custom Hook Behavior

The hook script can be modified for custom behavior:

**Location:** `.claude/hooks/council-plan-hook.sh` (in plugin directory)

**Example customization:** Add a 4th mode for specific project patterns:

```bash
case "$MODE" in
  off) exit 0 ;;
  prompt) ... ;;
  auto) ... ;;
  critical)
    # Custom mode: auto for security/backend, prompt otherwise
    if grep -q "security\|authentication\|payment" "$CLAUDE_PLAN_FILE"; then
      # Force review for security-sensitive plans
      echo '{"hookSpecificOutput": {...}}' # auto mode output
    else
      echo '{"hookSpecificOutput": {...}}' # prompt mode output
    fi
    ;;
esac
```

### Project-Specific Overrides

Create `.avengers-council.config` in project root:

```bash
# Project-specific council configuration
AVENGERS_COUNCIL_ON_PLAN=auto
AVENGERS_COUNCIL_FOCUS=security,mobile
```

Then modify hook to read this file if present (requires hook enhancement).

---

## Integration with Other Hooks

The Avengers Council hook can coexist with other `PreToolUse:ExitPlanMode` hooks. All hooks for the same event run in sequence.

**Execution order:** Alphabetical by hook file name

**Example hook chain:**
1. `council-plan-hook.sh` (from avengers-council)
2. `plan-validator-hook.sh` (hypothetical other plugin)
3. `security-check-hook.sh` (hypothetical)

All hooks' `additionalContext` messages are concatenated and shown to the assistant.

---

## Workflow Examples

### Example 1: Prompt Mode

```
User: "Let's add user authentication"
Assistant: [enters plan mode, designs auth system]
Assistant: [calls ExitPlanMode]
Hook: [prompts council review]
Assistant: "I've created the plan. The Avengers Council plugin suggests
        running `/avengers-council:plan-review` for advisory review."
User: "/avengers-council:plan-review"
Council: [reviews plan, finds security gaps]
Council: "NEEDS REVISION — add password hashing, rate limiting"
User: "Update the plan to include bcrypt and rate limiting"
Assistant: [updates plan]
User: "Proceed with implementation"
```

### Example 2: Auto Mode

```
User: "Let's migrate to microservices"
Assistant: [enters plan mode, designs migration]
Assistant: [calls ExitPlanMode]
Hook: [requires council review]
Assistant: "Before proceeding, I'm invoking the Avengers Council for
        mandatory plan review."
Assistant: [automatically runs /avengers-council:plan-review]
Council: [reviews, finds issues]
Council: "APPROVED WITH CONDITIONS — add distributed tracing"
Assistant: "The council approved with conditions. Would you like me to
        update the plan to include distributed tracing?"
User: "Yes"
Assistant: [updates plan, proceeds]
```

### Example 3: Off Mode (Manual)

```
User: "Let's refactor the database layer"
Assistant: [enters plan mode, designs refactor]
Assistant: [calls ExitPlanMode]
Hook: [does nothing — off mode]
Assistant: "Plan is ready. Shall I proceed?"
User: "Let me review it first. /avengers-council:plan-review"
Council: [reviews plan]
User: "Looks good, proceed"
Assistant: [implements]
```

---

## See Also

- **[README.md](../README.md)** — Plugin overview and installation
- **[commands.md](commands.md)** — Command reference
- **[references/debate-protocol.md](../references/debate-protocol.md)** — How council debate works
- **[examples/](../examples/)** — Example council verdicts


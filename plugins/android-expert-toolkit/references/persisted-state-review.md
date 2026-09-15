# Persisted state review

Checks for any change that touches state already stored on installed devices. Use as a **generation target** when writing such a change and as **evaluation criteria** when reviewing one.

## When to use

Read this reference when a change adds, renames, re-encodes, migrates, or changes the meaning of any SharedPreferences key, DataStore field, Room column, or file-format value that exists on installed devices. A diff-scoped review does not cover these changes. The risk sits in what an older release wrote to disk, not in the lines that changed.

## 1. Upgrade-path table per key

For every key the diff touches, write a row: the key, the value format on the old release, the value format on the new code, the writer, and what the first new run does when the key is absent, present and empty, present and non-empty, or undecodable.

**Why**: your users have run writers other than the new code. A value that automatic code wrote on every install is not a user signal.

**How to prove it**: read the old writer on the merge-base with `git show <merge-base>:<path>`. Do not read the new one. Then drive the pure decision functions through each row with a scratch unit test, paste the output, and delete the test.

## 2. Ambiguous legacy value

If one stored value carried two meanings on the old release, such as "the user chose empty" and "nothing was ever chosen", no migration can recover the intent. Pick the direction whose wrong case costs least. That is usually "show it again once", because the user can hide it again and the new code records the intent from then on. From then on, record the intent at write time in a separate key, in the same transaction as the value.

**Why**: a migration built on "this case is rare" changes behavior for every user in the case you assumed away.

**How to prove it**: use the table from check 1. Without the table, do not write the migration.

## 3. Composite string keys

When code parses a string it previously only wrote, such as `type::title::region`, every field becomes input. Find every split on the separator. Validate or sanitize the fields at the scan boundary or the ingest boundary. Log a non-fatal error on malformed input. Write a round-trip test with the separator inside a field. When you add a field, prefer a structured store over a flat string.

**Why**: a title that contains the separator produces a different key, and the old entry is orphaned.

**How to prove it**: query the code index first with `codegraph explore` or the `codegraph_explore` MCP tool when the repo has a `.codegraph/` directory. Fall back to grep only when the index returns nothing.

## 4. Locking changes add callers

A method that was a bare `apply()` and now takes a lock blocks every caller. List the callers of each method whose locking changed, and list the thread each caller runs on. If a scan-wide lock exists, publish an immutable snapshot at the end of the scan and let the UI paths read the snapshot under a narrower lock. State the lock order in a comment on the field. Keep the read, the write, and the event post that follows them inside one locked section. A read outside the lock and a write inside the lock is a race. Coalesce writes so that a scan posts one event per type, and check what each subscriber does when the event arrives.

**Why**: the diff shows the lock you added. It does not show the UI thread now waiting for a full scan.

**How to prove it**: list the callers from the code index. Then run a script over the source that shows no code under the narrow lock reaches the wide lock.

## 5. Tests that gate nothing

Wire a new test source set in a library module into the test runner script and into every CI dependency-check section. On a branch that adds tests, `git diff --stat -- <runner-script> <ci-config>` returning nothing is a red flag.

**Why**: tests that CI never invokes report coverage they do not provide.

**How to prove it**: confirm the CI wiring before you report any test count.

## Evidence rungs

Rung 1 is asserted. Rung 2 is read at file and line. Rung 3 is reasoned from source. Rung 4 is executed with pasted output. Get every upgrade-path claim to rung 4 with a scratch test over the pure functions, or label the claim unproven. A written table reads the same whether it is true or false, so run it.

## Smaller repeats

- `check()` or `require()` on a release code path. Log the problem, record a non-fatal error, and take the safe branch instead.
- `@VisibleForTesting` methods with zero callers.
- A comment that names the wrong method as the one that repairs the state.
- `ListAdapter.currentList` used as a synchronous guard. It returns the list that was last displayed, not the list you just submitted.
- A stable-id map cleared by accident on a path that also rebuilds the list.
- A change in behavior inside a commit labeled cleanup, such as `isNotBlank` to `isNotEmpty`.
- A review process rule that a reviewer cites and the repo does not define. Verify the rule before you accept it.

## Review breadth

A count of review passes is not evidence of breadth. Three reviews scoped to the diff or to comment wording still answer none of the questions above.

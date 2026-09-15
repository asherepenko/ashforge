# Persisted State Review

Checks for any change that touches state already sitting on installed devices. Use as a **generation target** when writing such a change and as **evaluation criteria** when reviewing one.

## When to use

Read this reference when a change adds, renames, re-encodes, migrates, or changes the meaning of any SharedPreferences key, DataStore field, Room column, or file-format value that exists on installed devices. A diff-scoped review does not cover this: the risk lives in what an older release wrote to disk, not in the lines that changed.

## 1. Upgrade-path table per key

For every key the diff touches, write a row: key, value format on the old release, value format on the new code, who writes it, and what the first new run does when the key is absent, present-and-empty, present-and-non-empty, and undecodable.

**Why**: the new code is not the only writer your users have run. A value that automatic code wrote on every install is not a user signal.

**How to prove it**: read the OLD writer on the merge-base (`git show <merge-base>:<path>`), not the new one. Then drive the pure decision functions through each row with a scratch unit test, paste the output, and delete the test.

## 2. Ambiguous legacy value

If one stored value carried two meanings on the old release (user chose empty vs. nothing ever chosen), no migration can recover the intent. Pick the direction whose wrong case costs least, usually "show it again once", since the user can re-hide it and the new code records the intent from then on. Record intent at write time in a separate key, in the same transaction as the value.

**Why**: a migration built on "this case is rare" ships a behaviour change to every user in the case you assumed away.

**How to prove it**: the table from check 1. Without it, do not write the migration.

## 3. Composite or stringly keys

The moment code parses back a string it previously only wrote (`type::title::region`), every field becomes input. Find every split on the separator, validate or sanitise at the scan or ingest boundary, log a non-fatal on malformed input, and write a round-trip test with the separator inside a field. Prefer a structured store over a flat string when adding fields.

**Why**: a title with a colon in it silently produces a different key, and the old entry is orphaned.

**How to prove it**: query the code index first (`codegraph explore` / `codegraph_explore` when `.codegraph/` exists); fall back to grep only when the index returns nothing.

## 4. Synchronisation changes create new callers

A method that was a bare `apply()` and now takes a lock gains every UI caller as a blocker. List callers of each method whose locking changed, and the thread each runs on. If a scan-wide lock exists, publish an immutable snapshot at the end of the scan and let UI paths read it under a narrower lock. State the lock order in a comment on the field. Keep read-modify-write and the event post that follows inside one locked section; a read outside plus a write inside is a race. Coalesce writes so a scan posts one event per type, and check what each subscriber does on receipt.

**Why**: the diff shows a lock added; it does not show the UI thread now waiting on a full scan.

**How to prove it**: list the callers from the index, and run a script over the source showing nothing under the narrow lock reaches the wide lock.

## 5. Tests that gate nothing

A new test source set in a library module must be wired into the test runner script and into every CI dependency-check section. `git diff --stat -- <runner script> <ci config>` coming back empty on a branch that adds tests is a red flag.

**Why**: tests that CI never invokes report coverage they do not provide.

**How to prove it**: confirm the CI wiring before reporting any test count.

## Evidence rungs

Rung 1 asserted, rung 2 read at file:line, rung 3 reasoned from source, rung 4 executed with pasted output. Get every upgrade-path claim to rung 4 with a scratch test over the pure functions, or label it unproven. A table that is merely written sounds right whether or not it is true.

## Smaller repeats

- `check()` / `require()` on a release code path. Log, record a non-fatal, take the safe branch instead.
- `@VisibleForTesting` methods with zero callers.
- Comments naming the wrong method as the one that repairs the state.
- `ListAdapter.currentList` used as a synchronous guard. It returns what was last displayed, not what you just submitted.
- Stable-id maps cleared by accident on a path that also rebuilds the list.
- A behaviour change hidden under a "cleanup" commit (`isNotBlank` to `isNotEmpty`).
- A review process rule a reviewer cites that does not exist in the repo. Verify it before accepting it.

## Review breadth

Do not treat a count of review passes as evidence of breadth. Three diff-scoped or prose-scoped reviews still answer none of the questions above.

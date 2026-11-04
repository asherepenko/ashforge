# Persisted state review

Checks for any change that touches state already stored on installed devices. Use as a **generation target** when writing such a change and as **evaluation criteria** when reviewing one.

## When to use

Read this reference when a change adds, renames, re-types, migrates, or changes the meaning of anything an older release wrote to the device: a SwiftData model, a Core Data entity, a `UserDefaults` or `@AppStorage` key, a Keychain item, a `Codable` file, or a CloudKit record type. A diff-scoped review does not cover these changes. The risk sits in what an older release wrote, not in the lines that changed. Storage choice and the Core Data to SwiftData path are in [data-layer](data-layer.md).

## 1. Upgrade-path table per key

For every key, attribute or file the diff touches, write a row: the name, the value format on the old release, the value format on the new code, the writer, and what the first new run does when the value is absent, present and empty, present and valid, or undecodable.

**Why**: your users ran writers other than the new code. Some skipped releases. The oldest store version still in the field is a real input.

**How to prove it**: read the old writer on the merge-base with `git show <merge-base>:<path>`. Then drive the pure decision functions through each row with a scratch unit test, paste the output, and delete the test.

## 2. SwiftData schema changes (iOS 17+)

- Every shipped schema is a `VersionedSchema` with its own `versionIdentifier`. Do not edit a shipped version in place; add a new one.
- List all versions in a `SchemaMigrationPlan`, in order, and pass the plan to the `ModelContainer`.
- Use `MigrationStage.lightweight` only for changes SwiftData can infer: an added optional or defaulted property, a removed property, a rename with `@Attribute(originalName:)`. Anything that transforms or de-duplicates values needs `MigrationStage.custom` with `willMigrate` / `didMigrate`.
- Adding `@Attribute(.unique)` to a property that already holds duplicates fails the migration. De-duplicate in `willMigrate` first.
- Model rules (`@Model`, relationships, CloudKit limits) are in the `swiftdata-pro` skill.

## 3. Core Data model changes

- Add a new model version in the `.xcdatamodeld` and make it current. Never edit the version that shipped.
- Lightweight migration (`shouldMigrateStoreAutomatically` and `shouldInferMappingModelAutomatically`, both on by default for `NSPersistentContainer`) covers added optional attributes, removed attributes, and renames that set the **Renaming ID**.
- A rename without a Renaming ID is a delete plus an add. The column's data is lost.
- Type changes, splits, and computed values need a mapping model or a custom `NSEntityMigrationPolicy`. Staged migration (`NSStagedMigrationManager`, iOS 17+) can chain lightweight and custom steps.
- Test a store from every model version still in the field, not only the previous one.

## 4. UserDefaults and @AppStorage

- A renamed key reads as absent. Read the old key once, write the new key, then remove the old key, and make that step idempotent.
- A changed type reads as `nil`. `defaults.object(forKey:) as? NewType` fails on a value of the old type, and `@AppStorage` falls back to its default without an error.
- `register(defaults:)` values are not stored. "Absent" and "equal to the default" look the same to `object(forKey:)` only if you never registered a default. Know which one the code checks.
- If one stored value carried two meanings on the old release, such as "the user turned it off" and "never set", no migration recovers the intent. Pick the direction whose wrong case costs least, and record the intent in a separate key from then on.
- App group suites (`UserDefaults(suiteName:)`) are shared with extensions that may run the old code until the user opens the app.

## 5. Keychain items

- An item is found by its class plus `kSecAttrService`, `kSecAttrAccount`, and `kSecAttrAccessGroup`. Changing any of them in the query orphans the old item. Read with the old query, write with the new one, then delete the old item.
- Changing `kSecAttrAccessible` on an existing item needs `SecItemUpdate` or a delete and re-add. Writing with a new value does not change what the stored item has. Rules for which class to use are in [security](security.md).
- A move to a `ThisDeviceOnly` class or a shared access group changes backup and restore behavior. Say so in the change.
- Keychain items can outlive an app deletion. Do not treat "item present" as "returning user on this install" without a check stored outside the Keychain.

## 6. Codable files on disk

- A new non-optional property makes old files fail to decode. Make it optional, or decode with `decodeIfPresent` and a default.
- A renamed property needs a `CodingKeys` entry that keeps the old string, or a custom `init(from:)` that tries both.
- Changing an enum's raw values breaks every stored case. Unknown raw values throw; decide on a fallback case.
- Add a `version` field to any format you own, and branch on it in `init(from:)`.
- A file that fails to decode must not be overwritten with an empty value on the next save. Move it aside and log the error.

## 7. CloudKit schema

- The production schema is additive only. Once deployed, record types and fields cannot be deleted or renamed, and a field's type cannot change.
- Old app versions keep reading and writing records. A new field must be optional for them, and new code must handle records that lack it.
- With `NSPersistentCloudKitContainer` or a SwiftData CloudKit store, the local model is limited the same way: no unique constraints, every attribute optional or defaulted, every relationship optional. Details are in `swiftdata-pro`.
- Deploy schema changes from the development environment to production before the build that needs them ships.

## Evidence rungs

Rung 1 is asserted. Rung 2 is read at file and line. Rung 3 is reasoned from source. Rung 4 is executed with pasted output. Get every upgrade-path claim to rung 4, or label it unproven. For model migrations, rung 4 means opening a store file created by the old build with the new code in a test, and asserting on the migrated rows.

## Review checklist

- [ ] Upgrade-path table written for every touched key, attribute, item and file.
- [ ] Old writer read on the merge-base, not inferred from the new code.
- [ ] SwiftData: new `VersionedSchema`, plan lists every version, custom stage for anything that transforms data.
- [ ] Core Data: new model version, Renaming IDs on renames, mapping model for type changes.
- [ ] `UserDefaults` renames migrate once and remove the old key; type changes handled.
- [ ] Keychain query changes read old, write new, delete old; accessibility change uses `SecItemUpdate`.
- [ ] `Codable` formats decode every older file; undecodable files are kept, not overwritten.
- [ ] CloudKit changes are additive and deployed to production before release.
- [ ] A migration test runs against a store or file from the oldest version still in the field.
- [ ] Extensions and widgets that share the store are on the same migration path.

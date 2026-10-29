# Security

## When to use

Read when handling network trust, storing secrets or tokens, or configuring release hardening. Deeper audits have official skills: exported components and IPC → `android-intent-security`; runtime permissions and component protection → `android-permissions-security`; keep rules → `r8-analyzer`.

## Network trust

Primary: `res/xml/network_security_config.xml`, referenced from the manifest with `android:networkSecurityConfig`.

```xml
<network-security-config>
    <base-config cleartextTrafficPermitted="false" />
    <domain-config>
        <domain includeSubdomains="true">api.example.com</domain>
        <pin-set expiration="2027-01-01">
            <pin digest="SHA-256">PRIMARY_KEY_HASH=</pin>
            <pin digest="SHA-256">BACKUP_KEY_HASH=</pin>
        </pin-set>
    </domain-config>
    <debug-overrides>
        <trust-anchors><certificates src="user" /></trust-anchors>
    </debug-overrides>
</network-security-config>
```

- Pin only if the team can rotate pins before expiry; always ship a backup pin. A wrong pin bricks networking for every installed build.
- OkHttp `CertificatePinner` only when pins must be decided at runtime.
- No cleartext in release; `debug-overrides` is the only place user CAs are trusted.

## Storing secrets and tokens

`androidx.security:security-crypto` (`EncryptedSharedPreferences`, `EncryptedFile`, `MasterKey`) is **deprecated**: all its APIs were deprecated in the stable 1.1.0 release and Google states there won't be further releases (developer.android.com, *Cryptography → Deprecated functionality → Jetpack security-crypto library*, checked with `android docs fetch kb://android/privacy-and-security/cryptography`). Don't add it to new code; in existing code, flag it and plan a migration rather than ripping it out mid-feature.

Instead, keep the key in the Android Keystore and encrypt with AES-GCM, storing ciphertext + IV in DataStore or a file:

```kotlin
class TokenCipher {
    private val keyStore = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }

    private fun key(): SecretKey =
        (keyStore.getEntry(ALIAS, null) as? KeyStore.SecretKeyEntry)?.secretKey
            ?: KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore").apply {
                init(
                    KeyGenParameterSpec.Builder(ALIAS, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                        .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                        .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                        .build()
                )
            }.generateKey()

    fun encrypt(plain: ByteArray): Pair<ByteArray, ByteArray> {
        val cipher = Cipher.getInstance(TRANSFORMATION).apply { init(Cipher.ENCRYPT_MODE, key()) }
        return cipher.doFinal(plain) to cipher.iv
    }

    fun decrypt(cipherText: ByteArray, iv: ByteArray): ByteArray =
        Cipher.getInstance(TRANSFORMATION)
            .apply { init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(128, iv)) }
            .doFinal(cipherText)

    private companion object {
        const val ALIAS = "app_token_key"
        const val TRANSFORMATION = "AES/GCM/NoPadding"
    }
}
```

- Handle `KeyPermanentlyInvalidatedException` and decrypt failures by clearing the stored value and re-authenticating — keys can vanish after a device restore or lock-screen change.
- Don't request a specific JCA provider other than `AndroidKeyStore` (the cryptography guide discourages it).
- Never hardcode API secrets in source or `BuildConfig`; anything in the APK is public. Secrets that matter stay server-side.
- Biometric-gated keys: `setUserAuthenticationRequired(true)` + `BiometricPrompt` (`android docs search "biometric auth"`).

Changing how an existing value is stored is a persisted-state change → `persisted-state-review.md`.

## Release hardening

- `isMinifyEnabled = true` and `isShrinkResources = true` for release (see `gradle-convention-plugins.md`).
- Keep rules: start from none. Libraries that need rules (kotlinx.serialization, Retrofit, Room, Hilt) ship consumer rules. Add a rule only for reflection the build can't see, scoped to the exact class or member — never `-keep class com.example.** { *; }`. Audit existing rules with the `r8-analyzer` skill.
- `FLAG_SECURE` on screens that show secrets or payment data.
- Logs: no tokens, PII, or full request bodies in release builds.

## Checklist

- [ ] No cleartext traffic in release; pins (if any) have a backup and an expiry plan.
- [ ] Tokens encrypted with a Keystore key; no `security-crypto` in new code.
- [ ] No secrets in source, resources, or `BuildConfig`.
- [ ] Exported components reviewed (`android-intent-security`); permissions minimal (`android-permissions-security`).
- [ ] R8 on for release; no package-wide keep rules.

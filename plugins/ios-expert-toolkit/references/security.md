# Security

## When to use

Read when storing secrets, talking to servers, or hardening a release. Project build-setting hardening (and what to audit) is the `audit-xcode-security-settings` skill.

## Rules

- **Secrets and tokens**: store in the Keychain (`kSecClassGenericPassword`), with an accessibility class no weaker than `kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly` unless a background job needs more. Never use `UserDefaults` or files for them.
- **Nothing secret in the bundle.** An API key shipped in the app is public. Use short-lived tokens issued by your server.
- **Transport**: keep App Transport Security on. Add an exception per domain only with a recorded reason. Pin certificates or public keys only when the threat model needs it, and plan their rotation.
- **Incoming data is untrusted**: URLs and deep links ([navigation](navigation.md)), pasteboard, push payloads, and file imports. Validate before use.
- **Logging**: use `Logger` with privacy levels; dynamic strings and objects are redacted in logs by default; mark a value `privacy: .public` only when it is safe. Don't log tokens or personal data.
- **Biometrics**: `LocalAuthentication` confirms the user is present; it does not protect data by itself. Pair it with a Keychain item that requires `.userPresence` or `.biometryCurrentSet`.
- **Data at rest**: use file protection (`.completeUnlessOpen` or stronger) for sensitive files.

## Privacy

Apps and third-party SDKs that use required-reason APIs or collect data declare it in a privacy manifest (`PrivacyInfo.xcprivacy`), and App Store Connect needs matching privacy answers. App Review policy detail is outside this plugin; check Apple's current guidelines before release.

## Reviewing

For a security review of a repository, use a dedicated audit rather than this page. For the Xcode project's settings, use `audit-xcode-security-settings`.

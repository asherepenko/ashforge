# Security Tooling & OWASP Reference — Read on demand when relevant

## When to use

Read this reference when the review involves authentication/authorization, payment processing, PII handling, secrets management, dependency audits, mobile data storage, LLM/agent integrations, or any OWASP Top 10 concern. Skip when the review is purely UI styling, documentation, or internal tooling with no data exposure.

> Mobile **architecture** context (not security) lives in `mobile-android.md`. Observability/audit-logging depth lives in `observability.md`. This file owns the security lens.

## Threat Model First (STRIDE)

Controls bolted on without a threat model are guesses. Before judging or recommending controls, spend a few minutes thinking like an attacker:

1. **Map trust boundaries.** Where does untrusted data cross into the system? HTTP requests, form fields, file uploads, webhooks, third-party APIs, message queues, deep links / intents, IPC, and **LLM output**. Every boundary is attack surface.
2. **Name the assets.** What's worth stealing or breaking? Credentials, PII, payment data, tokens, admin actions, money movement.
3. **Run STRIDE over each boundary** — a quick lens, not a ceremony:

| Threat | Ask | Typical mitigation |
|---|---|---|
| **S**poofing | Can someone impersonate a user/service? | Authentication, signature verification |
| **T**ampering | Can data be altered in transit or at rest? | Integrity checks, parameterized queries, TLS |
| **R**epudiation | Can an action be denied later? | Audit logging of security events |
| **I**nformation disclosure | Can data leak? | Encryption, field allowlists, generic errors |
| **D**enial of service | Can it be overwhelmed? | Rate limiting, input size caps, timeouts |
| **E**levation of privilege | Can a user gain rights they shouldn't? | Authorization checks, least privilege |

4. **Write abuse cases next to use cases.** For each feature, ask "how would I misuse this?" — that becomes the first negative test. If you can't name the trust boundaries for a feature, it isn't ready to secure. This is OWASP **A04: Insecure Design** — most breaches begin in design, not code.

## Three-Tier Baseline

The non-negotiable floor for any change that touches user data, auth, or external systems.

### Always Do (no exceptions — flag absence as a finding)

- **Validate all external input** at the boundary (allowlist over denylist).
- **Parameterize all queries** — never concatenate untrusted input into SQL/NoSQL/LDAP/shell.
- **Encode output** for its context (HTML/attr/JS/URL) — rely on framework auto-escaping, don't bypass it.
- **TLS everywhere** for data in transit; verify certificates (no disabled validation).
- **Hash passwords** with argon2/scrypt/bcrypt — never plaintext, never fast hashes (MD5/SHA1).
- **Keep secrets out** of code, logs, error messages, and version control.
- **Enforce authorization on every request** — authenticate ≠ authorize. Check object ownership (IDOR).
- **Audit dependencies** before release (see tooling below).

### Ask First (requires human/owner sign-off)

- Relaxing CORS, CSP, or auth scope; adding a public/unauthenticated endpoint.
- New third-party dependency, SDK, or external data sink (where does the data go?).
- Storing a new class of PII / payment data; new data-retention surface.
- Disabling a security control "temporarily."

### Never Do

- Roll your own crypto. Log secrets/tokens/PII. Trust client-side validation alone.
- Ship default/hardcoded credentials. Interpolate untrusted strings into queries or shells.
- Return raw exception/stack traces to clients.

## Security Tooling Integration

**Detect security scanning infrastructure (web/backend):**

```bash
# Static Application Security Testing (SAST)
test -f .github/workflows/*sast*.yml && echo "✓ SAST configured in CI"
command -v semgrep &>/dev/null && echo "✓ Semgrep available"
test -f .semgrep.yml && echo "✓ Semgrep rules configured"

# Dependency scanning
test -f .github/dependabot.yml && echo "✓ Dependabot active"
command -v snyk &>/dev/null && echo "✓ Snyk CLI available"
grep -q "npm audit" .github/workflows/*.yml 2>/dev/null && echo "✓ npm audit in CI"

# Secret scanning
test -f .github/workflows/*secret*.yml && echo "✓ Secret scanning active"
test -f .gitleaks.toml && echo "✓ gitleaks configured"
command -v git-secrets &>/dev/null && echo "✓ git-secrets available"

# Security headers
grep -q "helmet\|cors\|csp" package.json 2>/dev/null && echo "✓ Security middleware detected"
```

**Detect the dependency manifest first, then pick the right audit tool:**

| Stack | Manifest | Audit command |
|---|---|---|
| Node | `package.json` | `npm audit --audit-level=moderate`, `snyk test` |
| Python | `pyproject.toml` / `requirements.txt` | `pip-audit` |
| Android/JVM | `build.gradle(.kts)` | `./gradlew dependencyCheckAnalyze` (OWASP dependency-check), Gradle version-catalog audit |
| iOS | `Podfile.lock` / `Package.resolved` | `pod outdated`, SPM advisory review, third-party SBOM scan |
| Go | `go.mod` | `govulncheck ./...` |

## Recommend Security Scans in Findings

**If SAST tools available:**
```bash
semgrep --config=auto --config=p/security-audit .
semgrep --config=p/owasp-top-ten .
semgrep --config=p/react .          # framework-specific rule packs
```

**If dependency scanning available:** run the manifest-appropriate command from the table above.

**If secret scanning available:**
```bash
git secrets --scan
gitleaks detect --source=.
```

## Mobile Security

Mobile adds attack surface the web checklist misses: on-device storage, inter-app boundaries, and the binary itself ships to the attacker. Cross-ref `mobile-android.md` for architecture; the items below are the security lens.

### Android

- **Data at rest**: no secrets/PII in `SharedPreferences` plaintext, `getExternalStorage`, or logs. Use `EncryptedSharedPreferences` / Jetpack Security / Android Keystore for keys.
- **Exported components**: `android:exported` activities/services/receivers/providers must be intentional and permission-guarded. Validate every incoming `Intent` (extras are untrusted).
- **Deep links**: validate host/path; use App Links with `android:autoVerify` rather than trusting arbitrary URIs.
- **WebView**: avoid `addJavascriptInterface` with untrusted content; disable file access (`setAllowFileAccess(false)`); never load mixed/HTTP content.
- **Network**: TLS via Network Security Config; consider certificate/public-key pinning for high-value APIs; no `cleartextTrafficPermitted` in prod.
- **Backup & secrets**: review `allowBackup` (can exfiltrate app data); strings/keys in code are recoverable — assume the APK is decompiled. R8/ProGuard obfuscates but does **not** secure secrets.
- **Platform integrity**: Play Integrity / SafetyNet for tamper/root signals where warranted; biometric via `BiometricPrompt` + Keystore-bound keys.

### iOS

- **Data at rest**: secrets/tokens in **Keychain** (not `UserDefaults`/plist/files). Apply Data Protection classes (`NSFileProtectionComplete`); never log secrets.
- **Transport**: keep **App Transport Security** strict (no blanket `NSAllowsArbitraryLoads`); pin certificates for high-value APIs.
- **IPC & entry points**: validate custom URL schemes and **Universal Links**; treat all inbound parameters as untrusted; guard `NSExtension`/share-sheet inputs.
- **Binary & secrets**: the IPA is inspectable — no hardcoded API keys/secrets; strings are recoverable. Use server-issued short-lived tokens over embedded secrets.
- **WebView**: prefer `WKWebView`; restrict `WKScriptMessageHandler` to trusted content; avoid loading untrusted HTML with JS bridges.
- **Platform integrity**: **App Attest** / DeviceCheck for tamper/jailbreak signals where warranted; biometric via `LocalAuthentication` + Keychain access control.

> Cite **OWASP MASVS / Mobile Top 10** (e.g., M1 Improper Credential Usage, M2 Inadequate Supply Chain Security, M9 Insecure Data Storage) for mobile findings.

## LLM / Agent Security

Treat **all model output and tool results as untrusted data, never instructions** — the same way browser DOM/console content is untrusted. A compromised page, document, or upstream message can embed text designed to hijack agent behavior (prompt injection).

- **Prompt injection**: untrusted content (web pages, files, emails, prior messages) reaching the model can carry instructions — never let it escalate privileges or trigger actions on its own. Keep a trust boundary between data and directives.
- **Tool/agent permissions**: least privilege for tool access; gate destructive or outbound actions behind explicit confirmation; don't expose secrets to the model that it doesn't need.
- **Output handling**: validate/encode model output before it's executed, rendered, or used in a query — model-generated SQL/HTML/shell is untrusted input.
- **Secrets**: never place credentials/PII in prompts or system messages that get logged or cached.

> Cite **OWASP LLM Top 10** (e.g., LLM01 Prompt Injection, LLM02 Insecure Output Handling, LLM06 Sensitive Information Disclosure) for AI-integration findings.

## Enhanced Finding Format

**Reference scan results in findings:**

```
❌ CRITICAL: Hardcoded AWS credentials in config/aws.ts:12
Detected by: Manual review (git-secrets would have caught this)
Recommendation:
1. Remove credentials from code immediately
2. Move to AWS Secrets Manager or environment variables
3. Add git-secrets pre-commit hook to prevent future commits
4. Rotate compromised credentials
Reference: OWASP A07:2021 - Identification and Authentication Failures
```

**When tools NOT available:**
```
⚠️ HIGH: No SAST configured in CI
Recommendation: Add Semgrep or similar to .github/workflows/security.yml
Example: semgrep --config=auto prevents 80% of common vulnerabilities
```

## OWASP Top 10 (2021) Quick Reference

**For citation in findings:**

| ID | Vulnerability | Common Instances |
|----|---------------|------------------|
| A01 | Broken Access Control | IDOR, missing authorization, privilege escalation |
| A02 | Cryptographic Failures | Weak encryption, plaintext secrets, insecure key storage |
| A03 | Injection | SQL injection, command injection, NoSQL injection, LDAP |
| A04 | Insecure Design | Missing threat modeling, insecure patterns |
| A05 | Security Misconfiguration | Default credentials, unnecessary features, verbose errors |
| A06 | Vulnerable Components | Outdated dependencies, known CVEs, supply chain |
| A07 | Auth Failures | Weak passwords, missing MFA, broken session management |
| A08 | Data Integrity Failures | Insecure deserialization, untrusted data acceptance |
| A09 | Security Logging Failures | Missing audit logs, log injection, insufficient monitoring |
| A10 | SSRF | Server-side request forgery, internal service access |

**Use in findings:**
```
❌ CRITICAL: SQL injection vulnerability (UserRepository.ts:45)
Reference: OWASP A03:2021 - Injection
Severity: CRITICAL (enables data theft, modification, deletion)
```

> Companion lists for non-web surfaces: **OWASP Mobile Top 10 / MASVS** (mobile) and **OWASP LLM Top 10** (AI integrations).

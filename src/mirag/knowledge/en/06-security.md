# 06 · Security

> **Authentication = who you are. Authorization = what you're allowed to do.** Mixing them up in an interview is
> disqualifying. Most real breaches aren't broken cryptography: they're authorization done badly.


**Covers from the syllabus:** `concepts` · `authentication` · `authorization` · `attacks` · `cryptography` · `implementations` · `constraints` · `failure_modes` · `tradeoffs`

---

## Sessions vs tokens

### Cookie sessions (stateful)

The server stores the session (Redis/DB) and the client only carries an opaque ID in a cookie.

```
Set-Cookie: sid=random_256_bits; HttpOnly; Secure; SameSite=Lax; Path=/
```

- ✅ **Instant revocation** (delete the session from the store and that's it).
- ✅ The token contains no data: if it leaks, it reveals nothing.
- ✅ You can change permissions and they apply instantly.
- ❌ Shared state (you need Redis) and it requires care with CSRF.

### JWT (stateless)

A signed token that **contains** the claims. `header.payload.signature`, base64url.

```json
{"sub":"user_42","exp":1789..., "iat":1789..., "iss":"api.yourapp.com", "aud":"api", "scope":"orders:read"}
```

- ✅ No need to query a store on every request; convenient between services.
- ❌ **It cannot be revoked** before it expires (without adding a denylist, which takes you back to state).
- ❌ The payload is **readable by anyone** (signed ≠ encrypted). Never put sensitive data in it.
- ❌ If you change a user's role, their old token keeps saying "admin" until it expires.

**JWT mistakes that come up in interviews:**
1. **`alg: none`** — the attacker strips the signature. Your library must have an **algorithm allowlist**.
2. **RS256/HS256 confusion** — the attacker signs with the *public* key as if it were an HMAC secret.
3. **Not validating `exp`, `iss`, `aud`** — a token from another environment or another service is accepted.
4. **Storing it in `localStorage`** — any XSS steals it. An `HttpOnly` cookie is safer.
5. **Long expiry** — a 30-day JWT is a master key.

**The correct pattern:** **short access token (5-15 min) + long, opaque, revocable refresh token**,
stored in an `HttpOnly` cookie, with **rotation**: every use of the refresh token issues a new one and invalidates the previous one.
If an already-used one is presented again, that signals theft → **you invalidate that user's entire token family**.
(This is called *refresh token rotation with reuse detection* and it's what you're expected to know in 2026.)

**When to use each:** web app with a single backend → **sessions**, almost always. Microservices, public APIs,
mobile or federation → JWT with the discipline above.

> **Card** · **When:** designing the login for any system ·
> **Pattern:** short access token + long, opaque refresh token, **rotating with reuse detection** ·
> **Anti-pattern:** a 30-day JWT in `localStorage` ·
> **Limits:** **a JWT cannot be revoked** before it expires without going back to state ·
> **How it fails:** you change a user's role and their token keeps saying "admin" until it expires ·
> **Decision:** single backend and web? Sessions. Distributed APIs or mobile? Tokens with rotation ·
> **Trade-off:** immediate revocation (sessions, requires state) vs independence (JWT, requires short expiry) ·
> **Related:** cookies, OAuth2, CSRF `[02]`

---

## OAuth2 and OpenID Connect

**OAuth2 is delegated authorization**, not authentication. **OIDC is the authentication layer on top of OAuth2**
(it adds the `id_token`, which does say who the user is). Using the OAuth2 `access_token` to "log in"
is the classic conceptual mistake.

**Roles:** Resource Owner (the user) · Client (your app) · Authorization Server (Google, Auth0) ·
Resource Server (the API).

**Flows:**
- **Authorization Code + PKCE** — **the only one you should use** for web, SPA and mobile. PKCE (`code_verifier` /
  `code_challenge`) prevents someone who intercepts the `code` from redeeming it.
- **Client Credentials** — machine to machine, no user.
- **Device Code** — TVs and devices without a keyboard.
- ~~Implicit~~ and ~~Password (ROPC)~~ — **deprecated**. Saying you'd use implicit in an interview is a
  red flag.

**Details that matter:** the `state` parameter (anti-CSRF for the flow itself), `nonce` in OIDC (binds the
`id_token` to your request), validating the `id_token` signature against the provider's JWKS, and **redirect URIs
in an exact-match allowlist** (a wildcard `redirect_uri` is how accounts get stolen).

> **Card** · **When:** social login, federation and delegated access ·
> **Pattern:** **Authorization Code + PKCE**, always; `state` and `nonce` mandatory ·
> **Anti-pattern:** the Implicit or Password (ROPC) flow — deprecated; mentioning them is a red flag ·
> **Limits:** OAuth2 is **authorization**; to authenticate you need OIDC and the `id_token` ·
> **How it fails:** a wildcard `redirect_uri` lets an attacker steal the authorization code ·
> **Decision:** always validate the signature, `iss`, `aud` and `exp` against the provider's JWKS ·
> **Trade-off:** delegating identity (fewer passwords to store) vs depending on a third party ·
> **Related:** JWT, OAuth integrations `[16]`

---

## Authorization: RBAC and ABAC

- **RBAC** — permissions by role (`admin`, `editor`, `viewer`). Simple, auditable, and it falls short as soon as
  multi-tenancy shows up ("admin **of their organization**").
- **ABAC** — decisions based on attributes (user, resource, action, context): *"can edit if
  `resource.owner_id == user.id` and it's business hours"*. Flexible, harder to audit.
- **ReBAC** — relationship-based (the Google Zanzibar model, also used by OpenFGA / SpiceDB): *"can view the
  document if they're a member of the folder that contains it"*. It's where the industry is heading for complex
  hierarchical permissions.

**The principles you're evaluated on:**
- **Deny by default.** Everything is forbidden except what's explicitly allowed.
- **Authorize on the server, on every object.** Hiding a button in the frontend is not authorization.
- **IDOR / BOLA** (*Insecure Direct Object Reference* / *Broken Object Level Authorization*) is
  **the #1 API vulnerability in the OWASP API Top 10**: `GET /invoices/1234` returns someone else's invoice
  because you only checked that the caller is authenticated. **Every access must verify ownership of the resource**, and
  the robust way is for the query itself to include it: `WHERE id = $1 AND tenant_id = $2`.
- **Centralize the decision** (a policy layer) but **enforce it at the data-access point**, which is the
  only place everything goes through.

> **Card** · **When:** from the very first endpoint that returns someone's data ·
> **Pattern:** deny by default + an **object-level** check, in the query itself ·
> **Anti-pattern:** checking only authentication and trusting the ID in the URL (**IDOR/BOLA**) ·
> **Limits:** RBAC falls short as soon as there's multi-tenancy ("admin **of their** organization") ·
> **How it fails:** it's **#1 in the OWASP API Top 10** and raises no error at all: just a silent leak ·
> **Decision:** make it impossible by construction (RLS or a scoped repository), not with an `if` per endpoint ·
> **Trade-off:** granularity (ABAC/ReBAC) vs auditability and performance ·
> **Related:** multi-tenancy, permissions `[17]`

---

## MFA

- **TOTP** (authenticator apps, RFC 6238): shared secret + time. Cheap and good.
- **WebAuthn / Passkeys** — asymmetric cryptography bound to the domain: **phishing-resistant**, which is
  exactly what TOTP and SMS are not. It's the standard everyone is migrating to.
- **SMS** — the weakest (SIM swapping), but better than nothing.
- **Recovery codes**, single-use, hashed in the DB.
- **The detail people forget:** when MFA is enabled you must **invalidate existing sessions**, and sensitive
  operations (changing email, withdrawing money) must require **re-authentication** rather than trusting the session.

> **Card** · **When:** accounts with access to money, personal data or administration ·
> **Pattern:** WebAuthn/passkeys as the first option; TOTP as the alternative ·
> **Anti-pattern:** SMS as the only second factor (SIM swapping) ·
> **Limits:** TOTP and SMS do **not** resist phishing; WebAuthn does, because it's bound to the domain ·
> **How it fails:** enabling MFA without invalidating existing sessions leaves the door open ·
> **Decision:** sensitive operations require **re-authentication**; the session isn't enough ·
> **Trade-off:** security vs friction and support tickets for lost devices ·
> **Related:** sessions, account recovery `[16]`

---

## Password hashing

```
NEVER: md5, sha1, sha256 (they're fast — that's exactly the property you don't want)
YES:   Argon2id  (first choice in 2026)
       scrypt
       bcrypt    (acceptable; watch out for the 72-byte limit)
       PBKDF2    (if you need FIPS compliance)
```

- They're **deliberately slow** and use a **per-user salt** (which is stored inside the hash; it isn't secret).
- **Argon2id** also resists GPU/ASIC attacks because it's memory-hard. Ballpark parameters:
  ~19-64 MB of memory, 2-3 iterations, parallelism 1-4; tune them so it takes ~100-250 ms on your hardware.
- A **pepper** (a global secret, kept outside the DB) adds defense if only the database is stolen.
- **When verifying, compare in constant time** and return **the same error** for "user doesn't exist" and
  "wrong password" (otherwise you have a user-enumeration oracle). Also watch the
  *timing*: if the user doesn't exist and you don't hash anything, you respond faster and give yourself away.
- **Modern policy (NIST):** minimum length 8-12, **no** forced expiry, **no** absurd character
  rules, and **check against lists of leaked passwords** (k-anonymity with HaveIBeenPwned).

> **Card** · **When:** if you store passwords (and consider not doing so) ·
> **Pattern:** **Argon2id** with parameters calibrated to ~100-250 ms on your hardware ·
> **Anti-pattern:** SHA-256 or MD5 — they're fast, which is exactly the property you don't want ·
> **Limits:** bcrypt truncates at 72 bytes; raising Argon2's parameters costs RAM on every login ·
> **How it fails:** different messages for "user doesn't exist" and "wrong password" let attackers enumerate accounts ·
> **Decision:** NIST policy — minimum length, **no** forced expiry, check against leaked-password lists ·
> **Trade-off:** verification cost (defense) vs login latency and server CPU ·
> **Related:** cryptography, timing attacks `[01]`

---

## Encryption and secrets

- **In transit:** TLS 1.3 everywhere, including inside your VPC (mTLS between services).
- **At rest:** disk/volume encryption (the cloud gives you this) + field-level encryption for what's truly
  sensitive. **Envelope encryption**: one data key (DEK) per record, encrypted with a master key
  (KEK) that lives in a KMS/HSM. Rotating the KEK doesn't force you to re-encrypt all the data.
- **Symmetric** (AES-GCM, ChaCha20-Poly1305) — fast, one key. **Always use AEAD** (it encrypts *and* authenticates);
  AES-CBC without a MAC is vulnerable to padding oracle attacks.
- **Asymmetric** (RSA, Ed25519) — signing and key establishment.
- **Never roll your own crypto.** Use libsodium or your language's standard library. And never reuse a nonce/IV.
- **Hashing ≠ encryption ≠ encoding.** Base64 is not security.

**Secrets management:**
- Never in the repo. Never in the Docker image. Never in logs (be careful about logging the entire request object).
- Vault, AWS Secrets Manager, GCP Secret Manager, or environment variables injected by the platform.
- **Rotation** without downtime: accept both the old and the new key during the transition window.
- **Secret scanning** in CI and in pre-commit. And if a secret leaked: **rotating it is mandatory**;
  deleting the commit is useless because it's already in the forks and in the CI logs.

> **Card** · **When:** sensitive data at rest and every credential ·
> **Pattern:** AEAD (AES-GCM/ChaCha20-Poly1305) + envelope encryption with KMS ·
> **Anti-pattern:** rolling your own crypto, reusing a nonce, or baking secrets into the Docker image ·
> **Limits:** encryption at rest doesn't protect you from a compromised app, which holds the key ·
> **How it fails:** a leaked secret lives on in the forks and the CI logs: **deleting the commit doesn't help** ·
> **Decision:** if it leaked, **rotating is mandatory**, not optional ·
> **Trade-off:** field-level encryption (more protection) vs being unable to index and search ·
> **Related:** secrets management, IAM `[13, 14]`

---

## OWASP: the vulnerabilities you must be able to explain

### Injection (SQL, NoSQL, commands)
```python
# vulnerable
cur.execute(f"SELECT * FROM users WHERE email = '{email}'")
# correct: parameterized queries, ALWAYS
cur.execute("SELECT * FROM users WHERE email = %s", (email,))
```
ORMs protect you **except** when you concatenate raw SQL or pass dynamic column names (those can't be
parameterized: validate them against an allowlist). In NoSQL, the equivalent is passing an object where
you expected a string: `{"$gt": ""}` as the password.

### XSS
Running the attacker's JS in the victim's browser. **Stored** (saved in your DB), **reflected**
(in the response), **DOM-based** (on the client).
Defense: **contextual escaping by default** (modern templating engines do it), `Content-Security-Policy`,
`HttpOnly` cookies, and sanitizing HTML with a battle-tested library (DOMPurify) if you really need to allow it.
**It matters to you as a backend engineer** because your API is the one returning the data someone will render.

### CSRF
The victim's browser sends an authenticated request the victim never intended (because cookies are sent
automatically). **It only applies to cookie-based authentication**, not to `Authorization: Bearer`.
Defense: `SameSite=Lax/Strict`, an **anti-CSRF token** (double-submit or synchronized with the session), and
checking `Origin`/`Referer`. And GETs must never mutate state.

### SSRF
You trick the server into requesting a URL the attacker controls → it reaches internal services, or the
**cloud metadata endpoint** (`169.254.169.254`) and steals IAM credentials. **It has caused huge
breaches (Capital One).**
Defense: a domain allowlist, resolve the DNS and **block private ranges** (10/8, 172.16/12, 192.168/16,
127/8, 169.254/16), don't follow redirects blindly, IMDSv2 on AWS, and route outbound internet traffic through a
controlled proxy. **Highly relevant if your backend downloads user-supplied URLs or calls an AI
agent's tools** (see `18-ai-backend.md`).

### Others from the top list
- **Broken access control** (IDOR/BOLA) — the #1. Already covered above.
- **Security misconfiguration** — debug enabled, default permissions, public S3 buckets, CORS `*`.
- **Vulnerable components** — unpatched dependencies; `npm audit`/Dependabot and SBOM.
- **Insecure deserialization** — Python's `pickle` or Java's native deserialization on user data
  is remote code execution. Use JSON.
- **SSTI** — template injection: rendering a template built from user input.
- **Mass assignment** — already covered in `03-apis.md`.
- **Path traversal** — `../../etc/passwd`. Normalize the path and verify it's still inside the base directory.

> **Card** · **When:** in every code review and before exposing anything ·
> **Pattern:** parameterized queries, contextual escaping, allowlists, least privilege ·
> **Anti-pattern:** sanitizing with home-made regular expressions instead of using the right primitive ·
> **Limits:** ORMs protect you except with raw SQL and dynamic column names ·
> **How it fails:** **SSRF** reaches the cloud metadata endpoint and steals IAM credentials ·
> **Decision:** every piece of user input that becomes a URL, query, HTML or path needs its own specific defense ·
> **Trade-off:** strict validation breaks rare legitimate cases and prevents entire classes of attacks ·
> **Related:** IDOR, deserialization, IAM `[13, 18]`

---

## Security headers

```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Content-Security-Policy: default-src 'self'; object-src 'none'; frame-ancestors 'none'
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), camera=(), microphone=()
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Resource-Policy: same-origin
```

- **HSTS** forces HTTPS on future visits (eliminating downgrades). `preload` is hard to undo:
  try it first with a low `max-age`.
- **CSP** is the defense in depth against XSS. The serious version uses **nonces or hashes**, not
  `unsafe-inline`. Roll it out first as `Content-Security-Policy-Report-Only`.
- **`frame-ancestors 'none'`** replaces the old `X-Frame-Options` (clickjacking).
- **`nosniff`** stops the browser from guessing the type and executing something a user uploaded as JS.

> **Card** · **When:** on every HTML response, and several of them on APIs too ·
> **Pattern:** HSTS + CSP with nonces + `nosniff` + `frame-ancestors 'none'` ·
> **Anti-pattern:** a CSP with `unsafe-inline` — it protects against almost nothing ·
> **Limits:** HSTS `preload` is hard to undo; try it with a low `max-age` ·
> **How it fails:** without `nosniff`, a file uploaded by a user gets executed as JavaScript ·
> **Decision:** roll out CSP in `Report-Only` first and measure before enforcing ·
> **Trade-off:** defense in depth vs breaking legitimate third-party scripts ·
> **Related:** XSS, uploads, CORS `[02, 15]`

---

## Webhook signatures and token rotation

**Verifying an incoming webhook (the Stripe/GitHub pattern):**
```python
import hmac, hashlib, time

def verify(raw_payload: bytes, signature_header: str, secret: str, tolerance=300):
    ts, signature = parse(signature_header)
    if abs(time.time() - int(ts)) > tolerance:         # 1) anti-replay
        raise ValueError("timestamp outside tolerance")
    expected = hmac.new(secret.encode(), f"{ts}.".encode() + raw_payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):   # 2) constant-time comparison
        raise ValueError("invalid signature")
```
**Three things people get wrong:** signing the **already-parsed** body instead of the raw one (any re-serialization
changes bytes and breaks the signature), comparing with `==` (timing attack), and not checking the timestamp (replay).

**Key and token rotation:** always with an **overlap window** — the system accepts both the old key
and the new one for a while, clients are migrated, and then the old one is retired. The same applies to JWT
signing keys (publish several in the JWKS with different `kid` values), webhook secrets and API keys.

> **Card** · **When:** when sending or receiving webhooks, and when rotating any key ·
> **Pattern:** HMAC over the **raw body** + a timestamp in the signature + `compare_digest` ·
> **Anti-pattern:** signing the already-parsed body, or comparing with `==` (timing attack) ·
> **Limits:** the signature proves origin and integrity, it does **not** prevent duplicates: deduplicate separately ·
> **How it fails:** without a timestamp check, an attacker replays an old valid request ·
> **Decision:** every rotation gets an overlap window: accept the old and the new key at the same time ·
> **Trade-off:** overlap window (no downtime) vs a period with two valid keys ·
> **Related:** webhooks, integrations `[03, 16]`

---

## Implementation: a service's security stack

The order matters as much as the pieces.

```python
# 1) Authentication: resolves WHO you are. It decides nothing else.
async def authenticate(request) -> User:
    token = request.cookies.get("sid") or extract_bearer(request)
    if not token:
        raise NotAuthenticated()                    # -> 401
    session = await store.get(token)                # opaque -> lookup; JWT -> verify signature
    if not session or session.expired:
        raise NotAuthenticated()
    return session.user

# 2) Object-level authorization: decided ON THE RESOURCE, not on the route.
def authorize(actor: User, action: str, resource=None):
    if action not in PERMISSIONS.get(actor.role, ()):
        raise Forbidden()                           # -> 403
    if resource is not None and resource.tenant_id != actor.tenant_id:
        raise NotFound()                            # -> 404, NOT 403: don't reveal that it exists

# 3) The defense that actually works: the query cannot return someone else's data.
class ScopedRepository:
    def __init__(self, session, tenant_id):
        self.session, self.tenant_id = session, tenant_id

    def orders(self):
        return self.session.query(Order).filter(Order.tenant_id == self.tenant_id)
        #                                       ^ impossible to forget in the new endpoint
```

**The 404 vs 403 detail:** returning 403 for someone else's resource confirms that it **exists**. For private
resources, 404 is the correct response.

**Postgres Row-Level Security** pushes the defense down into the engine, where no developer can bypass it:

```sql
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY isolation ON orders
  USING (tenant_id = current_setting('app.tenant_id')::uuid);
-- and on every pool connection: SET app.tenant_id = '...';
```

> **Card** · **When:** every multi-user service ·
> **Pattern:** authenticate in middleware, authorize per object, and **enforce the scope in the data layer** ·
> **Anti-pattern:** an `if user.role == "admin"` repeated across endpoints ·
> **Limits:** RLS requires propagating the tenant per connection; with PgBouncer in transaction mode you have to set it per transaction ·
> **How it fails:** the new endpoint someone adds next month forgets the filter ·
> **Decision:** if the defense depends on remembering something, it will eventually fail ·
> **Trade-off:** enforcement in the DB (robust, rigid) vs in the app (flexible, forgettable) ·
> **Related:** multi-tenancy, IDOR, connection pooling `[04, 17]`

---

## Constraints: compliance and system limits

| Constraint | What it forces you to do |
|---|---|
| **GDPR** | legal basis, data minimization, right of access and erasure, **breach notification within 72 h** |
| **PCI DSS** | don't touch card data if you can avoid it; the PSP's widget reduces the scope to SAQ A `[07]` |
| **SOC 2 / ISO 27001** | access control, audit logs, change management, periodic permission reviews |
| **Data residency** | per-region infrastructure; it shapes the entire architecture `[05]` |
| **Retention** | accounting obligation to keep records for years **vs** right to erasure: anonymize, don't delete |
| **Sector-specific** (HIPAA, PSD2…) | specific encryption, mandatory MFA, logging of read access |

**Threat modeling** — the half-hour exercise that prevents half of all incidents. Draw the data
flow, mark the **trust boundaries** (where data goes from untrusted to trusted) and at each one ask
**STRIDE**: *Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of
privilege*.

```
[browser] --(untrusted)--> [CDN/WAF] --> [API] --(trusted)--> [DB]
                                         |
                                         +--(UNTRUSTED)--> [third-party webhook]
                                         +--(UNTRUSTED)--> [content retrieved by an agent] [18]
```

**The trust boundaries people forget:** incoming webhooks, uploaded files, the
content your backend downloads from a URL, and **the text that reaches an LLM** — which can contain
instructions (`[18]`).

> **Card** · **When:** designing a feature that touches personal data or money ·
> **Pattern:** STRIDE over a data-flow diagram, with the trust boundaries marked ·
> **Anti-pattern:** treating compliance as after-the-fact paperwork instead of a design requirement ·
> **Limits:** regulatory compliance is **not** security; it's the floor, not the ceiling ·
> **How it fails:** the personal data shows up in a log or an analytics tool, not in the database ·
> **Decision:** if you don't know where your personal data is, you can't comply with anything ·
> **Trade-off:** per-customer or per-region isolation (expensive) vs compliance and enterprise sales ·
> **Related:** PCI, audit logs, retention `[07, 15, 17]`

---

## Failure modes: security in practice

Real incidents are rarely broken cryptography. By frequency:

| Failure | How it gets in | What would have prevented it |
|---|---|---|
| **Broken authorization (IDOR)** | changing an ID in the URL | scope enforced in the data layer |
| **Leaked credential** | in the repo, in a log, in an image | secret scanning + rotation + OIDC instead of keys |
| **Vulnerable dependency** | an unpatched transitive dependency | Dependabot, SBOM, keeping up to date |
| **Public bucket** | default configuration | account-level public access block |
| **SSRF → IAM credentials** | a user-supplied URL | allowlist, block private ranges, IMDSv2 |
| **Social engineering** | phishing the team | passkeys (phishing-resistant), four-eyes approval for critical actions |
| **Insider or compromised account** | excessive permissions accumulated over time | least privilege + periodic review |
| **Injection** | concatenated raw SQL | parameterized queries |
| **Stored XSS** | uploaded file served from your domain | separate domain + `nosniff` + `attachment` `[15]` |

**Defense in depth:** no single layer is enough. WAF, authentication, authorization, least
privilege, encryption, monitoring and response capability. Design assuming that **one of them will fail**,
and that the goal is to limit the blast radius (`[10]`).

> **Card** · **When:** prioritizing security work ·
> **Pattern:** invest by probability × impact — authorization and secrets first ·
> **Anti-pattern:** debating the encryption algorithm while an IDOR sits uncovered ·
> **Limits:** there's no such thing as "secure"; there's "how much it costs to attack us" ·
> **How it fails:** the serious failures are **silent**: nobody gets an alert for a data leak ·
> **Decision:** if you can't detect it, you can't respond: monitoring before more controls ·
> **Trade-off:** security vs usability and delivery speed ·
> **Related:** incident response, observability `[10, 12]`

---

## Responding to a security incident

The process is **different** from a normal incident (`[10]`): here the evidence matters as much as
restoring service.

1. **Contain without destroying evidence.** Isolate the machine — **don't power it off**, memory is lost.
   Revoke credentials and tokens, close the entry vector.
2. **Assess the scope:** what was accessed, which data, since when. This is where audit logs `[17]` and
   log retention either save you or sink you.
3. **Rotate everything** that could have been compromised: keys, secrets, session tokens, service credentials.
4. **Notify.** GDPR requires notifying the supervisory authority within **72 hours** of becoming aware of a breach
   that poses a risk to people's rights. **Involve legal from minute one**: this is not an engineering
   decision.
5. **Postmortem** and closing the vector, including **the controls that should have detected it**.

**Advance preparation that makes the difference:** knowing who makes the call, having legal and
communications contacts at hand, having logs with enough retention, and being able to **rotate secrets quickly without breaking production**
(hence the overlap window). A breach drill reveals everything that's missing within an hour.

> **Card** · **When:** on suspicion of compromise, unauthorized access or a leak ·
> **Pattern:** contain → assess scope → rotate → notify → postmortem ·
> **Anti-pattern:** powering off the machine (you lose the memory) or reinstalling before investigating ·
> **Limits:** without logs with enough retention you can't determine the scope — and if you can't
> determine it, legally you have to assume the worst case ·
> **How it fails:** it's discovered months later, when the logs have already rotated out ·
> **Decision:** the 72-hour clock starts when you **become aware** of the breach, not when you confirm it ·
> **Trade-off:** containing fast (you restore sooner) vs preserving evidence (you understand what happened) ·
> **Related:** audit logs, retention, incident response `[10, 15, 17]`

---

## Interview questions and trade-offs

**Q: Sessions or JWT?**
It depends on whether you need immediate revocation and whether there's a single backend. Classic web → sessions. Distributed
APIs → short access token + rotating, revocable refresh token. *Signal:* you say explicitly that **a JWT
cannot be revoked** and that the denylist "solution" brings back the very state you were supposedly avoiding.

**Q: Where do you store the JWT in the browser?**
In an `HttpOnly; Secure; SameSite` cookie. In `localStorage` any XSS steals it. *Signal:* you accept the
trade-off — with a cookie you need CSRF protection again — and explain how you cover it (SameSite + anti-CSRF
token).

**Q: What is IDOR and how do you prevent it systematically?**
Accessing someone else's resource by changing the ID, because only authentication was checked. You prevent it by
**always** filtering by owner/tenant in the query itself, not with a stray `if` in the controller. *Signal:*
you say the robust approach is to make it impossible by construction (scoping in the repository, RLS in Postgres),
because an `if` gets forgotten in the new endpoint.

**Q: Your database gets stolen. What happens to the passwords?**
If they're hashed with Argon2id + salt, the attacker has to attack each hash separately and it's extremely expensive. *Signal:*
you explain **why** SHA-256 won't do (it's fast: billions of attempts per second on a GPU) and what
the pepper adds if it lives outside the DB.

**Q: What is SSRF and why is it so dangerous in the cloud?**
Because the server has access to the internal network and to the metadata endpoint, from which IAM credentials
can be extracted. *Signal:* you mention IMDSv2, the allowlist with DNS resolved up front (to prevent DNS rebinding) and that
it directly affects modern features like "give me the URL and I'll summarize it" or an agent's tools.

**Q: How do you design permissions in a multi-tenant app?**
`tenant_id` in every table and every query, roles within the tenant, and object-level
checks. *Signal:* you propose Postgres Row-Level Security or a repository that injects the `tenant_id`
automatically, because relying on every dev remembering it ends in data leaking between customers.

**Core trade-off of this box:** *security vs friction and operational complexity*. Every control has a cost
(latency, UX, support). What's expected of a senior is prioritizing by real risk: object-level authorization
and secrets management prevent more incidents than any debate about the encryption
algorithm.

---

## Sources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/) and [OWASP API Security Top 10](https://owasp.org/API-Security/) — the second is the one that matters for backend.
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/) — the practical reference, topic by topic.
- [NIST SP 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html) — modern password policy.
- [RFC 9700 — Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700.html)
- [WebAuthn / passkeys](https://webauthn.guide/) · [Argon2 RFC 9106](https://www.rfc-editor.org/rfc/rfc9106.html)
- [Microsoft STRIDE](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats)

# 14 · DevOps

> The goal is not to "automate": it is to **shrink the time between writing a line and having it work in
> production without fear**. The DORA metrics measure exactly that: deployment frequency, lead time,
> change failure rate and time to restore.


**Covers from the syllabus:** `git` · `cicd` · `deployment` · `infrastructure` · `secrets` · `rollback` · `failure_modes`

---

## Git

**What a senior uses every day:**

```bash
git rebase -i main          # clean up the history before the PR
git cherry-pick <sha>       # bring one specific commit to another branch
git bisect start            # binary search for the commit that broke something
git revert <sha>            # undo IN PUBLIC (creates a new commit)
git reset --hard <sha>      # rewrite LOCALLY (destructive)
git reflog                  # the safety net: recovers "lost" commits
git log -S "text"           # when that string entered or left the code
git blame -w -C             # who wrote this, ignoring whitespace and moved code
```

- **Merge vs rebase:** merge preserves the real history (and creates merge commits); rebase produces a
  linear, readable history. **The rule: rebase on your local branch, merge into main.** Never rewrite the
  history of a shared branch.
- **`revert` vs `reset`:** on any branch other people use, `revert`. `reset --hard` on something already pushed
  forces a force-push and breaks your teammates' repos.
- **Branching strategies:** **trunk-based** (short-lived branches, everything into main several times a day, behind
  feature flags) is what correlates with high performance in the DORA studies. GitFlow, with its
  `develop`/`release`/`hotfix` branches, is designed for versioned releases and for installable software, not
  for a SaaS that deploys daily.
- **Good commits:** one logical change per commit, a message that explains **why** (the "what" is already in the
  diff), and conventional commits if you want to generate changelogs automatically.

> **Card** · **When:** every day ·
> **Pattern:** trunk-based with short-lived branches and feature flags for unfinished work ·
> **Anti-pattern:** `reset --hard` and force-push on a shared branch ·
> **Limits:** rewriting public history breaks your teammates' repos ·
> **How it fails:** weeks-long branches that produce impossible merges ·
> **Decision:** rebase locally, merge into main, `revert` in public ·
> **Trade-off:** linear, readable history vs history faithful to what actually happened ·
> **Related:** CI/CD, feature flags `[05]`

---

## CI/CD

**CI (Continuous Integration):** every push is built and tested. **CD** can be *Delivery* (always
ready to deploy, with a human button) or *Deployment* (deploys automatically if everything passes).

**A typical pipeline and the order things go in (fast stuff first, to fail early):**

```
1. Lint + formatting + type-check     (seconds)
2. Unit tests                          (1-2 min)
3. Image build                         (cached)
4. Integration tests with real services (docker compose / testcontainers)
5. Scans: dependencies (SCA), SAST, secrets, image
6. Push the image with tag = commit SHA
7. Deploy to staging  → smoke tests / critical E2E
8. Deploy to production (progressive) → automatic verification → rollback if it fails
```

**Principles you get asked about:**
- **Build once, deploy many.** You build **one** artifact and **the same one** goes through staging and production.
  If you rebuild per environment, you are no longer deploying what you tested.
- **Configuration comes from the environment**, not from the artifact (12-factor).
- **Everything fast or nobody uses it.** A 40-minute pipeline makes people batch changes, and big changes
  are the ones that break production.
- **Red pipeline = everything stops.** A broken main that gets tolerated destroys trust in the tests.
- **Determinism:** dependencies with a lockfile, images by digest, no `latest`. **Flaky tests** are
  poison: they erode trust until people retry without looking. Quarantine them and fix them.

**GitHub Actions — the essentials:**
```yaml
on: [push, pull_request]
permissions:
  contents: read          # least privilege; raise it only where needed
  id-token: write         # for OIDC to the cloud, without static secrets
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.13', cache: 'pip'}
      - run: pip install -r requirements.txt
      - run: pytest -q
```
- **Pin third-party actions by SHA**, not by tag: a tag can be moved and run arbitrary code
  in your pipeline with access to your secrets (it is a real and frequent supply-chain attack).
- **Never use `pull_request_target` with code from a fork** unless you know exactly what you are doing.
- Matrix builds, dependency caching, parallel jobs, and `concurrency` to cancel stale builds.

> **Card** · **When:** from the first commit ·
> **Pattern:** **build once, deploy many** — one artifact goes through staging and production ·
> **Anti-pattern:** rebuilding the image for production (you are no longer deploying what you tested) ·
> **Limits:** a slow pipeline makes people batch changes, and big batches break more ·
> **How it fails:** **flaky tests** erode trust until people retry without looking ·
> **Decision:** pin third-party actions by SHA — a tag can move and run code with your secrets ·
> **Trade-off:** more checks vs feedback speed ·
> **Related:** testing, secrets, supply chain `[06, 11]`

---

## Deployment strategies

| Strategy | How | Pros | Cons |
|---|---|---|---|
| **Recreate** | shut down and start up | trivial | **downtime** |
| **Rolling** | replace pods gradually | no downtime, K8s default | two versions coexist; slow rollback |
| **Blue/green** | two full environments, traffic switched all at once | **instant rollback**, testing on the identical one | double infrastructure; tricky DB migrations |
| **Canary** | 1% → 10% → 50% → 100% | detects problems with little impact | requires good metrics and automation |
| **Feature flags** | the code ships to production switched off | deploy ≠ release, instant rollback | debt from old flags; they must be cleaned up |

**What you are expected to say:** *deploy* and *release* are different things. With feature flags, the code reaches
production switched off and you turn it on for 1% of users whenever you want — that turns rollback into a
one-second configuration change, with no redeploy. **It is the safest way to deploy there is**, and in
exchange it forces a discipline of cleaning up flags.

**What almost nobody mentions and shows experience:** in rolling and canary **two versions of the
code coexist at the same time**, so every change must be backward and forward compatible — in the database
(expand/contract, `04-databases.md`), in the API and in the format of queue messages.

> **Card** · **When:** every change that reaches users ·
> **Pattern:** canary with automatic verification, or feature flags (deploy ≠ release) ·
> **Anti-pattern:** blue/green assuming the database gets duplicated too ·
> **Limits:** in rolling and canary **two versions of the code coexist** ·
> **How it fails:** a backward-incompatible change breaks half the users during the deployment ·
> **Decision:** feature flags turn rollback into a one-second configuration change ·
> **Trade-off:** fine-grained control vs flag debt that has to be cleaned up ·
> **Related:** migrations, compatibility `[04]`

---

## Rollbacks

- **The question that defines a team's maturity: "how long does it take you to go back?"** If the answer is
  "it depends", there is no rollback strategy.
- **Code rollback** is easy: go back to the previous artifact (that is why immutable tags matter).
- **Data rollback** is the hard part: a migration that dropped a column cannot be undone. That is why
  expand/contract — **never destroy in the same deployment in which you introduce.**
- **Roll forward** (fixing forward) is often better when rolling back would mean reverting
  migrations. Decide before the incident, not during it.
- Automate the rollback on clear signals (error rate, latency) in the canary deployment.

> **Card** · **When:** planned **before** deploying ·
> **Pattern:** immutable artifacts by digest and automatic rollback on clear signals ·
> **Anti-pattern:** discovering during the incident that the migration cannot be reverted ·
> **Limits:** code reverts easily; **data does not** ·
> **How it fails:** reverting the code against an already-migrated schema breaks everything worse ·
> **Decision:** never destroy in the same deployment in which you introduce ·
> **Trade-off:** rollback (fast, sometimes impossible) vs roll-forward (slower, always viable) ·
> **Related:** expand/contract, incident response `[04, 10]`

---

## Infrastructure as Code

**Why:** infrastructure that is versioned, reviewable in a PR, reproducible and auditable. *ClickOps* (clicking
around the console by hand) produces environments nobody knows how to recreate and that silently drift apart.

**Terraform / OpenTofu:**
```hcl
resource "aws_db_instance" "main" {
  identifier     = "api-prod"
  engine         = "postgres"
  instance_class = var.db_size
  storage_encrypted = true
  deletion_protection = true      # the flag that saves you from a terraform destroy
}
```

- **State (`state`):** the map between your code and the real resources. **Store it remotely (S3 + locking)**,
  never in the repo — it contains sensitive data and gets corrupted if two people apply at the same time.
- **`plan` before `apply`**, always, and in the PR so it gets reviewed.
- **Modules** so you don't repeat yourself, **workspaces or directories** per environment.
- **Declarative vs imperative:** Terraform declares the final state; Ansible runs steps. Terraform to
  provision, Ansible/cloud-init to configure inside.
- **Drift:** someone touched the console by hand and reality no longer matches. Detect it with a periodic `plan` in
  CI. And disable manual write permissions in production if you can.

> **Card** · **When:** all infrastructure that is not an experiment ·
> **Pattern:** `plan` reviewed in the PR; remote state with locking ·
> **Anti-pattern:** ClickOps — touching the console and nobody knowing how to recreate the environment ·
> **Limits:** the state contains sensitive data and gets corrupted if two people apply at the same time ·
> **How it fails:** **drift** — someone changed something by hand and reality no longer matches the code ·
> **Decision:** `deletion_protection` on everything that holds data ·
> **Trade-off:** rigour and traceability vs agility for an urgent change ·
> **Related:** environments, IAM `[13]`

---

## Environments and configuration

- **dev → staging → production**, with staging as close to production as possible (same type of
  database, same version, anonymised data of similar volume). A staging that does not resemble production proves nothing.
- **12-factor:** configuration in environment variables, with no per-environment files inside the artifact.
- **Validate configuration at startup** and fail loudly if something is missing. A service that starts with an
  empty variable and fails three hours later is much worse than one that does not start.
- **Dev/prod parity:** use Docker Compose or devcontainers so that "it works on my machine" stops being a
  thing people say.
- **Production data in development: no.** Anonymise or generate synthetic data. It is a legal risk (GDPR),
  not just a technical one.

> **Card** · **When:** when setting up dev, staging and production ·
> **Pattern:** 12-factor — configuration per environment, identical artifact ·
> **Anti-pattern:** real production data in development (a legal risk, not just a technical one) ·
> **Limits:** a staging that does not resemble production proves nothing ·
> **How it fails:** the service starts with an empty variable and fails three hours later ·
> **Decision:** validate configuration at startup and fail loudly if something is missing ·
> **Trade-off:** staging fidelity vs the cost of maintaining it ·
> **Related:** secrets, dev/prod parity `[06]`

---

## Secrets management

- Source of truth: Vault / AWS Secrets Manager / GCP Secret Manager / the CI provider's secrets.
  Injected at runtime, never baked into the image.
- **OIDC instead of static keys** between CI and the cloud (`13-cloud-infrastructure.md`).
- **Rotation** with an overlap window (`06-security.md`).
- **Detection:** secret scanning in the repo, in the history and in the CI logs. If something leaked,
  **rotating is mandatory** — deleting the commit does not help.
- **Kubernetes secrets are base64-encoded, not encrypted.** Enable etcd encryption at rest or use
  an operator (External Secrets, Sealed Secrets).

> **Card** · **When:** every credential, from day one ·
> **Pattern:** secrets manager + runtime injection + **OIDC** instead of static keys ·
> **Anti-pattern:** secrets in the repo, in the image, or in the logs ·
> **Limits:** Kubernetes Secrets are **base64, not encrypted** by default ·
> **How it fails:** a leaked secret lives on in forks and CI logs: deleting the commit does not help ·
> **Decision:** if it leaked, rotating is mandatory ·
> **Trade-off:** frequent rotation (secure, operationally expensive) vs long-lived keys ·
> **Related:** IAM, cryptography `[06, 13]`

---

## The deployment checklist

**Before:**
- [ ] CI green (tests, lint, types, security scans).
- [ ] **Backward-compatible** migrations — expand/contract `[04]`.
- [ ] Feature flags ready to switch off the new code without a redeploy.
- [ ] Rollback plan **written down**; and if the migration is not reversible, say so out loud beforehand.

**During:**
- [ ] Progressive deployment with automatic verification between steps.
- [ ] Compare the golden signals **of the new version against the old one**, not the aggregate `[12]`.
- [ ] Watch for **new** errors, not just the total: 50 new errors hide inside an error rate
      that barely moves.

**After:**
- [ ] Verify the critical business path for real (a real checkout, not a 200 on `/health`).
- [ ] Watch for what takes time to show up: memory leaks, unclosed connections, slowly growing queues.
- [ ] Close the loop: switch off the old flag, contract the migration, delete the dead code.

**The principle that sums it up:** *deployments should be boring*. If deploying causes anxiety, the
problem is not the deployment — it is missing automation, observability or reversibility.

> **Card** · **When:** every deployment to production ·
> **Pattern:** progressive + automatic verification + rollback ready ·
> **Anti-pattern:** deploying and watching the aggregate dashboard (the old version hides the new one from you) ·
> **Limits:** the checklist does not replace automation; manual steps get forgotten ·
> **How it fails:** the problem shows up hours later, when nobody connects cause and effect anymore ·
> **Decision:** does the rollback require reverting data? Then plan a roll-forward ·
> **Trade-off:** ceremony vs deployment frequency ·
> **Related:** migrations, feature flags, observability `[04, 12]`

---

## The production checklist for a new service

What must exist **before** it receives real traffic. It is the operational summary of all the boxes:

**Operations:** `live`/`ready` health checks properly separated `[12]` · graceful shutdown that respects SIGTERM
`[10]` · resource limits `[13]` · timeouts on every outbound call `[10]` · tested rollback.

**Observability:** structured logs with `trace_id` · metrics for the four signals · distributed
tracing · SLO-based alerts with a runbook · dashboard `[12]`.

**Security:** authentication and **object-level authorisation** · secrets out of the code · TLS ·
rate limiting · input validation · scanned dependencies · security headers `[06]`.

**Data:** reversible migrations · **tested** backups · defined retention · PII identified `[04, 15]`.

**Resilience:** retries with backoff · circuit breakers · defined degradation per feature ·
idempotency wherever there are retries `[08, 10]`.

**Documentation:** a README on how to run it, a runbook for known failures, ADRs for the important
decisions `[05]`, and **who is on call**.

> **Card** · **When:** before the first real traffic of any service ·
> **Pattern:** the checklist as an acceptance criterion, not a suggestion ·
> **Anti-pattern:** "we'll add that after launch" ·
> **Limits:** meeting it does not guarantee it will not fail, only that you will know what happened and be able to revert ·
> **How it fails:** the three most often forgotten: graceful shutdown, separating liveness from readiness, and the runbook ·
> **Decision:** if there is no owner and no on-call, the service is not ready for production ·
> **Trade-off:** time before launch vs incidents afterwards ·
> **Related:** all the operational boxes `[06, 08, 10, 12, 13]`

---

## Interview questions and trade-offs

**Q: How do you deploy, with zero downtime, a version that changes the database schema?**
Expand/contract across several deployments, with the code compatible with both schemas during the transition.
*Signal:* you say explicitly that during a rolling update **two versions of the code coexist**, so
backward compatibility is not optional.

**Q: Blue/green or canary?**
Blue/green for instant rollback and big changes; canary when you want to detect regressions with
minimal impact and you have metrics to automate the decision. *Signal:* you point out that blue/green clashes with
database migrations (both environments share the data) and that canary needs good observability
so it is not just theatre.

**Q: What is trunk-based development and why?**
Short-lived branches that integrate into main daily, with feature flags for unfinished work. It reduces the pain of
merges and the size of changes, which is what correlates with fewer failures. *Signal:* you mention DORA
and that small batches are safer because the blast radius of each change is small.

**Q: Production is broken and you don't know which commit did it. What do you do?**
First mitigate (rollback or feature flag), then investigate — `git bisect` or reviewing what was deployed against the
timing of the incident. *Signal:* you separate mitigating from diagnosing; many people try to understand
the bug while users are still affected.

**Q: Why not build the image again for production?**
Because the artifact you test must be exactly the one you deploy. Rebuilding introduces differences
(transitive dependencies, date, cache). *Signal:* you call it by its name — build once, deploy many — and
tie it to immutable tags by digest.

**Core trade-off of this box:** *delivery speed vs change safety*. Intuition says they are
opposites; the DORA data says the opposite: teams that deploy more often **fail less**,
because small batches are easier to review, test and revert. Automation is what
makes it possible for both to go up at the same time.

---

## Sources

- [DORA — State of DevOps / Four Keys](https://dora.dev/) — why deploying more often correlates with failing less.
- *Accelerate* (Forsgren, Humble, Kim) — the research behind the DORA metrics.
- [Trunk Based Development](https://trunkbaseddevelopment.com/)
- [GitHub Actions — Security hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions) — pinning actions by SHA, `pull_request_target`.
- [Terraform — State](https://developer.hashicorp.com/terraform/language/state) · [OpenTofu](https://opentofu.org/)

# 13 · Cloud & Infrastructure

> You don't need to be an SRE, but you do need to know **where your code runs, how traffic reaches it and why
> it goes down**. In a senior interview you'll be asked to draw this on a whiteboard.


**Covers from the syllabus:** `linux` · `containers` · `orchestration` · `cloud` · `networking` · `storage` · `iam` · `tradeoffs`

---

## Linux: what a backend actually uses

**Diagnosing in production — the minimum kit:**

```bash
top / htop           # CPU and memory per process
ps aux --sort=-%mem  # who's eating memory
df -h                # disk full (the dumbest and most common cause of incidents)
du -sh *             # what's filling it
free -h              # RAM and swap
netstat -tlnp / ss -tlnp   # what's listening on which port
lsof -i :8000        # who holds that port
lsof -p PID | wc -l  # open file descriptors (the "too many open files")
dmesg | tail         # did the kernel kill something? (OOM killer)
strace -p PID        # which syscall it's stuck in
journalctl -u svc -f # the service's logs
```

**Concepts that come up in interviews:**
- **Processes and signals:** `SIGTERM` (please terminate — **it's the one you must handle** to shut down
  gracefully) vs `SIGKILL` (you die now, it can't be caught). Kubernetes sends SIGTERM, waits
  `terminationGracePeriodSeconds` and then sends SIGKILL.
- **OOM killer:** when memory runs out, the kernel picks a victim and kills it. In a container it shows up as
  `OOMKilled` and an unexplained restart.
- **File descriptors:** every open socket and file is one. A low `ulimit -n` is the real cause of many
  failures under load.
- **Permissions** (`chmod`/`chown`), non-root users, and **never run the container as root**.
- **cgroups and namespaces:** the two kernel mechanisms containers are built on —
  cgroups limit resources, namespaces isolate the view (processes, network, filesystem).

> **Card** · **When:** in any incident that touches the machine ·
> **Pattern:** handle SIGTERM to shut down in an orderly way; keep an eye on FDs and disk ·
> **Anti-pattern:** ignoring SIGTERM and letting SIGKILL cut off in-flight requests ·
> **Limits:** `ulimit -n` caps the number of simultaneously open connections ·
> **How it fails:** **disk full** — the dumbest and most frequent cause of incidents ·
> **Decision:** if the process isn't PID 1 via the exec form, it doesn't receive the signals ·
> **Trade-off:** minimal containers (no diagnostic tools) vs debuggability ·
> **Related:** graceful shutdown, file descriptors `[01, 10]`

---

## Docker

**The mental model:** an image is a layered filesystem + metadata. A container is a host process,
isolated with namespaces and limited with cgroups. **It's not a virtual machine**: it shares the kernel.

**A quality Dockerfile:**
```dockerfile
# 1) Multi-stage: build in a fat image, copy into a slim one
FROM python:3.13-slim AS build
WORKDIR /app
COPY requirements.txt .                  # 2) deps first: cached layer
RUN pip install --no-cache-dir -r requirements.txt --target /deps

FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1                   # 3) unbuffered logs -> you see them in real time
COPY --from=build /deps /usr/local/lib/python3.13/site-packages
COPY . /app
WORKDIR /app
USER 1000:1000                           # 4) non-root
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0"]
```

**The rules:**
- **Layer order = build speed.** What rarely changes (dependencies) goes at the top; the code, at the bottom.
- **Multi-stage** reduces size and attack surface (the compiler doesn't ship to production).
- **`.dockerignore`** — without it you put `.git`, `node_modules` and secrets into the image.
- **Small base images** (slim, distroless). Alpine uses musl instead of glibc, which sometimes causes subtle
  DNS and performance problems in Python: use it knowing that.
- **Never put secrets in the Dockerfile.** They stay in the layer forever, even if you delete them later.
- **Pin versions** (`python:3.13-slim`, not `latest`) or your builds aren't reproducible.
- **One process per container**, and have it write **logs to stdout/stderr**. Logs written to a file inside a
  container are lost logs.
- **Signals:** use the exec form of `CMD` (`["cmd","arg"]`) so your process is PID 1 and receives SIGTERM.
  With the shell form, `/bin/sh` receives it and your app dies without closing anything.

> **Card** · **When:** packaging any service ·
> **Pattern:** multi-stage, layers ordered by how often they change, non-root user, pinned versions ·
> **Anti-pattern:** secrets in the Dockerfile (they stay in the layer forever) and the `latest` tag ·
> **Limits:** it shares the kernel with the host: it's not strong security isolation ·
> **How it fails:** the shell form of `CMD` means your process never receives SIGTERM ·
> **Decision:** logs to stdout, one process per container, always a `.dockerignore` ·
> **Trade-off:** minimal image (secure, hard to debug) vs full image ·
> **Related:** signals, CI/CD `[14]`

---

## Kubernetes

**Objects you need to know:**

| Object | What it is |
|---|---|
| **Pod** | the smallest unit: one or more containers sharing network and volumes |
| **Deployment** | manages ReplicaSets: replicas, rolling updates and rollback |
| **Service** | a stable IP and DNS name that load-balances across the pods (ClusterIP, NodePort, LoadBalancer) |
| **Ingress / Gateway API** | HTTP entry from outside, routing by host/path, TLS |
| **ConfigMap / Secret** | configuration and secrets (a Secret is base64, **not encrypted** by default) |
| **StatefulSet** | pods with stable identity and disk (databases) |
| **Job / CronJob** | one-off or scheduled work |
| **HPA** | autoscaling based on metrics |
| **PDB** | PodDisruptionBudget: how many can go down at once during maintenance |

**What you really have to understand:**

- **It's a reconciliation loop.** You declare the desired state; the controller works nonstop to make
  reality match it. You don't give orders, you declare intentions.
- **Requests vs limits:**
  - `requests` = what the scheduler reserves. It determines **where** your pod fits.
  - `limits` = the ceiling. Exceeding the memory limit = **OOMKilled**; exceeding the CPU limit = **throttling**
    (your app doesn't die, it becomes inexplicably slow — a classic cause of p99 spikes).
  - Without `requests`, the scheduler piles pods up and the nodes get saturated.
- **Probes** — and mixing them up causes incidents:
  - `liveness`: if it fails, **the pod is restarted**. Make it too aggressive and you get a restart loop
    under load.
  - `readiness`: if it fails, **the pod is taken out of load balancing** without being killed. This is the one
    that should check dependencies.
  - `startup`: gives slow-starting apps some slack before the other two kick in.
- **Graceful shutdown:** when a pod terminates, Kubernetes removes it from the Service *and* sends SIGTERM
  **at the same time** (no guaranteed order). That's why you add a `preStop` hook that waits a few seconds:
  otherwise you receive traffic after you've started shutting down and return 502s on every deployment.
- **Rolling update** with `maxSurge`/`maxUnavailable` is the default; blue/green and canary are built on top
  (`14-devops.md`).

**When NOT to use Kubernetes:** a small team with three services. The operational cost (upgrades, networking,
RBAC, observability, the cluster itself) is real. **Cloud Run, ECS Fargate, App Runner or a PaaS solve
90% of cases with 10% of the effort.** Saying this in an interview shows judgment, not ignorance.

> **Card** · **When:** several services and a team with the capacity to operate it ·
> **Pattern:** explicit requests and limits, clearly separated probes, a PDB and `preStop` ·
> **Anti-pattern:** external dependencies in the liveness probe ·
> **Limits:** exceeding the memory limit = **OOMKilled**; exceeding the CPU limit = **silent throttling** ·
> **How it fails:** unexplained p99 spikes caused by the container's CPU throttling ·
> **Decision:** with 3 services and a small team, Cloud Run or ECS solve 90% of it with 10% of the effort ·
> **Trade-off:** full control vs a permanent operational cost ·
> **Related:** health checks, graceful shutdown, deployments `[10, 12, 14]`

---

## Cloud networking

```
Internet
   │
[ DNS ]  →  [ CDN ]  →  [ WAF ]  →  [ Load Balancer (TLS) ]
                                         │
                            ┌────────────┴────────────┐
                       [ public subnet: LB, NAT GW ]
                            │
                       [ private subnet: your services ]
                            │
                       [ isolated subnet: database ]
```

- **VPC:** your private network. **Public subnets** (with a route to an internet gateway) vs **private** ones (they
  reach the internet only through a NAT gateway; **nobody gets in from outside**).
- **The golden rule: your database is never in a public subnet.** It only accepts connections from your
  application's security group.
- **Security groups** (stateful, at the instance level; the response is allowed back automatically) vs **NACLs**
  (stateless, at the subnet level, with separate inbound and outbound rules).
- **Reverse proxy** (nginx, Envoy, Traefik): TLS, routing, buffering of slow clients, compression,
  basic rate limiting. It protects your app from maliciously slow clients (slowloris).
- **Availability zones (AZs):** deploy to at least two. A region is a set of AZs;
  **multi-region** is much more expensive and complex (data replication, latency, split-brain) and is almost never
  justified before you have a large business.

> **Card** · **When:** when setting up the infrastructure for an environment ·
> **Pattern:** LB in a public subnet; services in a private one; database in an isolated subnet ·
> **Anti-pattern:** a database reachable from the internet ·
> **Limits:** the NAT gateway charges per GB: outbound traffic can be an expensive surprise ·
> **How it fails:** once TLS is terminated at the LB, without `X-Forwarded-*` your app knows neither the IP nor the scheme ·
> **Decision:** multi-AZ always; multi-region only with a business reason ·
> **Trade-off:** network isolation vs configuration complexity ·
> **Related:** TLS, load balancing, cost `[02, 09]`

---

## Object storage (S3 and equivalents)

- **It's an object store, not a filesystem.** There are no real directories (the `/` characters are part of the
  name), there's no append, and renaming means copying and deleting.
- **Consistency:** since 2020 S3 is *strongly consistent* for read-after-write — the old interview question
  about eventual consistency is now obsolete, and knowing that earns you a point.
- **Storage classes:** Standard → Infrequent Access → Glacier. With automatic **lifecycle rules**,
  this is one of the most cost-effective optimizations there is.
- **Presigned URLs** to upload and download without going through your backend (`15-files-data.md`).
- **Security:** block public access at the account level, encryption at rest, versioning (protects against
  accidental deletions and ransomware), and minimal bucket policies.

> **Card** · **When:** every user file, backup or export ·
> **Pattern:** presigned URLs, blocked public access, versioning and lifecycle rules ·
> **Anti-pattern:** proxying the bytes through your application ·
> **Limits:** it's not a filesystem: there's no append and renaming means copying and deleting ·
> **How it fails:** buckets left public because of default configuration ·
> **Decision:** S3 has been *strongly consistent* since 2020 — the old question about eventual consistency is obsolete ·
> **Trade-off:** higher latency than a local disk vs durability and scale ·
> **Related:** uploads, backups, cost `[15]`

---

## Serverless

**Functions (Lambda, Cloud Functions) and serverless containers (Cloud Run, Fargate).**

- ✅ Zero server management, automatic scale-to-zero, pay-per-use; ideal for irregular traffic,
  webhooks, crons and event processing.
- ❌ **Cold starts**, execution time limits, trouble with persistent database connections
  (you need a pooler or an HTTP driver: see `04-databases.md`), and high cost with constant, heavy traffic.
- **The cost flips:** with low or sporadic traffic, serverless is dramatically cheaper; with constant
  24/7 traffic, an always-on container wins by a wide margin.
- **Modern models** (such as Fluid Compute) reuse instances across concurrent requests, which reduces
  cold starts and changes this calculation quite a bit compared to the classic 2018 Lambda.

> **Card** · **When:** irregular traffic, webhooks, crons, event processing ·
> **Pattern:** stateless functions with fast startup ·
> **Anti-pattern:** opening a new Postgres connection per invocation ·
> **Limits:** cold starts, maximum execution time, and persistent connections are hard ·
> **How it fails:** a concurrency spike opens thousands of connections and takes down the database ·
> **Decision:** you absolutely need an external pooler or an HTTP driver `[04]` ·
> **Trade-off:** cheap with sporadic traffic, expensive with constant traffic ·
> **Related:** connection pooling, cold starts `[04]`

---

## IAM

**The model you need to internalize:** *who* (principal) can do *what* (action) on *which resource*,
*under what conditions*.

- **Least privilege.** Start by denying everything and add what's needed. `Action: "*"` is an audit finding.
- **Roles, not keys.** An instance/pod assumes a role and gets temporary credentials that rotate on their own.
  **Static access keys in environment variables are what ends up leaked on GitHub.**
- **OIDC federation:** your CI pipeline (GitHub Actions) assumes a role in the cloud **without storing secrets**.
  It's the current standard and it replaces long-lived keys.
- **Environment separation:** separate accounts/projects for dev, staging and production. It's the most
  effective barrier against "I accidentally deleted it in prod".
- **Connects to SSRF** (`06-security.md`): if someone reaches the metadata endpoint, they get the role's
  credentials. That's why least privilege isn't bureaucracy — it limits the damage of a breach.

> **Card** · **When:** every cloud resource you create ·
> **Pattern:** roles with temporary credentials; OIDC between CI and the cloud ·
> **Anti-pattern:** static access keys in environment variables ·
> **Limits:** permissions accumulate over time and nobody reviews them ·
> **How it fails:** **SSRF** reaches the metadata endpoint and obtains the role's credentials `[06]` ·
> **Decision:** separate accounts per environment: the most effective barrier against "I deleted it in prod" ·
> **Trade-off:** least privilege (secure, friction) vs broad permissions ·
> **Related:** SSRF, secrets, CI/CD `[06, 14]`

---

## Storage: volumes and state in containers

A container's disk is **ephemeral**: it disappears on restart. Anything that has to survive needs
an explicit mechanism.

| Type | Lifetime | Use |
|---|---|---|
| Container filesystem | dies with the pod | single-use temporary files |
| `emptyDir` | lives as long as the pod | cache shared between containers in the same pod |
| **PersistentVolume (PVC)** | independent of the pod | databases, disk-backed queues |
| **Object storage (S3)** | permanent | user files, backups, exports `[15]` |

```yaml
# StatefulSet: stable identity and disk per replica (postgres-0, postgres-1...)
volumeClaimTemplates:
  - metadata: {name: data}
    spec:
      accessModes: ["ReadWriteOnce"]     # only one node can mount it at a time
      resources: {requests: {storage: 100Gi}}
```

**`ReadWriteOnce` is the constraint that catches people out:** most block volumes can only be mounted on
**one node**. If you want several pods to write to the same disk you need `ReadWriteMany` (NFS, EFS), which
is slower and more expensive. **In practice, the right answer is almost always not to share a disk:**
use object storage or the database.

> **Card** · **When:** any service that writes something that has to survive ·
> **Pattern:** stateless by default; state in the DB or in object storage ·
> **Anti-pattern:** storing uploads on the container's local disk — they disappear and aren't shared ·
> **Limits:** `ReadWriteOnce` prevents several nodes from mounting the same volume ·
> **How it fails:** it works with one replica and breaks as soon as you scale to two ·
> **Decision:** if a user uploads the file, it goes to object storage, never to local disk ·
> **Trade-off:** local disk (fast, tied to a node) vs object storage (scalable, with latency) ·
> **Related:** uploads, StatefulSets `[15]`

---

## Cost: where the money goes

Cost is an engineering responsibility. Ordered by return on the optimization:

| Money sink | Why it happens | What to do |
|---|---|---|
| **Runaway observability** | DEBUG-level logs, high-cardinality metrics | sample, filter in the Collector, tune retention `[12]` |
| **Storage without lifecycle rules** | nothing ever gets deleted or moved to a cheaper class | lifecycle rules: the most cost-effective optimization |
| **Oversized instances** | "just to be safe" | measure real usage; savings plans for the baseline, spot for what's fault-tolerant |
| **Non-production environments running 24/7** | nobody shuts them down | shut down dev and staging outside working hours |
| **Data transfer** | between zones and out to the internet | the cost that surprises people most; co-locate services in the same AZ |
| **Bot traffic** | sometimes half of all requests | WAF and rate limiting `[03]` |
| **Incomplete multipart uploads** | aborted uploads that keep getting billed | a lifecycle rule that aborts them `[15]` |
| **NAT gateway** | all outbound traffic goes through it | VPC endpoints for S3 and the cloud's services |
| **LLM tokens** | a large model for trivial tasks | one model per task, caching, limits `[18]` |

**Minimum hygiene:** tag resources by service and environment (without that you can't attribute spend),
budget alerts, and a monthly review of the bill. **An anomalous-spend alert is as important
as a latency alert:** an infinite loop or a retry storm shows up on the bill before it shows up in the metrics.

> **Card** · **When:** monthly review, and when designing anything that scales ·
> **Pattern:** mandatory tagging + budget alerts + lifecycle rules ·
> **Anti-pattern:** discovering the problem when the bill arrives ·
> **Limits:** optimizing cost can worsen latency or availability ·
> **How it fails:** observability ends up costing more than the infrastructure it observes ·
> **Decision:** go first after what doesn't affect the user (retention, stopped environments, storage classes) ·
> **Trade-off:** cost vs performance and visibility ·
> **Related:** observability, lifecycle, AI `[12, 15, 18]`

---

## Interview questions and trade-offs

**Q: Draw how a request gets from the browser to your container.**
DNS → CDN → WAF → load balancer (terminates TLS) → ingress/service → pod. *Signal:* you mention where TLS
terminates, that from that point on you need `X-Forwarded-For`, and that the database lives in a private subnet with no
route from the internet.

**Q: A pod keeps restarting. How do you debug it?**
`kubectl describe pod` (events, reason for the last state: OOMKilled, CrashLoopBackOff), logs from the previous
container (`--previous`), check the memory limits and the liveness probe. *Signal:* you know that an overly strict
liveness probe can cause the restart loop *by itself* when the app is slow but alive.

**Q: What's the difference between liveness and readiness?**
Liveness restarts, readiness takes the pod out of load balancing. *Signal:* you say that external dependencies are
checked in readiness and **not** in liveness — if you put the DB in the liveness probe, a DB outage restarts all
your pods and makes the incident worse.

**Q: Serverless or containers?**
It depends on the traffic pattern and the latency requirements. *Signal:* you talk about cold starts, the problem
of database connections and the cost flip with constant traffic, instead of saying one of them
is better.

**Q: Why not use `latest` as a tag?**
Because the build stops being reproducible and a rollback doesn't take you back to the same artifact. *Signal:* you tie it
to immutability: the same image with the same digest is promoted from staging to production without
being rebuilt (`14-devops.md`).

**Core trade-off of this box:** *control vs operational cost*. Kubernetes gives you full control and charges you
in permanent complexity; a PaaS takes away control and gives you back engineering time. The senior answer
depends on the size of the team, not on fashion: **choose the simplest thing that supports your real requirements
for scale, isolation and compliance.**

---

## Sources

- [Kubernetes docs — Configure Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Docker — Best practices for writing Dockerfiles](https://docs.docker.com/build/building/best-practices/)
- [The Twelve-Factor App](https://12factor.net/) — configuration, stateless processes, parity between environments.
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/) — the cost, reliability and security pillars.
- [Vercel — Fluid Compute](https://vercel.com/docs/fundamentals/fluid-compute) — instance reuse to reduce cold starts.

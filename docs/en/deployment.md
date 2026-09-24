# Deploying Mirag

## What changes on a server

By default this agent **does not run the code it generates** (`MIRAG_EXECUTION=off`). It
delivers it together with its test cases, and running them will be the QA agent's job, in an
environment built for that. What is still checked without running anything: structure,
syntax and imports.

That **was the big risk**: a server that runs code written by a model at a stranger's request
is a server that has to be locked up. Without execution the image needs neither `pytest` nor
`node`, and most of the reasons to be afraid disappear. And when execution is on (the demos,
the benchmarks), the child process **inherits no credential**: only `PATH`, `HOME`, the locale
and the temp variables.

What is left is a server that reads a corpus, calls a model and returns text and a ZIP. There
are still things to look after - below - but of another size.

## On your machine

```bash
docker compose up -d --build                      # the clean image, no dependencies
docker compose --profile identidad up -d --build  # + on-chain identity (stellar-sdk)
```

The page is at http://127.0.0.1:8000 and **only** there: the port is published as
`127.0.0.1:8000:8000`. It starts with `MIRAG_OFFLINE=1`: scripted demos, zero model calls,
zero cost.

## Publishing the images

Two paths that do the same. Today the first one rules, because the CI is blocked by the
GitHub account's billing and its jobs do not start.

**From your machine:**

```bash
scripts/publish.sh             # check, build, publish and verify what was published
scripts/publish.sh --no-push   # everything but the push
```

It aborts if the tree is dirty, if the commit is not on `origin/main`, if a demo breaks its
contract, if something shaped like a credential is versioned, or if the built image does not
start or serves something it must not. That rule - what does not pass is not published - is
half the value of a CI, and it is lost entirely if you publish by hand with `docker push`.

The registry is not hard-coded: when nothing is said, the image name is derived from the user
of your `docker login` (asking the credential helper when needed). Today it publishes to
**`andreajunes/agente-backend`**, with the tags `latest`, `<sha>` and their `-identidad`
variants.

**Docker Hub login**, once. Create the token in Docker Hub → avatar → *Account settings* →
*Personal access tokens*, with **Write** permission. A token and not the password: it can be
revoked on its own, without touching the account.

```bash
docker login --username YOURUSER      # and paste the token when it asks for the password
scripts/publish.sh
```

If `docker login` reports success but every `docker pull` then fails, look at `credsStore` in
`~/.docker/config.json`: if it points to a helper that is not installed - `desktop` without
Docker Desktop, for example - the login stores nothing and leaves an empty entry that breaks
even anonymous pulls.

**Or on GHCR:**

```bash
gh auth refresh -h github.com -s write:packages
gh auth token | docker login ghcr.io -u AndJunes --password-stdin
MIRAG_IMAGEN=ghcr.io/andjunes/agente-backend scripts/publish.sh
```

**From GitHub Actions**: `.github/workflows/ci.yml` does the same on every push to `main`
(lint, demo contracts, credentials, and it publishes to GHCR only if everything passed). As
soon as the account is unblocked it works on its own and `scripts/publish.sh` becomes plan B.

## What server is needed

Measured on the previous layout: the image took 154 MB (181 the identity one). The compose
caps the container at 1 GB of RAM and 1.5 CPU. The agent has no database and keeps nothing
between restarts. With CodeZard on the same machine, **2 vCPU and 2 GB** are comfortable; 4 GB
if CodeZard grows.

This agent **publishes no port**, so the server firewall only needs 22 (SSH) and, later, 80
and 443 for CodeZard.

## On the server, step by step

The server needs **neither the source code, nor Python, nor to build anything**: only Docker
and two files.

**1 · Docker**, if it is not there:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER && newgrp docker
```

**2 · The two files**, without cloning the repository:

```bash
mkdir -p ~/agente && cd ~/agente
RAW=https://raw.githubusercontent.com/AndJunes/agente-backend/main
curl -fsSL -O  "$RAW/docker-compose.prod.yml"
curl -fsSL -o .env "$RAW/.env.server.example"
```

`raw.githubusercontent.com` serves from a CDN that caches for a few minutes: right after a
change it may silently give you the previous version. To force a fresh one, add
`-H "Cache-Control: no-cache"` and `?$(date +%s)` to the URL.

**3 · The `.env`.** Generate the token, do not invent it, and paste your OpenRouter key:

```bash
# -i.bak and not a bare -i: macOS sed requires a suffix and Linux sed accepts one.
sed -i.bak "s|^MIRAG_TOKEN=.*|MIRAG_TOKEN=$(python3 -c 'import secrets;print(secrets.token_urlsafe(32))')|" .env && rm -f .env.bak
nano .env        # and set OPENROUTER_API_KEY
chmod 600 .env   # only your user reads it
```

**4 · Start it:**

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml logs -f    # Ctrl-C to leave
```

**5 · Check it works.** The confusing part: **there is no published port**, so
`curl localhost:8000` on the server does NOT answer, and that is correct. Check from inside the
network, where CodeZard lives:

```bash
docker run --rm --network codezard_interna curlimages/curl \
  -s -o /dev/null -w "%{http_code}\n" http://mirag:8000/api/v1/health       # 200

docker run --rm --network codezard_interna curlimages/curl \
  -s -o /dev/null -w "%{http_code}\n" -X POST http://mirag:8000/api/v1/chat \
  -H "Content-Type: application/json" -d '{"question":"hello"}'            # 401, no token
```

**6 · CodeZard** joins the same network and talks to it by name, `http://mirag:8000`, sending
`MIRAG_TOKEN` in the `X-Mirag-Token` header. If it has its own compose:

```yaml
networks:
  interna:
    external: true
    name: codezard_interna
```

The browser never talks to the agent: it talks to CodeZard, and CodeZard's server forwards.
The contract is in [api.md](api.md).

## Updating and rolling back

```bash
docker compose -f docker-compose.prod.yml pull && docker compose -f docker-compose.prod.yml up -d
```

To go back to an earlier version, `MIRAG_TAG=<sha>` in the `.env` and repeat. The sha is
printed by `scripts/publish.sh` when it publishes.

## The two images

One `Dockerfile`, three stages and two targets:

```bash
docker build --target base      -t mirag:base      .   # zero dependencies
docker build --target identidad -t mirag:identidad .   # + stellar-sdk
```

The middle stage installs `stellar-sdk` (pinned to 16.1.0) into a venv and the final one
**copies the venv**: `pip` and its caches never reach the image.

## The token

Without `MIRAG_TOKEN` the server is open to whoever reaches the port, and it says so at
startup. There is no default token on purpose: a factory secret is known to everybody. The
production compose refuses to start without one.

## The model key

Never in the `Dockerfile`, never in the compose, never in the image: what goes into a layer
stays there even if a later step deletes it. It goes in the `.env` next to it, which is in
`.gitignore` and `.dockerignore`. The image only copies `src/`, and without `pyproject.toml` it
does not behave as a checkout: it never reads a `.env` from disk.

The compose **does not use `env_file`**: `env_file` injects the whole `.env`. With `${VAR}`
only what is named gets in, so `STELLAR_SECRET_KEY` reaches no container.

For the proof of concept, `MIRAG_MODEL=openrouter/free` keeps spending at $0 and the cost panel
says so (`FREE`). Limits: 20 requests per minute and 50 per day (1,000 if you ever bought $10
of credit).

The earlier names (`MIRAG_MODELO`, `LIMITE_USD`, `MIRAG_EJECUCION`) are still read when the new
name is absent, so an old `.env` does not silently change model or cap.

## The on-chain identity, without the seed

**Showing** the identity only takes unsigned reads: `STELLAR_PUBLIC_KEY` and
`STELLAR_AGENT_ID` are enough, and **the seed never enters the container**. Signing is only
needed to *register*, a manual, local, one-off operation (`scripts/blockchain_agent_demo.py`).
See [blockchain.md](blockchain.md).

## What the container holds, and why

| | |
|---|---|
| **base image without dependencies** | the core is standard library: no supply chain to compromise |
| **user `mirag` (uid 10001)** | nothing runs as root |
| **`/app/src` belongs to root** | the process cannot rewrite its own code |
| **a single writable path** | `/app/var` (`MIRAG_DATA_DIR`): outputs, artifacts, traces and caches |
| **`/tmp` on tmpfs** | lives in RAM and dies with the container |
| **`cap_drop: ALL`, `no-new-privileges`** | not one capability, no setuid escalates |
| **`pids_limit`, `mem_limit`, `cpus`** | CPU, memory and process ceilings |

## What is still not solved

**There is no request rate limit.** `MIRAG_BUDGET_USD` is per request, not per hour. If
CodeZard is exposed, rate limiting belongs to CodeZard or the proxy in front. What does close
the worst case, and takes two minutes, is a **credit limit on the key in the OpenRouter
dashboard**.

**Artifacts expire**: one hour, 20 at a time, 64 MB, and they are lost on restart. CodeZard
has to download the ZIP as soon as it gets it ([api.md](api.md)).

**The token is a shared secret, not user authentication.** Whoever holds it can ask for
everything. If one day there are several consumers with different permissions, it falls short.

**When the QA agent arrives, execution comes back**, and with it the big problem - but in its
own service, which is where it can really be locked up. `MIRAG_EXECUTION` is the seam it will
come in through.

Part of that seam exists now, for the **bare-metal** deployment only: `MIRAG_EXECUTION_BACKEND=docker`
(see [configuration.md](configuration.md)) makes `mirag serve` — run directly on a host, as it is
in local development — launch each probe inside its own disposable, network-isolated,
resource-capped container instead of a plain subprocess. It requires that host to have Docker
reachable and is opt-in, off by default.

That is deliberately **not** wired into the hardened container above. This image already runs
`cap_drop: ALL` and publishes no ports; giving it a Docker socket so it could launch sibling
containers would hand it root-equivalent access to whatever host runs it, undoing every row in
the table. The "own service" this section already called for is still the right shape for that
case — a separate, purpose-built service with its own contained Docker access, reached over the
network rather than through this container's socket.

# Mirag. The image installs NOTHING: the core is pure standard library.
#
# That is the best security property this container has. Without `pip install` there is no
# supply chain to compromise and no dependency CVE to patch at 3 a.m.: the surface is the
# interpreter and nothing else. If this ever needs a dependency, make it a conscious, pinned
# decision.
FROM python:3.14-slim AS base

# PYTHONDONTWRITEBYTECODE: no __pycache__, which the unprivileged user could not write anyway.
# PYTHONUNBUFFERED: logs come out when they happen; otherwise `docker logs` is blind exactly
#   when you need it.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Unprivileged user, created BEFORE copying so the COPY can assign owners.
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin mirag

WORKDIR /app

# Only the package is copied, as ROOT, and the process runs as `mirag`: it cannot rewrite its
# own code, so nothing a request does can plant anything for the next one. Without
# pyproject.toml the package does not look like a source checkout, so it never reads a `.env`
# from disk: configuration only arrives through the environment.
COPY --chown=root:root src /app/src

# The only writable path: outputs, artifacts, traces and caches (MIRAG_DATA_DIR).
RUN mkdir -p /app/var && chown mirag:mirag /app/var

# 0.0.0.0 here does NOT relax the bind: inside the container there is no other network, and
# it is the only way a published port reaches the process. What isolates it is publishing
# with `127.0.0.1:8000:8000` (or not publishing at all). The code default is still loopback.
# MIRAG_OFFLINE=1 from the factory: a freshly built image cannot spend anybody's money.
# MIRAG_EXECUTION=off is the code default, written here anyway because an image should say
# what it does: it delivers code and tests WITHOUT running them (that is the QA agent's job),
# so it needs neither pytest nor node and runs nothing foreign.
ENV PYTHONPATH=/app/src \
    MIRAG_DATA_DIR=/app/var \
    MIRAG_HOST=0.0.0.0 \
    MIRAG_PORT=8000 \
    MIRAG_OFFLINE=1 \
    MIRAG_EXECUTION=off

USER mirag
EXPOSE 8000

# No curl in a slim image, and not worth adding a network binary for this: the interpreter
# already inside does the check.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys;\
sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health',timeout=4).status==200 else 1)"

CMD ["python", "-m", "mirag", "serve"]


# ══════════════════════════════════════════════════════════════════════════════
# Stage 2 · the dependencies of the blockchain layer, apart
# ══════════════════════════════════════════════════════════════════════════════
# Not to keep a compiler out: none is needed, the packages with native extensions ship
# prebuilt cp314 wheels for both architectures. What this stage buys:
#   1. pip and its caches never reach the final image.
#   2. Two targets from one Dockerfile (--target), without duplicating anything.
#   3. The dependencies live in their own venv, not mixed with the system.
# stellar-sdk is pinned to the version the lock of the previous layout had; its transitive
# dependencies are resolved at build time.
FROM python:3.14-slim AS dependencias

RUN python -m venv /opt/identidad \
 && /opt/identidad/bin/pip install --no-cache-dir "stellar-sdk==16.1.0"


# ══════════════════════════════════════════════════════════════════════════════
# Stage 3 · the image with the on-chain identity
# ══════════════════════════════════════════════════════════════════════════════
# Copying a venv between stages only works when both share the base image (a venv is
# platform specific and its pyvenv.cfg points to a concrete interpreter). Both are
# python:3.14-slim, which is exactly the condition.
#
# The venv belongs to root: `mirag` can use it and cannot touch it. Same idea as /app.
FROM base AS identidad

COPY --from=dependencias --chown=root:root /opt/identidad /opt/identidad

# The venv comes first in PATH, so the `python` of the CMD inherited from `base` is the one
# that sees stellar_sdk. The rest of the agent is standard library and does not care.
ENV PATH="/opt/identidad/bin:$PATH" \
    MIRAG_BLOCKCHAIN=testnet

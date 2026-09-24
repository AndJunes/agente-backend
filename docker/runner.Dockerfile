# The per-project execution sandbox. Not Mirag itself — Mirag's own image installs nothing on
# purpose (see the root Dockerfile); this is the DIFFERENT image `DockerCodeRunner` launches one
# disposable container from per probe, to run a GENERATED project's tests.
#
# Because it is disposable and network-isolated at run time (`--network none`, set by
# `DockerCodeRunner`, not here), the curated bundle below is safe to bake in even though it is
# real, pinned, third-party code: nothing here is chosen by a model, and nothing at generation
# time can add to it. `docker/runner-requirements.txt` is the one place that changes if the
# curated set ever needs to grow.
FROM python:3.14-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PYTHONUTF8=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Unprivileged user, created before anything is copied in, same convention as the root
# Dockerfile's `mirag` user. `DockerCodeRunner` always runs the container as this exact uid
# (`--user 10001:10001`) regardless of who it runs as inside the image's own passwd file.
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin runner

# Installed as ROOT, into the system site-packages — no `--user`. That is deliberate: a
# `--user` install is what silently broke on the host this session (`%APPDATA%`-dependent, and
# stripped from a hardened child environment); root-owned system packages have no such
# per-user indirection to break, and `runner` cannot modify them even if it wanted to.
COPY docker/runner-requirements.txt /tmp/runner-requirements.txt
RUN pip install --no-cache-dir -r /tmp/runner-requirements.txt \
 && rm /tmp/runner-requirements.txt

USER runner
WORKDIR /workspace

# No CMD, no ENTRYPOINT: `DockerCodeRunner` always supplies the full argv
# (`python3 _probe_tests.py`, `pytest -q`, ...) at `docker run` time. This image is never
# started bare, and a missing command should fail obviously rather than fall into a default.

#!/usr/bin/env bash
#
# Builds and publishes both images from this machine, with the same rule the CI has: NOTHING
# is published unless the checks pass. That rule is half the value of a CI; publishing by
# hand without it is publishing blind.
#
#   scripts/publish.sh              check, build, publish and verify what was published
#   scripts/publish.sh --no-push    everything but the push (to try the script)
#
# The registry is not hard-coded:
#   MIRAG_IMAGEN=youruser/agente-backend            scripts/publish.sh   # Docker Hub
#   MIRAG_IMAGEN=ghcr.io/andjunes/agente-backend    scripts/publish.sh   # GHCR
# When nothing is said, it is derived from the user of your `docker login`, which avoids the
# silliest mistake of all: tagging four images with the wrong user and finding out at push.

set -euo pipefail

IMAGE="${MIRAG_IMAGEN:-}"
if [ -z "$IMAGE" ]; then
  # `docker info` only shows the Username when the credential lives in config.json. With a
  # credential helper (osxkeychain, pass...), which is the usual case, ask the helper.
  user="$(docker info 2>/dev/null | awk -F': ' '/^ Username:/ {print $2}' | tr -d ' ')"
  if [ -z "$user" ]; then
    helper="$(python3 -c "import json,pathlib;p=pathlib.Path.home()/'.docker'/'config.json';print(json.loads(p.read_text() or '{}').get('credsStore',''))" 2>/dev/null || true)"
    if [ -n "$helper" ] && command -v "docker-credential-$helper" >/dev/null; then
      user="$("docker-credential-$helper" list 2>/dev/null \
        | python3 -c "import json,sys;print(json.load(sys.stdin).get('https://index.docker.io/v1/',''))" 2>/dev/null || true)"
    fi
  fi
  [ -n "$user" ] || { printf "\n\033[31m✗ cannot tell which user to tag the image with.\033[0m\n" >&2
    printf "  Log in:        docker login\n" >&2
    printf "  Or say it:     MIRAG_IMAGEN=youruser/agente-backend scripts/publish.sh\n" >&2
    exit 1; }
  # Repository names are lowercase in every registry.
  IMAGE="$(printf '%s' "$user" | tr '[:upper:]' '[:lower:]')/agente-backend"
  printf "\033[2m  (image derived from the login: %s)\033[0m\n" "$IMAGE"
fi
# Only for the messages: a dot in the first part means a registry (ghcr.io...), else Docker Hub.
case "${IMAGE%%/*}" in
  *.*) REGISTRY="${IMAGE%%/*}" ;;
  *)   REGISTRY="Docker Hub" ;;
esac

PUSH=1
[ "${1:-}" = "--no-push" ] && PUSH=0

cd "$(dirname "$0")/.."
fail() { printf "\n\033[31m✗ %s\033[0m\n" "$1" >&2; exit 1; }
step() { printf "\n\033[1m── %s\033[0m\n" "$1"; }
ok()   { printf "\033[32m  ✓ %s\033[0m\n" "$1"; }

# ── 0 · what is published is exactly what is in git ─────────────────────────────
# Otherwise an image can carry changes that only exist on this disk, and its `sha` tag lies.
step "The image matches a commit"
[ -z "$(git status --porcelain)" ] || fail "there are uncommitted changes: the sha tag would lie"
SHA="$(git rev-parse --short HEAD)"
git fetch -q origin main 2>/dev/null || true
if [ -n "$(git rev-list origin/main..HEAD 2>/dev/null)" ]; then
  fail "commit $SHA is not on origin/main: nobody else could rebuild this image"
fi
ok "commit $SHA, clean and pushed"

# ── 1 · the demo contracts ──────────────────────────────────────────────────────
# They switch execution on (the demos exist to show the verification machinery) and call no
# model: cost 0.
step "The demo contracts"
PYTHONPATH=src MIRAG_OFFLINE=1 python3 -m mirag demo all >/dev/null 2>&1 || fail "a demo breaks its contract: not published"
ok "all of them, cost 0"

# ── 2 · no credential in what is versioned ──────────────────────────────────────
step "Credentials in the versioned tree"
git ls-files | grep -qxF ".env" && fail ".env is versioned"
# -l and not -n: -n prints the LINE, which would write the credential to this terminal.
if git grep -lIE "sk-or-v1-[A-Za-z0-9]{20,}|\bS[A-Z2-7]{55}\b" -- . ; then
  fail "something shaped like a credential in the files above"
fi
ok "clean"

# ── 3 · build both ──────────────────────────────────────────────────────────────
step "Building"
docker build -q --target base      -t "$IMAGE:$SHA"           -t "$IMAGE:latest"           . >/dev/null
docker build -q --target identidad -t "$IMAGE:$SHA-identidad" -t "$IMAGE:latest-identidad" . >/dev/null
ok "base $(docker images --format '{{.Size}}' "$IMAGE:latest" | head -1) · identidad $(docker images --format '{{.Size}}' "$IMAGE:latest-identidad" | head -1)"

# ── 4 · the built image starts, BEFORE publishing it ────────────────────────────
# Publishing something that does not start is worse than not publishing: it fails on the server.
step "Trying the image before publishing it"
docker rm -f publish-check >/dev/null 2>&1 || true
docker run -d --name publish-check -p 127.0.0.1:8099:8000 "$IMAGE:$SHA" >/dev/null
trap 'docker rm -f publish-check >/dev/null 2>&1 || true' EXIT
docker exec publish-check sh -c 'test ! -f /app/.env' || fail "the image carries a .env"
code=""
for _ in $(seq 1 30); do
  code="$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8099/api/v1/health || true)"
  [ "$code" = "200" ] && break
  sleep 1
done
[ "$code" = "200" ] || fail "health does not answer (HTTP $code)"
for path in /.env /pyproject.toml /src/mirag/core/settings.py /var/traces/pipeline.jsonl; do
  c="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:8099$path")"
  [ "$c" = "404" ] || fail "$path answered $c, it should be 404"
done
docker rm -f publish-check >/dev/null
ok "it starts, answers health and serves nothing it should not"

# ── 5 · publish ─────────────────────────────────────────────────────────────────
if [ "$PUSH" -eq 0 ]; then
  step "Not published (--no-push)"
  ok "everything above passed; nothing was uploaded"
  exit 0
fi

step "Publishing to $REGISTRY"
for tag in "$SHA" latest "$SHA-identidad" latest-identidad; do
  docker push -q "$IMAGE:$tag" >/dev/null || fail "pushing $tag failed (did you log in?)"
  ok "$IMAGE:$tag"
done

# ── 6 · and what was published is what was checked ─────────────────────────────
step "Checking what was published"
docker rmi "$IMAGE:$SHA" >/dev/null 2>&1 || true
docker pull -q "$IMAGE:$SHA" >/dev/null || fail "cannot pull what was just pushed"
ok "$IMAGE:$SHA pulls correctly"

printf "\n\033[1mPublished.\033[0m On the server:\n"
printf "  docker compose -f docker-compose.prod.yml pull\n"
printf "  docker compose -f docker-compose.prod.yml up -d\n"
printf "\nTo roll back, set MIRAG_TAG=%s in the server's .env\n" "$SHA"

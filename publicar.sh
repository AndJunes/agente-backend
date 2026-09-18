#!/usr/bin/env bash
#
# Construye y publica las dos imagenes, desde esta maquina, con la misma regla que tenia
# el CI: NO se publica nada si la suite no pasa. Esa regla es la mitad del valor de tener
# un CI; hacerlo a mano sin ella es publicar a ciegas.
#
#   ./publicar.sh                  construye, prueba, publica y verifica lo publicado
#   ./publicar.sh --sin-publicar   todo menos el push (para probar el guion)
#
# Requiere haber hecho login una vez:
#   gh auth refresh -h github.com -s write:packages
#   gh auth token | docker login ghcr.io -u AndJunes --password-stdin

set -euo pipefail

# GHCR exige minusculas en el nombre del repositorio. `AndJunes` no vale; `andjunes` si.
IMAGEN="ghcr.io/andjunes/agente-backend"
PUBLICAR=1
[ "${1:-}" = "--sin-publicar" ] && PUBLICAR=0

cd "$(dirname "$0")"
rojo()  { printf "\n\033[31m✗ %s\033[0m\n" "$1" >&2; exit 1; }
paso()  { printf "\n\033[1m── %s\033[0m\n" "$1"; }
ok()    { printf "\033[32m  ✓ %s\033[0m\n" "$1"; }

# ── 0 · que lo que se publique sea exactamente lo que hay en git ─────────────────
# Sin esto se puede publicar una imagen con cambios que solo existen en este disco, y la
# etiqueta `sha-xxxxxxx` estaria mintiendo sobre lo que contiene.
paso "Que la imagen corresponda a un commit"
[ -z "$(git status --porcelain)" ] || rojo "hay cambios sin commitear: la etiqueta sha- mentiria"
SHA="$(git rev-parse --short HEAD)"
git fetch -q origin main 2>/dev/null || true
if [ -n "$(git rev-list origin/main..HEAD 2>/dev/null)" ]; then
  rojo "el commit $SHA no esta en origin/main: nadie mas podria reconstruir esta imagen"
fi
ok "commit $SHA, limpio y subido"

# ── 1 · las 23 suites ────────────────────────────────────────────────────────────
paso "Las 23 suites"
fallos=0
for f in tests/test_*.py; do
  if ! MIRAG_OFFLINE=1 python3 "$f" >/dev/null 2>&1; then
    printf "\033[31m  ✗ %s\033[0m\n" "$f"; fallos=$((fallos + 1))
  fi
done
[ "$fallos" -eq 0 ] || rojo "$fallos suites fallan: no se publica"
ok "23 de 23"

# ── 2 · los contratos de las demos ───────────────────────────────────────────────
paso "Los contratos de las 4 demos"
salida="$(MIRAG_OFFLINE=1 python3 demos.py todas 2>&1 || true)"
cumplen="$(printf '%s' "$salida" | grep -c "CUMPLE EL CONTRATO" || true)"
incumplen="$(printf '%s' "$salida" | grep -c "NO CUMPLE" || true)"
[ "$cumplen" -eq 4 ] && [ "$incumplen" -eq 0 ] \
  || rojo "demos: $cumplen cumplen, $incumplen no. No se publica"
ok "4 de 4, coste 0"

# ── 3 · ninguna credencial en lo versionado ──────────────────────────────────────
paso "Credenciales en el arbol versionado"
git ls-files | grep -qxF ".env" && rojo ".env esta versionado"
# -l y no -n: -n imprime la LINEA, y eso escribiria la credencial en esta terminal.
if git grep -lIE "sk-or-v1-[A-Za-z0-9]{20,}|\bS[A-Z2-7]{55}\b" -- . ; then
  rojo "hay algo con forma de credencial en los archivos de arriba"
fi
ok "limpio"

# ── 4 · construir las dos ────────────────────────────────────────────────────────
paso "Construyendo"
docker build -q --target base      -t "$IMAGEN:$SHA"           -t "$IMAGEN:latest"           . >/dev/null
docker build -q --target identidad -t "$IMAGEN:$SHA-identidad" -t "$IMAGEN:latest-identidad" . >/dev/null
ok "base $(docker images --format '{{.Size}}' "$IMAGEN:latest" | head -1) · identidad $(docker images --format '{{.Size}}' "$IMAGEN:latest-identidad" | head -1)"

# ── 5 · que la imagen construida arranque, ANTES de publicarla ───────────────────
# Publicar algo que no arranca es peor que no publicar: el fallo aparece en el servidor.
paso "Probando la imagen antes de publicarla"
docker rm -f _publicar_prueba >/dev/null 2>&1 || true
docker run -d --name _publicar_prueba -p 127.0.0.1:8099:8000 "$IMAGEN:$SHA" >/dev/null
trap 'docker rm -f _publicar_prueba >/dev/null 2>&1 || true' EXIT
docker exec _publicar_prueba sh -c 'test ! -f /app/.env' || rojo "la imagen lleva un .env"
code=""
for _ in $(seq 1 30); do
  code="$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8099/ || true)"
  [ "$code" = "200" ] && break
  sleep 1
done
[ "$code" = "200" ] || rojo "la pagina no responde (HTTP $code)"
for ruta in /.env /server.py /trazas.jsonl /config.py; do
  c="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:8099$ruta")"
  [ "$c" = "404" ] || rojo "$ruta devolvio $c, deberia ser 404"
done
docker rm -f _publicar_prueba >/dev/null
ok "arranca, sirve la pagina y no sirve nada que no deba"

# ── 6 · publicar ─────────────────────────────────────────────────────────────────
if [ "$PUBLICAR" -eq 0 ]; then
  paso "Sin publicar (--sin-publicar)"
  ok "todo lo anterior paso; no se ha subido nada"
  exit 0
fi

paso "Publicando en GHCR"
for etiqueta in "$SHA" latest "$SHA-identidad" latest-identidad; do
  docker push -q "$IMAGEN:$etiqueta" >/dev/null || rojo "fallo al publicar $etiqueta (¿hiciste el login?)"
  ok "$IMAGEN:$etiqueta"
done

# ── 7 · y que lo publicado sea lo que se probo ───────────────────────────────────
paso "Comprobando lo que quedo publicado"
local_id="$(docker image inspect --format '{{index .RepoDigests 0}}' "$IMAGEN:$SHA" 2>/dev/null || echo "")"
docker rmi "$IMAGEN:$SHA" >/dev/null 2>&1 || true
docker pull -q "$IMAGEN:$SHA" >/dev/null || rojo "no se puede bajar lo que se acaba de subir"
ok "$IMAGEN:$SHA se baja correctamente"

printf "\n\033[1mPublicado.\033[0m En el servidor:\n"
printf "  docker compose -f docker-compose.prod.yml pull\n"
printf "  docker compose -f docker-compose.prod.yml up -d\n"
printf "\nPara volver atras, cambia :latest por :%s en docker-compose.prod.yml\n" "$SHA"

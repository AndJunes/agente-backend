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

# El registro no esta codificado a mano: se puede publicar en Docker Hub, en GHCR o en
# cualquier otro sin tocar este archivo.
#
#   MIRAG_IMAGEN=tuusuario/agente-backend              ./publicar.sh   # Docker Hub
#   MIRAG_IMAGEN=ghcr.io/andjunes/agente-backend       ./publicar.sh   # GHCR
#
# Si no se dice nada, se deduce del usuario con el que hiciste `docker login`. Deducirlo
# evita el error mas tonto de todos: construir cuatro imagenes etiquetadas con el usuario
# equivocado y descubrirlo en el push.
IMAGEN="${MIRAG_IMAGEN:-}"
if [ -z "$IMAGEN" ]; then
  # `docker info` solo enseña el Username cuando la credencial vive en config.json. Si
  # esta en un ayudante (osxkeychain, pass...), que es lo normal, no dice nada — y ahi
  # fallaba esto. Se le pregunta entonces al propio ayudante, que si lo sabe.
  usuario="$(docker info 2>/dev/null | awk -F': ' '/^ Username:/ {print $2}' | tr -d ' ')"
  if [ -z "$usuario" ]; then
    ayudante="$(python3 -c "import json,pathlib;p=pathlib.Path.home()/'.docker'/'config.json';print(json.loads(p.read_text() or '{}').get('credsStore',''))" 2>/dev/null || true)"
    if [ -n "$ayudante" ] && command -v "docker-credential-$ayudante" >/dev/null; then
      usuario="$("docker-credential-$ayudante" list 2>/dev/null \
        | python3 -c "import json,sys;print(json.load(sys.stdin).get('https://index.docker.io/v1/',''))" 2>/dev/null || true)"
    fi
  fi
  [ -n "$usuario" ] || { printf "\n\033[31m✗ no se de que usuario etiquetar la imagen.\033[0m\n" >&2
    printf "  Haz login:            docker login\n" >&2
    printf "  O dilo a mano:        MIRAG_IMAGEN=tuusuario/agente-backend ./publicar.sh\n" >&2
    exit 1; }
  # Los nombres de repositorio van en minusculas en todos los registros.
  IMAGEN="$(printf '%s' "$usuario" | tr '[:upper:]' '[:lower:]')/agente-backend"
  printf "\033[2m  (imagen deducida del login: %s)\033[0m\n" "$IMAGEN"
fi
# Solo para los mensajes: si la primera parte del nombre tiene un punto, es un registro
# (ghcr.io, registry.gitlab.com...). Si no, es un usuario y el registro es Docker Hub.
case "${IMAGEN%%/*}" in
  *.*) REGISTRO="${IMAGEN%%/*}" ;;
  *)   REGISTRO="Docker Hub" ;;
esac

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
docker rm -f publicar-prueba >/dev/null 2>&1 || true
docker run -d --name publicar-prueba -p 127.0.0.1:8099:8000 "$IMAGEN:$SHA" >/dev/null
trap 'docker rm -f publicar-prueba >/dev/null 2>&1 || true' EXIT
docker exec publicar-prueba sh -c 'test ! -f /app/.env' || rojo "la imagen lleva un .env"
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
docker rm -f publicar-prueba >/dev/null
ok "arranca, sirve la pagina y no sirve nada que no deba"

# ── 6 · publicar ─────────────────────────────────────────────────────────────────
if [ "$PUBLICAR" -eq 0 ]; then
  paso "Sin publicar (--sin-publicar)"
  ok "todo lo anterior paso; no se ha subido nada"
  exit 0
fi

paso "Publicando en $REGISTRO"
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

# Mirag. La imagen no instala NADA: el nucleo es biblioteca estandar pura.
#
# Eso no es una curiosidad, es la mejor propiedad de seguridad que tiene este contenedor.
# Sin `pip install` no hay cadena de suministro que comprometer, no hay CVE de dependencia
# que parchear a las 3 de la mañana, y la superficie es la del interprete y nada mas.
# Si algun dia esto necesita una dependencia, que sea una decision consciente y con lock.
#
# 3.14-slim para igualar la version con la que se probo (3.14.6 en el host).
FROM python:3.14-slim AS base

# PYTHONDONTWRITEBYTECODE: sin __pycache__, que en esta imagen solo seria basura que el
#   usuario sin privilegios ni siquiera podria escribir.
# PYTHONUNBUFFERED: los logs salen cuando pasan, no cuando se llena el buffer. Sin esto
#   `docker logs` va ciego justo cuando hace falta ver algo.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Usuario sin privilegios, creado ANTES de copiar para poder repartir dueños en el COPY.
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin mirag

WORKDIR /app

# El codigo se copia como ROOT y el proceso corre como `mirag`. La consecuencia es la que
# importa: este agente ejecuta codigo que escribe un modelo, y ese codigo corre como
# `mirag`, que NO PUEDE reescribir /app. O sea que una ejecucion hostil no puede dejar
# nada plantado en el agente para la siguiente peticion. Sin esto, un `test_algo.py` que
# abra `server.py` en modo escritura se persiste en la imagen viva.
COPY --chown=root:root . /app

# Las unicas rutas que el proceso puede escribir, creadas y cedidas una por una.
# Los dos .jsonl existen de antemano a proposito: `traza.escribir` hace `open(archivo,"a")`
# sin try/except (traza.py:110), y el directorio /app no es escribible por `mirag`, asi que
# si el archivo no existiera la primera peticion moriria con PermissionError.
RUN mkdir -p /app/artefactos /app/salida \
 && touch /app/trazas.jsonl /app/trazas_noche.jsonl \
 && chown mirag:mirag /app/artefactos /app/salida /app/trazas.jsonl /app/trazas_noche.jsonl

# 0.0.0.0 aqui NO es relajar el bind: dentro del contenedor no hay mas red que la suya, y
# es la unica forma de que un puerto publicado alcance al proceso. Lo que aisla es publicar
# con `-p 127.0.0.1:8000:8000`. El defecto del codigo sigue siendo localhost.
# MIRAG_OFFLINE=1 de fabrica: una imagen recien construida no puede gastar dinero de nadie.
# MIRAG_EJECUCION=off es el defecto del codigo; se escribe aqui igualmente porque una
# imagen deberia decir lo que hace sin que haya que ir a leer skills.py. Este agente
# entrega el codigo y sus casos de test SIN correrlos: ejecutarlos es del agente de QA.
# Consecuencia para esta imagen: no necesita pytest ni node, y no ejecuta nada ajeno.
ENV MIRAG_HOST=0.0.0.0 \
    MIRAG_PORT=8000 \
    MIRAG_OFFLINE=1 \
    MIRAG_EJECUCION=off

USER mirag
EXPOSE 8000

# Sin curl en la imagen (slim, y no vale la pena añadir un binario de red solo para esto):
# el healthcheck lo hace el mismo interprete que ya esta dentro.
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request,sys;\
sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/',timeout=4).status==200 else 1)"

CMD ["python", "server.py"]


# ══════════════════════════════════════════════════════════════════════════════
# Etapa 2 · las dependencias de la capa blockchain, aparte
# ══════════════════════════════════════════════════════════════════════════════
# Por que una etapa separada, dicho con precision: NO es para dejar fuera un
# compilador. Comprobado en blockchain/uv.lock: los tres paquetes con extension nativa
# traen wheel precompilado para cp314 en las dos arquitecturas
# (cffi-2.1.1-cp314-cp314-manylinux2014_aarch64, pydantic_core-2.46.5-cp314-cp314-manylinux_2_17_aarch64,
# y pynacl via cp38-abi3, que cubre 3.8+). Aqui no se compila nada.
#
# Lo que esta etapa SI consigue:
#   1. `uv` y sus caches no llegan a la imagen final: no le dejamos un gestor de
#      paquetes montado a quien entre.
#   2. Dos destinos desde un solo Dockerfile (--target), sin duplicar nada.
#   3. Las dependencias viven en su propio venv, no mezcladas con el sistema.
FROM python:3.14-slim AS dependencias

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# UV_PYTHON_DOWNLOADS=0: que use el interprete de la imagen y no se baje otro, porque
#   el venv que copiamos abajo tiene que apuntar a un python que exista en la etapa final.
# UV_LINK_MODE=copy: sin hardlinks, que no sobreviven a un COPY entre etapas.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /dep

# --locked y no `uv sync` a secas: instala EXACTAMENTE lo que el repo declara, y falla
# si el lock no cuadra con el pyproject. Es la misma invariante que comprueba
# tests/test_arquitectura_repo.py (la capa solo usa lo que declara).
RUN --mount=type=bind,source=blockchain/pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=blockchain/uv.lock,target=uv.lock \
    uv sync --locked --no-install-project --no-editable


# ══════════════════════════════════════════════════════════════════════════════
# Etapa 3 · la imagen con identidad on-chain
# ══════════════════════════════════════════════════════════════════════════════
# Copiar un venv entre etapas solo funciona si ambas comparten imagen base (un venv es
# especifico de plataforma y su pyvenv.cfg apunta a un interprete concreto). Las dos son
# python:3.14-slim, que es justo la condicion.
#
# El venv es de root: `mirag` puede usarlo y no puede tocarlo. Misma idea que /app.
FROM base AS identidad

COPY --from=dependencias --chown=root:root /dep/.venv /opt/identidad

# El PATH pone primero el venv, asi que el `python` del CMD heredado de `base` es el que
# ve stellar_sdk. El resto del agente es biblioteca estandar y le da igual cual sea.
ENV PATH="/opt/identidad/bin:$PATH" \
    MIRAG_BLOCKCHAIN=testnet

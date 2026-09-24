# Desplegar Mirag

## Lo que cambia en un servidor

Por defecto este agente **no ejecuta el código que genera** (`MIRAG_EXECUTION=off`). Lo
entrega junto con sus casos de test, y ejecutarlos será trabajo del agente de QA, en un
entorno pensado para eso. Lo que sí se comprueba sin ejecutar nada: estructura, sintaxis e
imports.

Eso **era el riesgo grande**: un servidor que ejecuta código escrito por un modelo a petición
de un desconocido es un servidor que hay que encerrar. Sin ejecución desaparecen la necesidad
de `pytest` y `node` en la imagen y la mayor parte de las razones para tener miedo. Y cuando la
ejecución está encendida (las demos, los benchmarks), el proceso hijo **no hereda ninguna
credencial**: solo `PATH`, `HOME`, el locale y las variables de temporales.

Lo que queda es un servidor que lee un corpus, llama a un modelo y devuelve texto y un ZIP.
Sigue habiendo cosas que cuidar —abajo están— pero son de otro tamaño.

## En tu máquina

```bash
docker compose up -d --build                      # la imagen limpia, sin dependencias
docker compose --profile identidad up -d --build  # + identidad on-chain (stellar-sdk)
```

La página queda en http://127.0.0.1:8000 y **solo** ahí: el puerto se publica como
`127.0.0.1:8000:8000`. Arranca con `MIRAG_OFFLINE=1`: demos guionizadas, cero llamadas al
modelo, cero coste.

## Publicar las imágenes

Hay dos caminos y hacen lo mismo. Hoy manda el primero, porque el CI está bloqueado por la
facturación de la cuenta de GitHub y sus jobs no arrancan.

**Desde tu máquina:**

```bash
scripts/publish.sh             # comprueba, construye, publica y verifica lo publicado
scripts/publish.sh --no-push   # todo menos el push
```

Aborta si el árbol está sucio, si el commit no está en `origin/main`, si una demo incumple su
contrato, si hay algo con forma de credencial en lo versionado, o si la imagen construida no
arranca o sirve algo que no debe. Esa regla —no se publica lo que no pasa— es la mitad del
valor de tener un CI, y se pierde entera si publicas a mano con `docker push`.

El registro no está codificado en el guion: si no dices nada, deduce el nombre de la imagen
del usuario con el que hiciste `docker login` (preguntándole al ayudante de credenciales si
hace falta). Hoy publica en **`andreajunes/agente-backend`**, con las etiquetas `latest`,
`<sha>` y sus variantes `-identidad`.

**Login en Docker Hub**, una sola vez. El token se crea en Docker Hub → avatar → *Account
settings* → *Personal access tokens*, con permiso **Write**. Un token y no la contraseña: se
revoca solo, sin tocar la cuenta.

```bash
docker login --username TUUSUARIO      # y pega el token donde pide la password
scripts/publish.sh
```

Si `docker login` dice que funcionó pero luego falla cualquier `docker pull`, mira el
`credsStore` de `~/.docker/config.json`: si apunta a un ayudante que no está instalado
—`desktop` sin Docker Desktop, por ejemplo— el login no guarda nada y deja una entrada vacía
que rompe hasta las descargas anónimas.

**O en GHCR:**

```bash
gh auth refresh -h github.com -s write:packages
gh auth token | docker login ghcr.io -u AndJunes --password-stdin
MIRAG_IMAGEN=ghcr.io/andjunes/agente-backend scripts/publish.sh
```

**Desde GitHub Actions**: `.github/workflows/ci.yml` hace lo mismo en cada push a `main`
(lint, contratos de las demos, credenciales, y publica en GHCR solo si todo pasa). En cuanto se
desbloquee la cuenta funciona solo y `scripts/publish.sh` pasa a ser el plan B.

## Qué servidor hace falta

Medido con la estructura anterior: la imagen ocupaba 154 MB (181 la de identidad). El compose
le pone un techo de 1 GB de RAM y 1,5 CPU al contenedor. El agente no tiene base de datos ni
guarda nada entre reinicios. Con CodeZard al lado en la misma máquina, **2 vCPU y 2 GB** van
cómodos; 4 GB si CodeZard crece.

Este agente **no publica ningún puerto**, así que el cortafuegos del servidor solo necesita el
22 (SSH) y, más adelante, el 80 y el 443 para CodeZard.

## En el servidor, paso a paso

El servidor **no necesita el código fuente, ni Python, ni construir nada**: solo Docker y dos
archivos.

**1 · Docker**, si no lo tiene:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER && newgrp docker
```

**2 · Los dos archivos**, sin clonar el repositorio:

```bash
mkdir -p ~/agente && cd ~/agente
RAW=https://raw.githubusercontent.com/AndJunes/agente-backend/main
curl -fsSL -O  "$RAW/docker-compose.prod.yml"
curl -fsSL -o .env "$RAW/.env.server.example"
```

`raw.githubusercontent.com` sirve desde una CDN que cachea unos minutos: justo después de
publicar un cambio te puede dar la versión anterior sin avisar. Para forzar la fresca, añade
`-H "Cache-Control: no-cache"` y `?$(date +%s)` a la URL.

**3 · El `.env`.** Genera el token, no lo inventes, y pega tu clave de OpenRouter:

```bash
# -i.bak y no -i a secas: el sed de macOS exige un sufijo y el de Linux lo acepta.
sed -i.bak "s|^MIRAG_TOKEN=.*|MIRAG_TOKEN=$(python3 -c 'import secrets;print(secrets.token_urlsafe(32))')|" .env && rm -f .env.bak
nano .env        # y pon OPENROUTER_API_KEY
chmod 600 .env   # que solo lo lea tu usuario
```

**4 · Levantarlo:**

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml logs -f    # Ctrl-C para salir
```

**5 · Comprobar que funciona.** Lo que despista: **no hay puerto publicado**, así que
`curl localhost:8000` desde el servidor NO responde, y eso es lo correcto. Se comprueba desde
dentro de la red, que es donde vive CodeZard:

```bash
docker run --rm --network codezard_interna curlimages/curl \
  -s -o /dev/null -w "%{http_code}\n" http://mirag:8000/api/v1/health       # 200

docker run --rm --network codezard_interna curlimages/curl \
  -s -o /dev/null -w "%{http_code}\n" -X POST http://mirag:8000/api/v1/chat \
  -H "Content-Type: application/json" -d '{"question":"hola"}'             # 401, sin token
```

**6 · CodeZard** se une a la misma red y le habla por su nombre, `http://mirag:8000`, mandando
el `MIRAG_TOKEN` en la cabecera `X-Mirag-Token`. Si tiene su propio compose:

```yaml
networks:
  interna:
    external: true
    name: codezard_interna
```

El navegador nunca habla con el agente: habla con CodeZard, y el servidor de CodeZard reenvía.
El contrato está en [api.md](api.md).

## Actualizar y volver atrás

```bash
docker compose -f docker-compose.prod.yml pull && docker compose -f docker-compose.prod.yml up -d
```

Para volver a una versión anterior, `MIRAG_TAG=<sha>` en el `.env` y repetir. El sha lo imprime
`scripts/publish.sh` al publicar.

## Las dos imágenes

Un solo `Dockerfile`, tres etapas y dos destinos:

```bash
docker build --target base      -t mirag:base      .   # cero dependencias
docker build --target identidad -t mirag:identidad .   # + stellar-sdk
```

La etapa intermedia instala `stellar-sdk` (fijado a 16.1.0) en un venv y la final **copia el
venv**: `pip` y sus cachés no llegan a la imagen.

## El token

Sin `MIRAG_TOKEN` el servidor queda abierto a quien alcance el puerto, y lo dice al arrancar.
No hay token por defecto a propósito: un secreto de fábrica lo conoce todo el mundo. El
compose de producción se niega a arrancar sin él.

## La clave del modelo

Nunca en el `Dockerfile`, nunca en el compose, nunca en la imagen: lo que metes en una capa se
queda ahí aunque un paso posterior lo borre. Va en el `.env` de al lado, que está en
`.gitignore` y en `.dockerignore`. La imagen solo copia `src/`, y sin `pyproject.toml` no se
comporta como un checkout: nunca lee un `.env` del disco.

El compose **no usa `env_file`**: `env_file` inyecta el `.env` entero. Con `${VAR}` entra solo
lo que se nombra, y así `STELLAR_SECRET_KEY` no llega a ningún contenedor.

Para la prueba de concepto, `MIRAG_MODEL=openrouter/free` deja el gasto en $0 y el panel de
coste lo dice (`GRATIS`). Límites: 20 peticiones por minuto y 50 al día (1.000 si alguna vez
compraste 10 $ de crédito).

Los nombres de antes (`MIRAG_MODELO`, `LIMITE_USD`, `MIRAG_EJECUCION`) se siguen leyendo cuando
el nombre nuevo no está, para que un `.env` antiguo no cambie en silencio de modelo ni de tope.

## La identidad on-chain, sin la semilla

Para **mostrar** la identidad solo se hacen lecturas sin firmar: bastan `STELLAR_PUBLIC_KEY` y
`STELLAR_AGENT_ID`, y **la semilla no entra en el contenedor**. Firmar solo hace falta para
*registrar*, que es una operación manual, local y de una vez
(`scripts/blockchain_agent_demo.py`). Ver [blockchain.md](blockchain.md).

## Qué contiene el contenedor, y por qué

| | |
|---|---|
| **imagen base sin dependencias** | el núcleo es biblioteca estándar: no hay cadena de suministro que comprometer |
| **usuario `mirag` (uid 10001)** | nada corre como root |
| **`/app/src` es de root** | el proceso no puede reescribir su propio código |
| **una sola ruta escribible** | `/app/var` (`MIRAG_DATA_DIR`): salidas, artefactos, trazas y cachés |
| **`/tmp` en tmpfs** | vive en RAM y muere con el contenedor |
| **`cap_drop: ALL`, `no-new-privileges`** | ni una capability, ningún setuid escala |
| **`pids_limit`, `mem_limit`, `cpus`** | techos de CPU, memoria y procesos |

## Lo que sigue sin estar resuelto

**No hay límite de peticiones.** `MIRAG_BUDGET_USD` es por petición, no por hora. Si CodeZard
queda expuesto, el rate limiting es cosa de CodeZard o del proxy de delante. Lo que sí cierra el
peor caso, y cuesta dos minutos, es ponerle un **límite de crédito a la clave en el panel de
OpenRouter**.

**Los artefactos caducan**: una hora, 20 a la vez, 64 MB, y se pierden al reiniciar. CodeZard
tiene que bajarse el ZIP en cuanto lo recibe ([api.md](api.md)).

**El token es un secreto compartido, no autenticación de usuarios.** Quien lo tenga puede
pedirlo todo. Si algún día hay varios consumidores con permisos distintos, se queda corto.

**Cuando llegue el agente de QA volverá a haber ejecución**, y con ella el problema grande,
pero ya en su propio servicio, que es donde se puede encerrar de verdad. `MIRAG_EXECUTION` es
la costura por la que entrará.

Parte de esa costura ya existe, solo para el despliegue **sin contenedor**:
`MIRAG_EXECUTION_BACKEND=docker` (ver [configuration.md](configuration.md)) hace que
`mirag serve` — corriendo directo en un host, como en desarrollo local — lance cada prueba
dentro de su propio contenedor descartable, aislado de red y con techo de recursos, en vez de
un subproceso plano. Necesita que ese host tenga Docker alcanzable, y es opcional, apagado por
defecto.

Eso deliberadamente **no** está conectado al contenedor endurecido de arriba. Esa imagen ya
corre con `cap_drop: ALL` y no publica puertos; darle acceso al socket de Docker para que
lance contenedores hermanos le daría acceso equivalente a root sobre el host que la corra,
deshaciendo cada fila de la tabla. El "servicio propio" que ya pedía esta sección sigue siendo
la forma correcta para ese caso — un servicio aparte, hecho a propósito, con su propio acceso
contenido a Docker, alcanzado por red en vez de a través del socket de este contenedor.

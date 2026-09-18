# Desplegar Mirag

## Qué cambió, y por qué esto es mucho más fácil que antes

Este agente **ya no ejecuta el código que genera**. Lo entrega junto con sus casos de test,
y ejecutarlos será trabajo del agente de QA, en un entorno pensado para eso
(`MIRAG_EJECUCION`, apagado por defecto).

No es una resta cualquiera: **era el riesgo grande**. Un servidor que ejecuta código
escrito por un modelo a petición de un desconocido es un servidor que hay que encerrar.
Sin eso desaparecen de golpe la fuga por la red del proceso hijo, la necesidad de `pytest`
y `node` dentro de la imagen, y la mayor parte de las razones para tener miedo.

Lo que queda es un servidor que lee un corpus, llama a un modelo y devuelve texto y un
ZIP. Sigue habiendo cosas que cuidar —abajo están— pero son de otro tamaño.

## En tu maquina

```bash
docker compose up -d --build                      # la imagen limpia, sin dependencias
docker compose --profile identidad up -d --build  # + identidad on-chain (stellar-sdk)
```

## Publicar las imagenes

Hay dos caminos y hacen lo mismo. El que manda hoy es el segundo, porque el CI esta
bloqueado por la facturacion de la cuenta de GitHub y sus jobs no arrancan.

**Desde tu maquina** (el que se usa hoy):

```bash
./publicar.sh                  # prueba, construye, publica y verifica lo publicado
./publicar.sh --sin-publicar   # todo menos el push
```

Aborta si el arbol esta sucio, si el commit no esta en `origin/main`, si falla una de las
23 suites o uno de los 4 contratos, si hay algo con forma de credencial en lo versionado,
o si la imagen construida no arranca. Esa regla —no se publica lo que no pasa— es la mitad
del valor de tener un CI, y se pierde entera si publicas a mano con `docker push`.

El registro no esta codificado en el guion: si no dices nada, deduce el nombre del usuario
con el que hiciste `docker login`.

**Login en Docker Hub**, una sola vez. El token se crea en Docker Hub → avatar →
*Account settings* → *Personal access tokens* → *Generate new token*, con permiso
**Write** (Read no basta para publicar). Un token y no la contraseña: se puede revocar
solo, sin tocar la cuenta.

```bash
docker login --username TUUSUARIO      # y pega el token donde pide la password
./publicar.sh
```

El guion deduce el nombre de la imagen del usuario con el que hiciste login, preguntandole
al ayudante de credenciales. Hoy publica en **`andreajunes/agente-backend`**, publica, con
las etiquetas `latest`, `<sha>` y sus variantes `-identidad`.

Si `docker login` reporta exito pero luego falla cualquier `docker pull`, mira el
`credsStore` de `~/.docker/config.json`: si apunta a un ayudante que no esta instalado
—`desktop` sin Docker Desktop, por ejemplo— el login no guarda nada Y deja una entrada
vacia que rompe hasta las descargas anonimas. En macOS el que siempre esta es
`osxkeychain`.

**O en GHCR**, si algun dia se desbloquea la cuenta de GitHub:

```bash
gh auth refresh -h github.com -s write:packages
gh auth token | docker login ghcr.io -u AndJunes --password-stdin
MIRAG_IMAGEN=ghcr.io/andjunes/agente-backend ./publicar.sh
```

Docker Hub gratis da **repositorios publicos ilimitados** y 1 privado. Las descargas estan
limitadas a 100 cada 6 horas sin autenticar y 200 autenticado — de sobra para un servidor
que solo descarga al desplegar.

**Desde GitHub Actions**: `.github/workflows/ci.yml` hace exactamente lo mismo en cada
push a `main`. Esta escrito y sin estrenar; en cuanto se desbloquee la cuenta, funciona
solo y `publicar.sh` pasa a ser el plan B.

## En el servidor, paso a paso

El servidor **no necesita el codigo fuente, ni Python, ni construir nada**: solo Docker y
dos archivos.

**1 · Docker**, si no lo tiene:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER && newgrp docker      # para no escribir sudo cada vez
```

**2 · Los dos archivos.** No hace falta clonar el repositorio:

```bash
mkdir -p ~/agente && cd ~/agente
RAW=https://raw.githubusercontent.com/AndJunes/agente-backend/main
curl -fsSL -O  "$RAW/docker-compose.prod.yml"
curl -fsSL -o .env "$RAW/.env.servidor.example"
```

Si acabas de publicar un cambio en esos archivos, `raw.githubusercontent.com` sirve desde
una CDN que cachea unos minutos y te va a dar la version anterior sin avisar. El sintoma
es desconcertante: el despliegue se comporta como el codigo de ayer. Para forzar la fresca,
`curl -H "Cache-Control: no-cache" -o docker-compose.prod.yml "$RAW/docker-compose.prod.yml?$(date +%s)"`.

**3 · El `.env`.** Genera el token, no lo inventes; y pega tu clave de OpenRouter:

```bash
# -i.bak y no -i a secas: el `sed` de macOS (BSD) exige un sufijo y el de Linux (GNU) lo
# acepta. `sed -i` sin sufijo funciona en el VPS y falla en un Mac con un error que no
# explica nada ("invalid command code .").
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

**5 · Comprobar que funciona.** Aqui viene lo que despista: **no hay puerto publicado**, asi
que `curl localhost:8000` desde el servidor NO responde, y eso es exactamente lo correcto.
Se comprueba desde dentro de la red, que es donde vive CodeZard:

```bash
docker run --rm --network codezard_interna curlimages/curl \
  -s -o /dev/null -w "%{http_code}\n" http://mirag:8000/          # 200

docker run --rm --network codezard_interna curlimages/curl \
  -s -o /dev/null -w "%{http_code}\n" -X POST http://mirag:8000/chat \
  -H "Content-Type: application/json" -d '{"pregunta":"hola"}'     # 401, sin token
```

**6 · CodeZard** se une a la misma red y ya le habla por su nombre, `http://mirag:8000`,
mandando el `MIRAG_TOKEN` en la cabecera `X-Mirag-Token`.

## Actualizar y volver atras

```bash
docker compose -f docker-compose.prod.yml pull && docker compose -f docker-compose.prod.yml up -d
```

Para volver a una version anterior, `MIRAG_TAG=<sha>` en el `.env` y repetir. El sha lo
imprime `./publicar.sh` al publicar.

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

Ese es el despliegue entero. Volver atras es cambiar `:latest` por el `:sha-xxxxxxx` de un
commit anterior y repetir las dos lineas — el CI publica esa etiqueta en cada push.

**Y no publica ningun puerto.** No es un olvido: CodeZard alcanza al agente por el nombre
del servicio dentro de la red de Docker (`http://mirag:8000`), y ese puerto no existe
fuera de esa red — ni en internet, ni en las interfaces del host, ni para otro proceso de
la maquina. No hay nada que cortafuegar porque no hay nada abierto. Para mirarlo tu, un
tunel SSH puntual.

CodeZard se une a la misma red. Si tiene su propio `compose`:

```yaml
networks:
  interna:
    external: true
    name: codezard_interna
```

La página queda en http://127.0.0.1:8000 — y **solo** ahí: el puerto se publica como
`127.0.0.1:8000:8000`, así que existe para la máquina y para nadie más.

Arranca con `MIRAG_OFFLINE=1`: tres demos guionizadas, cero llamadas al modelo, cero
coste. Para respuestas reales hace falta una clave.

## Las dos imágenes

Un solo `Dockerfile`, tres etapas y dos destinos:

```bash
docker build --target base      -t mirag:base      .   # 154 MB · cero dependencias
docker build --target identidad -t mirag:identidad .   # 181 MB · + stellar-sdk
```

La etapa intermedia instala las dependencias con `uv sync --locked` y la final **copia el
venv**; `uv` y sus cachés no llegan a la imagen. Conviene decir con precisión qué compra
eso y qué no: **no** evita cargar con un compilador, porque no hace falta ninguno —las
tres dependencias con extensión nativa traen wheel precompilado para `cp314` en las dos
arquitecturas, comprobado en `blockchain/uv.lock`. Lo que compra es que la imagen final no
lleve un gestor de paquetes montado, y poder tener las dos variantes sin duplicar nada.

## Cómo llegar a él desde fuera

El puerto está atado a localhost a propósito. Para usarlo tú:

```bash
ssh -N -L 8000:127.0.0.1:8000 usuario@tu-servidor
```

**Para que lo llame CodeZard**, lo natural es la red interna de Docker: los dos
contenedores en la misma red y CodeZard pidiendo a `http://mirag:8000`, sin publicar nada
al exterior. El navegador nunca habla con el agente; habla con CodeZard, y el servidor de
CodeZard reenvía. Ver [API.md](API.md).

Lo que no hay que hacer es publicar `- "8000:8000"` a secas en un VPS con una clave de
OpenRouter cargada.

## El token

```yaml
MIRAG_TOKEN: "${MIRAG_TOKEN:-}"     # y CodeZard lo manda en X-Mirag-Token
```

Sin él el servidor queda abierto a quien alcance el puerto, y lo dice al arrancar. No hay
token por defecto a propósito: un secreto de fábrica lo conoce todo el mundo.

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## La clave del modelo

Nunca en el `Dockerfile`, nunca en el `docker-compose.yml`, nunca en la imagen: lo que
metes en una capa se queda ahí aunque un paso posterior lo borre. Va en el `.env` de al
lado, que ya está en `.gitignore` y en `.dockerignore`.

El compose **no usa `env_file`**, y el motivo es concreto: `env_file` inyecta el `.env`
entero. Con `${VAR}` entra solo lo que se nombra, y así `STELLAR_SECRET_KEY` no llega a
ningún contenedor.

Para la prueba de concepto, `MIRAG_MODELO=openrouter/free` deja el gasto en $0. Límites:
20 peticiones por minuto y 50 al día (1.000 si alguna vez compraste 10 $ de crédito).

## La identidad on-chain, sin la semilla

Para **mostrar** la identidad solo se hacen lecturas sin firmar. Bastan
`STELLAR_PUBLIC_KEY` y `STELLAR_AGENT_ID`: **la semilla no entra en el contenedor**, y
está comprobado que la ruta funciona sin ella. Firmar solo hace falta para *registrar*,
que es una operación manual, local y de una vez (`demos/blockchain_agent_demo.py
--registrar`).

## Qué contiene el contenedor, y por qué

| | |
|---|---|
| **imagen base sin dependencias** | el núcleo es biblioteca estándar: no hay cadena de suministro que comprometer |
| **usuario `mirag` (uid 10001)** | nada corre como root |
| **`/app` es de root** | el proceso no puede reescribir su propio código |
| **solo 4 rutas escribibles** | `artefactos/`, `salida/` y los dos `.jsonl` de trazas |
| **`/tmp` en tmpfs** | vive en RAM y muere con el contenedor |
| **`cap_drop: ALL`, `no-new-privileges`** | ni una capability, ningún setuid escala |
| **`pids_limit`, `mem_limit`, `cpus`** | techos de CPU, memoria y procesos |

Comprobado sobre la imagen: no lleva `.env`, corre como uid 10001,
`echo >> /app/server.py` da *Permission denied*, y `--target base` no tiene `stellar_sdk`
mientras `--target identidad` sirve la identidad verificada on-chain sin la semilla.

## Lo que sigue sin estar resuelto

**No hay límite de peticiones.** `LIMITE_USD` es por petición, no por hora. Si CodeZard
queda expuesto, el rate limiting es cosa de CodeZard o del proxy de delante. Lo que sí
cierra el peor caso, y cuesta dos minutos, es ponerle un **límite de crédito a la clave en
el panel de OpenRouter**.

**Los artefactos caducan**: una hora, 20 a la vez, 64 MB, y se pierden al reiniciar.
CodeZard tiene que bajarse el ZIP en cuanto lo recibe. Está en [API.md](API.md).

**El token es un secreto compartido, no autenticación de usuarios.** Quien lo tenga puede
pedirlo todo. Si algún día hay varios consumidores con permisos distintos, esto se queda
corto.

**Cuando llegue el agente de QA volverá a haber ejecución**, y con ella volverá el
problema grande — pero ya en su propio servicio, que es donde se puede encerrar de verdad.
`MIRAG_EJECUCION` es la costura por la que entrará.

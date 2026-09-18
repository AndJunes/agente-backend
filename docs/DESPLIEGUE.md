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

## Arrancarlo

```bash
docker compose up -d --build                      # la imagen limpia, sin dependencias
docker compose --profile identidad up -d --build  # + identidad on-chain (stellar-sdk)
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

# Desplegar Mirag

## Lo primero, porque cambia todo lo demás

Mirag **ejecuta código que escribe un modelo** y **no tiene autenticación**. Las dos cosas
a la vez. Quien pueda abrir la página puede hacer que tu servidor ejecute lo que el modelo
produzca, y gastar tu saldo de OpenRouter haciéndolo.

Eso no es un defecto que se arregle con un `Dockerfile`: es lo que hace la herramienta. El
contenedor no lo elimina, lo **acota**. La pregunta útil no es «¿es seguro?» sino «¿qué se
lleva por delante cuando algo salga mal?». Todo lo de aquí abajo responde a eso.

## Arrancarlo

```bash
docker compose up -d --build
```

La página queda en http://127.0.0.1:8000 — y **solo** ahí: el puerto se publica como
`127.0.0.1:8000:8000`, así que existe para la máquina y para nadie más.

Arranca con `MIRAG_OFFLINE=1`, o sea con el candado puesto: tres demos guionizadas, cero
llamadas al modelo, cero coste. Para respuestas reales hace falta una clave (más abajo).

```bash
docker compose logs -f      # ver qué hace
docker compose down         # pararlo
```

## Cómo llegar a él desde fuera

El puerto está atado a localhost a propósito. Para usarlo desde tu portátil:

```bash
ssh -N -L 8000:127.0.0.1:8000 usuario@tu-servidor
```

Y abres http://127.0.0.1:8000 en tu máquina. El tráfico va cifrado por SSH y el servidor
no expone nada nuevo a internet. [Tailscale](https://tailscale.com) hace lo mismo sin
tocar la configuración de SSH.

**Si necesitas que lo use alguien más**, no quites el `127.0.0.1` del `ports`. Pon delante
un proxy que autentique — Cloudflare Access, oauth2-proxy, o Caddy con `basic_auth` — y
que hable con el contenedor por la red interna de Docker. La regla: *nada llega al agente
sin haber pasado antes por algo que sepa quién es*.

Lo que no hay que hacer nunca es publicar `- "8000:8000"` a secas en un VPS con una clave
de OpenRouter cargada. Eso es tu tarjeta pagando las peticiones de quien encuentre la IP,
y los escáneres de puertos la encuentran en horas.

## La clave

Nunca en el `Dockerfile`, nunca en el `docker-compose.yml`, nunca en la imagen. Una imagen
se publica, y lo que metes en una capa se queda en esa capa aunque un paso posterior lo
borre.

Va en un `.env` junto al compose, que ya está en `.gitignore` y en `.dockerignore`:

```bash
OPENROUTER_API_KEY=sk-or-v1-...
```

y se enciende el modo real:

```yaml
environment:
  MIRAG_OFFLINE: "0"
  LIMITE_USD: "0.20"      # tope POR petición; el agente corta antes de pasarse
```

En un orquestador de verdad (Swarm, Kubernetes, Fly, Render) usa su almacén de secretos en
vez del `.env`, y comprueba que no acabe en los logs de despliegue.

## Qué contiene el contenedor, y por qué cada cosa

| | |
|---|---|
| **imagen sin dependencias** | el núcleo es biblioteca estándar: no hay `pip install`, así que no hay cadena de suministro que comprometer ni CVE de terceros que parchear |
| **usuario `mirag` (uid 10001)** | nada corre como root |
| **`/app` es de root** | el proceso **no puede reescribir su propio código**: una ejecución hostil no deja nada plantado para la siguiente petición |
| **solo 4 rutas escribibles** | `artefactos/`, `salida/` y los dos `.jsonl` de trazas. Nada más |
| **`/tmp` en tmpfs, `noexec`** | ahí se escribe y ejecuta el código generado: vive en RAM, muere con el contenedor, y no se pueden lanzar binarios desde ahí |
| **`cap_drop: ALL`** | ni una capability del kernel |
| **`no-new-privileges`** | ningún setuid escala desde dentro |
| **`pids_limit`, `mem_limit`, `cpus`** | un `while True: fork()` o un minero en el código generado muere contra el techo, no contra la máquina |

Comprobado, no prometido: el usuario no es root, `echo >> /app/server.py` da *Permission
denied*, las trazas y `artefactos/` sí se escriben, `noexec` **no** rompe la ejecución de
los tests generados (ahí quien ejecuta es el intérprete, que vive en `/usr/local/bin`), y
el código generado ya no ve ninguna credencial.

## Lo que sigue sin estar resuelto

Decirlo es parte del despliegue.

**El código generado tiene red.** Ya no puede leer tus claves —el entorno se limpia antes
de ejecutarlo, y hay un test que lo comprueba—, pero sí puede abrir conexiones: escanear
la red interna del servidor, o usar tu máquina de puente. Si el servidor está en una VPC
con cosas interesantes al lado, ponle al contenedor una red sin salida salvo a
`openrouter.ai`. Con `MIRAG_OFFLINE=1` no necesita salida ninguna.

**No hay límite de peticiones.** El tope de `LIMITE_USD` es por petición, no por hora. Mil
peticiones son mil veces ese tope. Si lo abres a alguien más, el rate limiting es cosa del
proxy de delante.

**`pytest` y `node` no están en la imagen.** La lista blanca de intérpretes se filtra por
lo que existe (`skills.py:26`), así que dentro solo hay `python` y `python3`. Un proyecto
generado cuyos tests se lancen con `pytest` se queda en `NO EJECUTADO` en vez de fallar
a medias. Si lo necesitas, instálalo en el Dockerfile a sabiendas de que dejas de tener
una imagen sin dependencias.

**La capa `blockchain/` no funciona en esta imagen.** Declara `stellar-sdk` y aquí no se
instala nada. `server.py` la importa de forma perezosa, así que el servidor arranca igual
y solo falla esa ruta. Si la quieres, es otra imagen con su `uv sync`.

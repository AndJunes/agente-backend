# La API de agente-backend

Para quien construye **CodeZard** y necesita pedirle código a este agente.

## Cómo se habla con él

**De servidor a servidor.** El navegador habla con CodeZard; el servidor de CodeZard habla
con el agente. No es una preferencia de estilo:

- no hace falta CORS, y no hay ni una cabecera CORS en este servidor
- el agente no se expone a internet: se publica en `127.0.0.1` y se alcanza por la red
  interna de Docker o por un túnel
- el token compartido no viaja nunca al navegador

Si algún día tiene que llamarlo el navegador directamente, hay que añadir CORS, un
`do_OPTIONS` y un token que sea seguro poner en el cliente. Hoy nada de eso existe.

## Autenticación

Una cabecera, en todas las peticiones a `/chat` y `/descarga`:

```
X-Mirag-Token: <el valor de MIRAG_TOKEN>
```

Sin `MIRAG_TOKEN` en el servidor, queda abierto —el modo local de siempre— y lo avisa al
arrancar. Con token puesto, cualquier otra cosa es **401**. El 401 no dice si falta la
cabecera o si el valor está mal.

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"   # para generarlo
```

## `POST /chat`

```http
POST /chat
Content-Type: application/json
X-Mirag-Token: ...

{"pregunta": "Creá una API REST de libros con CRUD completo.", "modo": "pipeline"}
```

`modo` es `"pipeline"` (por defecto) o `"arquitecto"` (más lento, ~10 min).
`POST /` es un alias exacto de `POST /chat`.

**Respuestas de error**: `401` sin token, `400` si el cuerpo no es JSON o no trae una
`pregunta` que sea texto no vacío, `404` en cualquier otra ruta.

### La respuesta es un stream

`Content-Type: text/event-stream`. Cada evento es una línea `data: {json}` seguida de una
línea en blanco. **No hay campo `event:`**: cada evento se distingue por su clave `tipo`.

```js
const r = await fetch(`${AGENTE}/chat`, {
  method: "POST",
  headers: { "Content-Type": "application/json", "X-Mirag-Token": TOKEN },
  body: JSON.stringify({ pregunta, modo: "pipeline" }),
});

const lector = r.body.getReader();
const dec = new TextDecoder();
let buffer = "";
for (;;) {
  const { done, value } = await lector.read();
  if (done) break;
  buffer += dec.decode(value, { stream: true });
  const trozos = buffer.split("\n\n");
  buffer = trozos.pop();                    // el último puede venir a medias
  for (const trozo of trozos) {
    if (!trozo.startsWith("data: ")) continue;
    const ev = JSON.parse(trozo.slice(6));
    if (ev.tipo === "fin") { /* ver abajo */ }
    else if (ev.tipo === "paso") { /* progreso */ }
  }
}
```

Para reenviarlo al navegador desde CodeZard, pasa `r.body` tal cual con
`Content-Type: text/event-stream`: no hace falta reconstruir nada.

| `tipo` | cuándo | campos |
|---|---|---|
| `paso` | una etapa del pipeline | `nombre`, `estado` (`ejecutado`/`omitido`/`fallback`/`error`), `resumen`, `ms`, `fuente`, `detalle` |
| `fase` | modo arquitecto | `texto` |
| `pensamiento` | modo arquitecto | `texto` |
| `skill` | una tool que usó el modelo | `nombre`, `args`, `resultado` |
| `gasto` | solo en modo arquitecto | `texto` |
| `fin` | el último, siempre | ver abajo |

### El evento `fin`

```jsonc
{
  "tipo": "fin",
  "respuesta": "…markdown…",
  "modo": "pipeline",
  "entregable": null,          // o {archivos:{ruta:texto}, comando, carpeta, estado, simulado}
  "gasto": "1 llamadas · 12,257 tokens · $0.0000",
  "afirmacion": "sin_afirmacion",   // respaldada | sin_respaldo | refutada | no_ejecutado | sin_afirmacion
  "evidencia": { "claim": [], "observed": null, "verified": [], "simulated": [],
                 "not_verified": [], "sin_cubrir": [] },
  "linea_tiempo": [ { "t": 0.09, "ms": 61.3, "etapa": "recuperacion", "estado": "ejecutado",
                      "fuente": "corpus", "resumen": "…" } ],
  "coste": { "simulado": false, "gratuito": true, "modelo": "openrouter/free",
             "texto": "GRATIS · $0 · openrouter/free", "llamadas": 1, "tokens": 12257 },
  "proyecto": null             // o el objeto de abajo
}
```

Si la pregunta era sobre el propio Mirag, hay un atajo de dos eventos y el `fin` **no
trae** `entregable`, `evidencia`, `linea_tiempo`, `coste` ni `proyecto`: las claves están
ausentes, no en `null`. Compruébalas antes de leerlas.

### `proyecto` — lo que hay que pintar

```jsonc
{
  "id": "ccc5813aefa0d8c7c064aab5",
  "nombre": "libros-api",
  "estado": "GENERADO",
  "simulado": true,
  "por_que": "hay archivos y nada se ha llegado a ejecutar",
  "archivos": [
    { "ruta": "app/libros/servicio.py", "bytes": 1841, "lineas": 62,
      "sha256": "…", "texto": "…el código, entero…" }
  ],
  "totales": { "archivos": 14, "directorios": 5, "lineas": 430 },
  "fases": [ { "nombre": "sintaxis", "estado": "ok", "detalle": null } ],
  "zip": { "nombre": "libros-api.zip", "bytes": 9211, "sha256": "…" },
  "integridad": { "ok": true, "motivo": "", "comprobaciones": [] },
  "descarga": "/descarga?id=ccc5813aefa0d8c7c064aab5"
}
```

`texto` es el contenido completo de cada archivo: con eso se pinta sin descomprimir nada.
Puede venir en `null`, y entonces hay un `sin_texto` que dice por qué — el proyecto pasa
de 2 MB en total, o el archivo contiene algo con forma de credencial. Un archivo vacío
tiene `texto: ""`, que no es lo mismo que `null`.

**`descarga` es una URL relativa y hay que usarla tal cual**, prefijando el origen del
agente. No la compongas a mano a partir del `id`: si algún día cambia el formato, quien
la componía se rompe en silencio.

## `GET /descarga?id=<24 hex>`

Devuelve el ZIP. Cabeceras: `application/zip`, `Content-Disposition` con el nombre, y
**`X-Mirag-Sha256`** con el sha256 del contenido, que debería coincidir con `zip.sha256`
del JSON — compruébalo.

| código | qué pasó |
|---|---|
| 400 | el `id` no tiene la forma de 24 hex |
| 401 | falta el token |
| 409 | el paquete no pasó el control de integridad; no se entrega |
| 410 | el artefacto ya no existe (ver abajo) |

### Los artefactos caducan, y esto importa

Viven en memoria, en el proceso. Se pierden:

- a la **hora** de creados
- cuando hay más de **20** a la vez (se van los más viejos)
- cuando pasan de **64 MB** en total
- **al reiniciar el agente**, todos

**Baja el ZIP en cuanto recibas el `fin` y guárdalo tú.** Guardar el `id` para más tarde
es guardar algo que va a dar 410.

## `GET /api/blockchain/agent`

La identidad on-chain del agente (Stellar testnet, ERC-8004). Devuelve `disponible: false`
con un `motivo` si la capa está apagada o falta el SDK — el resto del agente funciona
igual. Con la imagen `--target identidad`:

```jsonc
{ "disponible": true, "motivo": "",
  "identidad": { "agent_id": 26, "registro": "CDE3K4CO…", "red": "testnet",
                 "wallet_en_cadena": "GDKCQKGN…", "uri": "data:application/json;base64,…",
                 "verificada": true },
  "wallet": { "direccion": "GDKCQKGN…", "saldo": "10013.4216711", "existe": true },
  "ultimo_pago": { "hash": "…", "de": "…", "cantidad": "13.5000000", "cuando": "…" },
  "enlaces": { "cuenta": "…", "registro": "…", "tx": "…" } }
```

El registro es multi-agente por diseño: `agent_uri(id)`, `agent_exists(id)` y
`find_owner(id)` leen **cualquier** id, no solo el propio. Ahí está el gancho para que
CodeZard descubra a cada agente por su identidad en la cadena en vez de por una URL
escrita a mano. Hoy no hace falta, pero el sitio ya existe.

## Lo que este agente NO hace, y cómo pintarlo

**No ejecuta el código que genera.** Entrega el código y sus casos de test sin correrlos;
ejecutarlos será trabajo del agente de QA. En consecuencia, y siempre:

| campo | valor | qué significa |
|---|---|---|
| `proyecto.estado` | `GENERADO` | hay archivos y nada se ha llegado a ejecutar |
| `evidencia.observed` | `null`, o `{"estado": "no_ejecutado"}` | no se observó nada |
| `entregable.estado` | `no_ejecutado` | ídem |

**Píntalo como «pendiente de QA», nunca como aprobado ni como fallo.** `no_ejecutado` no
es un suspenso: es que nadie ha mirado todavía. Esa distinción es el producto entero; si
CodeZard la pierde al renderizar, la pierde el usuario.

Lo que **sí** se comprueba, y viaja en `fases`: estructura, sintaxis (con `ast.parse`, sin
ejecutar nada) e importaciones. Un proyecto con sintaxis rota sale `FALLIDO` de verdad.

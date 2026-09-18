# API HTTP

Mirag expone un conjunto chico y explícito de rutas. Todo lo que no esté listado aquí es un `404`
(y una ruta conocida con el método equivocado es un `405`). Ninguna ruta de un request se mapea
nunca al filesystem: la página se lee de un archivo fijo y los artefactos se buscan en memoria
por un id opaco.

Todas las respuestas JSON son UTF-8 y llevan `Cache-Control: no-store`, `X-Content-Type-Options:
nosniff`, `X-Frame-Options: DENY` y `Referrer-Policy: no-referrer`. Los errores siempre tienen
esta forma:

```json
{"error": {"code": "missing_question", "message": "'question' is required and must be a non-empty string"}}
```

Por defecto el servidor escucha en loopback (`127.0.0.1:8000`). Para correrlo al servicio de
otra aplicación (CodeZard), ver [deployment.md](deployment.md).

## Autenticación

Con `MIRAG_TOKEN` definido, `POST /api/v1/chat` y la descarga exigen la cabecera:

```
X-Mirag-Token: <el valor de MIRAG_TOKEN>
```

Cualquier otra cosa es `401 unauthorized`, y la respuesta no dice si falta la cabecera o si el
valor está mal. La página, health y las demás rutas de solo lectura siguen abiertas. Sin
`MIRAG_TOKEN` el servidor queda abierto —el modo local— y lo avisa al arrancar. Es un secreto
compartido entre dos servidores, no autenticación de usuarios: el navegador habla con CodeZard,
el servidor de CodeZard habla con Mirag, y el token nunca llega a un navegador. Por eso tampoco
hay CORS. Con token puesto, la página web incluida no puede preguntar (no tiene el token): es
para uso local.

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"   # para generarlo
```

## Rutas

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/` (también `/index.html`) | La página web |
| `GET` | `/api/v1/health` | Liveness y un resumen de la configuración |
| `GET` | `/api/v1/locales` | Los locales soportados y el predeterminado para este cliente |
| `GET` | `/api/v1/i18n/{locale}` | Los textos de la UI de un locale |
| `GET` | `/api/v1/demos?locale={locale}` | Las demos preparadas, localizadas |
| `GET` | `/api/v1/artifacts/{id}/download` | El ZIP verificado de un proyecto generado |
| `GET` | `/api/v1/blockchain/agent` | El panel opcional de identidad Stellar |
| `POST` | `/api/v1/chat` | Hacer una pregunta. La respuesta es un stream de Server-Sent Events |

`HEAD` se acepta en todas las rutas `GET` salvo la de descarga, y nunca devuelve body.

### Resolución del locale

Todos los endpoints localizados resuelven el locale en este orden: un `locale` explícito (campo
del body o parámetro de query), después el header `Accept-Language` y después `MIRAG_LOCALE`
(por defecto `en`). Locales soportados: `en`, `es`. Un locale explícito no soportado pasa a la
siguiente fuente.

### `GET /api/v1/health`

```json
{
  "status": "ok", "version": "2.0.0", "offline": true, "execution": false, "token_required": true,
  "model": "anthropic/claude-haiku-4.5",
  "locales": ["en", "es"], "default_locale": "en",
  "interpreters": ["node", "python", "python3"],
  "features": {"retrieval_plan": true, "reranker": true, "vector_signal": false, "...": false}
}
```

### `GET /api/v1/locales`

```json
{"default": "es", "supported": ["en", "es"]}
```

### `GET /api/v1/i18n/{locale}`

```json
{"locale": "es", "messages": { "...nested UI strings from locales/es/ui.json..." }}
```

`404 unknown_locale` para cualquier cosa que no sea un locale soportado.

### `GET /api/v1/demos?locale=en`

```json
{
  "locale": "en",
  "offline": true,
  "demos": [
    {"key": "knowledge", "title": "Query the corpus",
     "question": "What is a PostgreSQL index and when does it stop helping?",
     "demonstrates": "the corpus answers: what was retrieved, ...", "script": "conceptual"},
    {"key": "construction", "...": "..."},
    {"key": "abstention", "...": "...", "script": null},
    {"key": "project", "...": "..."}
  ]
}
```

### `GET /api/v1/artifacts/{id}/download`

`id` son 24 caracteres hexadecimales en minúscula. Respuestas: `200 application/zip` con
`Content-Disposition: attachment; filename="<name>.zip"` y `X-Mirag-Sha256` (compáralo con
`project.zip.sha256`); `400 malformed_id`; `401 unauthorized`; `410 gone` (vencido o desconocido); `409 integrity_error` (el paquete no pasó la
inspección); `500 integrity_error` (los bytes cambiaron entre la inspección y la entrega). La
URL siempre se toma de `project.download_url` en el stream del chat; el cliente nunca la arma.

### `GET /api/v1/blockchain/agent`

```json
{
  "available": false,
  "reason": "MIRAG_BLOCKCHAIN is off: Stellar is not contacted",
  "identity": null, "wallet": null, "last_payment": null, "links": {}
}
```

Cuando está disponible, `identity` es `{agent, agent_id, registry, network, onchain_wallet, uri,
registration_tx, wallet_tx, verified, reason}`, `wallet` es `{agent, address, network, balance,
exists}` y `last_payment` es `{hash, from, amount, asset, at}`; `links` puede contener URLs del
explorador para `account`, `registry` y `tx`. La respuesta nunca puede contener una secret seed
de Stellar.

### `POST /api/v1/chat`

Request (`Content-Type: application/json`, 64 KiB como máximo):

```json
{"question": "What is a PostgreSQL index?", "mode": "pipeline", "locale": "en"}
```

| Campo | Tipo | Obligatorio | Notas |
|---|---|---|---|
| `question` | string | sí | de 1 a 8000 caracteres |
| `mode` | string | no | `pipeline` (por defecto, producción) o `architect` (experimental) |
| `locale` | string | no | `en` o `es` |

Un token ausente o incorrecto es `401` y los errores de validación son `400`, ambos en JSON y
**antes** de que empiece el stream. Una
vez que el stream empieza, el status es `200 text/event-stream` y cada evento es una línea
`data: <json>\n\n`.

#### Eventos del stream

| `type` | Campos | Cuándo |
|---|---|---|
| `step` | `name`, `status`, `summary`, `ms`, `source`, `detail` | En cada etapa del pipeline |
| `phase` | `text` | Una fase del modo arquitecto, o el atajo de self-knowledge |
| `thought` | `text` | Lo que razonó el modelo (modo arquitecto) |
| `tool` | `name`, `args`, `result` | Una llamada a herramienta (modo arquitecto) |
| `cost` | `text` | Gasto acumulado (modo arquitecto) |
| `done` | ver abajo | Siempre el último evento |

`step.status` es uno de `executed`, `skipped`, `fallback`, `error`, `warning` - más dos valores
que solo se emiten para la etapa `offline_lock`: `simulated` (responde una demo preparada) y
`no_model` (ninguna demo coincide: no se inventa ninguna respuesta). `step.source` es
`execution`, `model`, `corpus` o `""`. `step.summary` ya viene localizado; `step.name` es un
identificador estable que la página traduce a través de `ui.json` (`steps.<name>`).

Nombres de etapa que emite el pipeline, en orden: `offline_lock` (solo offline), `project_state`,
`retrieval_plan`, `filter:<index>`, `bm25:<index>`, `vector:<index>`, `rrf:<index>`,
`reranker:<index>` (para cada índice: `knowledge`, `anti_patterns`, `failures`),
`fallback:<stage>:<index>` (solo cuando una etapa hizo fallback), `retrieval`, `symbols`,
`graph`, `sufficiency`, `context`, y después la rama de código - `model`, `delivery`,
`verification`, `repair`, `verification_after_repair`, `evidence`, `anti_patterns`,
`persistence` - o la rama de proyecto - `specification`, `plan`, `generation:<group>` (`core`,
`domain`, `tests`, `docs`), `project`, `structure`, `syntax`, `imports`, `repair:<n>`,
`execution`, `tests`, `documented_command`, `tests_after_repair`, `crud`, `packaging`,
`artifact`.

La etapa `retrieval` lleva `detail = {"ids": [...], "methods": [...]}`; la etapa `project` lleva
`detail = {"tree": ["app/main.py", ...], "totals": {...}}`.

#### El evento `done`

```json
{
  "type": "done",
  "answer": "markdown (already localised)",
  "mode": "pipeline",
  "locale": "en",
  "cost_summary": "1 calls · 0 tokens · $0.0000 of $0.50",
  "claim_status": "no_claim",
  "evidence": { "...": "evidence panel, or null" },
  "timeline": [ { "...": "timeline rows, or null" } ],
  "cost": { "...": "cost panel, or null" },
  "project": { "...": "project panel, or null" },
  "deliverable": { "...": "single-file deliverable, or null" }
}
```

En el atajo de self-knowledge, `mode` es `"state"` y solo están presentes `answer`, `mode`,
`locale` y `cost_summary`.

`claim_status` es `supported`, `unsupported`, `refuted`, `not_executed` o `no_claim`: el
resultado de comparar lo que afirma la respuesta con los marcadores de las ejecuciones reales.

**Panel de evidencia** - cuatro capas que nunca comparten lugar:

```json
{
  "claim":        [{"risk": "...", "property": "...", "test_id": "add", "status": "verified"}],
  "observed":     {"status": "passed", "header": "TESTS PASSED · 6 of 6 markers",
                   "markers": {"add": "PASS"}, "passed": 6, "failed": 0, "truncated": false},
  "verified":     [ "...rows with status verified..." ],
  "simulated":    [ "...rows with status verified_in_simulation..." ],
  "not_verified": [ "...rows with status unverified or refuted..." ],
  "uncovered":    ["risks the model admitted not covering"]
}
```

`observed` es `null` cuando no se ejecutó nada, y `{"status": "not_executed", "header": "..."}`
cuando se entregó código que nunca se ejecutó. `observed.status` es uno de `passed`, `failed`,
`no_evidence`, `not_executed`. El `status` de cada fila es uno de `verified`,
`verified_in_simulation`, `refuted`, `unverified`.

**Filas del timeline** - las etapas internas de retrieval se pliegan en la fila `retrieval`:

```json
{"t": 0.05, "ms": 48.2, "stage": "retrieval", "status": "executed", "summary": "...", "source": "corpus"}
```

**Panel de costo**:

```json
{"simulated": true, "demo": "code", "calls": 0, "text": "SIMULATED · $0"}
{"simulated": false, "free": false, "text": "$0.0123", "calls": 2, "tokens": 5120}
{"simulated": false, "free": true, "model": "openrouter/free", "text": "GRATIS · $0 · openrouter/free",
 "calls": 2, "tokens": 5120}
```

`free` son llamadas reales que reportaron un coste de exactamente 0 (un modelo gratuito): no se
disfraza de `$0.0000`.

**Entregable** (rama de código, un solo archivo):

```json
{"files": {"calculator.py": "..."}, "command": "python3 test_calculator.py",
 "folder": "/abs/path/var/output", "status": "passed", "simulated": ["PostgreSQL"]}
```

`status` es el estado de ejecución observado; `simulated` lista las tecnologías que pedía el
request y que el código ejecutado reemplazó por una simulación.

**Panel de proyecto** (rama de proyecto):

```json
{
  "id": "24-hex", "name": "books-api", "status": "VERIFIED", "simulated": true,
  "reason": "the 16 markers pass, including the full CRUD over HTTP",
  "files": [{"path": "app/main.py", "bytes": 1234, "lines": 60, "sha256": "...", "text": "...el archivo entero..."}],
  "totals": {"files": 14, "directories": 4, "lines": 386, "bytes": 12000},
  "verification": {"status": "VERIFIED", "reason": "...", "markers": {}, "passed": 16, "failed": 0},
  "phases": [{"name": "tests", "status": "ok", "detail": "..."}],
  "zip": {"name": "books-api.zip", "bytes": 8236, "sha256": "..."},
  "integrity": {"ok": true, "reason": "", "checks": [["reopens", true, "15 entries"]]},
  "download_url": "/api/v1/artifacts/<id>/download"
}
```

`status` es uno de `GENERATED`, `VALIDATED`, `EXECUTED`, `TESTED`, `VERIFIED`, `PARTIAL`,
`FAILED`. `phases[].status` es `ok`, `failed`, `limited` o `skipped`. `integrity.checks` son
`[code, ok, detail]`; los códigos son estables (`fits_cap`, `reopens`, `crc_ok`, `single_root`,
`no_path_escapes`, `no_symlinks`, `no_junk_or_secret_names`, `no_missing_files`,
`no_extra_files`, `extracts`, `hashes_match`, `no_secret_content`,
`embedded_manifest_matches`, `builds`) y la página los traduce. `download_url` es `null`
cuando el paquete no pasó la inspección: en ese caso no hay botón de descarga.

`files[].text` es el contenido completo de cada archivo: con eso se muestra el código sin
descomprimir nada. Puede venir en `null`, y entonces `text_omitted` dice por qué: el proyecto
pasa de 2 MB en total, o el archivo contiene algo con forma de credencial. Un archivo vacío es
`""`, que no es lo mismo que `null`.

**Los artefactos caducan.** Viven en la memoria del proceso y se pierden a la hora, cuando hay
más de 20 (se van los más viejos), al pasar de 64 MB en total, y en cada reinicio. Baja el ZIP
en cuanto llegue el evento `done` y guárdalo tú: guardar el id para más tarde es guardar un
`410` futuro.

## Cuando la ejecución está apagada

Con `MIRAG_EXECUTION=off` (el valor por defecto) el agente entrega el código y sus tests sin
correrlos; ejecutarlos es trabajo del agente de QA. Entonces, siempre:

| Campo | Valor | Qué significa |
|---|---|---|
| `project.status` | `GENERATED` | hay archivos y nada se ejecutó |
| `project.phases` | `structure`, `syntax`, `imports` y luego `execution: skipped` | los chequeos estáticos sí corrieron |
| `evidence.observed.status` | `not_executed` | no se observó nada |
| `deliverable.status` | `not_executed` | ídem |
| `step` `verification` | `skipped` | no falló: no corrió |

**Muéstralo como «pendiente de QA», nunca como aprobado ni como fallo.** `not_executed` no es
un suspenso: es que nadie ha mirado todavía. Esa distinción es el producto entero; un cliente
que la pierde al pintar se la hace perder al usuario. Un proyecto con la sintaxis rota sigue
saliendo `FAILED` de verdad.

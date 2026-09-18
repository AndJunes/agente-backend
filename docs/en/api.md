# HTTP API

Mirag serves a small, explicit set of routes. Anything that is not listed here is a `404`
(and a known path with the wrong method is a `405`). No request path is ever mapped to the
filesystem: the page is read from a fixed file and artifacts are looked up by an opaque id in
memory.

All JSON responses are UTF-8 and carry `Cache-Control: no-store`, `X-Content-Type-Options:
nosniff`, `X-Frame-Options: DENY` and `Referrer-Policy: no-referrer`. Errors always have the
shape:

```json
{"error": {"code": "missing_question", "message": "'question' is required and must be a non-empty string"}}
```

The server listens on loopback (`127.0.0.1:8000`) by default. To run it for another
application (CodeZard) see [deployment.md](deployment.md).

## Authentication

With `MIRAG_TOKEN` set, `POST /api/v1/chat` and the download require the header:

```
X-Mirag-Token: <the value of MIRAG_TOKEN>
```

Anything else is `401 unauthorized`, and the answer does not say whether the header is missing
or wrong. The page, health and the other read-only routes stay open. Without `MIRAG_TOKEN`
the server is open - the local mode - and it says so at startup. It is a secret shared between
two servers, not user authentication: the browser talks to CodeZard, CodeZard's server talks to
Mirag, and the token never reaches a browser. That is also why there is no CORS. With a token
set, the bundled web page cannot ask (it does not have the token): it is meant for local use.

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"   # to generate one
```

## Routes

| Method | Path | Description |
|---|---|---|
| `GET` | `/` (also `/index.html`) | The web page |
| `GET` | `/api/v1/health` | Liveness and a configuration summary |
| `GET` | `/api/v1/locales` | Supported locales and the default one for this client |
| `GET` | `/api/v1/i18n/{locale}` | The UI strings of a locale |
| `GET` | `/api/v1/demos?locale={locale}` | The prepared demos, localised |
| `GET` | `/api/v1/artifacts/{id}/download` | The verified ZIP of a generated project |
| `GET` | `/api/v1/blockchain/agent` | The optional Stellar identity panel |
| `POST` | `/api/v1/chat` | Ask a question. The answer is a Server-Sent Events stream |

`HEAD` is accepted on every `GET` route except the download, and never returns a body.

### Locale resolution

Every localised endpoint resolves the locale in this order: an explicit `locale` (body field
or query parameter), then the `Accept-Language` header, then `MIRAG_LOCALE` (default `en`).
Supported locales: `en`, `es`. An unsupported explicit locale falls back to the next source.

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

`404 unknown_locale` for anything that is not a supported locale.

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

`id` is 24 lowercase hex characters. Responses: `200 application/zip` with
`Content-Disposition: attachment; filename="<name>.zip"` and `X-Mirag-Sha256` (compare it with
`project.zip.sha256`); `400 malformed_id`; `401 unauthorized`; `410 gone` (expired or unknown); `409 integrity_error` (the package did not pass
inspection); `500 integrity_error` (the bytes changed between inspection and delivery). The URL
is always taken from `project.download_url` in the chat stream, never built by the client.

### `GET /api/v1/blockchain/agent`

```json
{
  "available": false,
  "reason": "MIRAG_BLOCKCHAIN is off: Stellar is not contacted",
  "identity": null, "wallet": null, "last_payment": null, "links": {}
}
```

When available, `identity` is `{agent, agent_id, registry, network, onchain_wallet, uri,
registration_tx, wallet_tx, verified, reason}`, `wallet` is `{agent, address, network, balance,
exists}` and `last_payment` is `{hash, from, amount, asset, at}`; `links` may contain `account`,
`registry` and `tx` explorer URLs. The response can never contain a Stellar secret seed.

### `POST /api/v1/chat`

Request (`Content-Type: application/json`, at most 64 KiB):

```json
{"question": "What is a PostgreSQL index?", "mode": "pipeline", "locale": "en"}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `question` | string | yes | 1 to 8000 characters |
| `mode` | string | no | `pipeline` (default, production) or `architect` (experimental) |
| `locale` | string | no | `en` or `es` |

A missing or wrong token is `401` and validation errors are `400`, both JSON and **before**
the stream starts. Once the stream
starts the status is `200 text/event-stream`, and every event is one `data: <json>\n\n` line.

#### Stream events

| `type` | Fields | When |
|---|---|---|
| `step` | `name`, `status`, `summary`, `ms`, `source`, `detail` | Each pipeline stage |
| `phase` | `text` | A phase of the architect mode, or the self-knowledge shortcut |
| `thought` | `text` | What the model reasoned (architect mode) |
| `tool` | `name`, `args`, `result` | A tool call (architect mode) |
| `cost` | `text` | Running spend (architect mode) |
| `done` | see below | Always the last event |

`step.status` is one of `executed`, `skipped`, `fallback`, `error`, `warning` - plus two values
only emitted for the `offline_lock` step: `simulated` (a prepared demo answers) and `no_model`
(no demo matches: no answer is invented). `step.source` is `execution`, `model`, `corpus` or
`""`. `step.summary` is already localised; `step.name` is a stable identifier the page
translates through `ui.json` (`steps.<name>`).

Step names emitted by the pipeline, in order: `offline_lock` (offline only), `project_state`,
`retrieval_plan`, `filter:<index>`, `bm25:<index>`, `vector:<index>`, `rrf:<index>`,
`reranker:<index>` (for each index `knowledge`, `anti_patterns`, `failures`),
`fallback:<stage>:<index>` (only when a stage fell back), `retrieval`, `symbols`, `graph`,
`sufficiency`, `context`, then either the code branch - `model`, `delivery`, `verification`,
`repair`, `verification_after_repair`, `evidence`, `anti_patterns`, `persistence` - or the
project branch - `specification`, `plan`, `generation:<group>` (`core`, `domain`, `tests`,
`docs`), `project`, `structure`, `syntax`, `imports`, `repair:<n>`, `execution`, `tests`,
`documented_command`, `tests_after_repair`, `crud`, `packaging`, `artifact`.

The `retrieval` step carries `detail = {"ids": [...], "methods": [...]}`; the `project` step
carries `detail = {"tree": ["app/main.py", ...], "totals": {...}}`.

#### The `done` event

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

For the self-knowledge shortcut `mode` is `"state"` and only `answer`, `mode`, `locale` and
`cost_summary` are present.

`claim_status` is `supported`, `unsupported`, `refuted`, `not_executed` or `no_claim`: the
result of comparing what the answer claims with the markers of the real executions.

**Evidence panel** - four layers that never share a place:

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

`observed` is `null` when nothing ran; `{"status": "not_executed", "header": "..."}` when code
was delivered and never executed. `observed.status` is one of `passed`, `failed`,
`no_evidence`, `not_executed`. Row `status` is one of `verified`, `verified_in_simulation`,
`refuted`, `unverified`.

**Timeline rows** - the internal retrieval stages are folded into the `retrieval` row:

```json
{"t": 0.05, "ms": 48.2, "stage": "retrieval", "status": "executed", "summary": "...", "source": "corpus"}
```

**Cost panel**:

```json
{"simulated": true, "demo": "code", "calls": 0, "text": "SIMULATED · $0"}
{"simulated": false, "free": false, "text": "$0.0123", "calls": 2, "tokens": 5120}
{"simulated": false, "free": true, "model": "openrouter/free", "text": "FREE · $0 · openrouter/free",
 "calls": 2, "tokens": 5120}
```

`free` is real calls that reported a cost of exactly 0 (a free model): it is not dressed as
`$0.0000`.

**Deliverable** (single-file code branch):

```json
{"files": {"calculator.py": "..."}, "command": "python3 test_calculator.py",
 "folder": "/abs/path/var/output", "status": "passed", "simulated": ["PostgreSQL"]}
```

`status` is the observed execution status; `simulated` lists technologies the request asked
for and the executed code replaced with a simulation.

**Project panel** (project branch):

```json
{
  "id": "24-hex", "name": "books-api", "status": "VERIFIED", "simulated": true,
  "reason": "the 16 markers pass, including the full CRUD over HTTP",
  "files": [{"path": "app/main.py", "bytes": 1234, "lines": 60, "sha256": "...", "text": "...the whole file..."}],
  "totals": {"files": 14, "directories": 4, "lines": 386, "bytes": 12000},
  "verification": {"status": "VERIFIED", "reason": "...", "markers": {}, "passed": 16, "failed": 0},
  "phases": [{"name": "tests", "status": "ok", "detail": "..."}],
  "zip": {"name": "books-api.zip", "bytes": 8236, "sha256": "..."},
  "integrity": {"ok": true, "reason": "", "checks": [["reopens", true, "15 entries"]]},
  "download_url": "/api/v1/artifacts/<id>/download"
}
```

`status` is one of `GENERATED`, `VALIDATED`, `EXECUTED`, `TESTED`, `VERIFIED`, `PARTIAL`,
`FAILED`. `phases[].status` is `ok`, `failed`, `limited` or `skipped`. `integrity.checks` are
`[code, ok, detail]`; the codes are stable (`fits_cap`, `reopens`, `crc_ok`, `single_root`,
`no_path_escapes`, `no_symlinks`, `no_junk_or_secret_names`, `no_missing_files`,
`no_extra_files`, `extracts`, `hashes_match`, `no_secret_content`,
`embedded_manifest_matches`, `builds`) and the page translates them. `download_url` is `null`
when the package did not pass inspection: then there is no download button.

`files[].text` is the full content of each file, so the code can be shown without unpacking
anything. It can be `null`, and then `text_omitted` says why: the project exceeds 2 MB in
total, or the file contains something shaped like a credential. An empty file is `""`, which
is not the same as `null`.

**Artifacts expire.** They live in the process memory and are lost after one hour, when more
than 20 exist (the oldest go first), past 64 MB in total, and on every restart. Download the
ZIP as soon as the `done` event arrives and keep it: storing the id for later is storing a
future `410`.

## When execution is off

With `MIRAG_EXECUTION=off` (the default) the agent delivers the code and its tests without
running them; running them is the QA agent's job. Then, always:

| Field | Value | Meaning |
|---|---|---|
| `project.status` | `GENERATED` | there are files and nothing ran |
| `project.phases` | `structure`, `syntax`, `imports`, then `execution: skipped` | the static checks did run |
| `evidence.observed.status` | `not_executed` | nothing was observed |
| `deliverable.status` | `not_executed` | same |
| `step` `verification` | `skipped` | it did not fail: it did not run |

**Show it as "pending QA", never as passed nor as failed.** `not_executed` is not a failure:
nobody has looked yet. That distinction is the whole product; a client that loses it when
rendering loses it for the user. A project with broken syntax is still `FAILED` for real.

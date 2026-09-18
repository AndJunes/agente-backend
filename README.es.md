# Mirag

**Le das un problema. Mirag busca lo que sabe, propone una solución, la ejecuta y te muestra
exactamente en qué se apoya esa solución - y en qué no.**

*[Read in English](README.md)*

Solo biblioteca estándar de Python: **el núcleo tiene cero dependencias de terceros** (lo
verifica un test de arquitectura). La capa opcional de identidad Stellar declara `stellar-sdk`
como extra. Inglés y español tienen soporte completo: corpus de conocimiento, UI, respuestas y
heurísticas de idioma.

```bash
pip install -e ".[dev]"
mirag serve                 # http://127.0.0.1:8000
```

Con `MIRAG_OFFLINE=1` (el valor por defecto) cuatro demos preparadas corren de punta a punta y
nada cuesta dinero. Para respuestas reales, guarda tu key en `.env` (copiando `.env.example`) y
arranca con `MIRAG_OFFLINE=0`.

## Qué hace

```
Pregunta → Plan → Retrieval (3 índices) → Contexto → Modelo
         → Herramienta → Verificación → Evidencia → Respuesta
```

Y si pides un proyecto entero en lugar de un solo archivo:

```
Creá una API REST de libros con CRUD completo. Arquitectura por dominios.
        ↓
books-api · 14 archivos · sus tests ejecutados · [ Descargar ZIP ]
```

## Qué lo hace distinto

**El estado lo decide la ejecución, nunca el modelo.** Cuatro veredictos posibles:

| | |
|---|---|
| `passed` | hubo marcadores de test y todos pasaron |
| `failed` | se ejecutó y falló |
| `no_evidence` | terminó sin error y **no imprimió ni un solo marcador** - eso no es pasar |
| `not_executed` | nunca se ejecutó |

**Cada respuesta separa tres cosas** que la mayoría de las herramientas mezclan: lo que el modelo
*dice* (`MODEL CLAIM`), lo que la máquina *vio* (`OBSERVED`) y lo que está *demostrado*
(`VERIFIED`). Si el modelo afirma que los tests pasan y no hay marcadores, aparece un aviso
arriba y su texto se conserva entero para que lo juzgues.

**Si el corpus no cubre lo que preguntas, lo dice antes de responder.**

## Estructura del repositorio

```
.
├── src/mirag/               el paquete (ver docs/es/architecture.md)
│   ├── locales/{en,es}/     mensajes, textos de la UI, heurísticas de idioma, marcadores del corpus
│   ├── knowledge/{en,es}/   el corpus de conocimiento: 19 cajas de backend senior por idioma
│   └── web/index.html       la página
├── tests/                   suites unitarias, de integración y de arquitectura (pytest)
├── benchmarks/              benchmarks de retrieval y de proyectos, datasets y resultados
├── scripts/                 demos manuales (identidad Stellar)
├── docs/{en,es}/            documentación en los dos idiomas
└── docs/history/            los informes que explican cómo llegó el proyecto hasta aquí (en español)
```

## Cómo correrlo

```bash
mirag serve                          # la página (offline, $0)
mirag demo all --locale es           # las 4 demos canónicas, con sus contratos verificados
mirag ask "What is an idempotency key?" --locale en
mirag features                       # qué etapas del pipeline están encendidas, y por qué
pytest                               # la suite rápida, offline
pytest -m "not network"              # todo, incluidos los tests lentos
```

`make run`, `make test`, `make lint`, `make demo` hacen lo mismo en sistemas con `make`.

## El tope de gasto

Cada llamada devuelve el costo real de OpenRouter, así que el agente **se detiene antes de
pasarse**, no después de la factura:

```bash
MIRAG_BUDGET_USD=0.20 MIRAG_OFFLINE=0 mirag serve
```

El valor por defecto es $0.50 por request.

## La API

`POST /api/v1/chat` emite un stream de Server-Sent Events; los proyectos generados se descargan
de `GET /api/v1/artifacts/{id}/download`. El contrato completo está en
[docs/es/api.md](docs/es/api.md).

## Lo que no está demostrado

La generación de proyectos funciona de punta a punta - genera, ejecuta, repara, empaqueta,
verifica la integridad del ZIP y lo sirve - pero, **medido sobre 10 corridas con un modelo real,
ninguna llegó a `VERIFIED`**: fallan en sintaxis, en imports o en sus propios tests. Lo que sí
está demostrado es que la máquina no miente cuando eso pasa. Ver
[docs/history/reports/PROJECT_BENCHMARK_REPORT.md](docs/history/reports/PROJECT_BENCHMARK_REPORT.md).

## Documentación

| | English | Español |
|---|---|---|
| Arquitectura | [docs/en/architecture.md](docs/en/architecture.md) | [docs/es/architecture.md](docs/es/architecture.md) |
| API HTTP | [docs/en/api.md](docs/en/api.md) | [docs/es/api.md](docs/es/api.md) |
| i18n | [docs/en/i18n.md](docs/en/i18n.md) | [docs/es/i18n.md](docs/es/i18n.md) |
| Configuración | [docs/en/configuration.md](docs/en/configuration.md) | [docs/es/configuration.md](docs/es/configuration.md) |
| Desarrollo | [docs/en/development.md](docs/en/development.md) | [docs/es/development.md](docs/es/development.md) |
| Identidad Stellar | [docs/en/blockchain.md](docs/en/blockchain.md) | [docs/es/blockchain.md](docs/es/blockchain.md) |
| Changelog | [CHANGELOG.md](CHANGELOG.md) | |

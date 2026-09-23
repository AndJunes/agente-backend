# Mirag

**Le das un problema. Mirag busca lo que sabe, propone una solución y te muestra exactamente
en qué se apoya esa solución - y en qué no.**

Genera el código y sus casos de test y, por defecto, **no los ejecuta**: eso será trabajo del
agente de QA (`MIRAG_EXECUTION=off`). Lo que no cambia es que no se afirma nada que no se haya
observado, y hoy eso significa decir `not_executed` en vez de fingir un aprobado.

*[Read in English](README.md)*

Solo biblioteca estándar de Python: **el núcleo tiene cero dependencias de terceros**
(`dependencies = []` en `pyproject.toml`). La capa opcional de identidad Stellar declara
`stellar-sdk` como extra. Inglés y español tienen soporte completo: corpus de conocimiento, UI,
respuestas y heurísticas de idioma.

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

**El estado lo decide la ejecución, nunca el modelo.** Cuatro veredictos posibles. Con la
ejecución apagada, en producción sale siempre el cuarto; la maquinaria sigue entera y las demos
la encienden para enseñarla. Estructura, sintaxis e imports se comprueban sin ejecutar nada:

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
├── src/mirag_pm/            el agente PM: el mismo código, al que se le dice que es otro agente
├── src/mirag_manager/       los dos agentes detrás de un solo puerto (`python -m mirag_manager serve`)
├── benchmarks/              benchmarks de retrieval y de proyectos, datasets y resultados
├── scripts/                 las comprobaciones que corre el CI, el sondeo de modelos y la demo Stellar
├── docs/{en,es}/            documentación en los dos idiomas
└── docs/history/            los informes que explican cómo llegó el proyecto hasta aquí (en español)
```

## Cómo correrlo

```bash
mirag serve                          # la página (offline, $0)
mirag demo all --locale es           # las 4 demos canónicas, con sus contratos verificados
mirag ask "What is an idempotency key?" --locale en
mirag features                       # qué etapas del pipeline están encendidas, y por qué
docker compose up -d                 # lo mismo, en un contenedor sin privilegios
```

`make run`, `make run-manager`, `make lint`, `make typecheck` y `make demo` hacen lo mismo en
sistemas con `make`. Es opcional: cada target es una línea `python -m ...` del `Makefile`, que es
lo que hay que correr en Windows si no lo tienes.

## Correrlo con CodeZard

La pantalla de CodeZard no habla con `mirag serve`. Necesita **dos** agentes, este (el agente
de backend) y el PM (`mirag_pm`), y llega a los dos a través del gateway. `mirag_manager` los
corre en un solo proceso, en un solo puerto, distinguidos por el primer segmento de la ruta:

| Ruta | Agente | Operaciones |
|---|---|---|
| `/backend/...` | `mirag` | `chat` |
| `/pm/...` | `mirag_pm` | `analyze`, `plan`, `revise` |

```bash
python -m venv .venv                       # una vez
# PowerShell: .venv\Scripts\Activate.ps1        bash/zsh: source .venv/bin/activate
pip install -e ".[dev]"                    # una vez
cp .env.example .env                       # una vez (PowerShell: Copy-Item .env.example .env)

python -m mirag_manager serve              # o: make run-manager
#   backend: chat
#   pm: analyze, plan, revise
```

Edita primero `.env`. Estos son los valores que importan para CodeZard:

| Variable | Ponla en | Por qué |
|---|---|---|
| `MIRAG_PORT` | `8100` | El ejemplo dice `8000`, que es el puerto del gateway. El `.env` del gateway apunta a `8100` |
| `MIRAG_TOKEN` | un secreto | El gateway lo envía como `X-Mirag-Token`, así que debe ser igual a `MIRAG_TOKEN` en `CodeZard/.env`. Un solo token cubre a los dos agentes |
| `MIRAG_OFFLINE` | `0` | `1` (el valor por defecto) es el candado de ensayo: el PM repite un plan fijo, marcado como simulado, y este agente solo responde sus demos preparadas. `0` llama al modelo de verdad |
| `OPENROUTER_API_KEY` | tu key | Hace falta con `MIRAG_OFFLINE=0` |
| `MIRAG_BACKEND_MODEL`, `MIRAG_PM_MODEL` | opcional | Un modelo por agente. Sin definir, los dos usan `MIRAG_MODEL` |
| `MIRAG_EXECUTION` | `off` o `true` | Si el código generado y sus tests se ejecutan. `off`: se entregan sin correr y el veredicto es `not_executed` |
| `MIRAG_CONSOLE` | `1`, opcional | Deja que la pantalla ejecute comandos en un proyecto entregado. El gateway también necesita `GATEWAY_ORCHESTRATION__CONSOLE=true` |

Comprueba que responde:

```bash
curl http://127.0.0.1:8100/backend/api/v1/health
curl http://127.0.0.1:8100/pm/api/v1/health
```

Después arranca el gateway (`CodeZard`, comando `gateway`) y la pantalla (`codezard-front`,
comando `npm run dev`); el README de `codezard-front` tiene el recorrido completo y una tabla
de qué revisar cuando algo falla. Algunas cosas que salen mal aquí:

- **`mirag serve` es el proceso equivocado para la pantalla.** Solo sirve `/api/v1/...`, así que
  toda llamada a `/pm/...` da `404`. Usa `python -m mirag_manager serve`.
- **El comando `mirag-manager`** está declarado en `pyproject.toml`, pero un entorno instalado
  antes de que se añadiera no lo tiene. `python -m mirag_manager serve` siempre funciona.
- **En Windows, un reinicio puede dejar dos managers en el mismo puerto.**
  `netstat -ano | findstr :8100` debería mostrar un solo listener.
- **En Docker**, `CodeZard/docker-compose.local.yml` construye el `Dockerfile` de esta carpeta
  (`--target base`) y corre el manager en un contenedor.

## Comprobaciones

Este checkout no tiene suite de tests (se eliminó `tests/`). Lo que corre el CI es:

```bash
python -m ruff check src benchmarks scripts     # make lint
python -m mypy                                  # make typecheck
python -m mirag demo all                        # make demo; añade --locale es para la corrida en español
python -m mirag_pm.cli doctor                   # cada locale del PM carga, y sus cuatro índices
python -m mirag_pm.cli coverage --by-domain     # cada documento del PM es alcanzable desde una skill
python scripts/check_delivery.py                # un proyecto que no coincide con su plan no es entregable
python scripts/check_deadlines.py               # una llamada colgada termina, y cerrar la pestaña detiene el trabajo
python scripts/check_repair.py                  # un test que falla le dice al reparador dónde mirar
python scripts/check_parallel.py                # los lotes corren a la vez sin perder archivos ni contar mal las llamadas
```

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

## En un servidor

```bash
docker compose up -d --build       # http://127.0.0.1:8000, y solo ahí
```

Usuario sin privilegios, su propio código en solo lectura, `/tmp` en RAM, sin capabilities y
con techo de CPU, memoria y procesos. El puerto se publica contra `127.0.0.1` a propósito, y
`MIRAG_TOKEN` le cierra la puerta a quien no traiga el secreto. Dos imágenes desde el mismo
`Dockerfile`: `--target base` sin una sola dependencia, y `--target identidad` con
`stellar-sdk`. Cómo se hace, qué protege cada pieza y **qué sigue sin estar resuelto**:
[docs/es/deployment.md](docs/es/deployment.md).

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
| Despliegue | [docs/en/deployment.md](docs/en/deployment.md) | [docs/es/deployment.md](docs/es/deployment.md) |
| i18n | [docs/en/i18n.md](docs/en/i18n.md) | [docs/es/i18n.md](docs/es/i18n.md) |
| Configuración | [docs/en/configuration.md](docs/en/configuration.md) | [docs/es/configuration.md](docs/es/configuration.md) |
| Desarrollo | [docs/en/development.md](docs/en/development.md) | [docs/es/development.md](docs/es/development.md) |
| Identidad Stellar | [docs/en/blockchain.md](docs/en/blockchain.md) | [docs/es/blockchain.md](docs/es/blockchain.md) |
| Changelog | [CHANGELOG.md](CHANGELOG.md) | |

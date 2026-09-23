# Desarrollo

## Instalación

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"            # agregar ",blockchain" para la capa opcional de Stellar
```

Python 3.11 o superior. El runtime no tiene dependencias de terceros; `dev` trae ruff y mypy.

## Comandos de todos los días

| Comando | Qué hace |
|---|---|
| `make run` / `mirag serve` | Levanta el agente solo en http://127.0.0.1:8000 (offline, $0) |
| `make run-manager` / `python -m mirag_manager serve` | Levanta el agente de backend y el PM detrás de un solo puerto, que es lo que usa la pantalla de CodeZard (ver el README) |
| `make lint` / `python -m ruff check src benchmarks scripts` | Lint |
| `make typecheck` / `python -m mypy` | Chequeo de tipos |
| `make demo` / `mirag demo all` | Corre las cuatro demos canónicas y verifica sus contratos |
| `mirag ask "question" --locale es` | Una pregunta a través del pipeline, impresa |
| `mirag features` | El estado de cada feature flag y por qué |
| `mirag traces -n 20` | Las últimas líneas de traza |

En Windows sin `make`, usa los comandos de la derecha.

## Comprobaciones

Este checkout no tiene suite de tests: se eliminó `tests/`. Lo que la reemplaza es lo que corre
el CI (`.github/workflows/ci.yml`):

| Comando | Qué protege |
|---|---|
| `python -m ruff check src benchmarks scripts` | Lint |
| `python -m mypy` | Tipos |
| `python -m mirag demo all`, y otra vez con `--locale es` | Los contratos de las cuatro demos, en los dos idiomas |
| `python -m mirag_pm.cli doctor` | Cada locale del PM carga, y ninguno de sus cuatro índices está vacío |
| `python -m mirag_pm.cli coverage --by-domain` | Cada documento del PM es alcanzable desde una skill |
| `python scripts/check_delivery.py` | Un proyecto que no coincide con su plan no es entregable |
| `python scripts/check_deadlines.py` | Una llamada colgada termina, y cerrar la pestaña detiene el trabajo |
| `python scripts/check_repair.py` | Un test que falla le llega al reparador como archivo, línea y motivo |
| `python scripts/check_parallel.py` | Los lotes corren a la vez sin perder archivos ni contar mal las llamadas |

Reglas:

- Toda comprobación es offline. El gateway se niega a llamar a un modelo mientras `MIRAG_OFFLINE`
  está activo, así que una comprobación no puede gastar dinero por accidente; las decisiones del
  modelo vienen de guiones de `ScriptedChatModel`. El CI pone `MIRAG_OFFLINE=1`. Haz lo mismo en
  local si tu `.env` tiene una key real: `.env` solo completa lo que el entorno no definió ya.

## Convenciones

- Identificadores, comentarios y docstrings en inglés. El texto que ve el usuario pasa por los
  catálogos de **ambos** locales. Mantén las claves y los placeholders idénticos a mano: los
  tests de paridad de i18n se fueron con `tests/`.
- Los comentarios explican el *porqué* (una medición, un bug pasado), no el *qué*.
- Los value objects son dataclasses congeladas; los conjuntos cerrados de valores son `StrEnum`s.
- Las dependencias se inyectan por constructor; `container.py` es el único composition root.
- Siempre pasar `encoding="utf-8"` al leer o escribir texto.

## Configuración

Ver [configuration.md](configuration.md).

## Benchmarks

Ver `benchmarks/README.md`. El benchmark de calibración es el único que escribe
`src/mirag/resources/feature_gains.json`, el archivo que lee el feature gate.

# Desarrollo

## Instalación

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"            # agregar ",blockchain" para la capa opcional de Stellar
```

Python 3.11 o superior. El runtime no tiene dependencias de terceros; `dev` trae pytest, ruff
y mypy.

## Comandos de todos los días

| Comando | Qué hace |
|---|---|
| `make run` / `mirag serve` | Levanta el servidor en http://127.0.0.1:8000 (offline, $0) |
| `make test` / `pytest` | La suite rápida (offline, carpetas temporales aisladas). Los tests marcados `slow` se saltean por defecto |
| `make test-all` / `pytest -m "not network"` | Todo, incluidos los tests `slow` (subprocesos, servidores HTTP) |
| `make lint` / `ruff check src tests` | Lint |
| `make typecheck` / `mypy` | Chequeo de tipos |
| `make demo` / `mirag demo all` | Corre las cuatro demos canónicas y verifica sus contratos |
| `mirag ask "question" --locale es` | Una pregunta a través del pipeline, impresa |
| `mirag features` | El estado de cada feature flag y por qué |
| `mirag traces -n 20` | Las últimas líneas de traza |

En Windows sin `make`, usa los comandos de la derecha.

## Tests

```
tests/
├── conftest.py        fixtures compartidos (settings offline, data dir aislado, engines por locale)
├── unit/<area>/       una carpeta por paquete
├── integration/       servidor HTTP real, generación completa de proyectos, suites opcionales de red
├── architecture/      reglas sobre el AST: capas, sin imports de terceros, encodings, identificadores en inglés
└── fixtures/          repositorios de ejemplo
```

Reglas:

- Todos los tests son offline. El gateway se niega a llamar a un modelo mientras `MIRAG_OFFLINE`
  está activo, así que un test no puede gastar dinero por accidente; las decisiones del modelo
  vienen de guiones de `ScriptedChatModel`.
- Los tests escriben solo bajo `tmp_path`: los fixtures `settings`/`container` apuntan
  `MIRAG_DATA_DIR` ahí.
- Los tests que lanzan intérpretes o servidores se marcan con `@pytest.mark.slow`.
- Los tests que necesitan la red real de Stellar están marcados `network` y se saltean salvo que
  se habiliten.

## Convenciones

- Identificadores, comentarios y docstrings en inglés. El texto que ve el usuario pasa por los
  catálogos de **ambos** locales (los tests de i18n fallan si falta una clave o un placeholder
  en alguno de los dos).
- Los comentarios explican el *porqué* (una medición, un bug pasado), no el *qué*.
- Los value objects son dataclasses congeladas; los conjuntos cerrados de valores son `StrEnum`s.
- Las dependencias se inyectan por constructor; `container.py` es el único composition root.
- Siempre pasar `encoding="utf-8"` al leer o escribir texto.

## Configuración

Ver [configuration.md](configuration.md).

## Benchmarks

Ver `benchmarks/README.md`. El benchmark de calibración es el único que escribe
`src/mirag/resources/feature_gains.json`, el archivo que lee el feature gate.

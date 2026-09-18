# Dónde está cada cosa, y por qué

La clasificación **no** es por extensión ni por nombre: sale del grafo de imports real y de la
cadena transitiva de `server.py`. Un archivo está en producción si participa de una petición HTTP,
no si «parece» código de producción.

```
agente_backend/
├── *.py (30)              PRODUCCIÓN — la cadena de server.py
├── index.html             la pantalla
├── README.md · .gitignore · .env.example
├── conocimientos/ (22)    EL CORPUS — datos, no documentación
├── tests/ (21)            las suites + fixtures/
├── demos/ (2)             demos ejecutables a mano
├── benchmarks/ (5 + json) los bancos y sus datos
├── experimental/ (3)      existe, funciona, NO está en el camino
├── blockchain/            identidad Stellar 8004 — la ÚNICA con dependencias externas
├── docs/ (6)              cómo se usa Mirag
├── reports/ (13)          cómo llegamos hasta aquí
├── salida/ · artefactos/  salida de runtime (ignorados)
```

## Producción — raíz

Los 26 módulos de la cerradura de `server.py`, más tres que entran por la rama offline.

| grupo | módulos |
|---|---|
| entrada | `server.py`, `arquitecto.py` |
| orquestación | `pipeline.py`, `agent.py`, `estado.py`, `auditoria.py`, `traza.py` |
| recuperación | `recuperacion.py`, `hibrido.py`, `rag.py`, `plan.py`, `metadatos.py`, `suficiencia.py`, `obligaciones.py`, `grafo.py`, `vectores.py`, `simbolos.py` |
| ejecución y evidencia | `skills.py`, `rapido.py`, `sondas.py` |
| proyectos | `proyecto.py`, `generador.py`, `dependencias.py`, `verificacion_proyecto.py`, `empaquetado.py`, `artefactos.py` |
| configuración | `config.py` |
| modo offline | `demos.py`, `dobles.py`, `fixture_proyecto.py` — ver [RELOCATION_EXCEPTIONS.md](RELOCATION_EXCEPTIONS.md) |

**`grafo.py` y `vectores.py` no son experimentales**, aunque lo parezcan: `config.ESTADO_FLAGS`
los declara `CONECTADO` y `pipeline`/`hibrido` los importan. Hay un test que falla si alguien los
mueve a `experimental/`.

## `blockchain/`

La capa de identidad on-chain, y **la única carpeta del repositorio con una dependencia externa**
(`stellar-sdk`, declarada en su propio `pyproject.toml` y gestionada con `uv`).

Está aquí y no en la raíz porque la frontera es dura y comprobada:

- ningún módulo de producción importa `stellar_sdk` — `tests/test_arquitectura_repo.py`
- `import blockchain` **no** carga el SDK; entra solo cuando se pide hablar con la red
- `server.py` la importa **perezosamente** dentro del handler: sin el paquete, el servidor
  arranca igual y la ruta contesta `{"disponible": false, "motivo": …}`
- el socket vive en un solo archivo, `blockchain/stellar/client.py`
- la clave secreta vive en un solo archivo, `blockchain/wallet/claves.py`

Las 21 suites del núcleo siguen corriendo con el intérprete del sistema, sin el venv y sin red.
Detalle en [docs/blockchain.md](docs/blockchain.md).

```
blockchain/
├── pyproject.toml · uv.lock     la dependencia, declarada y fijada
├── config.py                    el candado (MIRAG_BLOCKCHAIN) y las redes
├── modelos.py · metadata.py     stdlib puro: el core puede leerlos
├── dobles.py                    respuestas fijas, para probar sin red
├── servicio.py                  junta identidad y wallet en un Estado
├── stellar/client.py            EL socket, y el SDK
├── identity/registro.py         register_with_uri · set_agent_wallet · verificar
└── wallet/claves.py             LA clave. No sale de aquí.
```

## `tests/`

21 suites, sin pytest: cada archivo es su propio runner con `✅/❌` y `sys.exit(1)`.

```bash
python3 tests/test_proyecto.py               # una
for f in tests/test_*.py; do python3 "$f"; done   # todas
```

`tests/fixtures/repo_ejemplo/` es un repo falso que usa `test_simbolos` para probar el indexador.

**La regla que sostiene esta carpeta**: una ruta que apunta a producción se deriva de **un módulo
de producción**, nunca de `__file__`. Cuando colgaban de `AQUI`, mover el test las dejaba mirando
una carpeta vacía y el test pasaba sin comprobar nada.

## `benchmarks/`

Los scripts (`eval.py`, `banco.py`, `banco_recuperacion.py`, `banco_proyectos.py`,
`calibracion.py`) y los `.json` que producen. **`ganancias.json` lo lee producción** —
`config.activar()` decide con él qué etapas se encienden, así que no se ignora ni se borra.

## `experimental/`

`cache.py`, `arbol.py`, `enrutador.py`. `config.ESTADO_FLAGS` los declara `EXPERIMENTAL`: existen,
tienen sus tests, y **producción no los importa**. Un test lo comprueba con AST.

## `docs/` vs `reports/`

| | pregunta que responde |
|---|---|
| `docs/` | **cómo se usa Mirag** — `PRODUCT_OVERVIEW`, `CURRENT_ARCHITECTURE`, `CURRENT_STATUS`, `DEMO`, `DEMO_CONTRACTS`, `EXPERIMENTAL_CAPABILITIES` |
| `reports/` | **cómo llegamos hasta aquí y qué se descubrió** — las auditorías y los 12 informes de fase |

No todo `.md` es documentación: `conocimientos/*.md` es el **corpus**, o sea datos que lee
`rag.py`, y `reports/ejemplo-salida.md` es una ejecución capturada.

## La dirección de dependencias

```
                      producción
                          ↑
        ┌────────┬────────┴────────┬──────────────┐
      tests    demos          benchmarks    experimental
```

Producción no conoce sus tests, sus demos ni sus bancos.
`tests/test_arquitectura_repo.py` lo comprueba con AST en cada corrida, y **declara la única
excepción** en vez de ignorarla.

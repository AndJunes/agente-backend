# Mirag

**Le das un problema. Mirag busca lo que sabe, propone una solución, la ejecuta, y te enseña
exactamente en qué se apoya para confiar en ella — y en qué no.**

Python de biblioteca estándar. **El núcleo no tiene ninguna dependencia externa** —los 30 módulos
de la raíz, verificado recorriendo su AST. La capa `blockchain/`, que vive fuera de esa cadena y
tiene su propio entorno, declara `stellar-sdk`; ver [docs/blockchain.md](docs/blockchain.md).

```bash
python3 server.py          # la pantalla: http://127.0.0.1:8000
docker compose up -d       # lo mismo, dentro de un contenedor sin privilegios
```

Con `MIRAG_OFFLINE=1` (el valor por defecto) hay tres demos preparadas y no cuesta nada. Para
respuestas reales, pon tu clave en `.env` (copia `.env.example`) y arranca con `MIRAG_OFFLINE=0`.

## Qué hace

```
Pregunta → Plan → Recuperación (3 índices) → Contexto → Modelo
        → Herramienta → Verificación → Evidencia → Respuesta
```

Y si le pides un proyecto entero, en vez de un archivo suelto:

```
Creá una API REST de libros con CRUD completo. Arquitectura por dominios.
        ↓
libros-api · 14 archivos · sus tests ejecutados · [ Descargar ZIP ]
```

## Lo que lo hace distinto

**El estado lo decide la ejecución, nunca el modelo.** Cuatro veredictos posibles:

| | |
|---|---|
| `verde` | hubo marcadores de test y todos pasaron |
| `rojo` | se ejecutó y falló |
| `sin evidencia` | terminó sin error y **no imprimió ni un marcador** — esto no es aprobar |
| `no ejecutado` | ni llegó a correr |

**Cada respuesta separa tres cosas** que casi todas las herramientas mezclan: lo que el modelo
*dice* (`MODEL CLAIM`), lo que la máquina *vio* (`OBSERVED`), y lo que queda *demostrado*
(`VERIFIED`). Si el modelo afirma que los tests pasan y no hay marcadores, sale un aviso encima y
su texto se deja entero para que lo juzgues.

**Si el corpus no cubre lo que preguntas, lo dice antes de responder.**

## Cómo está organizado

| | |
|---|---|
| **raíz** | los ~30 módulos de producción: `server.py`, `pipeline.py`, `recuperacion.py`, `skills.py`… |
| `conocimientos/` | el corpus: 19 cajas de backend en formato *knowledge item* |
| `tests/` | 21 suites, sin pytest — cada archivo es su propio runner |
| `demos/` | demos ejecutables a mano |
| `benchmarks/` | los bancos de medición y sus datos |
| `experimental/` | existe, funciona, **no está en el camino de producción** |
| `docs/` | cómo se usa Mirag |
| `blockchain/` | identidad Stellar 8004 — la única carpeta con dependencias externas |
| `reports/` | cómo llegamos hasta aquí, y qué se descubrió por el camino |

Detalle en [REPOSITORY_STRUCTURE.md](REPOSITORY_STRUCTURE.md), lo que se queda donde está y por qué
en [RELOCATION_EXCEPTIONS.md](RELOCATION_EXCEPTIONS.md), y cómo se llegó a esta forma —con los tres
problemas que la mudanza destapó— en
[reports/REPOSITORY_CLEANUP_REPORT.md](reports/REPOSITORY_CLEANUP_REPORT.md).

## Correrlo

```bash
python3 server.py                      # la pantalla
python3 demos.py todas                 # las 4 demos canónicas, con el candado puesto, $0
python3 demos/demo_proyecto.py         # genera un proyecto entero y lo empaqueta
python3 benchmarks/eval.py             # mide la recuperación
python3 benchmarks/banco_proyectos.py 10   # cuántos proyectos de diez salen verificados
for f in tests/test_*.py; do python3 "$f"; done   # la suite, sin llamar al modelo

# la identidad on-chain del Backend Agent (Stellar Testnet, $0)
MIRAG_BLOCKCHAIN=testnet uv run --project blockchain python demos/blockchain_agent_demo.py
```

Si sale `CERTIFICATE_VERIFY_FAILED`, tu Python no tiene los certificados raíz. Arreglo permanente:
`/Applications/Python 3.14/Install Certificates.command`. Atajo: `/opt/homebrew/bin/python3`.

## En un servidor

```bash
docker compose up -d --build       # http://127.0.0.1:8000, y solo ahí
```

Mirag ejecuta código que escribe un modelo y **no tiene autenticación**: el contenedor no
elimina eso, lo acota —usuario sin privilegios, su propio código en solo lectura, `/tmp` en
RAM, sin capabilities y con techo de CPU, memoria y procesos. El puerto se publica contra
`127.0.0.1` a propósito; para llegar desde fuera, túnel SSH o un proxy que autentique.

Cómo se hace, qué protege cada pieza y **qué sigue sin estar resuelto**, en
[docs/DESPLIEGUE.md](docs/DESPLIEGUE.md).

## El tope de gasto

Cada llamada trae el coste real de OpenRouter, así que el agente **corta antes de pasarse**, no
después de la factura:

```bash
LIMITE_USD=0.20 MIRAG_OFFLINE=0 python3 server.py
```

Por defecto, 0,50 $ por petición.

## Lo que no está demostrado

La generación de proyectos funciona de punta a punta —genera, ejecuta, repara, empaqueta, comprueba
la integridad del ZIP y lo sirve—, pero **medido sobre 10 corridas con modelo real, cero llegaron a
`VERIFICADO`**: fallan por sintaxis, por imports o por sus propios tests. Lo demostrado es que la
máquina no miente cuando eso pasa. Los números están en
[reports/PROJECT_BENCHMARK_REPORT.md](reports/PROJECT_BENCHMARK_REPORT.md).

Más límites conocidos, todos medidos, en [docs/PRODUCT_OVERVIEW.md](docs/PRODUCT_OVERVIEW.md).

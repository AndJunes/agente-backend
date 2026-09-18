# Mirag

**Le das un problema. Mirag busca lo que sabe, propone una solución, y te enseña exactamente
en qué se apoya para confiar en ella — y en qué no.**

Genera el código y sus casos de test, y **no los ejecuta**: eso será trabajo del agente de QA.
Lo que no cambia es lo de siempre —que no se afirma nada que no se haya observado— y ahora eso
significa decir `no ejecutado` en vez de fingir un aprobado.

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
libros-api · 14 archivos · con sus tests, sin ejecutar · [ Descargar ZIP ]
```

## Lo que lo hace distinto

**El estado lo decide la ejecución, nunca el modelo.** Cuatro veredictos posibles, y hoy el
que sale en producción es siempre el tercero, porque la ejecución está apagada
(`MIRAG_EJECUCION=off`). La maquinaria sigue entera y la heredará QA; las demos la encienden
para poder enseñarla:

| | |
|---|---|
| `verde` | hubo marcadores de test y todos pasaron |
| `rojo` | se ejecutó y falló |
| `sin evidencia` | terminó sin error y **no imprimió ni un marcador** — esto no es aprobar |
| `no ejecutado` | ni llegó a correr — **el de hoy**, y no es un suspenso: es que nadie ha mirado |

Lo que sí se comprueba sin ejecutar nada, y caza fallos de verdad: estructura, sintaxis
(`ast.parse`, en el propio proceso) e importaciones.

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

Al dejar de ejecutar código generado, desapareció el riesgo grande de tenerlo en un servidor.
Lo que queda se acota igual: usuario sin privilegios, su propio código en solo lectura, `/tmp`
en RAM, sin capabilities y con techo de CPU, memoria y procesos. El puerto se publica contra
`127.0.0.1` a propósito, y `MIRAG_TOKEN` cierra la puerta a quien no traiga el secreto.

Hay dos imágenes desde el mismo `Dockerfile`: `--target base` sin una sola dependencia, y
`--target identidad` con `stellar-sdk` para la identidad on-chain —que funciona **sin** que la
semilla entre en el contenedor.

Cómo se hace, qué protege cada pieza y **qué sigue sin estar resuelto**, en
[docs/DESPLIEGUE.md](docs/DESPLIEGUE.md). El contrato HTTP para consumirlo desde otra
aplicación —eventos, esquema del JSON, token y caducidad de los artefactos— en
[docs/API.md](docs/API.md).

## El tope de gasto

Cada llamada trae el coste real de OpenRouter, así que el agente **corta antes de pasarse**, no
después de la factura:

```bash
LIMITE_USD=0.20 MIRAG_OFFLINE=0 python3 server.py
```

Por defecto, 0,50 $ por petición.

## Lo que no está demostrado

La generación de proyectos funciona de punta a punta —genera, empaqueta, comprueba la integridad
del ZIP y lo sirve—, pero cuando **sí** se ejecutaba, medido sobre 10 corridas con modelo real,
**cero llegaron a `VERIFICADO`**: fallaban por sintaxis, por imports o por sus propios tests. Lo
demostrado es que la máquina no miente cuando eso pasa. Ese número es también el motivo de que
exista un agente de QA aparte: la verificación necesita más que un intento de reparación. Los números están en
[reports/PROJECT_BENCHMARK_REPORT.md](reports/PROJECT_BENCHMARK_REPORT.md).

Más límites conocidos, todos medidos, en [docs/PRODUCT_OVERVIEW.md](docs/PRODUCT_OVERVIEW.md).

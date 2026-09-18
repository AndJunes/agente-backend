# Lo que no se movió, y por qué

Ninguna excepción está escondida. Cada una tiene un motivo medible y, donde se puede, un test que
la vigila.

## 1. Los 30 módulos de producción se quedan en la raíz

**Motivo medido**: 264 sentencias de import por nombre desnudo (`import rag`, `import skills`) y
**14 módulos que derivan rutas de su propia ubicación** — `conocimientos/`, `index.html`,
`trazas*.jsonl`, `salida/`, `artefactos/`, `benchmarks/ganancias.json`.

Moverlos a `app/` no es una mudanza: es reescribir 264 imports, reanclar 14 rutas y cambiar todos
los comandos documentados. Cada ruta reanclada es una ocasión de romper algo **en silencio** —
`config._ganancias()` se traga el `OSError` y apaga las etapas `auto`; `simbolos.indexar` devuelve
`[]` en vez de lanzar.

Sacar todo lo demás ya lleva el root de **91 a 37 entradas**, que es la mayor parte del beneficio
con una fracción del riesgo.

## 2. `demos.py`, `dobles.py` y `fixture_proyecto.py` se quedan en producción

**No pueden ir a `demos/`**: `server.py:374`, dentro de `do_POST` y en la rama `if agent.OFFLINE`
—que es **el modo por defecto**— hace:

```python
import dobles, demos
demo, guion = demos.guion_para(pregunta)
with dobles.usar(guion):
    e = pipeline.ejecutar(pregunta, al_avanzar=emitir)
```

Y `dobles` importa `fixture_proyecto`. Los tres están en el árbol de producción. Moverlos rompe el
arranque con el candado puesto.

Es una inversión de dependencia real y **está declarada**, con su motivo, en
`tests/test_arquitectura_repo.py`. El test también falla si una excepción **deja de ocurrir**, para
que la lista no acumule excusas muertas.

Merece arreglarse algún día —los guiones de demo son datos, no lógica de servidor— pero eso es un
cambio de diseño, no una reorganización de carpetas, y no entra aquí.

## 3. `grafo.py` y `vectores.py` no van a `experimental/`

Lo parecen y no lo son: `config.ESTADO_FLAGS` los declara `CONECTADO`, `pipeline.py:214` importa
`grafo` y `hibrido.py:106` importa `vectores`. Que `VECTOR_SIGNAL` esté apagado **por medición** no
lo convierte en experimental — el código es alcanzable.

Hay un test (`lo_conectado_sigue_en_la_raiz`) que falla si alguien los mueve creyendo lo contrario.

## 4. `conocimientos/` se queda donde está

`rag.py:22` lo ancla a su propio directorio. Y no es documentación: es el **corpus**, los datos que
el sistema recupera. Mezclarlo con `docs/` sería clasificar por extensión, que es justamente lo que
esta reorganización no hace.

## 5. `salida/` y `artefactos/` se quedan en la raíz

Producción escribe ahí en runtime (`rapido.py:189`, `artefactos.py:33`) derivando la ruta de su
propia ubicación. Van al `.gitignore`, no a otra carpeta.

## 6. `benchmarks/*.json` no se ignoran

Parecen datos generados y **`ganancias.json` lo lee producción**: `config.activar()` decide con él
qué etapas se encienden. Ignorarlo dejaría el sistema sin su política de activación.

# Limpieza y reorganización del repositorio

**Qué se hizo**: sacar de la raíz todo lo que no participa de una petición HTTP, sin tocar un solo
import de producción. **Coste: $0** — ninguna llamada real al modelo en toda la fase.

La clasificación salió del **grafo de imports**, no de la extensión ni del nombre. El criterio
operativo fue uno solo:

> Un archivo es producción si está en la cerradura transitiva de `server.py`.

Y al terminar ese criterio se cumple exactamente: la raíz tiene **30 módulos** y los 30 están en la
cerradura. **Cero huérfanos**. Eso ya no es una afirmación de este informe, es un test
([`tests/test_arquitectura_repo.py`](../tests/test_arquitectura_repo.py)).

---

## 1 · El resultado

| | antes | después |
|---|---|---|
| entradas en la raíz | 91 | **49** (43 versionables; 6 son salida de runtime, ignoradas) |
| `.py` en la raíz | 60 | **30** — exactamente la cerradura de `server.py` |
| `.md` en la raíz | 20 | **3** — README + los dos que describen el repositorio |
| carpetas clasificadas | 2 | 9 |
| suite | 444 casos | **456 casos · 0 rojas · 21 suites** |

---

## 2 · Qué se movió

| destino | qué | cuántos |
|---|---|---|
| `tests/` | las suites | 20 movidas + 1 nueva |
| `tests/fixtures/repo_ejemplo/` | `pruebas/app/` — el repo falso que indexa `test_simbolos` | 4 |
| `demos/` | `demo_proyecto.py`, `prueba_bucle.py` | 2 |
| `benchmarks/` | `banco.py`, `banco_proyectos.py`, `banco_recuperacion.py`, `calibracion.py`, `eval.py` | 5 `.py` (+ los 9 `.json` que ya estaban) |
| `experimental/` | `cache.py`, `arbol.py`, `enrutador.py` | 3 |
| `docs/` | lo que explica **qué es** Mirag | 6 |
| `reports/` | lo que explica **cómo llegamos** aquí | 13 (14 con este) |

**Borrado**: `index.html.bak` (18 KB, obsoleto, ya señalado en la auditoría previa) y los
`__pycache__/`.

**Nada se escondió.** No hay ningún `local/`, ni ninguna carpeta entera metida en `.gitignore` para
que la raíz parezca limpia. Lo que el `.gitignore` cubre es exclusivamente salida de runtime
(`salida/`, `artefactos/`, `trazas*.jsonl`, `__pycache__/`, `*.log`, `*.bak`) y el secreto (`.env`).
`conocimientos/`, `benchmarks/*.json`, `tests/fixtures/`, `docs/` y `reports/` **se versionan**, y el
propio `.gitignore` lo dice por escrito, con el motivo de cada uno.

---

## 3 · Imports y comandos reparados

**Producción: 0 imports tocados.** Los 30 módulos siguen en la raíz precisamente para que eso sea
cierto; moverlos exigía reescribir 264 imports, que es justo lo que el plan prohibía.

Lo que sí cambió, todo fuera de producción:

| reparación | dónde | por qué |
|---|---|---|
| arranque de rutas de 3 líneas | 31 archivos | `python3 tests/x.py` pone `tests/` en `sys.path[0]`, no la raíz |
| `sys.path` con `experimental/` y `benchmarks/` | los que importan `cache` o `eval` por nombre desnudo | son carpetas, no paquetes |
| `cwd=AQUI` → `cwd=_RAIZ_PROD` | 5 llamadas a `subprocess` | lanzaban el intérprete desde `tests/`, donde no hay producción que importar |
| `AQUI/"index.html"` → anclado a `server.py` | 3 tests | la página está en la raíz |
| `AQUI/"benchmarks"` → `config.GANANCIAS.parent` | `test_banderas` | el JSON lo lee producción |

**Comandos actualizados** en README, `docs/DEMO.md` y las cabeceras de cada módulo:
`python3 test_x.py` → `python3 tests/test_x.py`, `python3 banco.py` → `python3 benchmarks/banco.py`,
y equivalentes para `demos/` y `experimental/`.

---

## 4 · Las seis roturas silenciosas

El mapa previo localizó seis tests que **habrían seguido pasando sin comprobar nada** al moverse.
Ninguna se descubre ejecutando la suite: el síntoma de todas es el verde.

| # | qué pasaba | qué se hizo |
|---|---|---|
| 1 | `test_proyecto` escaneaba `tests/` en vez de producción: `assert not decisiones` pasaba sin mirar un archivo | ancla a `Path(rapido.__file__).parent` + cota inferior de archivos |
| 2 | 4 canarios vigilaban `tests/salida/`, que nadie toca | anclados al `salida/` real de producción |
| 3 | dos tests leían un `trazas_noche.jsonl` que producción nunca escribe | anclados a `traza.ARCHIVO.parent` |
| 4 | `test_calibracion` hacía `touch()` sobre un `simbolos.py` **que creaba vacío** | `Path(simbolos.__file__).touch()` |
| 5 | `test_evidencia` lanzaba un subproceso y no miraba el `returncode` | comprobado |
| 6 | `test_resiliencia` parcheaba `__import__` por nombre literal | documentado; el nombre se lee del módulo |

La regla que las cierra a todas, y que ahora se aplica en 9 tests:

> Una ruta que apunta a producción se deriva de **un módulo de producción**, nunca de `__file__`.

Y su complemento, en todo escaneo por patrón: **una cota inferior**, para que un glob que deja de
encontrar cosas falle en vez de pasar en vacío.

---

## 5 · Problemas encontrados

### 5.1 Un bug de producción: `simbolos.py` clasificaba por ruta absoluta

`_es_archivo_de_test` miraba **todos** los componentes de la ruta absoluta. Cualquier proyecto
guardado bajo un directorio llamado `tests/` —que es exactamente donde acabó el fixture— tenía
**todos** sus símbolos marcados como test: las 14 funciones del fixture pasaban a contarse como 19
tests. Esto no lo causó la mudanza; la mudanza lo destapó.

```python
ruta = Path(ruta)
return (ruta.stem.startswith("test_") or ruta.stem.endswith("_test")
        or any(p in ("test", "tests") for p in ruta.parts[:-1]))
...
es_test = _es_archivo_de_test(rel)      # relativa a la raiz, no absoluta
```

Arreglado en producción, con un test que falla si vuelve
(`la clasificacion no depende de donde este guardado el proyecto`).

### 5.2 Los bancos escribían en `benchmarks/benchmarks/`

Los cuatro scripts que se mudaron a `benchmarks/` seguían calculando su destino como
`Path(__file__).parent / "benchmarks"` — correcto cuando vivían en la raíz, y ahora una carpeta más
abajo. Ya había un `proyectos.json` escrito ahí dentro cuando se encontró.

**Nada fallaba.** El banco corría, imprimía su resumen y decía «escrito en proyectos.json». Solo que
`config.activar()` seguía leyendo el `ganancias.json` viejo: la medición dejaba de llegar a quien
decide. Es la misma forma de error que este proyecto lleva nueve fases persiguiendo — algo se
afirma y nada lo observa — solo que aquí el que afirmaba era yo al mover los archivos.

Arreglado anclando el que escribe al que lee:

```python
DESTINO = config.GANANCIAS.parent      # calibracion.py, banco_recuperacion.py
```

Y con un test que falla si alguien vuelve a colgar `"benchmarks"` de `__file__`.

### 5.3 Mi propio test pasaba en vacío

El caso `la raiz es exactamente la cerradura de server` comparaba dos conjuntos que **encogen a la
vez**: al sacar `skills.py` de la raíz, el `skills` que importa `pipeline` dejaba de parecer local,
el recorrido lo saltaba, y el test pasaba igual. Verificado sacando `skills.py` de verdad: **pasaba
en verde con un módulo de producción fuera**.

Corregido con la comprobación en el otro sentido: Mirag no tiene ninguna dependencia externa, así
que un import que no es stdlib y no está en la raíz ni en las carpetas clasificadas es un módulo que
falta. Repetida la prueba del vacío, ahora falla:

```
❌ la raiz es exactamente la cerradura de server  → produccion importa modulos que no estan
```

### 5.4 Dos errores de medición míos, por concurrencia

Dos rojas y un fallo de canario resultaron ser **ruido de mi propia instrumentación**: corrí
comandos que escribían en `salida/` y `trazas_noche.jsonl` mientras una suite estaba en marcha.
Comprobado ejecutando los tests sospechosos en aislamiento, donde pasan. La suite que se reporta
arriba se corrió **en secuencia y sin nada más tocando el repositorio**.

---

## 6 · El canario en `salida/`: lo que se puede y lo que no se puede afirmar

El plan pedía: «se pone un archivo en `salida/`, se corre la suite entera, sigue ahí».
**Ese enunciado no es satisfacible, y es correcto que no lo sea.**

`salida/` es la carpeta de entrega, y `rapido.guardar` la vacía antes de escribir, a propósito y
documentado («no mezclar con la ejecución anterior»). Cualquier test que ejercite de verdad el
camino de entrega la vacía. Exigir que un canario sobreviva a la suite entera sería exigir que los
tests no prueben la entrega.

Lo que sí es exigible, y es lo que protegen los canarios que ya existen, es más estrecho y más útil:

- `el banco no escribe en la carpeta de produccion` — diez ejecuciones del banco no se llevan por
  delante la última entrega del usuario (`tests/test_cimientos.py`).
- `las demos no escriben en la carpeta de produccion` — `demos.correr()` con su `guardar=False` por
  defecto no toca `salida/` (`tests/test_demos_contratos.py`).

Los dos apuntan ahora al `salida/` **real** de producción; antes de la mudanza vigilaban una carpeta
que nadie tocaba. Esa era la rotura silenciosa nº 2, y era la más grave de las seis: el guardián del
borrado destructivo fallaba abierto.

---

## 7 · Verificación

| # | comprobación | resultado |
|---|---|---|
| 1 | `python3 -c "import server"` desde la raíz | ✅ arranca la cadena de 30 módulos |
| 2 | suite completa, secuencial, sin nada más corriendo | ✅ **456 casos · 0 rojas · 21 suites** |
| 3 | los `subprocess` que importan producción desde otro cwd | ✅ dentro de la suite |
| 4 | las 4 demos canónicas | ✅ **4/4 CUMPLE EL CONTRATO**, $0 |
| 4b | `demos/demo_proyecto.py` | ✅ **VERIFICADO** · 14 archivos · 16/16 marcadores · ZIP de 8.408 bytes · 13 comprobaciones de integridad · 2,6 s · $0 |
| 5 | el servidor: una consulta y una descarga de extremo a extremo | ✅ `POST /chat` → 38 eventos → **VERIFICADO** → `GET /descarga?id=…` → **HTTP 200, 8.408 bytes**, ZIP de 15 entradas, sin corrupción, raíz única |
| 6 | 13 rutas internas, por GET **y** por HEAD | ✅ **13/13 → 404**, incluidas `tests/`, `docs/`, `reports/`, `benchmarks/`, `experimental/`, `demos/` y `.gitignore` |
| 7 | canario en `salida/` | ⚠️ ver §6 — el enunciado del plan se reemplazó por el invariante correcto |
| 8 | prueba del vacío: sacar un módulo de producción | ✅ y encontró que mi test pasaba en vacío (§5.3) |

---

## 8 · Excepciones

Documentadas en [RELOCATION_EXCEPTIONS.md](../RELOCATION_EXCEPTIONS.md) y **comprobadas**, no
prometidas: `test_arquitectura_repo` las lleva en una tabla con el motivo escrito, y falla si alguna
deja de ocurrir (una excepción muerta es una excusa que sobra) o si aparece una nueva.

| excepción | motivo medible |
|---|---|
| `demos.py`, `dobles.py`, `fixture_proyecto.py` se quedan en la raíz | `server.py:374` los importa en la rama `if agent.OFFLINE`, que es el modo por defecto |
| `pipeline` → `dobles` | solo bajo `__main__`, para el self-test del módulo |
| los 30 módulos de producción se quedan donde están | moverlos exigía reescribir 264 imports y reanclar 14 rutas |
| `grafo.py` y `vectores.py` **no** van a `experimental/` | `config.ESTADO_FLAGS` los declara `CONECTADO` y `pipeline`/`hibrido` los importan |

---

## 9 · Lo que no se hizo

No se refactorizó producción, no se renombró ningún módulo, no se cambió ninguna API pública, no se
tocó la configuración de retrieval y no se ejecutó `git init`. El `.gitignore` queda preparatorio:
correcto para el día en que el repositorio se inicialice, que es el día en que `.env` pasaría a ser
un riesgo de verdad.

---

## 10 · El árbol final

```
agente_backend/   (49 entradas)
├── 30 módulos de PRODUCCIÓN  ── la cerradura transitiva de server.py, sin huérfanos
│     agent           arquitecto      artefactos      auditoria       config
│     demos           dependencias    dobles          empaquetado     estado
│     fixture_proyecto generador      grafo           hibrido         metadatos
│     obligaciones    pipeline        plan            proyecto        rag
│     rapido          recuperacion    server          simbolos        skills
│     sondas          suficiencia     traza           vectores        verificacion_proyecto
├── index.html                      la pantalla
├── README.md · REPOSITORY_STRUCTURE.md · RELOCATION_EXCEPTIONS.md
├── .gitignore · .env.example       (.env NO se versiona)
├── conocimientos/   (22)           el corpus que recupera rag.py
├── tests/           (25)           las 21 suites + fixtures/repo_ejemplo/
├── demos/            (2)           ejecutables a mano
├── benchmarks/      (14)           los bancos y sus datos de medición
├── experimental/     (3)           existe, funciona, NO está en el camino
├── docs/             (6)           cómo se usa Mirag
├── reports/         (14)           cómo llegamos hasta aquí
└── salida/ · artefactos/ · trazas*.jsonl · eval_cache.json    runtime (ignorados)
```

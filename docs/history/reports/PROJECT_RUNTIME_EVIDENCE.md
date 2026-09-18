# Mirag — Evidencia de ejecución

Comandos ejecutados durante la auditoría del 15/09/2026 y su salida observada, sin editar.
Intérprete: `/opt/homebrew/bin/python3` (3.14.6). `MIRAG_OFFLINE` sin poner = candado puesto,
salvo donde se indique.

---

## 0. Modificaciones hechas por la auditoría

La auditoría fue read-only sobre el código. Tres efectos secundarios, todos reportados:

| qué | por qué | reversible |
|---|---|---|
| `rm -rf salida/__pycache__` | **necesario**: bloqueaba `test_full_pipeline.py` y cualquier tarea de código (ver §4) | sí, se regenera al ejecutar el código entregado |
| `salida/` reescrito | los 10 casos manuales y los tests generan entregas | sí |
| `trazas_noche.jsonl` creció | `pipeline.ejecutar(guardar=True)` en los tests | sí, es un log de append |

**No se modificó ningún `.py`, ni `index.html`, ni el corpus, ni la configuración.**

---

## 1. Inventario

```
$ for f in *.py; do wc -l $f; done | sort -rn | head -5
   440 test_vectores.py
   434 rapido.py
   417 cache.py
   383 vectores.py
   380 test_cache.py

$ ls requirements.txt pyproject.toml setup.py Pipfile package.json
  NINGUNA (no existe ningun archivo de dependencias)

$ grep -h "^import \|^from " *.py | sed 's/...//' | sort -u
agent arbol arquitecto ast auditoria cache calculator codecs collections config
contextlib datetime dobles enrutador estado eval functools grafo hashlib hibrido
http.server json math metadatos os pathlib pipeline plan rag rapido re shlex shutil
simbolos skills statistics subprocess suficiencia sys tempfile threading time traza
typing unicodedata urllib.error urllib.request vectores zlib
```

**Conclusión:** 36 `.py`, 8.161 líneas. Todo lo importado es stdlib o local. Cero terceros.

---

## 2. Tests — los 11 archivos, con exit code

```
$ for f in test_*.py; do python3 $f; echo "exit=$?"; done

  exit=0   test_cimientos.py        21 casos · TODO OK
  exit=0   test_plan.py             22 casos · TODO OK
  exit=0   test_metadatos.py        19 casos · TODO OK
  exit=0   test_vectores.py         29 casos · TODO OK
  exit=0   test_simbolos.py         18 casos · TODO OK
  exit=0   test_cache.py            24 casos · TODO OK
  exit=0   test_grafo_arbol.py      23 casos · TODO OK
  exit=0   test_enrutador.py        13 casos · TODO OK
  exit=0   test_auditoria.py        15 casos · TODO OK
  exit=0   test_resiliencia.py      24 casos · TODO OK
  exit=1   test_full_pipeline.py    16 casos · 1 FALLOS
          ❌ la traza se escribe aparte  → PermissionError: [Errno 1]
             Operation not permitted: 'salida/__pycache__'
```

**224 casos. 1 suite en rojo**, y el fallo es un bug real del producto, no del test.

Suites heredadas:
```
$ python3 prueba_bucle.py      → TODO OK (5 escenarios, node real)
$ python3 estado.py --probar   → TODO OK · 7 preguntas resueltas con 0 llamadas
$ python3 auditoria.py         → 6 casos · TODO OK
$ python3 suficiencia.py       → 7/7 TODO OK
$ python3 eval.py              → OFFLINE (0 llamadas) · facil 27/31 R@1 · duro MRR 0.562
```

---

## 3. PRUEBA DECISIVA — ¿el reranker cambia lo que ve el modelo?

Se captura el `messages[-1]["content"]` real que recibe `agent.llm`, con el reranker forzado ON y
forzado OFF, misma pregunta.

```python
class Espia(dobles.Doble):
    def __call__(self, messages, tools=None):
        capturado.setdefault("ctx", messages[-1]["content"])
        return super().__call__(messages, tools)
```

```
  contexto con reranker ON : 8,535 caracteres · sha 00cb0796ccc4dfb6
  contexto con reranker OFF: 8,535 caracteres · sha 00cb0796ccc4dfb6

  ¿IDENTICOS? SI — el reranker NO afecta a lo que ve el modelo

  top-5 de hibrido (lo que se mide en el banco):
    ['Carritos, pedidos e inventario', 'Cómo se prueba todo esto',
     'Preguntas de entrevista y trade-offs']
```

**Conclusión:** `hibrido.recuperar()` — la función que `banco_recuperacion.py` mide y que
`benchmarks/ganancias.json` gobierna — no produce el contexto del modelo. El reranker, única etapa
condicional encendida, mejora un ranking que solo consume `suficiencia.evaluar`.

---

## 4. BUG CRÍTICO — `guardar()` se rompe al ejecutar lo que entrega

```
$ python3 -c "import rapido; rapido.guardar({'archivos':{'x.py':'print(1)'}, ...})"
   ROTO: PermissionError: [Errno 1] Operation not permitted: 'salida/__pycache__'
```

Reproducción limpia en un tempdir, sin depender del estado actual del repo:

```
  1. guardar() → ['COMO_EJECUTAR.txt', 'm.py', 'test_m.py']
  2. el usuario ejecuta lo que dice COMO_EJECUTAR.txt → [..., '__pycache__', ...]
  3. siguiente tarea: ROTO → PermissionError: Operation not permitted: '.../__pycache__'
```

Causa: `rapido.py:196-197` usa `viejo.unlink()`, que no borra directorios.

Cómo le llega al usuario:
```
$ python3 -c "import dobles, pipeline; ... pipeline.ejecutar(..., guardar=True)"
   EXCEPCION SIN CAPTURAR en pipeline.ejecutar:
   PermissionError: [Errno 1] Operation not permitted: 'salida/__pycache__'
```
`server.py:183` la convierte en `Error: PermissionError: ...` y descarta la respuesta entera —
**después** de haber pagado la llamada y verificado el código.

Llamadores afectados: `server.py:26`, `server.py:145`, `server.py:171`, `pipeline.py:279`,
`rapido.py:422`.

### Ciclo cerrado, reproducido al final de la auditoría

Tras borrar `salida/__pycache__`, `test_full_pipeline.py` vuelve a pasar (16 casos · TODO OK).
Después se ejecuta el código entregado **exactamente como indica el propio `COMO_EJECUTAR.txt`**:

```
$ head -1 salida/COMO_EJECUTAR.txt
  python3 test_calculator.py

$ cd salida && python3 test_calculator.py
  TEST:operacion_invalida:PASS
  === RESUMEN === 6 PASADOS, 0 FALLIDOS        ← el código entregado es correcto

$ ls salida/
  COMO_EJECUTAR.txt  __pycache__  calculator.py  test_calculator.py

$ python3 test_full_pipeline.py
  ❌ la traza se escribe aparte → PermissionError: 'salida/__pycache__'
  16 casos · 1 FALLOS
```

El bucle es cerrado y reincidente: entregar → ejecutar como se indica → romper. Una corrección
manual (`rm -rf salida/__pycache__`) dura hasta la siguiente vez que el usuario haga lo que se le
dice que haga.

*(Nota de método: mi primer intento de reproducir esto no probó nada — importé un módulo que ya
no existía, el import falló en silencio y no se creó `__pycache__`. La reproducción válida es la
de arriba.)*

---

## 5. SEGURIDAD — los dos CRÍTICOS, verificados contra el servidor en marcha

```
$ curl -s -o /dev/null -w "%{http_code} %{size_download}" http://127.0.0.1:8000/.env
  200 93

$ curl -s http://127.0.0.1:8000/.env | sed 's/=.*/=<REDACTADO>/'
  OPENROUTER_API_KEY=<REDACTADO>

$ grep -n 'ThreadingHTTPServer(' server.py
  198:    ThreadingHTTPServer(("", 8000), Handler).serve_forever()

$ python3 -c "import socket; s=socket.socket(); print(s.connect_ex(('0.0.0.0',8000)))"
  conexion a 0.0.0.0:8000 → ACEPTA (escucha en todas las interfaces)

$ for f in trazas.jsonl index.html.bak eval_cache.json; do curl ... ; done
  /trazas.jsonl    → HTTP 200 (5802 bytes)
  /index.html.bak  → HTTP 200 (18758 bytes)
  /eval_cache.json → HTTP 200 (2028 bytes)
```

```
$ grep -n "def calcular" -A 2 skills.py
  144:def calcular(expresion: str) -> str:
  145-    return str(eval(expresion))  # demo local; en produccion nunca uses eval
```

**El valor de la clave no se leyó ni se imprimió en ningún momento**; solo se comprobó el código
HTTP, el tamaño y el nombre de la variable.

---

## 6. Veredicto del ejecutor — 6 casos

```
$ python3 -c "import skills; ..."
  script vacio           sin_evidencia  SIN EVIDENCIA: el comando termino sin error pero...
  marcadores ok          verde          TESTS EN VERDE · 2 de 2 marcadores
  FAIL con exit 0        rojo           FALLO: 1 de 2 marcadores fallaron
  crash                  rojo           FALLO (exit 1)
  interprete prohibido   no_ejecutado   NO EJECUTADO: solo se permite ejecutar node, python3
  timeout                no_ejecutado   NO EJECUTADO: TIMEOUT, no termino en 30s
```

---

## 7. Los 10 casos manuales (offline, dobles, $0.00)

```
1. Pregunta conceptual          1 llamada · 43.8 ms  · cubierto
   bm25=ejecutado vector=omitido reranker=ejecutado simbolos=omitido grafo=omitido

2. Conocimiento del corpus      1 llamada · 25.0 ms  · cubierto
   respuesta: 'Un indice de PostgreSQL es una estructura...'   ← FIXTURE, no el corpus

3. Generacion de codigo         1 llamada · 124.0 ms · evidencia: {'verificado': 3}

4. Codigo + verificacion fallida 2 llamadas · 210.0 ms · verificacion=error
   evidencia: {'refutado': 1}

5. Tool failure (bash)          2 llamadas · 92.4 ms · verificacion=error
   evidencia: {'sin verificar': 1}

6. Retrieval insuficiente       1 llamada · 27.1 ms · suficiencia=ausente
   'El corpus no cubre webrtc: no aparece en ninguna de las 19 cajas.'

7. Multi-hop                    1 llamada · 28.9 ms · suficiencia=mencionado · grafo=omitido

8. Requiere simbolos            1 llamada · 186.4 ms · simbolos=ejecutado

9. Contexto enorme (56k chars)  1 llamada · 54.6 ms · no revienta

10. Respuesta malformada        1 llamada · 15.9 ms · entrega=error, no revienta
```

**Caso 2 es el hallazgo:** con el candado puesto, cualquier pregunta que no contenga
`calculator|calculadora|calculate(` recibe el párrafo fijo de `dobles.py:63`, sea cual sea la
pregunta. La UI lo declara como simulado, pero es el camino por defecto del servidor.

---

## 8. Observabilidad — campos realmente persistidos

```
$ python3 -c "import json; print(list(json.loads(open('trazas_noche.jsonl').readlines()[-1])))"
  cuando, version, tarea, modo, estado, llamadas, decision_simulada, tokens, coste_usd,
  segundos, tokens_contexto, cajas, arreglado, propiedades, exito_verificado,
  exito_en_simulacion, valor
```

No aparecen: filtros, métodos de retrieval, conteos de candidatos, chunks elegidos, reranker,
graph, symbols, cache, fallbacks, ruta de modelo. Esos existen como `Paso` en memoria y se emiten
por SSE, pero **no se guardan**.

---

## 9. Contrato de eventos backend ↔ UI

```
$ grep -o '"tipo": "[a-z]*"' *.py | sort -u
  agent.py: pensamiento, skill
  arquitecto.py: fase, gasto, pensamiento
  server.py: fase, fin, paso, pensamiento, skill

$ grep -o "ev.tipo === '[a-z]*'" index.html | sort -u
  fase, fin, gasto, paso, pensamiento
```

Los seis tipos coinciden. **Sin discrepancia de contrato**; la discrepancia es semántica (§3).

---

## 10. Coste y latencia reales medidos hoy

```
$ python3 -c "... trazas_noche.jsonl, filas con decision_simulada=False"
  ejecuciones con modelo real: 3 de 9
    1 llamada  ·  4,854 tokens · $0.0065 ·  6.5s · sin_codigo
    1 llamada  ·  7,218 tokens · $0.0117 · 27.2s · verde
    2 llamadas · 13,628 tokens · $0.0311 · 34.9s · rojo
```

Pipeline sin LLM: P50 31.9 ms · P95 167.7 ms. Retrieval Stack A: 2.33 ms mediana.
**Stack B — el que alimenta al modelo — no está medido por ningún benchmark.**

---

## 11. Qué NO se pudo verificar

| | motivo |
|---|---|
| `banco.py` a nivel agente | cuesta ~$1 en llamadas reales; no se ejecutó |
| Modo `arquitecto` de punta a punta | ~9-55 llamadas; solo se probó su orquestación con LLM falso |
| `plan.needs_symbols` puesto a `True` por un modelo real | depende de la salida del modelo; con dobles nunca ocurre por esa vía |
| `VectorOpenRouter` contra el endpoint real | nunca se ha ejecutado; `embeddings/` no existe |
| `skills.hora_actual` | registrada, nunca invocada en ninguna prueba |
| Si `trazas.jsonl` lo lee alguien fuera del proyecto | dentro del directorio, cero lectores salvo `banco.py` |

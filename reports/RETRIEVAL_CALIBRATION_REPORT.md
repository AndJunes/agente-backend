# Fase 3 — Calibración del retrieval real

**Coste: $0.0753 de un techo de $2.00.** Seis consultas con modelo real; todo lo demás offline.
Todas las cifras salen de `recuperacion.recuperar()`, la misma función que usa producción.

---

## Baseline

`BM25 + tres índices`, sin reranker, vector, graph, tree ni cache. Es el nuevo punto de
comparación: los números de ayer se midieron sobre un ranking que no llegaba al modelo y por eso
la compuerta se vació al empezar la Fase 2.

| | R@1 | R@3 | MRR | MRR duro | ms | contexto |
|---|---|---|---|---|---|---|
| **baseline** | 35/49 | 43/49 | 0.805 | **0.553** | 3.68 | 21.317 chars |

## Experiments

| brazo | R@1 | R@3 | MRR | MRR duro | ms | contexto | Δ MRR duro |
|---|---|---|---|---|---|---|---|
| baseline · BM25 + 3 índices | 35/49 | 43/49 | 0.805 | 0.553 | 3.68 | 21.317 | — |
| **+ reranker** | 37/49 | 44/49 | 0.829 | **0.634** | 10.09 | 21.808 | **+0.082** |
| + vector | 35/49 | 41/49 | 0.791 | 0.538 | 47.49 | 22.999 | −0.015 |
| + vector + reranker | 39/49 | 43/49 | 0.845 | 0.651 | 8.79 | 23.045 | +0.099 |

### Por familia — aquí está lo que el número global esconde

| brazo | parafrasis | mixto | erratas | multisalto |
|---|---|---|---|---|
| baseline | **0.490** | 0.800 | 0.167 | 0.778 |
| + reranker | **0.427** | 1.000 | 0.500 | 0.833 |
| + vector | 0.455 | 0.875 | 0.278 | 0.567 |
| + vector + reranker | 0.403 | 1.000 | 0.667 | 0.833 |

**El reranker empeora las paráfrasis** (0.490 → 0.427, −0.062 sobre 8 casos) y arrasa en erratas
(0.167 → 0.500) y en mezcla es/en (0.800 → 1.000). El `+0.082` global es un agregado que tapa esa
regresión. Se enciende igual, porque las paráfrasis son la familia donde *nada* funciona bien
todavía y el resto mejora mucho — pero queda escrito, no enterrado.

**Limitación honesta:** la tabla por familia está guardada en `ganancias.json` y **en runtime no
se usa**. `pipeline.ejecutar()` siempre pasa `familia="general"` porque no hay clasificador de
consultas. Solo la fila `general` es load-bearing. Clasificar familias en runtime es complejidad
que estos datos todavía no justifican.

### RRF

```
RRF con una sola señal: 20 → 20 candidatos · passthrough = True
```

Con el vector apagado, RRF **no hace nada**: no hay segunda señal que fusionar. Está en el camino
y es inerte. Se deja porque es donde entraría el vector si algún día se justifica, y porque
quitarlo no ahorra nada medible (0.0 ms).

### Vector

```
vector vs BM25 (20 consultas): 106 candidatos nuevos, 174 compartidos (37.9% nuevo)
```

Trae un 38% de candidatos que BM25 no encuentra — y aun así el MRR **baja** 0.015. Traer
candidatos distintos no es traer candidatos mejores. Además cuesta 47,49 ms frente a 3,68 del
baseline: **13× más lento**, dominado por reindexar los subconjuntos filtrados en cada consulta.

Ayuda de verdad en dos familias (erratas +0.111, mixto +0.075) y hunde multisalto (−0.211). Como
en runtime solo cuenta `general`, queda **DISABLED**.

### Los tres índices

```
conocimiento   104 trozos distintos
antipatrones   150 trozos distintos
fallos         112 trozos distintos
604 recuperados → 442 al contexto (26.8% se descarta por duplicado)
```

`antipatrones` es el que más material distinto aporta. Un 26,8% de lo recuperado se descarta por
duplicación entre índices — lo hace el ContextBuilder, y antes de la Fase 2 ese solape iba entero
al prompt.

### Graph

Sobre tres consultas multi-hop reales, añade **+8 trozos por consulta en ~0,1–1 ms**. Pero "más
trozos" no es "mejor contexto": no hay evidencia de que esos 8 ayuden, y sí de que cuestan tokens.
La auditoría ya midió que a 2 saltos el grafo alcanza 17 de 18 cajas, o sea que no filtra nada por
sí solo. Queda **EXPERIMENTAL**.

Dato secundario: de las tres consultas multi-hop, el plan detectó `needs_graph=True` en dos. El
detector falla una de tres.

### Symbols

Correctamente condicionado: **0 ms** cuando `needs_symbols=False`, y se activa en las dos consultas
que lo piden. Encuentra `validate_token`, `verify_jwt`, `auth_middleware`.

Indexar 671 símbolos costaba **118 ms en cada petición**. Se cacheó por `(ruta, mtime máximo de
los .py)`: **154 ms → 5 ms** en la segunda consulta, y se reconstruye solo si el código cambia.

---

## Real model validation — 6 consultas, $0.0753

| tipo | seg | coste | recuperación | contexto | resultado |
|---|---|---|---|---|---|
| conceptual | 65,5 | $0.0041 | 3·6·1 | 1.648 tok, 9 trozos | cubierto |
| corpus | 5,6 | $0.0046 | 3·6·5 | 1.887 tok, 9 trozos | cubierto |
| código | 107,3 | $0.0463 | 3·6·5 | 2.005 tok, 9 trozos | **rojo**, 10 sin verificar |
| multi-hop | 6,5 | $0.0070 | 3·4·5 | 3.495 tok, 10 trozos | cubierto |
| símbolos | 4,9 | $0.0052 | 3·6·2 | 2.702 tok, 9 trozos | **error** (bug, ver abajo) |
| sin evidencia | 7,5 | $0.0081 | 3·6·5 | 3.191 tok, 10 trozos | **mencionado** ✓ |

El reranker se ejecutó en las seis. Ninguna respuesta llevó aviso de afirmación no respaldada
(`afirmacion: sin_afirmacion` en las seis).

**La abstención sobrevive al modelo real:** Raft salió `mencionado` y la respuesta empieza por el
aviso de cobertura. Y la consulta de código, cuyo tema (`slugify`) no está en el corpus, salió
`ausente` — el pipeline lo dijo y generó código igual, que es lo correcto: en una tarea de código
la corrección la decide la ejecución, no los documentos.

---

## Tres bugs que encontraron las consultas reales

1. **`simbolos=error`** — regresión mía al cachear el índice: sustituí el `import simbolos` y dejé
   `simbolos.buscar(...)` referenciando un nombre ya no importado. **El test `r5` sí lo cubría; yo
   no volví a correr la suite tras la optimización.** Lo cazó una consulta pagada en vez de un test
   gratis. Arreglado y verificado.
2. **`arreglado` nunca se registraba** en las trazas del pipeline. La consulta de código hizo 2
   llamadas —generación y reparación— y la traza decía `arreglado: false`. El bucle funcionaba; el
   registro no.
3. **Los tests escribían en `salida/`**, la carpeta de producción, y pisaban la última entrega del
   usuario. La entrega de `slugify` desapareció por eso. Ahora `pipeline.ejecutar` acepta
   `carpeta=` y los dos tests usan un temporal.

Sobre el fallo de `slugify`: acabó `rojo` con las 10 propiedades declaradas `sin verificar` y con
el arreglo ya consumido. Ninguno de los 10 `test_id` apareció en la salida. **No se reintentó** —
no aporta evidencia nueva y el presupuesto se reserva para la Fase 7.

---

## Addendum (Fase 7) — el detector de "¿me piden código?" estaba roto

El banco a nivel agente destapó algo que ninguna métrica de retrieval podía ver: **3 de las 5
tareas no generaban código en absoluto**. No era el retrieval — era `plan.needs_code`.

La detección era una lista de palabras:

```
"Rate limiter por usuario con token bucket, seguro ante peticiones concurrentes. Node.js."
    → needs_code = False   (no lleva verbo imperativo)
"necesito rate limiting en mi endpoint"
    → needs_code = True    (dispara por "endpoint", y es una consulta)
```

Medido contra 11 peticiones reales de código y las 49 consultas de `eval`:

| | aciertos | falsos positivos |
|---|---|---|
| antes | **5 / 11** | 5 / 49 |
| ahora | **11 / 11** | 1 / 49 |

Lo que separa no es el vocabulario técnico —lo comparten las dos cosas— sino la **forma**: una
petición de código nombra un artefacto o un runtime y **no empieza preguntando**. Una firma
(`slugify(texto)`) o un nombre de archivo (`calculator.py`) manda sobre todo lo demás.

`postgres` y `redis` quedaron deliberadamente fuera de la lista de runtimes: son almacenes sobre los
que se pregunta tanto como se programa, y meterlos devolvía *"tipos de índices en postgres"* como
petición de código.

Efecto observado con modelo real, mismo brazo baseline: **de 2 de 5 tareas entregando código a
4 de 5**.

Esto vuelve a ser el patrón de siempre, en una capa nueva: una afirmación (`needs_code`) que
gobernaba una decisión cara y que **nadie había medido nunca**. Lo caza el banco, con dinero. Ahora
hay dos tests que lo miden gratis.

## Final configuration

| componente | estado | evidencia |
|---|---|---|
| **BM25** | `ACTIVE` | es el suelo; el IDF anterior da 0.469 MRR duro frente a 0.553 |
| **Tres índices** | `ACTIVE` | 366 trozos distintos entre los tres; `antipatrones` aporta 150 |
| **RRF** | `ACTIVE (inerte)` | passthrough con una sola señal. Se mantiene como punto de entrada del vector |
| **Reranker** | `ACTIVE` | +0.082 MRR duro por 0.006 de coste. Con la salvedad de paráfrasis, escrita arriba |
| **Vector local** | `DISABLED` | −0.015 MRR y 13× más lento. 38% de candidatos nuevos que no mejoran nada |
| **Symbols** | `CONDITIONAL` | solo con `needs_symbols`; 0 ms cuando no toca; índice cacheado |
| **Graph** | `EXPERIMENTAL` | +8 trozos sin evidencia de utilidad |
| **Knowledge Tree** | `NOT USEFUL YET` | sin medir, sin integrar |
| **Semantic cache** | `NOT USEFUL YET` | sin medir, sin integrar |
| **Model routing** | `NOT USEFUL YET` | sin datos por modelo |
| **Embeddings remotos / ColBERT / reranker remoto** | no implementados | la arquitectura actual no los necesita todavía |

Ninguna etapa está `ACTIVE` porque exista. Hay un test (`ninguna_etapa_esta_on_sin_evidencia`) que
falla si alguna lo está sin medición, sin ser del núcleo o sin activación manual explícita.

## Regression tests

**270 casos, 0 suites rojas.** 255 al empezar la fase + 15 de `test_calibracion.py`.

Los 10 obligatorios del prompt están cubiertos: baseline reproducible · el reranker cambia ranking
· el reranker cambia contexto · el vector se conmuta sin romper · benchmark y producción usan los
mismos índices · símbolos solo con `needs_symbols` · graph apagado y lo dice · la abstención
aguanta con las cuatro combinaciones de vector/reranker · las métricas dicen sobre qué pipeline se
tomaron · la configuración es reproducible.

## Budget

| | |
|---|---|
| Techo de la fase | $2.00 |
| Gastado | **$0.0753** |
| Llamadas reales | 7 (6 consultas + 1 verificación de UI) |
| Acumulado del proyecto | $0.1365 |

## Important discovery

**El `+0.082 MRR` del reranker no significa "el reranker es bueno".** Significa que por primera vez
esa cifra es load-bearing: se midió sobre el camino que consume el modelo. La cifra anterior
(`+0.0441`) venía de un ranking que no llegaba al prompt.

Y hay un patrón que conviene fijar como invariante: **las tres veces que un componente pareció
funcionar y no funcionaba, el síntoma fue el mismo — una medición o un registro tomado sobre algo
distinto de lo que el usuario recibe.** El reranker medido sobre un ranking descartado,
`arreglado` registrado sobre un campo que nadie escribía, y los tests escribiendo sobre la carpeta
de producción. Vale la pena mirar con esa lente todo lo que quede por integrar.

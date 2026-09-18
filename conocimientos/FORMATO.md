# Formato común de los documentos

Cada documento es **una caja**. Cada `##` dentro de él es un **knowledge_item**.
Los 15 campos del esquema se reparten así:

| campo | dónde vive |
|---|---|
| `concept` | el título `##` |
| `explanation` | la prosa que sigue |
| `implementation` | el bloque de código |
| `example` | dentro de la prosa o del código, con datos concretos |
| `pattern` | ficha → **Patrón** |
| `anti_pattern` | ficha → **Anti-patrón** |
| `constraint` | ficha → **Límites** |
| `failure_mode` | ficha → **Cómo falla** |
| `dependency` | ficha → **Depende de** |
| `use_case` | ficha → **Cuándo** |
| `decision` | ficha → **Decisión** |
| `tradeoff` | ficha → **Trade-off** |
| `related_concepts` | ficha → **Relacionado** |
| `related_boxes` | ficha → `[NN]` al final de la ficha |
| `sources` | sección `## Fuentes` al final del documento |

## Plantilla de un knowledge_item

```markdown
## Nombre del concepto

Prosa: qué es, por qué existe, cómo funciona.

​```lenguaje
código real, ejecutable, con nombres concretos
​```

> **Ficha** · **Cuándo:** ... · **Patrón:** ... · **Anti-patrón:** ... · **Límites:** ...
> · **Cómo falla:** ... · **Decisión:** ... · **Depende de:** ... · **Trade-off:** ...
> · **Relacionado:** ... `[04, 08]`
```

## Estructura del documento

```
# NN · Nombre de la caja
> una línea de para qué sirve

**Cubre del temario:** concepts · patterns · implementations · ...

## <knowledge_item 1>
## <knowledge_item 2>
...
## Preguntas de entrevista y trade-offs     <- decision + tradeoff a nivel de caja
## Fuentes                                   <- sources
```

## Reglas

1. **Un concepto se desarrolla en una sola caja.** Las demás lo referencian con `[NN]`.
   Sin duplicar: dos copias acaban contradiciéndose.
2. **Toda ficha lleva al menos** *Cuándo*, *Cómo falla* y *Trade-off*. El resto, si aplica.
3. **El código es real**, no pseudocódigo: nombres concretos, valores concretos.
4. **Los `##` son las fronteras de chunk del RAG** (`../rag.py`). Un `##` = una unidad recuperable,
   así que cada uno debe sostenerse solo.

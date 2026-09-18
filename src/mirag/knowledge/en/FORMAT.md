# Common document format

Each document is **one box**. Each `##` inside it is a **knowledge_item**.
The 15 fields of the schema are distributed like this:

| field | where it lives |
|---|---|
| `concept` | the `##` title |
| `explanation` | the prose that follows |
| `implementation` | the code block |
| `example` | inside the prose or the code, with concrete data |
| `pattern` | card → **Pattern** |
| `anti_pattern` | card → **Anti-pattern** |
| `constraint` | card → **Limits** |
| `failure_mode` | card → **How it fails** |
| `dependency` | card → **Depends on** |
| `use_case` | card → **When** |
| `decision` | card → **Decision** |
| `tradeoff` | card → **Trade-off** |
| `related_concepts` | card → **Related** |
| `related_boxes` | card → `[NN]` at the end of the card |
| `sources` | `## Sources` section at the end of the document |

## Template for a knowledge_item

```markdown
## Concept name

Prose: what it is, why it exists, how it works.

​```language
real, runnable code, with concrete names
​```

> **Card** · **When:** ... · **Pattern:** ... · **Anti-pattern:** ... · **Limits:** ...
> · **How it fails:** ... · **Decision:** ... · **Depends on:** ... · **Trade-off:** ...
> · **Related:** ... `[04, 08]`
```

## Document structure

```
# NN · Box name
> one line on what it is for

**Covers from the syllabus:** concepts · patterns · implementations · ...

## <knowledge_item 1>
## <knowledge_item 2>
...
## Interview questions and trade-offs     <- decision + tradeoff at box level
## Sources                                <- sources
```

## Markers read by the parser

The English documents are parsed by [`../../retrieval/corpus.py`](../../retrieval/corpus.py), which
matches these markers literally: same spelling, same bold, same colon. The Spanish edition (`../es/`)
uses the equivalents in the right-hand column; the two sets must never be mixed within one document.

| Marker (exact) | Where it goes | Spanish equivalent |
|---|---|---|
| `> **Card** · ` | start of the card blockquote | `> **Ficha** · ` |
| `**When:**` | card field → `use_case` | `**Cuándo:**` |
| `**Pattern:**` | card field → `pattern` | `**Patrón:**` |
| `**Anti-pattern:**` | card field → `anti_pattern` | `**Anti-patrón:**` |
| `**Limits:**` | card field → `constraint` | `**Límites:**` |
| `**How it fails:**` | card field → `failure_mode` | `**Cómo falla:**` |
| `**Decision:**` | card field → `decision` | `**Decisión:**` |
| `**Depends on:**` | card field → `dependency` | `**Depende de:**` |
| `**Trade-off:**` | card field → `tradeoff` | `**Trade-off:**` |
| `**Related:**` | last card field → `related_concepts` + `[NN]` | `**Relacionado:**` |
| `**Covers from the syllabus:**` | under the H1, lists the backticked syllabus tokens | `**Cubre del temario:**` |
| `## Interview questions and trade-offs` | second-to-last section of the document | `## Preguntas de entrevista y trade-offs` |
| `**Core trade-off of this box:**` | closing paragraph of the interview section | `**Trade-off central de esta caja:**` |
| `## Sources` | last section: the bibliography, not a knowledge_item | `## Fuentes` |

**Shape of the card.** It is a blockquote: the first line starts with `> **Card** · **When:** ...` and
every continuation line starts with `> `. Fields are separated by ` · ` and each field is
`**Name:** value`, in the order of the template. The card ends with the `**Related:**` field, whose
last token is the list of related boxes.

**Box references.** Always in backticks, `` `[04, 09]` ``: they are read with the regex
`` `\[([0-9,\s]+)\]` ``, so the backticks and the brackets are part of the marker.

**Failure sections.** A `##` title that starts with `Failure modes`, `Failure scenarios` or
`Business inconsistencies` marks the whole section as failure content (e.g. `## Failure modes: a database`).
No other title may start with those prefixes. The Spanish prefixes are `Cómo falla`,
`Escenarios de fallo` and `Inconsistencias de negocio`.

**Code fences.** A `##` inside a fenced code block is not a section boundary.

## Rules

1. **A concept is developed in a single box.** The others reference it with `[NN]`.
   No duplication: two copies end up contradicting each other.
2. **Every card has at least** *When*, *How it fails* and *Trade-off*. The rest, where it applies.
3. **The code is real**, not pseudocode: concrete names, concrete values.
4. **The `##` headings are the RAG chunk boundaries** (`../../retrieval/corpus.py`). One `##` = one
   retrievable unit, so each one must stand on its own.

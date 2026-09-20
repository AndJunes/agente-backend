# The PM agent

The same code as `mirag`, told it is a different agent. Retrieval, ranking, the model gateway,
the budget, the HTTP server and the SSE stream are all shared; what lives in this package is
only what makes this a different agent.

| | `mirag` | `mirag_pm` |
|---|---|---|
| corpus | 19 backend boxes, cards in blockquotes | 91 PM documents in domain folders, YAML frontmatter |
| loader | `KnowledgeCorpus.load` | `PmCorpus.load` |
| lexicon | code and project vocabulary | product vocabulary; every code pattern never matches |
| tools | search, **run_code**, calculate | search, limitations, disputed, evidence, sources, glossary, skills |
| serves | `POST /api/v1/chat` | `POST /api/v1/{analyze,plan,revise}` |
| prompt | "You are a backend tutor." | "You are a product manager…" |

## Running it

```
python -m mirag_pm serve          # needs MIRAG_TOKEN; MIRAG_OFFLINE=0 and a key to answer
python -m mirag_pm.cli doctor     # loads every locale, checks the four indices
python -m mirag_pm.cli coverage   # every document reachable by a skill
```

In production it is a second service off the same image — see `mirag-pm` in
`docker-compose.prod.yml`. CodeZard reaches it by service name, which means adding one entry
to the gateway's registry:

```json
{"name": "pm", "base_url": "http://mirag-pm:8000", "health_path": "/api/v1/health"}
```

`health_path` has to be given: the gateway defaults to `/health` and this server does not
serve that. Worth checking whether the backend's existing entry has the same omission.

## Why two processes and not two modes

Because "the two agents do not mix" should be a property of the system rather than of anyone
remembering. One process holds one container, one container holds one `I18n`, and that object
is told at construction which corpus to read. No field of any request can reach across, and
the whole thing rests on `KNOWLEDGE_DIR` being imported in exactly one module — which CI
asserts with a three-line `git grep`, because an invariant nobody checks is a comment.

The lexicon is the second lock: `intent.code_verbs` and every `intent.project_*` pattern are
`(?!)`, so `asks_for_code` and `asks_for_project` are permanently False and this process
cannot take the code branch whatever it is asked. The absent `run_code` tool is the third.

## Skills are files

`skills/` holds 65 cards. Each declares its trigger, its inputs, its ordered method, what it
produces, the documents it `draws_on`, and — the part that does the most work — what it must
refuse to claim. Several exist mainly to refuse: estimation, metric design and MVP scoping are
gaps this knowledge base declares about itself, and a skill that occupies the question is what
stops the model filling it from memory.

Adding a skill is writing a file. `coverage` reads `draws_on` across all of them and fails if
any document is named by none, which is how "nothing was discarded" stays true after this
commit.

## The corpus has one language

There is no `es/` tree and there should not be one. The documents are English; the answer
language is decided by the message catalogue's directive. `PmCorpus.load` falls back and says
so in its report — `Path.glob` over a missing directory returns an empty list rather than
raising, so a missing corpus and an empty one look identical, and it refuses to return a
corpus with no chunks at all.

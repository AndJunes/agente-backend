# 18 · AI Backend

> The newest box and the one that changes fastest. The key point: **an AI backend is still a backend**.
> What changes is that your main dependency is non-deterministic, slow, priced per token and sometimes
> makes things up. Everything else (queues, idempotency, timeouts, observability) applies exactly the same.
>
> *2026 data verified with web search; see the sources section at the end of this document.*


**Covers from the syllabus:** `llms` · `prompting` · `embeddings` · `vector_databases` · `rag` · `search` · `reranking` · `tool_calling` · `agents` · `mcp` · `evals` · `guardrails` · `observability` · `failure_modes`

---

## Calling an LLM: the mental model

A chat API is **stateless**. There is no session: on every call you send the **entire** conversation.

```python
messages = [
    {"role": "system",    "content": "You are the company's assistant."},
    {"role": "user",      "content": "How many vacation days do I have?"},
    {"role": "assistant", "content": None, "tool_calls": [...]},   # it asked for a tool
    {"role": "tool",      "tool_call_id": "1", "content": "20 days"},
]
```

**Consequences of it being stateless, and they are the ones you feel most in production:**
- **Cost grows with the conversation.** Every turn resends everything before it: the spend of a long chat
  is quadratic, not linear.
- **The context window is finite.** You have to decide what to trim (see *context management*).
- **"Memory" is something you implement.** It does not exist by default.

**Parameters that matter:** `temperature` (0 for extraction and classification, high for creativity),
`max_tokens` (protects you from endless responses), `stop`, `seed` (partial reproducibility), and
`response_format` / structured outputs.

> **Card** · **When:** first integration with any LLM ·
> **Pattern:** the API is stateless: you send the whole conversation on every call ·
> **Anti-pattern:** assuming the provider remembers the conversation ·
> **Limits:** finite context window; `temperature` 0 for extraction and classification ·
> **How it fails:** the cost of a chat grows **quadratically**, not linearly ·
> **Decision:** you implement memory yourself: progressive summarisation or retrieval ·
> **Trade-off:** rich context (better answer, more expensive and slower) vs minimal ·
> **Related:** context management, cost `[13]`

---

## OpenRouter and model gateways

**What a gateway solves** (OpenRouter, Vercel AI Gateway, LiteLLM):
- **A single API** for dozens of providers, in an OpenAI-compatible format — switching models means
  changing a string.
- **Automatic fallback** if a provider fails or is overloaded.
- **Routing by cost, latency or availability.**
- **Centralised observability and spend control** per key.

```python
# OpenRouter: the same shape as the OpenAI API, different host and model
requests.post("https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
    json={"model": "anthropic/claude-haiku-4.5", "messages": messages, "tools": TOOLS})
```

**Honest trade-offs:** you add an intermediary (one more latency hop and one more point of failure), and
you can lose provider-specific features. In exchange you get real portability, which is worth a lot in a
market where the best model changes every few months.

**Design rule:** the model must be **a configuration constant**, never something hardcoded throughout the
code. You should be able to switch models with an environment variable and an eval run.

> **Card** · **When:** when you want portability across providers ·
> **Pattern:** the model as a **configuration constant**, never hardcoded ·
> **Anti-pattern:** coupling the logic to one specific provider's SDK ·
> **Limits:** one more latency hop and an extra point of failure ·
> **How it fails:** you lose provider-specific features that only their SDK exposes ·
> **Decision:** in a market where the best model changes every few months, portability is worth a lot ·
> **Trade-off:** independence vs provider-specific functionality and latency ·
> **Related:** adapters, fallback `[05, 16]`

---

## Prompt engineering (the parts that apply to backend)

- **Instructions in the system prompt, data in the user message.** Don't mix them.
- **Be specific about the output format** and give examples (few-shot). One well-chosen example is worth
  more than three paragraphs of instructions.
- **Delimit external data** with clear tags (`<document>...</document>`) and say explicitly that its
  content is **data, not instructions**.
- **Ask it to cite** which fragment each claim came from: it reduces hallucinations and gives you traceability.
- **Give it an emergency exit:** *"if it is not in the documents, say you don't know"*. Without this, the
  model fills in the gaps.
- **Version prompts like code**, with evals attached. A prompt change is a deployment: it can break
  production exactly like a code change.
- **Prompt caching:** several providers cache the common prefix (long system prompt, fixed documents)
  at big discounts. **Put the stable parts first and the variable parts last** to maximise the cache hit
  rate. It is one of the biggest and easiest cost optimisations.

> **Card** · **When:** in every prompt that reaches production ·
> **Pattern:** instructions in the system prompt, delimited data in the user message, and an explicit emergency exit ·
> **Anti-pattern:** mixing instructions and user data without delimiting them ·
> **Limits:** prompt caching only hits if the **prefix** is stable ·
> **How it fails:** without "if it is not in the documents, say so", the model fills in the gaps ·
> **Decision:** version prompts like code: a prompt change is a deployment ·
> **Trade-off:** long, explicit prompt (better, more expensive) vs short ·
> **Related:** evals, prompt injection, cost `[06]`

---

## Structured outputs and tool calling

**Structured outputs:** forcing the response to conform to a JSON Schema. In 2026 the serious providers
guarantee it at the decoding level, not by "asking nicely". **Use it whenever the consumer is code**, and
still validate with your own schema (Pydantic/Zod) before using it.

**Tool calling / function calling** is the mechanism that turns a text model into an agent:

```
1. You send messages + tool definitions (name, description, JSON Schema of the parameters)
2. The model responds: "call search_docs with {query: 'vacation'}"
3. YOU execute the function (the model never executes anything)
4. You return the result as a message with role "tool"
5. The model responds with text, or asks for another tool → back to step 2
```

**The critical, underestimated part: the tool description is a prompt.** The model chooses based on it.
2026 evaluations show that **rewriting tool descriptions alone fixes between 40% and 60% of
selection-accuracy regressions** — because the model treats the description as a routing signal.

**Tool design rules:**
- **Few and clearly differentiated.** Twenty overlapping tools produce erratic choices.
- **Explicit names and parameters**, and descriptions that say **when to use it and when not to**.
- **Strict argument validation** before executing: the model can hallucinate parameters.
- **Every tool that mutates something needs authorisation and limits.** The model is not a trusted user:
  apply the same permissions you would apply to the original HTTP request.

> **Card** · **When:** whenever the consumer of the output is code ·
> **Pattern:** enforced JSON Schema + your own validation on receipt ·
> **Anti-pattern:** asking for JSON "please" in the prompt and parsing it with a regex ·
> **Limits:** the model can hallucinate values that are valid per the schema but false ·
> **How it fails:** overlapping tools produce erratic choices ·
> **Decision:** **the tool description is a prompt**: rewriting it fixes 40-60% of selection regressions ·
> **Trade-off:** many tools (more capability) vs few (better accuracy) ·
> **Related:** agents, MCP, guardrails `[03]`

---

## RAG (Retrieval-Augmented Generation)

**The problem it solves:** the model does not know your private data or anything after its training, and
stuffing everything into the context is expensive and imprecise. RAG **retrieves** what is relevant and puts it in the prompt.

```
Documents → chunking → embeddings → vector DB
                                         ↑
Question → embedding → hybrid search → reranking → top 5-10 → prompt → answer
```

### Chunking

- **Fixed-size with overlap** (e.g. 500 tokens, 50 of overlap): the baseline, and it works surprisingly well.
- **By structure** (headings, sections, paragraphs): better when the document is well formatted —
  markdown with headings is the ideal case.
- **Semantic:** split where the meaning changes (computing the similarity between consecutive sentences and
  splitting when it drops below a threshold). Better quality, higher preprocessing cost.
- **Add context to each chunk** (document title, section, date). A loose fragment with no context
  retrieves poorly and confuses the model.
- **Size is a trade-off:** small chunks → precise retrieval but no context; large ones →
  context but noise and cost.

### Hybrid search (the production standard)

Run a vector search (meaning) and a **BM25 / lexical** search (exact match: proper nouns, error codes,
references) **in parallel**, and fuse them with **Reciprocal Rank Fusion**, whose standard constant
is **k=60**.

**Why:** embeddings fail precisely on exact matches. If you search for error `E4021` or product `SKU-9931`,
lexical search finds it and vector search does not. **Vector-only is the most common design mistake in RAG.**

### Reranking

The recommended pattern in 2026: **retrieve ~100 candidates with hybrid search → run them through a
cross-encoder (reranker) → keep the best 5-10** for the prompt.

A *bi-encoder* (embeddings) encodes the question and the document separately — fast, less accurate. A
*cross-encoder* processes them together — much more accurate, too slow for the whole corpus. Hence the
two-phase pattern: broad, cheap retrieval, then precise, expensive reordering over a small set.

### Vector databases

- **pgvector** if you already use Postgres: **the right default answer** up to large scale. One fewer
  source of truth to operate, and you can filter by metadata with plain SQL.
- **Qdrant, Weaviate, Milvus** (self-hosted) or **Pinecone** (managed) for larger scale or
  specific needs.
- **ANN indexes** (HNSW, IVF): approximate, with a parameter that trades accuracy for speed.
- **Metadata filtering is essential** in multi-tenant: `WHERE tenant_id = ...` **must be applied inside
  the search**, not afterwards, or you leak other customers' results (and if you filter afterwards, you end up
  with no results).

### What actually moves the needle

According to 2026 production analyses, **most of the improvement comes from four levers**: the chunking
strategy, hybrid retrieval, reranking, and choosing well between long context and retrieval. Getting those
four right puts you ahead of 80% of deployments.

**Long context does not replace RAG:** stuffing in 500,000 tokens is expensive, slow and degrades accuracy
(*lost in the middle*: models pay less attention to what sits in the middle of the context). Retrieving 5-20
reranked fragments and using a 16-64K token prompt is the usual sweet spot.

> **Card** · **When:** the model needs private or recent data ·
> **Pattern:** chunking with context → hybrid (vector + BM25, RRF k=60) → reranking → 5-10 fragments ·
> **Anti-pattern:** vector-only search — it fails precisely on codes, SKUs and proper nouns ·
> **Limits:** long context does **not** replace retrieval: it is expensive, slow and loses accuracy in the middle ·
> **How it fails:** in multi-tenant, filtering **after** searching leaves you with no results or leaks other tenants' data ·
> **Decision:** if you need verifiable exactness, generate SQL or call an API instead of searching by similarity ·
> **Trade-off:** more fragments (more context, more noise and cost) ·
> **Related:** embeddings, reranking, evals `[04]`

---

## Agents

An agent is a **loop**: the model decides, you execute, you hand the result back, repeat until it
answers. (Exactly what `../../agent/loop.py` in this project implements.)

```python
for turn in range(MAX_TURNS):        # the limit is NOT optional
    msg = llm(messages, tools=TOOLS)
    messages.append(msg)
    if not msg.get("tool_calls"):
        return msg["content"]
    for call in msg["tool_calls"]:
        result = execute_with_permissions_and_timeout(call)
        messages.append({"role": "tool", "tool_call_id": call["id"], "content": result})
```

**What you need to add for it to be production and not a demo:**
- **A turn limit and a budget limit** (tokens and money) per run. Without this, a tool loop can cost
  hundreds of euros in minutes.
- **A timeout per tool and per complete run.**
- **Idempotency in the tools that mutate** — the agent may retry.
- **Human approval** for destructive or irreversible actions (delete, pay, send).
- **Full traceability:** every decision, tool, argument and result stored. Without this you cannot
  debug why the agent did something weird, and it will.

**Patterns:** a single agent with tools (the simplest, start here) · a router or supervisor that
delegates to specialised sub-agents · planner + executor · reflection (the model critiques its own
output). **Multi-agent complexity is rarely justified**: most problems people try to solve with five
agents are better solved with one good agent and well-designed tools.

### Agent memory

- **Short-term:** the message list itself.
- **Progressive summarisation:** as the conversation grows, summarise the old part and keep the recent part verbatim.
- **Long-term:** facts extracted and stored (in a regular or vector DB) and retrieved when they are
  relevant. **It is RAG applied to the conversation**, not a separate mechanism.
- **Episodic vs semantic memory:** what happened in a given session vs stable facts about the user. Mix them
  up and you get an agent that remembers badly.
- **All of this is state with permissions:** one user's memory must not leak to another. It is just another table,
  with `tenant_id`, retention and right to erasure.

> **Card** · **When:** the task requires several steps that the model must decide ·
> **Pattern:** loop with a **turn limit and a budget limit**, per-tool timeouts and full traceability ·
> **Anti-pattern:** granting broad write permissions "so that it is useful" ·
> **Limits:** without a turn cap, a loop costs hundreds of euros in minutes ·
> **How it fails:** it gets stuck in a loop calling the same tool with the same arguments ·
> **Decision:** human approval for anything irreversible (delete, pay, send) ·
> **Trade-off:** autonomy vs predictability, cost and security ·
> **Related:** tool calling, guardrails, cost `[06, 13]`

---

## MCP (Model Context Protocol)

An open protocol for connecting models to tools and data: a standard so that any client can talk to any
tool server, instead of N×M bespoke integrations.

**Status in 2026:** introduced by Anthropic in November 2024 and **donated to the Linux Foundation's Agentic
AI Foundation in December 2025**. By March 2026 it exceeded **97 million monthly SDK downloads**
(Python + TypeScript) and has been adopted by Anthropic, OpenAI, Google, Microsoft and Amazon.

**Primitives:** *tools* (actions), *resources* (data), *prompts* (templates).

**What the protocol does not solve yet** (and that is exactly your job as the backend): identity
propagation, adaptive tool budgeting, and structured error semantics. That is why today's production
patterns are: **per-tool timeouts, per-server rate limits, pre-execution guardrails that block dangerous
write tools without approval, post-execution guardrails that scan returned content for indirect injection,
and *traffic mirroring* to test a new MCP server in shadow mode before promoting it.**

> **Card** · **When:** when connecting agents to third-party tools ·
> **Pattern:** per-server timeouts and rate limits, pre- and post-execution guardrails, traffic mirroring before promoting ·
> **Anti-pattern:** connecting an unaudited MCP server with write permissions ·
> **Limits:** the protocol does **not yet** standardise identity propagation, tool budgeting or structured errors ·
> **How it fails:** a `resource` returns content with injected instructions ·
> **Decision:** scan returned content for indirect injection before handing it to the model ·
> **Trade-off:** a ready-to-use tool ecosystem vs attack surface ·
> **Related:** prompt injection, least privilege `[06]`

---

## Evals

**Without evals you are deploying blind.** A change of prompt, model or temperature can improve one
case and break ten others without you noticing.

**What to measure:**
- **Retrieval (RAG):** `recall@k` and MRR — is the correct fragment among those retrieved? If
  retrieval fails, nothing else matters.
- **Answer quality:** LLM-as-judge with an explicit rubric, plus sampled human review.
- **Faithfulness / citations:** is the answer grounded in what was retrieved, or did it make it up?
- **Agents:** tool-selection accuracy, argument correctness, and **task
  completion** (did the full trajectory reach the goal?). They are three different metrics and they fail for
  different reasons.
- **Cost and latency per task** as first-class metrics, not as a footnote.

**How:** a **dataset of real cases** (start with 30-50 well-chosen ones; it is surprisingly effective),
run in CI on any prompt or model change. Treat it like your test suite: the examples
come from production failures.

**Beware of LLM-as-judge:** it has known biases (it prefers long answers, and favours models
from its own family). Calibrate it against human judgements before you trust it.

> **Card** · **When:** before any change of prompt, model or parameters ·
> **Pattern:** a dataset of 30-50 real cases run in CI, with separate retrieval and answer metrics ·
> **Anti-pattern:** validating a prompt change by trying it twice by hand ·
> **Limits:** LLM-as-judge has biases (it prefers long answers and models from its own family) ·
> **How it fails:** a change improves one case and breaks ten without anyone noticing ·
> **Decision:** if retrieval fails, nothing else matters: measure `recall@k` first ·
> **Trade-off:** cost of running evals vs deploying blind ·
> **Related:** testing, observability `[11, 12]`

---

## Guardrails and security

**Prompt injection is the security problem with no complete solution.** It is not a bug you patch: it is a
consequence of instructions and data travelling through the same channel.

- **Direct:** the user writes "ignore your instructions".
- **Indirect (the dangerous one):** the content you retrieve — a web page, an email, a document, a
  tool's response — contains instructions, and the model obeys them.

**Mitigations (layered, none sufficient on its own):**
- **Treat all external content as untrusted data**, delimited and marked as such in the prompt.
- **Least privilege on tools.** If the agent cannot delete, an injection cannot delete.
  **This is the control that actually works**, because it does not depend on detecting the attack.
- **Human approval** for irreversible or high-impact actions.
- **Input and output filters** (PII, secrets, dangerous content) and scanning of retrieved content.
- **Isolation:** sandboxed code execution, network egress restricted by allowlist. **Remember SSRF**
  (`06-security.md`): a tool that downloads URLs can reach the cloud metadata
  endpoint.
- **Never put secrets in the model's context.** It can repeat them in the response.

**And the backend basics still apply:** per-user rate limiting, quotas, input and output
validation, and logging everything.

> **Card** · **When:** any system that puts external content into a prompt ·
> **Pattern:** least privilege on tools + human approval + sandbox + network allowlist ·
> **Anti-pattern:** trying to **detect** injection with filters and relying on that ·
> **Limits:** prompt injection **has no complete solution**: data and instructions share a channel ·
> **How it fails:** a tool that downloads URLs reaches the cloud metadata endpoint (**SSRF**) `[06]` ·
> **Decision:** the control that works is limiting what the agent **can** do, not detecting the attack ·
> **Trade-off:** capability vs risk surface ·
> **Related:** SSRF, IAM, MCP `[06, 13]`

---

## Observability and cost/token management

**What to trace on every call:** model, prompt (or its hash/version), input and output tokens, cached
tokens, latency, cost, tools used, number of turns, and the outcome. With OpenTelemetry and its
GenAI conventions it integrates with the rest of your observability (`12-observability.md`), and there are
dedicated tools (Langfuse, LangSmith, Braintrust).

**Cost levers, by impact:**
1. **The right model for the task.** Most of an agent's steps (classify, route, extract) are
   done just as well by a small model at a tenth of the price. **Cascade:** try the small one, escalate
   to the large one only if needed.
2. **Prompt caching** — big discounts on the stable prefix. Structure the prompt to take advantage of it.
3. **Control the context:** don't resend the entire conversation; summarise, and retrieve only what is needed.
4. **Cache responses** to frequent questions (exact or by semantic similarity).
5. **Hard limits per user and per tenant**, with spend alerts. An uncapped agent loop is a
   billing incident.

**Latency:** **always stream (SSE)** to the user (`02-web-protocols.md`) — it completely changes the
perception even if the total takes just as long. Parallelise calls to independent tools, and move
everything that can be asynchronous out of the response path.

> **Card** · **When:** from the first AI feature in production ·
> **Pattern:** trace model, prompt, tokens, cache, cost, tools and turns per request ·
> **Anti-pattern:** a large model to classify or route ·
> **Limits:** cost grows with the length of the conversation, not with the number of requests ·
> **How it fails:** an uncapped agent loop turns into a billing incident ·
> **Decision:** cascade — small model first, large one only if needed ·
> **Trade-off:** quality vs cost and latency ·
> **Related:** observability, cost `[12, 13]`

---

## Embeddings

An embedding is a vector of numbers that represents the **meaning** of a text. Similar texts end up
close together in vector space; that closeness (cosine) is the whole magic of semantic search.

**What has to be decided, and almost nobody reasons through:**

| Decision | What it implies |
|---|---|
| **Model** | determines quality, cost and dimensions. Changing it forces you to **reindex the whole corpus** |
| **Dimensions** | 384 → fast and cheap · 1536 → typical · 3072 → better and 2× the storage and index |
| **Multilingual** | if your corpus and your questions are in different languages, you need a model that supports it |
| **Normalisation** | if the vectors are normalised (norm 1), cosine and dot product coincide: faster |
| **Model window** | text that exceeds its limit is **silently truncated**: the end is lost |
| **Symmetric vs asymmetric** | a short question and a long document are not the same kind of text; some models have different prefixes for each |

```python
# The detail most people overlook: you must embed the QUESTION and the DOCUMENT
# with the SAME model, and some models require different prefixes for each role.
doc_vec      = embed("passage: " + chunk_text)
question_vec = embed("query: "   + user_question)
```

**Real costs and limits:** embedding is cheap compared to generating (orders of magnitude less per
token), but reindexing a large corpus is neither free nor instant. **Always store the model and version
it was generated with alongside the vector** — the day you switch models you need to know what is
stale, and mixing vectors from two different models produces meaningless results.

**Dimensionality reduction (Matryoshka):** some models let you truncate the vector to fewer dimensions
while losing little quality. It is the direct lever for cutting storage cost and search latency.

> **Card** · **When:** before indexing the first document ·
> **Pattern:** store `model`, `version` and `dimensions` alongside each vector ·
> **Anti-pattern:** mixing vectors from different models in the same index ·
> **Limits:** text that exceeds the window is truncated without warning; embeddings do not understand negation or exact figures ·
> **How it fails:** you search for `SKU-9931` or "error E4021" and vector search does not find it — which is why you need hybrid ·
> **Decision:** start with a 1536-dimension model and measure before going higher ·
> **Trade-off:** more dimensions = better quality, more storage, slower index ·
> **Related:** hybrid search, vector databases, chunking `[04]`

---

## Failure modes: an AI system

The failures here are **plausible**, which is what makes them dangerous: the system answers confidently
and the error is indistinguishable from a correct answer.

| Failure | Symptom | Mitigation |
|---|---|---|
| **Hallucination** | confident, made-up answer | require citations; "say you don't know" instruction; faithfulness evals |
| **Retrieval failure** | the data **is** in the corpus and is not retrieved | hybrid search, reranking, measure `recall@k` |
| **Truncated chunk** | the right thing is retrieved but cut off | review the chunk size and what gets sent to the prompt |
| **Lost in the middle** | ignores what is in the middle of a long context | fewer fragments, reordered by relevance |
| **Tool loop** | the agent calls the same thing over and over | turn limit, repetition detection, better tool description |
| **Wrong tool** | picks badly among similar tools | rewrite descriptions (fixes 40-60% of regressions) |
| **Hallucinated arguments** | parameters that do not exist | strict validation before executing |
| **Prompt injection** | the agent obeys the retrieved content | least privilege + human approval `[06]` |
| **Runaway cost** | bill shoots up without warning | hard limits per user, spend alerts `[13]` |
| **Model drift** | the provider updates and the behaviour changes | pin the model version + evals in CI |
| **Cross-tenant leak** | retrieves another customer's documents | filter by `tenant_id` **inside** the search `[17]` |
| **Unacceptable latency** | the user leaves before the answer | SSE streaming, parallelise tools `[02]` |

**The difference from a normal backend:** here **there is no stack trace**. When the agent does something
weird, the only way to understand it is to have stored exactly what it saw — full prompt, retrieved fragments,
tools called and results. **Without that traceability, debugging is impossible.**

```python
# The bare minimum you need to be able to debug later
await trace.save(
    request_id=rid, model=MODEL, prompt_version="v7",
    fragments=[{"id": f.id, "score": f.score} for f in retrieved],
    turns=[{"tool": c.name, "args": c.args, "result": truncate(c.result)} for c in calls],
    input_tokens=usage.input, output_tokens=usage.output, cost_usd=cost, ms=duration)
```

> **Card** · **When:** any AI feature in production ·
> **Pattern:** full traceability + evals in CI + hard limits on turns and budget ·
> **Anti-pattern:** deploying a prompt change without evals ·
> **Limits:** you cannot guarantee it will not hallucinate; only reduce it and make it detectable ·
> **How it fails:** the failure is **plausible**, so it goes unnoticed until someone checks ·
> **Decision:** if the answer must be exact and verifiable, use a structured query, not an LLM ·
> **Trade-off:** autonomy and usefulness vs predictability and cost ·
> **Related:** evals, guardrails, observability `[11, 12]`

---

## Interview questions and trade-offs

**Q: How do you design a RAG system for a company's internal documentation?**
Ingestion with structure-based chunking and metadata → embeddings in pgvector → **hybrid search (vector +
BM25) fused with RRF** → reranker over ~100 candidates → 5-10 fragments into the prompt with a mandatory
citation requirement → recall and faithfulness evals. *Signal:* you mention hybrid search (codes and proper nouns fail
with vectors alone), tenant filtering **inside** the search, and how you reindex when a
document changes.

**Q: When should you NOT use RAG?**
When the corpus is small and fits in the context; when what you need is a structured query
(then the right move is to generate SQL or call an API, not to search by similarity); or when you need
reasoning over the **entire** document. *Signal:* you point out that many people use RAG where a database
query would be exact, cheaper and verifiable.

**Q: What is indirect prompt injection and how do you mitigate it?**
Instructions hidden in the content the system retrieves. You mitigate it with least privilege on the
tools, human approval for anything irreversible, and treating external content as data. *Signal:*
you say explicitly that it **has no complete solution** and that this is why the effective control is limiting what
the agent *can* do, not trying to detect the attack.

**Q: Your agent sometimes gets stuck in a loop calling the same tool. What do you do?**
Turn and budget limits, detection of identical repeated calls, improving the tool's description
and the error message it returns, and traceability to see what the model saw. *Signal:* you mention
that **the tool description is the most powerful lever** and the data point that rewriting descriptions fixes
most selection regressions.

**Q: How do you control the cost of an AI feature?**
The right model per step with a cascade, prompt caching, context management, response caching, and hard
per-user limits with alerts. *Signal:* you mention that the cost of a chat grows quadratically because
every turn resends the full conversation.

**Q: How do you know a prompt change has not made anything worse?**
With an eval suite in CI: a dataset of real cases, retrieval and quality metrics, and a comparison
against the previous version. *Signal:* you treat prompts and models as deployable code, with versioning and
the ability to roll back, and you mention the biases of LLM-as-judge.

**Core trade-off of this box:** *capability vs control*. The more autonomy and the more tools you give
a model, the more useful it is and the less predictable, more expensive and harder to secure it becomes. Senior design is about
**giving the minimum autonomy that solves the problem**, with hard limits on budget, permissions and turns,
and with full traceability — exactly the same discipline you would apply to a service you do not control.

---

## Sources

- [RAG Best Practices 2026: Chunking, Reranking, Hybrid Search — CallMissed](https://www.callmissed.com/en/blog/rag-best-practices-2026)
- [9 advanced RAG techniques and how to implement them (2026) — Meilisearch](https://www.meilisearch.com/blog/rag-techniques)
- [RAG Is Not Dead: Advanced Retrieval Patterns That Actually Work in 2026 — DEV](https://dev.to/young_gao/rag-is-not-dead-advanced-retrieval-patterns-that-actually-work-in-2026-2gbo)
- [How to Evaluate MCP-Connected AI Agents in Production (2026) — FutureAGI](https://futureagi.com/blog/evaluate-mcp-connected-ai-agents-production/)
- [MCP Security Guide 2026 — explainx.ai](https://www.explainx.ai/blog/mcp-security-guide-2026)
- [MCP Tools 2026: The Complete Model Context Protocol Guide — n1n.ai](https://explore.n1n.ai/blog/mcp-tools-2026-model-context-protocol-guide-2026-05-12)

# 18 · AI Backend

> La caja más nueva y la que más rápido cambia. Lo importante: **un backend de IA sigue siendo un backend**.
> Lo que cambia es que tu dependencia principal es no determinista, lenta, cara por token y a veces se
> inventa cosas. Todo lo demás (colas, idempotencia, timeouts, observabilidad) sigue aplicando igual.
>
> *Datos de 2026 verificados con búsqueda web; ver la sección de fuentes al final de este documento.*


**Cubre del temario:** `llms` · `prompting` · `embeddings` · `vector_databases` · `rag` · `search` · `reranking` · `tool_calling` · `agents` · `mcp` · `evals` · `guardrails` · `observability` · `failure_modes`

---

## Llamar a un LLM: el modelo mental

Una API de chat es **stateless**. No hay sesión: en cada llamada mandas **toda** la conversación.

```python
mensajes = [
    {"role": "system",    "content": "Eres un asistente de la empresa."},
    {"role": "user",      "content": "¿Cuántos días de vacaciones tengo?"},
    {"role": "assistant", "content": None, "tool_calls": [...]},   # pidió una herramienta
    {"role": "tool",      "tool_call_id": "1", "content": "20 días"},
]
```

**Consecuencias de que sea stateless, y son las que más se notan en producción:**
- **El coste crece con la conversación.** Cada turno reenvía todo lo anterior: el gasto de un chat largo
  es cuadrático, no lineal.
- **La ventana de contexto es finita.** Hay que decidir qué recortar (ver *context management*).
- **La "memoria" la implementas tú.** No existe por defecto.

**Parámetros que importan:** `temperature` (0 para extracción y clasificación, alto para creatividad),
`max_tokens` (protege de respuestas infinitas), `stop`, `seed` (reproducibilidad parcial), y
`response_format` / structured outputs.

> **Ficha** · **Cuándo:** primera integración con cualquier LLM ·
> **Patrón:** la API es stateless: mandas la conversación entera en cada llamada ·
> **Anti-patrón:** asumir que el proveedor recuerda la conversación ·
> **Límites:** ventana de contexto finita; `temperature` 0 para extracción y clasificación ·
> **Cómo falla:** el coste de un chat crece de forma **cuadrática**, no lineal ·
> **Decisión:** la memoria la implementas tú: resumen progresivo o recuperación ·
> **Trade-off:** contexto rico (mejor respuesta, más caro y lento) vs mínimo ·
> **Relacionado:** gestión de contexto, coste `[13]`

---

## OpenRouter y los gateways de modelos

**Qué resuelve un gateway** (OpenRouter, Vercel AI Gateway, LiteLLM):
- **Una sola API** para docenas de proveedores, con formato compatible con OpenAI — cambiar de modelo es
  cambiar un string.
- **Fallback automático** si un proveedor falla o está saturado.
- **Routing por coste, latencia o disponibilidad.**
- **Observabilidad y control de gasto centralizados** por clave.

```python
# OpenRouter: la misma forma que la API de OpenAI, distinto host y modelo
requests.post("https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
    json={"model": "anthropic/claude-haiku-4.5", "messages": mensajes, "tools": TOOLS})
```

**Trade-offs honestos:** añades un intermediario (un salto más de latencia y un punto de fallo más), y
puedes perder funciones específicas de cada proveedor. A cambio ganas portabilidad real, que en un mercado
donde el mejor modelo cambia cada pocos meses vale mucho.

**Regla de diseño:** el modelo debe ser **una constante de configuración**, nunca algo hardcodeado por el
código. Deberías poder cambiar de modelo con una variable de entorno y una evaluación.

> **Ficha** · **Cuándo:** al querer portabilidad entre proveedores ·
> **Patrón:** el modelo como **constante de configuración**, nunca hardcodeado ·
> **Anti-patrón:** acoplar la lógica al SDK de un proveedor concreto ·
> **Límites:** un salto más de latencia y un punto de fallo añadido ·
> **Cómo falla:** pierdes funciones específicas del proveedor que solo su SDK expone ·
> **Decisión:** en un mercado donde el mejor modelo cambia cada pocos meses, la portabilidad vale mucho ·
> **Trade-off:** independencia vs funcionalidad específica y latencia ·
> **Relacionado:** adaptadores, fallback `[05, 16]`

---

## Prompt engineering (lo que aplica a backend)

- **Instrucciones en el system prompt, datos en el mensaje de usuario.** No mezcles.
- **Sé específico sobre el formato de salida** y da ejemplos (few-shot). Un ejemplo bien elegido vale más
  que tres párrafos de instrucciones.
- **Delimita los datos externos** con etiquetas claras (`<documento>...</documento>`) y di explícitamente
  que su contenido es **datos, no instrucciones**.
- **Pide que cite** de qué fragmento sacó cada afirmación: reduce alucinaciones y te da trazabilidad.
- **Dale una salida de emergencia:** *"si no está en los documentos, di que no lo sabes"*. Sin esto, el
  modelo rellena huecos.
- **Versiona los prompts como código**, con evals asociadas. Un cambio de prompt es un despliegue: puede
  romper producción exactamente igual que un cambio de código.
- **Prompt caching:** varios proveedores cachean el prefijo común (system prompt largo, documentos fijos)
  con descuentos grandes. **Pon lo estable al principio y lo variable al final** para maximizar el acierto
  de cache. Es una de las optimizaciones de coste más grandes y más fáciles.

> **Ficha** · **Cuándo:** en todo prompt que llegue a producción ·
> **Patrón:** instrucciones en el system, datos delimitados en el user, y salida de emergencia explícita ·
> **Anti-patrón:** mezclar instrucciones y datos del usuario sin delimitar ·
> **Límites:** el prompt caching solo acierta si el **prefijo** es estable ·
> **Cómo falla:** sin "si no está en los documentos, dilo", el modelo rellena huecos ·
> **Decisión:** versiona los prompts como código: un cambio de prompt es un despliegue ·
> **Trade-off:** prompt largo y explícito (mejor, más caro) vs corto ·
> **Relacionado:** evals, prompt injection, coste `[06]`

---

## Structured outputs y tool calling

**Structured outputs:** forzar que la respuesta cumpla un JSON Schema. En 2026 los proveedores serios lo
garantizan a nivel de decodificación, no "pidiéndolo por favor". **Úsalo siempre que el consumidor sea
código**, y valida igualmente con tu propio schema (Pydantic/Zod) antes de usarlo.

**Tool calling / function calling** es el mecanismo que convierte un modelo de texto en un agente:

```
1. Mandas mensajes + definiciones de herramientas (nombre, descripción, JSON Schema de parámetros)
2. El modelo responde: "llama a buscar_en_docs con {query: 'vacaciones'}"
3. TÚ ejecutas la función (el modelo nunca ejecuta nada)
4. Devuelves el resultado como un mensaje con role "tool"
5. El modelo responde con texto, o pide otra herramienta → vuelta al paso 2
```

**Lo crítico y lo que se subestima: la descripción de la herramienta es un prompt.** El modelo elige
basándose en ella. En las evaluaciones de 2026 se observa que **reescribir descripciones de herramientas
resuelve por sí solo entre el 40% y el 60% de las regresiones de precisión de selección** — porque el modelo
trata la descripción como señal de enrutamiento.

**Reglas de diseño de herramientas:**
- **Pocas y bien diferenciadas.** Veinte herramientas con solapamiento producen elecciones erráticas.
- **Nombres y parámetros explícitos**, descripciones que digan **cuándo usarla y cuándo no**.
- **Validación estricta de argumentos** antes de ejecutar: el modelo puede alucinar parámetros.
- **Toda herramienta que muta algo necesita autorización y límites.** El modelo no es un usuario de
  confianza: aplica los mismos permisos que aplicarías a la petición HTTP original.

> **Ficha** · **Cuándo:** siempre que el consumidor de la salida sea código ·
> **Patrón:** JSON Schema forzado + validación propia al recibir ·
> **Anti-patrón:** pedir JSON "por favor" en el prompt y parsear con una regex ·
> **Límites:** el modelo puede alucinar valores válidos según el esquema pero falsos ·
> **Cómo falla:** herramientas solapadas producen elecciones erráticas ·
> **Decisión:** **la descripción de la tool es un prompt**: reescribirla resuelve el 40-60% de las regresiones de selección ·
> **Trade-off:** muchas herramientas (más capacidad) vs pocas (mejor precisión) ·
> **Relacionado:** agentes, MCP, guardrails `[03]`

---

## RAG (Retrieval-Augmented Generation)

**El problema que resuelve:** el modelo no conoce tus datos privados ni lo posterior a su entrenamiento, y
meterlo todo en el contexto es caro e impreciso. RAG **recupera** lo relevante y lo pone en el prompt.

```
Documentos → chunking → embeddings → vector DB
                                         ↑
Pregunta → embedding → búsqueda híbrida → reranking → top 5-10 → prompt → respuesta
```

### Chunking

- **Fijo con solapamiento** (p. ej. 500 tokens, 50 de solape): la línea base, funciona sorprendentemente bien.
- **Por estructura** (títulos, secciones, párrafos): mejor cuando el documento está bien formateado —
  markdown con encabezados es el caso ideal.
- **Semántico:** cortar donde cambia el significado (calculando la similitud entre frases consecutivas y
  cortando cuando cae por debajo de un umbral). Mejor calidad, más coste de preproceso.
- **Añade contexto a cada chunk** (título del documento, sección, fecha). Un fragmento suelto sin contexto
  recupera mal y confunde al modelo.
- **El tamaño es un trade-off:** chunks pequeños → recuperación precisa pero sin contexto; grandes →
  contexto pero ruido y coste.

### Búsqueda híbrida (lo estándar en producción)

Ejecutar **en paralelo** una búsqueda vectorial (significado) y una **BM25 / léxica** (coincidencia exacta:
nombres propios, códigos de error, referencias), y fusionar con **Reciprocal Rank Fusion**, cuya constante
estándar es **k=60**.

**Por qué:** los embeddings fallan justo en lo exacto. Si buscas el error `E4021` o el producto `SKU-9931`,
la búsqueda léxica lo encuentra y la vectorial no. **Solo-vectorial es el error de diseño más común en RAG.**

### Reranking

El patrón recomendado en 2026: **recuperar ~100 candidatos con búsqueda híbrida → pasarlos por un
cross-encoder (reranker) → quedarte con los 5-10 mejores** para el prompt.

Un *bi-encoder* (embeddings) codifica pregunta y documento por separado — rápido, menos preciso. Un
*cross-encoder* los procesa juntos — mucho más preciso, demasiado lento para todo el corpus. De ahí el
patrón de dos fases: recuperación amplia y barata, reordenación precisa y cara sobre un conjunto pequeño.

### Vector databases

- **pgvector** si ya usas Postgres: **la respuesta correcta por defecto** hasta escalas grandes. Una fuente
  de verdad menos que operar, y puedes filtrar por metadatos con SQL normal.
- **Qdrant, Weaviate, Milvus** (autogestionados) o **Pinecone** (gestionado) para escalas mayores o
  necesidades específicas.
- **Índices ANN** (HNSW, IVF): aproximados, con un parámetro que cambia precisión por velocidad.
- **Filtrado por metadatos es imprescindible** en multi-tenant: `WHERE tenant_id = ...` **debe aplicarse en
  la búsqueda**, no después, o filtras resultados de otros clientes (y si filtras después, te quedas sin
  resultados).

### Lo que de verdad mueve la aguja

Según los análisis de producción de 2026, **la mayor parte de la mejora viene de cuatro palancas**: la
estrategia de chunking, la recuperación híbrida, el reranking, y decidir bien entre contexto largo y
recuperación. Acertar en esas cuatro te pone por delante del 80% de los despliegues.

**El contexto largo no sustituye a RAG:** meter 500.000 tokens es caro, lento y degrada la precisión
(*lost in the middle*: los modelos atienden peor a lo que está en medio del contexto). Recuperar 5-20
fragmentos reordenados y usar un prompt de 16-64K tokens es el punto óptimo habitual.

> **Ficha** · **Cuándo:** el modelo necesita datos privados o recientes ·
> **Patrón:** chunking con contexto → híbrida (vectorial + BM25, RRF k=60) → reranking → 5-10 fragmentos ·
> **Anti-patrón:** solo búsqueda vectorial — falla justo en códigos, SKUs y nombres propios ·
> **Límites:** el contexto largo **no** sustituye a recuperar: es caro, lento y pierde precisión en el medio ·
> **Cómo falla:** en multi-tenant, filtrar **después** de buscar te deja sin resultados o filtra datos ajenos ·
> **Decisión:** si necesitas exactitud verificable, genera SQL o llama a una API en vez de buscar por similitud ·
> **Trade-off:** más fragmentos (más contexto, más ruido y coste) ·
> **Relacionado:** embeddings, reranking, evals `[04]`

---

## Agentes

Un agente es un **bucle**: el modelo decide, tú ejecutas, le devuelves el resultado, repite hasta que
responde. (Exactamente lo que implementa `../../agent/loop.py` de este proyecto.)

```python
for vuelta in range(MAX_VUELTAS):        # el límite NO es opcional
    msg = llm(mensajes, tools=TOOLS)
    mensajes.append(msg)
    if not msg.get("tool_calls"):
        return msg["content"]
    for call in msg["tool_calls"]:
        resultado = ejecutar_con_permisos_y_timeout(call)
        mensajes.append({"role": "tool", "tool_call_id": call["id"], "content": resultado})
```

**Lo que hay que añadir para que sea producción y no demo:**
- **Límite de vueltas y de presupuesto** (tokens y dinero) por ejecución. Sin esto, un bucle de
  herramientas puede costar cientos de euros en minutos.
- **Timeout por herramienta y por ejecución completa.**
- **Idempotencia en las herramientas que mutan** — el agente puede reintentar.
- **Aprobación humana** para acciones destructivas o irreversibles (borrar, pagar, enviar).
- **Trazabilidad completa:** cada decisión, herramienta, argumento y resultado guardados. Sin esto no puedes
  depurar por qué el agente hizo algo raro, y lo hará.

**Patrones:** un solo agente con herramientas (lo más simple, empieza aquí) · router o supervisor que
delega en sub-agentes especializados · planificador + ejecutor · reflexión (el modelo critica su propia
salida). **La complejidad multiagente rara vez se justifica**: la mayoría de los problemas que se intentan
resolver con cinco agentes se resuelven mejor con uno bueno y herramientas bien diseñadas.

### Agent memory

- **Corto plazo:** la propia lista de mensajes.
- **Resumen progresivo:** cuando la conversación crece, resume lo viejo y conserva lo reciente literal.
- **Largo plazo:** hechos extraídos y guardados (en una DB normal o vectorial) y recuperados cuando sean
  relevantes. **Es RAG aplicado a la conversación**, no un mecanismo distinto.
- **Memoria episódica vs semántica:** qué pasó en tal sesión vs hechos estables del usuario. Mézclalas y
  tendrás un agente que recuerda mal.
- **Todo esto es estado con permisos:** la memoria de un usuario no puede filtrarse a otro. Es una tabla más,
  con `tenant_id`, retención y derecho de borrado.

> **Ficha** · **Cuándo:** la tarea requiere varios pasos que el modelo debe decidir ·
> **Patrón:** bucle con **límite de vueltas y de presupuesto**, timeouts por herramienta y trazabilidad total ·
> **Anti-patrón:** dar permisos de escritura amplios "para que sea útil" ·
> **Límites:** sin tope de vueltas, un bucle cuesta cientos de euros en minutos ·
> **Cómo falla:** entra en bucle llamando a la misma herramienta con los mismos argumentos ·
> **Decisión:** aprobación humana para lo irreversible (borrar, pagar, enviar) ·
> **Trade-off:** autonomía vs previsibilidad, coste y seguridad ·
> **Relacionado:** tool calling, guardrails, coste `[06, 13]`

---

## MCP (Model Context Protocol)

Protocolo abierto para conectar modelos con herramientas y datos: un estándar para que cualquier cliente
hable con cualquier servidor de herramientas, en vez de N×M integraciones a medida.

**Estado en 2026:** introducido por Anthropic en noviembre de 2024 y **donado a la Agentic AI Foundation de
la Linux Foundation en diciembre de 2025**. En marzo de 2026 superaba los **97 millones de descargas
mensuales de SDK** (Python + TypeScript) y está adoptado por Anthropic, OpenAI, Google, Microsoft y Amazon.

**Primitivas:** *tools* (acciones), *resources* (datos), *prompts* (plantillas).

**Lo que todavía no resuelve el protocolo** (y es exactamente lo que te toca a ti como backend): propagación
de identidad, presupuesto adaptativo de herramientas, y semántica estructurada de errores. Por eso los
patrones de producción actuales son: **timeouts por herramienta, rate limits por servidor, guardarraíles
previos que bloquean herramientas de escritura peligrosas sin aprobación, guardarraíles posteriores que
escanean el contenido devuelto por inyección indirecta, y *traffic mirroring* para probar un servidor MCP
nuevo en sombra antes de promocionarlo.**

> **Ficha** · **Cuándo:** al conectar agentes con herramientas de terceros ·
> **Patrón:** timeouts y rate limits por servidor, guardarraíles previos y posteriores, traffic mirroring antes de promocionar ·
> **Anti-patrón:** conectar un servidor MCP no auditado con permisos de escritura ·
> **Límites:** el protocolo **aún no** estandariza propagación de identidad, presupuesto de herramientas ni errores estructurados ·
> **Cómo falla:** un `resource` devuelve contenido con instrucciones inyectadas ·
> **Decisión:** escanea el contenido devuelto por inyección indirecta antes de dárselo al modelo ·
> **Trade-off:** ecosistema de herramientas listo para usar vs superficie de ataque ·
> **Relacionado:** prompt injection, mínimo privilegio `[06]`

---

## Evals

**Sin evals estás desplegando a ciegas.** Un cambio de prompt, de modelo o de temperatura puede mejorar un
caso y romper otros diez sin que te enteres.

**Qué medir:**
- **Recuperación (RAG):** `recall@k` y MRR — ¿está el fragmento correcto entre los recuperados? Si la
  recuperación falla, nada de lo demás importa.
- **Calidad de la respuesta:** LLM-as-judge con una rúbrica explícita, más revisión humana por muestreo.
- **Fidelidad / citas:** ¿la respuesta se apoya en lo que se recuperó, o se lo inventó?
- **Agentes:** precisión de selección de herramienta, corrección de los argumentos, y **completitud de la
  tarea** (¿la trayectoria completa llegó al objetivo?). Son tres métricas distintas y fallan por motivos
  distintos.
- **Coste y latencia por tarea** como métricas de primera clase, no como nota al pie.

**Cómo:** un **dataset de casos reales** (empieza con 30-50 bien elegidos; es sorprendentemente eficaz),
ejecutado en CI ante cualquier cambio de prompt o modelo. Trátalo como tu suite de tests: los ejemplos
salen de los fallos de producción.

**Cuidado con el LLM-as-judge:** tiene sesgos conocidos (prefiere respuestas largas, y favorece al modelo
de su propia familia). Calíbralo contra juicios humanos antes de fiarte.

> **Ficha** · **Cuándo:** antes de cualquier cambio de prompt, modelo o parámetros ·
> **Patrón:** dataset de 30-50 casos reales ejecutado en CI, con métricas separadas de recuperación y de respuesta ·
> **Anti-patrón:** validar un cambio de prompt probándolo dos veces a mano ·
> **Límites:** el LLM-as-judge tiene sesgos (prefiere respuestas largas y a modelos de su familia) ·
> **Cómo falla:** un cambio mejora un caso y rompe diez sin que nadie se entere ·
> **Decisión:** si la recuperación falla, nada de lo demás importa: mide `recall@k` primero ·
> **Trade-off:** coste de ejecutar evals vs desplegar a ciegas ·
> **Relacionado:** testing, observabilidad `[11, 12]`

---

## Guardrails y seguridad

**Prompt injection es el problema de seguridad sin solución completa.** No es un bug que se parchea: es
consecuencia de que instrucciones y datos viajan por el mismo canal.

- **Directa:** el usuario escribe "ignora tus instrucciones".
- **Indirecta (la peligrosa):** el contenido que recuperas — una página web, un email, un documento, la
  respuesta de una herramienta — contiene instrucciones, y el modelo las obedece.

**Mitigaciones (en capas, ninguna suficiente sola):**
- **Trata todo el contenido externo como datos no confiables**, delimitado y marcado como tal en el prompt.
- **Mínimo privilegio en las herramientas.** Si el agente no puede borrar, una inyección no puede borrar.
  **Este es el control que de verdad funciona**, porque no depende de detectar el ataque.
- **Aprobación humana** para acciones irreversibles o de alto impacto.
- **Filtros de entrada y salida** (PII, secretos, contenido peligroso) y escaneo del contenido recuperado.
- **Aislamiento:** ejecución de código en sandbox, salida de red restringida por allowlist. **Recuerda SSRF**
  (`06-security.md`): una herramienta que descarga URLs puede alcanzar el endpoint de metadatos del
  cloud.
- **Nunca pongas secretos en el contexto** del modelo. Puede repetirlos en la respuesta.

**Y lo básico de backend que sigue aplicando:** rate limiting por usuario, cuotas, validación de entradas y
salidas, y logging de todo.

> **Ficha** · **Cuándo:** todo sistema que meta contenido externo en un prompt ·
> **Patrón:** mínimo privilegio en herramientas + aprobación humana + sandbox + allowlist de red ·
> **Anti-patrón:** intentar **detectar** la inyección con filtros y confiar en eso ·
> **Límites:** la inyección de prompts **no tiene solución completa**: datos e instrucciones comparten canal ·
> **Cómo falla:** una herramienta que descarga URLs alcanza el endpoint de metadatos del cloud (**SSRF**) `[06]` ·
> **Decisión:** el control que funciona es limitar lo que el agente **puede** hacer, no detectar el ataque ·
> **Trade-off:** capacidad vs superficie de riesgo ·
> **Relacionado:** SSRF, IAM, MCP `[06, 13]`

---

## Observabilidad y gestión de coste/tokens

**Qué trazar en cada llamada:** modelo, prompt (o su hash/versión), tokens de entrada y salida, tokens
cacheados, latencia, coste, herramientas usadas, número de vueltas, y el resultado. Con OpenTelemetry y sus
convenciones de GenAI se integra con el resto de tu observabilidad (`12-observability.md`), y hay
herramientas específicas (Langfuse, LangSmith, Braintrust).

**Palancas de coste, por impacto:**
1. **Modelo adecuado a la tarea.** La mayoría de los pasos de un agente (clasificar, enrutar, extraer) los
   hace un modelo pequeño igual de bien y diez veces más barato. **Cascada:** intenta con el pequeño, escala
   al grande solo si hace falta.
2. **Prompt caching** — descuentos grandes en el prefijo estable. Estructura el prompt para aprovecharlo.
3. **Controlar el contexto:** no reenvíes la conversación entera; resume, y recupera solo lo necesario.
4. **Cachear respuestas** de preguntas frecuentes (exactas o por similitud semántica).
5. **Límites duros por usuario y por tenant**, con alertas de gasto. Un bucle de agente sin tope es un
   incidente de facturación.

**Latencia:** **streaming (SSE) siempre** de cara al usuario (`02-web-protocols.md`) — cambia por completo
la percepción aunque el total tarde lo mismo. Paraleliza las llamadas a herramientas independientes, y saca
de la respuesta todo lo que pueda ser asíncrono.

> **Ficha** · **Cuándo:** desde la primera feature de IA en producción ·
> **Patrón:** trazar modelo, prompt, tokens, caché, coste, herramientas y vueltas por petición ·
> **Anti-patrón:** un modelo grande para clasificar o enrutar ·
> **Límites:** el coste crece con la longitud de la conversación, no con el número de peticiones ·
> **Cómo falla:** un bucle de agente sin tope se convierte en un incidente de facturación ·
> **Decisión:** cascada — modelo pequeño primero, grande solo si hace falta ·
> **Trade-off:** calidad vs coste y latencia ·
> **Relacionado:** observabilidad, coste `[12, 13]`

---

## Embeddings

Un embedding es un vector de números que representa el **significado** de un texto. Textos parecidos
quedan cerca en el espacio vectorial; esa cercanía (coseno) es toda la magia de la búsqueda semántica.

**Lo que hay que decidir, y casi nadie razona:**

| Decisión | Qué implica |
|---|---|
| **Modelo** | determina calidad, coste y dimensiones. Cambiarlo obliga a **reindexar todo el corpus** |
| **Dimensiones** | 384 → rápido y barato · 1536 → habitual · 3072 → mejor y 2× de almacenamiento e índice |
| **Multilingüe** | si tu corpus y tus preguntas están en idiomas distintos, necesitas un modelo que lo soporte |
| **Normalización** | si los vectores están normalizados (norma 1), coseno y producto escalar coinciden: más rápido |
| **Ventana del modelo** | el texto que supere su límite se **trunca en silencio**: el final se pierde |
| **Simétrico vs asimétrico** | una pregunta corta y un documento largo no son el mismo tipo de texto; algunos modelos tienen prefijos distintos para cada uno |

```python
# El detalle que mas gente pasa por alto: hay que embeber la PREGUNTA y el DOCUMENTO
# con el MISMO modelo, y algunos exigen prefijos distintos para cada rol.
vec_doc      = embed("passage: " + texto_del_chunk)
vec_pregunta = embed("query: "   + pregunta_del_usuario)
```

**Costes y límites reales:** embeber es barato comparado con generar (órdenes de magnitud menos por
token), pero reindexar un corpus grande no es gratis ni instantáneo. **Guarda siempre junto al vector el
modelo y la versión con que se generó** — el día que cambies de modelo necesitas saber qué está
desactualizado, y mezclar vectores de dos modelos distintos produce resultados sin sentido.

**Reducción de dimensiones (Matryoshka):** algunos modelos permiten truncar el vector a menos dimensiones
perdiendo poca calidad. Es la palanca directa para bajar coste de almacenamiento y latencia de búsqueda.

> **Ficha** · **Cuándo:** antes de indexar el primer documento ·
> **Patrón:** guardar `modelo`, `version` y `dimensiones` junto a cada vector ·
> **Anti-patrón:** mezclar vectores de modelos distintos en el mismo índice ·
> **Límites:** el texto que excede la ventana se trunca sin aviso; los embeddings no entienden negación ni cifras exactas ·
> **Cómo falla:** buscas `SKU-9931` o "error E4021" y la búsqueda vectorial no lo encuentra — por eso hace falta la híbrida ·
> **Decisión:** empieza con un modelo de 1536 dimensiones y mide antes de subir ·
> **Trade-off:** más dimensiones = mejor calidad, más almacenamiento, índice más lento ·
> **Relacionado:** búsqueda híbrida, vector databases, chunking `[04]`

---

## Cómo falla un sistema de IA

Los fallos aquí son **plausibles**, que es lo que los hace peligrosos: el sistema responde con seguridad
y el error no se distingue de un acierto.

| Fallo | Síntoma | Mitigación |
|---|---|---|
| **Alucinación** | respuesta segura e inventada | obligar a citar; instrucción de "di que no lo sabes"; evals de fidelidad |
| **Fallo de recuperación** | el dato **está** en el corpus y no se recupera | búsqueda híbrida, reranking, medir `recall@k` |
| **Chunk truncado** | se recupera lo correcto pero cortado | revisar el tamaño de chunk y lo que se manda al prompt |
| **Lost in the middle** | ignora lo que está en medio de un contexto largo | menos fragmentos, reordenados por relevancia |
| **Bucle de herramientas** | el agente llama a lo mismo una y otra vez | límite de vueltas, detección de repetición, mejor descripción de tool |
| **Tool equivocada** | elige mal entre herramientas parecidas | reescribir descripciones (resuelve el 40-60% de las regresiones) |
| **Argumentos alucinados** | parámetros que no existen | validación estricta antes de ejecutar |
| **Prompt injection** | el agente obedece al contenido recuperado | mínimo privilegio + aprobación humana `[06]` |
| **Coste desbocado** | factura disparada sin aviso | límites duros por usuario, alertas de gasto `[13]` |
| **Deriva del modelo** | el proveedor actualiza y cambia el comportamiento | fijar versión del modelo + evals en CI |
| **Fuga entre tenants** | recupera documentos de otro cliente | filtrar por `tenant_id` **dentro** de la búsqueda `[17]` |
| **Latencia inaceptable** | el usuario se va antes de la respuesta | streaming SSE, paralelizar herramientas `[02]` |

**La diferencia con un backend normal:** aquí **no hay stack trace**. Cuando el agente hace algo raro, la
única forma de entenderlo es haber guardado qué vio exactamente — prompt completo, fragmentos recuperados,
herramientas llamadas y resultados. **Sin esa trazabilidad, depurar es imposible.**

```python
# El minimo imprescindible para poder depurar despues
await traza.guardar(
    peticion_id=rid, modelo=MODEL, prompt_version="v7",
    fragmentos=[{"id": f.id, "puntuacion": f.score} for f in recuperados],
    vueltas=[{"tool": c.nombre, "args": c.args, "resultado": recortar(c.resultado)} for c in llamadas],
    tokens_entrada=uso.entrada, tokens_salida=uso.salida, coste_usd=coste, ms=duracion)
```

> **Ficha** · **Cuándo:** cualquier feature de IA en producción ·
> **Patrón:** trazabilidad completa + evals en CI + límites duros de vueltas y presupuesto ·
> **Anti-patrón:** desplegar un cambio de prompt sin evals ·
> **Límites:** no puedes garantizar que no alucine; solo reducirlo y hacerlo detectable ·
> **Cómo falla:** el fallo es **plausible**, así que pasa desapercibido hasta que alguien lo comprueba ·
> **Decisión:** si la respuesta debe ser exacta y verificable, usa una query estructurada, no un LLM ·
> **Trade-off:** autonomía y utilidad vs previsibilidad y coste ·
> **Relacionado:** evals, guardrails, observabilidad `[11, 12]`

---

## Preguntas de entrevista y trade-offs

**Q: ¿Cómo diseñas un RAG para la documentación interna de una empresa?**
Ingesta con chunking por estructura y metadatos → embeddings en pgvector → **búsqueda híbrida (vectorial +
BM25) fusionada con RRF** → reranker sobre ~100 candidatos → 5-10 fragmentos al prompt con obligación de
citar → evals de recall y fidelidad. *Señal:* mencionas la híbrida (los códigos y nombres propios fallan
con solo vectores), el filtrado por tenant **dentro** de la búsqueda, y cómo reindexas cuando cambia un
documento.

**Q: ¿Cuándo NO usar RAG?**
Cuando el corpus es pequeño y cabe en el contexto; cuando lo que necesitas es una consulta estructurada
(entonces lo correcto es generar SQL o llamar a una API, no buscar por similitud); o cuando hace falta
razonamiento sobre el documento **entero**. *Señal:* señalas que mucha gente usa RAG donde una query a la
base de datos sería exacta, más barata y verificable.

**Q: ¿Qué es prompt injection indirecta y cómo la mitigas?**
Instrucciones escondidas en el contenido que el sistema recupera. Se mitiga con mínimo privilegio en las
herramientas, aprobación humana para lo irreversible, y tratando el contenido externo como datos. *Señal:*
dices explícitamente que **no tiene solución completa** y que por eso el control efectivo es limitar lo que
el agente *puede* hacer, no intentar detectar el ataque.

**Q: Tu agente a veces entra en bucle llamando a la misma herramienta. ¿Qué haces?**
Límite de vueltas y de presupuesto, detección de llamadas repetidas idénticas, mejorar la descripción de la
herramienta y el mensaje de error que devuelve, y trazabilidad para ver qué vio el modelo. *Señal:* mencionas
que **la descripción de la herramienta es la palanca más potente** y el dato de que reescribirlas resuelve
la mayoría de las regresiones de selección.

**Q: ¿Cómo controlas el coste de una feature de IA?**
Modelo adecuado por paso con cascada, prompt caching, gestión del contexto, cache de respuestas, y límites
duros por usuario con alertas. *Señal:* mencionas que el coste de un chat crece de forma cuadrática porque
cada turno reenvía la conversación completa.

**Q: ¿Cómo sabes que un cambio de prompt no ha empeorado nada?**
Con una suite de evals en CI: dataset de casos reales, métricas de recuperación y de calidad, y comparación
contra la versión anterior. *Señal:* tratas prompts y modelos como código desplegable, con versionado y
posibilidad de rollback, y mencionas los sesgos del LLM-as-judge.

**Trade-off central de esta caja:** *capacidad vs control*. Cuanta más autonomía y más herramientas le das a
un modelo, más útil es y menos predecible, más caro y más difícil de asegurar. El diseño senior consiste en
**dar la mínima autonomía que resuelve el problema**, con límites duros de presupuesto, permisos y vueltas,
y con trazabilidad completa — exactamente la misma disciplina que aplicarías a un servicio que no controlas.

---

## Fuentes

- [RAG Best Practices 2026: Chunking, Reranking, Hybrid Search — CallMissed](https://www.callmissed.com/en/blog/rag-best-practices-2026)
- [9 advanced RAG techniques and how to implement them (2026) — Meilisearch](https://www.meilisearch.com/blog/rag-techniques)
- [RAG Is Not Dead: Advanced Retrieval Patterns That Actually Work in 2026 — DEV](https://dev.to/young_gao/rag-is-not-dead-advanced-retrieval-patterns-that-actually-work-in-2026-2gbo)
- [How to Evaluate MCP-Connected AI Agents in Production (2026) — FutureAGI](https://futureagi.com/blog/evaluate-mcp-connected-ai-agents-production/)
- [MCP Security Guide 2026 — explainx.ai](https://www.explainx.ai/blog/mcp-security-guide-2026)
- [MCP Tools 2026: The Complete Model Context Protocol Guide — n1n.ai](https://explore.n1n.ai/blog/mcp-tools-2026-model-context-protocol-guide-2026-05-12)

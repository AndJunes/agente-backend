# Configuración

Mirag lee su configuración una sola vez, del entorno y de un archivo `.env` opcional en la raíz
del repositorio (se crea copiando `.env.example`). Las variables de entorno existentes siempre
tienen prioridad sobre `.env`.

## Runtime

| Variable | Por defecto | Significado |
|---|---|---|
| `MIRAG_OFFLINE` | `1` | El candado. Mientras está activo, nunca se llama a un modelo real (las demos son guionadas y se etiquetan SIMULADO). Poner `0` para gastar de verdad. |
| `OPENROUTER_API_KEY` | - | Solo hace falta con `MIRAG_OFFLINE=0` (o con el backend vectorial remoto). |
| `MIRAG_MODEL` | `anthropic/claude-haiku-4.5` | Id del modelo en OpenRouter. `openrouter/free` reparte entre los modelos gratuitos (20 peticiones por minuto, 50 al día); el panel de coste dice entonces `GRATIS`. |
| `MIRAG_LLM_URL` | el chat/completions de OpenRouter | Cualquier proveedor que hable el mismo dialecto (NVIDIA, Groq, Gemini): solo cambian la URL y el modelo. |
| `MIRAG_BUDGET_USD` | `0.50` | Tope de gasto por request; la llamada que lo superaría nunca se hace. `0` = sin tope. |
| `MIRAG_MAX_OUTPUT_TOKENS` | `12000` | `max_tokens` por llamada al modelo. |
| `MIRAG_LOCALE` | `en` | Locale por defecto cuando ni el request ni `Accept-Language` dicen nada (`en`, `es`). |
| `MIRAG_HOST` / `MIRAG_PORT` | `127.0.0.1` / `8000` | Dónde escucha el servidor. Cualquier cosa que no sea loopback se avisa al arrancar; en un contenedor se publica contra `127.0.0.1` ([deployment.md](deployment.md)). |
| `MIRAG_TOKEN` | - | Secreto compartido que exigen `POST /api/v1/chat` y la descarga en la cabecera `X-Mirag-Token`. Vacío = abierto a quien alcance el puerto, y el arranque lo dice. |
| `MIRAG_EXECUTION` | `off` | ¿Se ejecutan el código generado y sus tests? Apagado, se entregan sin correrlos (eso es trabajo del agente de QA) y el veredicto es `not_executed`; estructura, sintaxis e imports se siguen comprobando. `mirag demo` y los benchmarks la encienden salvo que esté definida. |
| `MIRAG_DATA_DIR` | `<repo>/var` o `~/.mirag` | Dónde se escriben salidas, artefactos, trazas y cachés. |
| `MIRAG_SYMBOLS_ROOT` | la carpeta `src` | El código que lee el índice de símbolos. |
| `MIRAG_VECTOR_BACKEND` | `local` | `local` (n-gramas de caracteres, gratis) u `openrouter` (embeddings reales, con fallback a local). |
| `MIRAG_CODE_TIMEOUT_S` | `30` | Timeout de cada ejecución de código. El código ejecutado no recibe ninguna credencial: solo `PATH`, `HOME`, el locale y las variables de temporales. |
| `MIRAG_HTTP_LOG` | - | `1` para imprimir el access log HTTP. |

## Feature flags

Todos los flags aceptan `on`, `off` o `auto` a través de `MIRAG_<NAME>`. `mirag features`
imprime el estado de cada uno y **por qué**.

| Flag | Tipo | En `auto` |
|---|---|---|
| `RETRIEVAL_PLAN`, `METADATA_ROUTING`, `HYBRID_RETRIEVAL`, `SYMBOL_RETRIEVAL`, `SUFFICIENCY` | core | siempre encendidos (salvo que se apaguen a mano) |
| `VECTOR_SIGNAL`, `RERANKER`, `GRAPH_RETRIEVAL` | condicional | encendidos solo si `feature_gains.json` midió una ganancia de más de 0.02 de MRR que compense su costo |
| `MODEL_ROUTING`, `SEMANTIC_CACHE`, `KNOWLEDGE_TREE` | experimental | nunca se encienden solos; encendidos a mano con `on`, se etiquetan EXPERIMENTAL |
| `CONTEXTUAL_CHUNKS`, `COLBERT` | no implementado | nunca encendidos, ni siquiera a mano |

Configurar un flag que no hace nada se reporta, en lugar de ignorarse en silencio.

## Capa opcional de Stellar

`MIRAG_BLOCKCHAIN` (`off` por defecto, `testnet` para habilitarla) y las variables `STELLAR_*`
se describen en [blockchain.md](blockchain.md).

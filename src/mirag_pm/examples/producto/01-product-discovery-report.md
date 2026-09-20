# Product Discovery Report — Brújula

| | |
|---|---|
| **Producto** | Brújula |
| **Versión del documento** | 1.0 |
| **Fecha** | 16 de septiembre de 2026 |
| **Autor** | PM Agent · método: `pm-knowledge-base` v1.1.0 |
| **Input** | `brujula-vision-hackathon-target.md` |
| **Estado** | Discovery completo — input del PRD |
| **Contexto de plazo** | ABC Hackathon (Stellar / Argentina), 12–27 sept 2026. **Quedan 11 días de construcción.** |

---

## Nota de método

Este documento no razona desde memoria. Cada afirmación factual lleva su fuente. Dos registros:

| Marca | Significado |
|---|---|
| `[Snnn]` / `[Ennn]` | Método de producto — `pm-knowledge-base` (corpus / investigación externa) |
| `[Rnn]` | **Investigación de industria hecha para este documento** — registro completo al final |
| ⚠ | Dato de proveedor, no verificado, o con interés comercial declarado |
| ❌ | **No se encontró evidencia.** No se rellena |
| **[HIPÓTESIS]** | Creencia sin validar, no un hecho |

> **Regla aplicada**: donde la investigación no encontró dato, dice ❌. Cuando un buscador devolvió
> una cifra y la fuente original no la sostenía, la cifra se descartó — ver §3.5.

---

## 0. Resumen ejecutivo

La investigación produjo tres hechos que, juntos, reordenan la propuesta original.

> ### Hecho 1 — El mercado de *generar* software con IA ya está ganado
> Lovable: **US$ 500M de ARR** en junio 2026 y **valuación de US$ 13.300M** tras levantar US$400M
> en agosto 2026 [R08]. Replit, Bolt, v0 y Base44 compiten en el mismo espacio.
> **Brújula no puede ganar en "prompt → aplicación".**

> ### Hecho 2 — El mercado de *confiar* en ese software está completamente abierto
> Un escaneo pasivo de **30.998 aplicaciones generadas con IA en producción** (agosto 2026)
> encontró que **el 57% de las apps con backend Supabase alcanzables permitían lectura no
> autenticada de tablas** — 2.096 de 3.680 — y que **1 de cada 23 publicaba secretos en el
> bundle** [R10]. La adopción diaria es del 92% con **29% de confianza** [R09].
> **Nadie verifica. Ese es el hueco.**

> ### Hecho 3 — Stellar ya construyó exactamente las piezas que esto necesita
> **MPP (Machine Payments Protocol)** está **vivo en mainnet**, soporta **canales de pago
> off-chain** para alta frecuencia, funciona con **cualquier keypair de Stellar** y permite que
> **el servidor patrocine las fees — el agente nunca toca XLM** [R05][R06]. **x402** está
> documentado oficialmente con USDC por defecto [R04]. Las **reservas patrocinadas (CAP-33)**
> permiten crear wallets de agente **con saldo inicial 0** [R03].
> **La capa económica no hay que inventarla. Hay que integrarla.**

### La reposición que se deriva

> **Brújula no es un generador de aplicaciones. Es la capa de verificación y liquidación del
> software generado por IA: el pago se libera contra evidencia, no contra la afirmación del
> agente de que terminó.**

Eso convierte el pago agente-a-agente de adorno arquitectónico en **mecanismo de cumplimiento**:
un agente que no pasa verificación no cobra. Es la única lectura en la que la economía entre
agentes es *necesaria* y no decorativa — y es, además, un problema de pagos, que es de lo que
Stellar se trata.

### Recomendación en una línea

**Construir un corte vertical: una categoría de aplicación, 3 agentes, verificación dentro de cada
etapa, pago liberado contra evidencia sobre Stellar testnet con MPP, y un boletín de calificaciones
legible por el usuario.** Detalle en §10.

---

## 1. Problema identificado

### 1.1 Cómo se llegó a este enunciado

El documento original no contiene un enunciado de problema. Describe una solución. [S081] exige
como paso 1 escribir un enunciado de problema con quién lo sufre, por qué, y qué consecuencia
tiene — *"siendo tan específico y estrecho como sea posible"*.

La investigación reencuadró el problema dos veces:

```
Enunciado inicial (implícito en el documento original)
"La gente no técnica no puede construir software"
        ↓  [R08] Lovable US$500M ARR, US$13.3B valuación
        ↓  Este problema ya tiene soluciones bien financiadas
Segundo enunciado
"La gente no técnica no puede construir software PROFESIONAL"
        ↓  [R09][R10] 57% de apps con Supabase permiten lectura anónima
        ↓  [R11] 42,3 vulnerabilidades por repo asistido por IA vs 9,6 humano
        ↓  El problema no es generar. Es saber si lo generado sirve.
ENUNCIADO FINAL
```

### 1.2 Enunciado de problema

> **Quien encarga software generado por IA no tiene forma de saber si lo que recibió es seguro,
> completo y desplegable — y precisamente la persona que más necesita esa garantía es la que menos
> capacidad tiene de evaluarla.**
>
> El resultado observable: el 57% de las aplicaciones generadas con IA y respaldadas por Supabase
> que estaban en línea en agosto de 2026 permitían que cualquier visitante anónimo leyera sus
> tablas [R10]. Sus dueños, en su mayoría, no lo saben.

### 1.3 Por qué importa resolverlo, con evidencia

| Evidencia | Dato | Fuente |
|---|---|---|
| **La brecha adopción/confianza** | 92% de adopción diaria, **29% de confianza** | [R09] ⚠ |
| **Exposición real, medida pasivamente** | **57%** de apps Supabase alcanzables permiten lectura no autenticada (2.096 de 3.680, sobre 30.998 apps escaneadas) | [R10] ⚠ |
| **Secretos filtrados** | **1 de cada 23** apps publica secretos en el bundle (1.332 apps) | [R10] ⚠ |
| **Densidad de vulnerabilidades** | **42,3** por repo asistido por IA vs **9,6** humano | [R11] ⚠ |
| **Vulnerabilidades explotables confirmadas** | 74 casos confirmados de vulnerabilidades introducidas por IA; **18 casos en 7 meses de 2025 → 56 en 3 meses de 2026** | [R12] 🟢 académica |
| **Código con OWASP Top 10** | 45% de las muestras generadas | [R13] ⚠ |
| **La confirmación desde la otra punta** | *"En ausencia de un foco centrado en el usuario, la adopción de IA tiene un impacto **negativo** en el rendimiento del equipo"* — n≈5.000 | [E008] |

> ⚠ **Calidad de la evidencia, declarada.** [R10] es una empresa que **vende escaneo de seguridad
> y pentesting**, y lo declara abiertamente en su propio informe. [R11] infiere el estatus
> "asistido por IA" de metadatos de commits y **su propio publicador dice que debe leerse como
> direccional**. [R12] es **Georgia Tech, académica**, y es la más confiable — pero mide CVEs
> confirmados (74 casos), no porcentaje de apps, que es una medición distinta y mucho más estrecha.
>
> **La tendencia es consistente en cinco fuentes independientes con métodos distintos. Las
> magnitudes específicas no deben citarse como constantes.**

### 1.4 Y la consecuencia económica en Argentina

Lo que cuesta hoy la alternativa, en el mercado al que apunta la hackathon:

| Ítem | Dato | Fuente |
|---|---|---|
| Desarrollo a medida | **US$ 20–60 / hora** | [R14] |
| Proyecto simple (app interna, panel admin) | **~ARS 1,5 millones** | [R14] |
| Proyecto de complejidad media | **~ARS 2,5 millones** | [R14] |
| **Mantenimiento anual** | **15–20% del costo de desarrollo** — un software de ARS 3M necesita ARS 450–600k/año | [R14] |

> **La línea de mantenimiento es la más importante y la que el documento original ignora por
> completo.** Entregar una ZIP no termina el problema del usuario: lo empieza. Ver §9.4.

---

## 2. Usuarios y personas

### 2.1 Advertencia metodológica — leer antes que las personas

> ⚠ **Estas son proto-personas, no personas de investigación.** [S081] exige un mínimo de **8–10
> conversaciones de calidad** para identificar patrones. **Se hicieron cero.**
>
> Lo que sigue está construido a partir de datos de mercado [R08][R09][R10][R14], no de entrevistas.
> Su función es **enfocar a quién entrevistar**, no reemplazar la entrevista. Cada una lleva la
> hipótesis que la haría falsa.

### 2.2 El problema del usuario declarado en el documento original

> *"personas que pueden pagar tecnología pero no tienen el conocimiento técnico para construirla."*

[S081] pide *"lo más específico y estrecho posible"*. Esa frase describe simultáneamente a una
dueña de restaurante, un abogado con una idea, un director de ONG, un PM no técnico, un fundador
pre-semilla y un equipo de marketing corporativo. **Son mercados con disposiciones a pagar,
tolerancias al riesgo y definiciones de "terminado" incompatibles.** La misma ZIP no sirve para
tres de ellos.

### 2.3 Proto-persona primaria — **la que se recomienda**

> ## P1 · Martín · fundador técnico-adyacente en pre-semilla
>
> **Perfil.** 29 años, Buenos Aires. Producto o comercial, no ingeniero. Sabe leer un README y
> seguir instrucciones de despliegue; no sabe auditar una policy de Supabase. Ya usó Lovable o
> Bolt. Tiene un prototipo que funciona en demo.
>
> **Su Job to be Done** (formato job story, [S052]):
> > *Cuando tengo que enseñarle mi producto a un inversor o a un cliente que va a cargar datos
> > reales, quiero poder afirmar que es seguro sin mentir, para no quemar la relación cuando
> > alguien lo mire en serio.*
>
> **Qué ya hizo.** Generó la app. **El problema no es que no la tenga — es que no sabe si aguanta.**
>
> **Qué mide el éxito.** Un documento que puede reenviar. No un dashboard que tiene que interpretar.
>
> **Por qué esta persona y no otra.** Es la única del conjunto que (a) **ya demostró disposición a
> pagar** por herramientas de IA para software [R08], (b) tiene una **consecuencia concreta y
> fechada** por no saber —la reunión con el inversor—, y (c) **puede evaluar el output lo suficiente
> como para que su feedback sirva.**
>
> **[HIPÓTESIS QUE LA HARÍA FALSA]** Que a Martín no le importe la seguridad hasta que algo se
> rompa, y que hasta entonces la velocidad le gane siempre. **Sin validar.**

### 2.4 Proto-persona secundaria

> ## P2 · Carolina · dueña de PyME de servicios
>
> **Perfil.** 44 años, Salta. Centro de estética con 6 empleadas. Agenda por WhatsApp y una
> planilla. Le cotizaron ARS 1,5M por un sistema de turnos [R14] y no lo hizo.
>
> **Job story:**
> > *Cuando pierdo un turno porque se me traspapeló un mensaje, quiero un sistema que lo maneje
> > solo, para dejar de perder plata sin tener que contratar a alguien que me lo mantenga.*
>
> **La barrera real, y es dura.** No es el precio de generación. Es que **no puede desplegar ni
> mantener una ZIP.** [R14]: el mantenimiento anual es 15–20% del costo. Nadie se lo va a hacer.
>
> **Veredicto: NO es el usuario del MVP.** Requiere despliegue gestionado y soporte continuo —
> otro producto, otro modelo de negocio. Se registra porque **es el mercado grande**, y porque el
> ejemplo del propio documento original ("reservar turnos y recibir notificaciones") es literalmente
> el caso de Carolina. Ver §8.2.

### 2.5 El usuario que el documento original nunca menciona

> ## P3 · El proveedor de agentes
>
> Si los agentes se contratan y cobran entre sí, **alguien los ofrece.** El documento no lo nombra
> en ninguna parte.
>
> **Esto tiene una implicación estructural:** si el mercado de agentes es abierto, Brújula es un
> **marketplace de dos lados** y falta la mitad del análisis —por qué se sumarían los proveedores,
> cómo se garantiza su calidad, cómo se resuelven las disputas.
>
> ❌ **La `pm-knowledge-base` no contiene material sobre marketplaces de dos lados.** Registrado
> como pregunta abierta en §11.
>
> **Decisión para el MVP:** los agentes son **propios**. Sin terceros. Eso elimina el lado dos y
> reduce el alcance a un producto de un solo lado. La apertura es una decisión posterior, no de la
> hackathon.

---

## 3. Investigación de mercado

### 3.1 El mercado de generación

| Hecho | Dato | Fuente |
|---|---|---|
| Lovable — Serie B | **US$ 330M a valuación de US$ 6.600M**, dic 2025, liderada por CapitalG y Menlo | [R08] 🟢 TechCrunch |
| Lovable — ARR | **US$ 200M (nov 2025) → US$ 500M (jun 2026)** | [R08] |
| Lovable — Serie C | **US$ 400M a US$ 13.300M**, ago 2026 | [R08] 🟢 TechCrunch |
| Lovable — velocidad | US$100M ARR en 8 meses desde el lanzamiento (2024) | [R08] |
| Replit | de US$10M a US$100M ARR en nueve meses | [R07] ⚠ |
| Replit Agent | lanzado sept 2025, *"10x más autonomía"*, testing en navegador real | [R07] ⚠ |

> **Lectura.** Esto no es un mercado emergente. Es un mercado con un líder capitalizado a
> US$13.300M creciendo 2,5x en siete meses. **Entrar a competir en generación es competir contra
> eso, con 11 días y sin equipo formado.**

### 3.2 El mercado de confianza — el hueco

| Hecho | Dato | Fuente |
|---|---|---|
| Brecha adopción/confianza | **92% adopción diaria / 29% confianza** | [R09] ⚠ |
| Apps escaneadas pasivamente | **30.998** aplicaciones en producción, ago 2026 | [R10] ⚠ |
| Lectura anónima de tablas | **57%** de las apps Supabase alcanzables (2.096 / 3.680) | [R10] ⚠ |
| Escritura/borrado anónimo | 16% | [R11] ⚠ |
| Secretos en el bundle | **1.332 apps — 1 de cada 23** | [R10] ⚠ |
| Source maps públicos | 13% | [R10] ⚠ |
| Tablas con nombres de datos personales expuestas | 394 apps | [R10] ⚠ |
| Crecimiento de CVEs atribuibles a IA | **18 casos en 7 meses de 2025 → 56 en 3 meses de 2026** (35 solo en marzo) | [R12] 🟢 Georgia Tech |

> **Ninguna herramienta de generación líder ofrece una atestación de que lo generado es seguro.**
> Esa es la conclusión operativa. No es que lo hagan mal — **es que no es el producto que venden.**

### 3.3 El mercado de pagos entre agentes

| Hecho | Dato | Fuente |
|---|---|---|
| Tamaño proyectado del comercio agéntico | **US$ 3–5 billones (trillion) en ingresos B2C para 2030** — Galaxy Research, citado por SDF | [R02] ⚠ proyección |
| x402 | protocolo abierto de Coinbase Developer Platform, **documentado oficialmente en Stellar** | [R04] 🟢 |
| MPP | **lanzado en marzo de 2026 por Stripe y Tempo (Paradigm)** | [R06] ⚠ |
| Organismo de estándares | x402 Foundation, **~40 miembros incluidos Visa, Mastercard, American Express y Stripe** | [R01] ⚠ |
| Caso real en producción | Nous Research factura **por inferencia** de su modelo Hermes 4 vía x402 | [R02] |
| Infraestructura ya viva | **MPP Router: 446 rutas pagables en 20 servicios verificados** (OpenAI, Anthropic, DeepSeek, Perplexity, Exa, Firecrawl, Tavily), mainnet desde **9 jul 2026** | [R06] ⚠ |

> **La consecuencia para el alcance es enorme:** *"los agentes pagan por su uso de LLM"* —punto 4
> del documento original— **ya existe como infraestructura desplegada.** No hay que construirlo.
> Hay que consumirlo.

### 3.4 El contexto argentino

| Hecho | Dato | Fuente |
|---|---|---|
| Volumen cripto en pesos que va a stablecoins | **94%** — el más alto de cualquier moneda importante rastreada por Artemis | [R15] 🟢 a16z crypto, 30 ago 2026 |
| Penetración | **~1 de cada 5 argentinos** usa cripto | [R15] |
| Inflación mensual | de un pico de 25,5% a **2,1%** | [R15] |
| Brecha del dólar digital | ~4% sobre el oficial a fines de agosto 2026 | [R15] |
| Costo de desarrollo | **US$ 20–60/hora**; app simple ~ARS 1,5M | [R14] ⚠ |
| Mantenimiento | **15–20% anual** del costo de desarrollo | [R14] ⚠ |

> **Pagar en USDC sobre Stellar no es fricción añadida en Argentina — es el comportamiento
> mayoritario ya existente en el segmento cripto-activo.** Y el 4% de brecha significa que el
> costo de conversión es bajo.

### 3.5 Una cifra que se investigó y se descartó

Una búsqueda devolvió *"mercado de US$4.700M con 63% de usuarios no desarrolladores"*. **Al abrir
la fuente original, la página no contiene esos números ni cita ninguna fuente externa; es el blog
de un competidor.** La cifra se descarta.

> ❌ **No existe dimensionamiento público confiable de la categoría de generadores de aplicaciones
> con IA.** Cualquier TAM que se presente en el pitch tendrá que construirse bottom-up y
> declararse como estimación propia.

---

## 4. Competencia

Método: [S025] — *"seleccioná de cinco a siete competidores entre directa, indirecta y sustituta."*
El documento original nombraba cero.

### 4.1 Mapa competitivo

| # | Competidor | Categoría | Qué hace bien | Dónde deja el hueco |
|---|---|---|---|---|
| 1 | **Lovable** | Directo | Onboarding más suave; default para fundadores no técnicos. US$500M ARR [R08] | **No atesta seguridad.** Genera |
| 2 | **Bolt** | Directo | Más control, entrada más barata [R07] | Ídem |
| 3 | **Replit Agent** | Directo | Testing en navegador real; **puede generar otros agentes** [R07] | Ídem. **El más cercano a Brújula arquitectónicamente** |
| 4 | **v0 (Vercel)** | Directo | Apps Next.js con base de datos incluida [R07] | Ídem |
| 5 | **Freelancer / software factory argentina** | **Sustituto humano** | **Alguien responsable si falla.** US$20–60/h [R14] | Costo mínimo supera el valor anual del problema para PyMEs |
| 6 | **Statu quo — planilla + WhatsApp** | **Sustituto / "no hacer nada"** | Costo cero, riesgo cero, ya funciona | Pierde turnos, no escala |
| 7 | **Escáneres de seguridad** (Snyk, Semgrep, VibeEval) | **Adyacente — y potencial socio** | Encuentran las vulnerabilidades | **Le hablan a ingenieros.** Reportan; no arreglan ni atestan |

### 4.2 La categoría que [S025] llama la más importante

> *"En muchos casos, **el verdadero competidor es el flujo de trabajo existente, no otro producto
> de software.**"* [S025] — converge con [S054]: *"la competencia más significativa no es otro
> producto similar sino **el statu quo**."*

Para P1 (Martín) el statu quo no es una planilla: **es generar con Lovable y no mirar.** Ese es el
competidor real, y es gratis, rápido y ya está en su flujo.

### 4.3 La pregunta competitiva que el documento original no respondía

[S090] exige: *"¿Qué harás diferente? ¿Cómo destacarás en un mercado saturado?"*

> #### ¿Por qué una red de agentes que se contratan y se pagan, en lugar de un solo agente capaz?
>
> **La investigación encontró una respuesta, y es incómoda para la versión original.**
>
> Anthropic publicó guía específica el **23 de enero de 2026** [R16]. Sus condiciones donde el
> multi-agente **no ayuda**:
>
> - *"**Trabajo secuencial fuertemente acoplado**: los traspasos pierden contexto por efecto
>   teléfono descompuesto"*
> - *"**Dependencias compartidas**: cuando los agentes necesitan sincronización constante"*
> - *"**Descomposición por tipo de problema: dividir por tipo de trabajo (planificación,
>   implementación, testing) crea sobrecarga de coordinación**"*
>
> **La arquitectura original de Brújula —Frontend Agent, Backend Agent, Database Agent, UI/UX
> Agent, Security Agent, QA Agent, Deployment Agent— es literalmente descomposición por tipo de
> trabajo.** Es el caso que Anthropic nombra como el que no funciona.
>
> Y el costo: *"las implementaciones multi-agente típicamente usan **3–10x más tokens** que los
> enfoques de un solo agente para tareas equivalentes"* [R16].

**Pero el mismo documento nombra el patrón que sí funciona:**

> *"El enfoque multi-agente más confiable usa un **agente de verificación dedicado que prueba la
> salida como caja negra contra criterios explícitos**, minimizando los requisitos de transferencia
> de contexto."* [R16]

> ### Esa es la respuesta a "por qué nosotros"
>
> **No porque tengamos siete especialistas. Porque tenemos un verificador que cobra por atestar, y
> especialistas que no cobran si no pasan.** Nadie más en la tabla §4.1 hace eso — y es, además, el
> único patrón multi-agente que la mejor guía disponible respalda.

### 4.4 Dentro del ecosistema Stellar

| Proyecto | Qué hace | Implicación |
|---|---|---|
| **MPP Router** | Paga 446 rutas en 20 servicios con USDC de Stellar. Mainnet desde 9 jul 2026 [R06] | **Infraestructura a consumir, no competidor.** Resuelve el pago de LLMs |
| **AI Real World Payment Agents** | Proyecto en el SCF [R17] | ❌ Detalle no investigado. Revisar antes de aplicar al SCF |
| **Stellar Hacks: Agents** (DoraHacks) | Hackathon previa de agentes + x402 + MPP [R06] | Ya hubo builders en este espacio. **Revisar entregas antes de posicionarse** |

---

## 5. Hipótesis

Formato: creencia falsable + cómo se rompe. Ordenadas por el cuadrante **importancia × incertidumbre**
de [S087]: *"los supuestos que son a la vez críticos e inciertos son prioridad máxima."*

### 5.1 Hipótesis críticas — validar primero

> **H1 · Valor.** Existe un segmento que ya generó software con IA y **pagaría por una atestación
> independiente** de que es seguro y desplegable.
> **Se rompe si:** los usuarios dicen que les importa pero no pagan, o si asumen que la herramienta
> generadora ya lo garantiza.
> **Evidencia a favor:** 92% adopción / 29% confianza [R09]. **Evidencia en contra:** ninguna
> encontrada. **La brecha de confianza está medida; la disposición a pagar por cerrarla no.**

> **H2 · Arquitectura.** Una cadena de agentes con **verificación dentro de cada etapa** produce
> resultados materialmente mejores que un solo agente con las mismas herramientas.
> **Se rompe si:** un agente único con un bucle de verificación iguala el resultado a 3–10x menos
> tokens — que es exactamente lo que [R16] sugiere que puede pasar.
> **⚠ Esta es la hipótesis que la evidencia actual pone en duda, no a favor.**

> **H3 · Verificación.** La verificación automática detecta suficientes fallos como para que el
> usuario no técnico no necesite revisar.
> **Se rompe si:** el verificador tiene el *"**problema de la victoria temprana**: verificadores que
> marcan salidas como aprobadas tras pruebas mínimas"* [R16]. **Es un modo de fallo nombrado, no
> hipotético.**

> **H4 · Economía.** El pago condicionado a evidencia **cambia el comportamiento** de los agentes
> frente a simplemente registrar el resultado.
> **Se rompe si:** el mismo resultado se obtiene con un flag booleano y el pago es contabilidad.
> **Esta hipótesis es la que justifica que haya blockchain.** Si cae, Stellar es opcional.

> **H5 · Expresión.** Un usuario no técnico puede expresar la intención con precisión suficiente.
> **Se rompe si:** el output correcto depende de detalles que el usuario no sabe que existen.
> **Mitigación conocida:** EARS [E014] tiene un patrón específico para el caso — *"**If** `<disparador>`,
> **then** el `<sistema>` **shall** `<respuesta>`"* — y es el que los PM más omiten. Un agente
> humano pregunta qué hacer cuando la tarjeta es inválida; **un agente de IA elige algo plausible.**

### 5.2 Hipótesis secundarias

| # | Hipótesis | Se rompe si |
|---|---|---|
| H6 | El destinatario puede desplegar y mantener lo que recibe | No puede — [R14]: 15–20% anual de mantenimiento que nadie hará |
| H7 | Un boletín de calificaciones legible es más valioso que el código | El usuario quiere el código y el boletín le resulta indiferente |
| H8 | Los agentes con RAG especializado superan a los agentes con solo prompt | ❌ No investigado |
| H9 | Pagar en USDC sobre Stellar no añade fricción en Argentina | Añade — aunque [R15] sugiere fuertemente que no |

---

## 6. Validación

### 6.1 Lo que se puede validar en 11 días, y lo que no

| Hipótesis | ¿Validable antes del 27/09? | Método |
|---|---|---|
| **H2 · Arquitectura** | ✅ **Sí** | **Prueba A/B interna**: mismo enunciado, un agente con verificación vs tres agentes con verificación. Medir tasa de convergencia, tokens y hallazgos del escáner. **Es el experimento más valioso y cuesta horas, no días** |
| **H3 · Verificación** | ✅ **Sí** | 20–50 tareas extraídas de fallos reales [E011]. **Sembrar deliberadamente vulnerabilidades conocidas** (tabla Supabase abierta, secreto en el bundle) y medir cuántas detecta |
| **H4 · Economía** | ✅ **Sí** | Ejecutar con el gate de pago activo y desactivado. ¿Cambia algún resultado observable? **Si no cambia nada, decirlo — es un hallazgo** |
| **H5 · Expresión** | 🟨 **Parcial** | 5 personas describen una app en lenguaje natural. Contar cuántos requisitos EARS quedan sin especificar |
| **H1 · Valor** | ❌ **No** | Requiere **8–10 entrevistas** [S081]. ⚠ Cifra declarada sin justificación por la fuente. **Hacerlas durante el sprint de Instaward, no ahora** |
| **H6 · Despliegue** | ❌ **No** | Requiere observar a un usuario real intentándolo |

### 6.2 La advertencia sobre qué cuenta como validación

> - **El interés declarado es actitudinal** [S081][S074]. *"¿Pagarías por esto?"* no es evidencia.
> - [S074]: *"**Tanto los datos cualitativos como los cuantitativos pueden mentir. Los números no
>   siempre dicen la verdad, pero los clientes tampoco.**"*
> - **[E006]** midió el caso extremo: desarrolladores predijeron que la IA los haría **24% más
>   rápidos**, reportaron después **20% más rápidos**, y midieron **19% más lentos**. *"Están bien
>   calibrados sobre cuánto tarda una tarea, pero **sus expectativas sobre la utilidad de la IA
>   están invertidas.**"*
>
>   ⚠ **Condiciones de alcance obligatorias**: 16 desarrolladores experimentados, sus propios
>   repositorios grandes y maduros, herramientas de principios de 2025. **[E007]: los propios
>   autores creen que el panorama cambió y que sus datos nuevos son "evidencia muy débil" del
>   tamaño del cambio.** No es un pronóstico para Brújula.
>
> **La lección transferible no es "la IA es lenta". Es: el autorreporte no es medición.**

### 6.3 Diseño del experimento decisivo (H2)

```
Enunciado fijo: "Sistema de turnos con notificaciones por email"

Brazo A — 1 agente + bucle de verificación
Brazo B — 3 agentes (build / verify / integrate) + bucle de verificación
Brazo C — 3 agentes SIN verificación   ← control

5 ejecuciones desde cero por brazo. Medir:
  · tasa de convergencia (pasa los criterios EARS §7 del PRD)
  · tokens consumidos
  · hallazgos de un escáner externo sobre el output
  · reintentos hasta converger

Resultado que cambia la estrategia:
  Si A ≈ B → la especialización no aporta; el valor está en la verificación.
             Simplificar y decirlo en el pitch. Es un hallazgo publicable.
  Si B > A → la especialización aporta. Cuantificar cuánto y a qué costo de tokens.
  Si C ≪ A,B → la verificación es el mecanismo. Es la tesis del producto, demostrada.
```

> **Este experimento vale más que una feature adicional.** Produce un dato que, según §11, **no
> existe públicamente**, y responde la única pregunta que un juez de hackathon o un evaluador del
> SCF va a hacer: *¿por qué así y no más simple?*

---

## 7. Oportunidades

### 7.1 Oportunidad primaria — **recomendada**

> ## Ser la capa de verificación y liquidación del software generado por IA
>
> **Tesis.** Generar está resuelto y bien capitalizado [R08]. **Atestar no lo está** [R09][R10][R12].
> Brújula produce, junto al código, **evidencia firmada** de que pasó criterios explícitos, y
> **libera el pago contra esa evidencia.**
>
> **Por qué es defendible:**
> - **Diferenciación real** — ninguno de los 4 competidores directos lo hace (§4.1)
> - **Respaldada por la mejor guía disponible** — es el patrón del verificador dedicado [R16]
> - **Nativa de Stellar** — pago-contra-prueba *es* un problema de pagos, no un adorno
> - **El multi-agente se vuelve necesario**, no decorativo: el verificador debe ser independiente
>   del constructor para que la atestación signifique algo
>
> **Encaje con la hackathon** — contra los cuatro criterios publicados:
>
> | Criterio | Cómo responde |
> |---|---|
> | **Validación del problema** | 57% de apps con lectura anónima, 30.998 escaneadas [R10] |
> | **Foco de negocio** | Mercado de US$13.3B en generación [R08]; la confianza es el cuello sin resolver |
> | **Foco de producto** | El usuario recibe **un boletín que puede reenviar**, no un dashboard |
> | **Ejecución técnica** | MPP/x402 son **building blocks oficiales** [R04][R05] — la integración es sustantiva, no decorativa |

### 7.2 Oportunidades secundarias

| # | Oportunidad | Estado |
|---|---|---|
| **O2** | **Verificar output de otras herramientas.** Subís lo que generó Lovable → Brújula lo audita y atesta | **Complemento en lugar de competir.** Reduce el alcance drásticamente. Mercado inmediato: los usuarios de §3.1 |
| **O3** | **Vertical argentino: turnos + notificaciones**, desplegado y mantenido | Es P2 (Carolina). Requiere operación continua. **Post-SCF** |
| **O4** | **Marketplace abierto de agentes** | Requiere el lado dos (§2.5). ❌ La KB no cubre marketplaces |
| **O5** | **Publicar la evidencia de H2** como investigación abierta | **Barato y diferenciador.** §11 dice que este dato no existe públicamente |

> **[JUICIO DEL PM] O2 es la jugada más subestimada.** Convierte a los cuatro competidores directos
> en canal de distribución en lugar de en rivales, y el alcance de ingeniería se desploma: no hay
> que generar nada.

---

## 8. Riesgos

Método: taxonomía de 16 ítems de [S087], más los riesgos encontrados en la investigación.

### 8.1 Riesgos rojos

| # | Riesgo | Evidencia | Respuesta [S065] |
|---|---|---|---|
| **R1** | **La descomposición por tipo de trabajo es el patrón contraindicado** | [R16] la nombra explícitamente. 3–10x tokens | **EVITAR** — rediseñar a build/verify/integrate |
| **R2** | **Victoria temprana del verificador** — aprueba tras pruebas mínimas | [R16] lo nombra como modo de fallo principal | **MITIGAR** — criterios explícitos + calibración humana de muestra. ⚠ Riesgo residual: no detectado entre muestras |
| **R3** | **Fondos reales + agentes autónomos + código de hackathon** | [S106]: consecuencia alta × probabilidad alta = **temerario** | **EVITAR** — testnet. Ver §8.3 |
| **R4** | **La cadena no converge en la demo en vivo** | Aritmética de §8.4 | **MITIGAR** — 3 agentes, no 7 + ejecución grabada de respaldo |
| **R5** | **El usuario no puede desplegar ni mantener la ZIP** | [R14]: 15–20% anual de mantenimiento | **ACEPTAR y declarar** — el MVP apunta a P1, no a P2 |
| **R6** | **Sobreingeniería** — *"construir más de lo necesario añade complejidad y retrasos"* [S087] | 7 agentes + wallets + pagos + RAG en 11 días | **EVITAR** — MoSCoW del PRD §20 |
| **R7** | **Dependencia de un solo proveedor de modelos** — *"riesgo estructural que no podés controlar del todo"* [S087] | — | **ACEPTAR** — decisión registrada, no omisión |
| **R8** | **Un incumbente añade verificación como feature** | Replit Agent ya hace testing en navegador real [R07] | **MONITOREAR** — la ventana es corta |

### 8.2 El riesgo que ninguna lista de la KB cubre

> **[JUICIO DEL PM]** El ejemplo trabajado de [S087] es una app de notas con edición en tiempo real
> que *"funcionaba perfectamente en pruebas. Técnicamente, sólida como una roca"* — y fracasó porque
> los usuarios no entendían cuándo usarla.
>
> **El análogo de Brújula:** entregar una ZIP técnicamente correcta y verificada a alguien que **no
> puede desplegarla ni mantenerla.** Para P2, *"un camino claro a producción"* no es un camino: es
> un obstáculo con formato de entregable.
>
> ❌ **La `pm-knowledge-base` no tiene material sobre onboarding ni activación.** Solo puedo
> nombrarlo. Es el gap que más dolió en este análisis y está registrado en el backlog.

### 8.3 El componente de mayor consecuencia y menor necesidad

[S106], matriz probabilidad × consecuencia del fallo:

| | Consecuencia baja | Consecuencia alta |
|---|---|---|
| **Probabilidad alta** | Tolerable | ⚠ **TEMERARIO** |
| **Probabilidad baja** | Seguro | **Calculado** |

Fondos **reales** + agentes autónomos + sin humano + software de 11 días → **temerario**.

[S106]: *"normalmente no podés cambiar la **consecuencia** del fallo, pero a menudo sí su
**probabilidad**."*

> **Traducción:** **Stellar testnet.** No es una versión degradada — [R04] confirma que el
> facilitador de Coinbase soporta testnet **con fees patrocinadas**, y [R05] que MPP corre allí. La
> demo se ve idéntica. El fallo cuesta un log mal calculado en lugar de dinero.
>
> Y hay un refuerzo: [R03] — las **reservas patrocinadas (CAP-33)** permiten crear las wallets de
> agente **con saldo inicial 0**, con el patrocinador cargando las dos reservas base. Sin eso, cada
> wallet de agente cuesta **1 XLM de mínimo** más 0,5 por subentrada. **Con 7 agentes eso es
> dinero inmovilizado por ejecución.**

### 8.4 La aritmética que gobierna el alcance

**[INFERENCIA] — marcada como tal.** [E011] define `pass^k`: probabilidad de que **todos** los *k*
intentos tengan éxito. Su ejemplo: 75% por intento en 3 intentos → **pass^3 ≈ 42%**.

⚠ [E011] mide **intentos repetidos de la misma tarea**; Brújula tiene **etapas distintas
encadenadas**. Es análogo matemáticamente, **no es lo que [E011] midió**, y como los intentos reales
no son independientes, el número puede ser **peor**.

| Fiabilidad por etapa | Éxito extremo a extremo · **7 etapas** | **3 etapas** |
|---|---|---|
| 95% | ≈ 70% | **≈ 86%** |
| **90%** | **≈ 48%** | **≈ 73%** |
| 85% | ≈ 32% | ≈ 61% |
| 75% | ≈ 13% | ≈ 42% |

> **Cada especialista adicional es otro multiplicando menor que 1.** Siete agentes al 90% entregan
> menos de la mitad de las veces; tres entregan tres de cada cuatro.
>
> **Y por eso la verificación rescata la arquitectura en lugar de ser un paso más:** si una etapa
> falla, se detecta y se reintenta, deja de ser un multiplicando frágil y pasa a ser un bucle con
> condición de salida. [E012] (`spec-kit`) lo implementa literalmente: *"Repetí implement → converge
> hasta que la convergencia reporte **Converged**."*
>
> **La verificación no es la sexta característica de Brújula. Es lo que hace que la aritmética
> funcione.**

---

## 9. Conclusiones

### 9.1 Lo que cambió respecto del documento original

| Original | Después de investigar | Por qué |
|---|---|---|
| *"Red de agentes que transforma intención en resultados"* | **Capa de verificación y liquidación del software generado por IA** | Generar está resuelto [R08]; atestar no [R10][R12] |
| 7 agentes por tipo de trabajo | **3 agentes: build / verify / integrate** | [R16] nombra la descomposición por tipo de trabajo como el caso que no funciona |
| Pagos con fondos reales en la hackathon | **Testnet, con liquidación real como paso posterior** | [S106] — temerario → calculado |
| *"Verificación"* como paso 6 del flujo | **Verificación dentro de cada etapa** | §8.4 — convierte `pass^k` en `pass@k` |
| Construir la capa de pagos | **Integrar MPP; consumir MPP Router** | [R05][R06] — ya existe en mainnet |
| Entregable: ZIP | **ZIP + boletín de evidencia firmado** | La evidencia es el diferencial; el código es commodity |
| Usuario: "gente no técnica con dinero" | **P1 · fundador técnico-adyacente pre-semilla** | [S081] exige un segmento estrecho |

### 9.2 Lo que la evidencia sostiene y lo que no

| Afirmación | Estado |
|---|---|
| Existe un problema de confianza medible en el software generado por IA | ✅ **Cinco fuentes independientes**, magnitudes variables |
| Stellar tiene la infraestructura para pago-contra-prueba | ✅ **Documentación oficial**, mainnet [R04][R05][R06] |
| La descomposición por tipo de trabajo es subóptima | ✅ **Guía primaria del proveedor**, ene 2026 [R16] |
| El patrón del verificador dedicado es el más confiable | ✅ [R16] |
| Alguien **pagará** por verificación de software generado | ❌ **Sin validar.** Es H1 y requiere entrevistas |
| El multi-agente supera al agente único aquí | ⚠ **La evidencia apunta en contra.** Es H2 y es el experimento decisivo |
| Un usuario no técnico puede desplegar una ZIP | ❌ **Sin validar**, y [R14] sugiere que no |

### 9.3 Lo que sigue sin respuesta en la literatura

> **No existe fuente publicada sobre cómo organizar un equipo de software multi-agente** — roles,
> traspasos, orquestación, escalado. La `pm-knowledge-base` lo registra explícitamente:
> *"Ninguna fuente consultada estudia el trabajo del product manager bajo implementación por
> agentes. Ni una."*
>
> **Eso corta para los dos lados:** Brújula no tiene manual que copiar, y tampoco hay literatura que
> diga que no funciona. Un equipo que **instrumente** lo que construye estaría produciendo datos que
> no existen públicamente. Ver O5.

---

## 10. Recomendación

### 10.1 La recomendación

> ## Construir un corte vertical de la capa de verificación, sobre Stellar testnet, con 3 agentes.
>
> **No construir:** siete especialistas · fondos reales · marketplace abierto · despliegue
> gestionado · RAG por especialista.
>
> **Sí construir:** un flujo completo para **una** categoría de aplicación, donde cada etapa se
> verifica, el pago se libera contra evidencia, y el usuario recibe **un boletín que puede
> reenviar**.

### 10.2 Por qué esta y no la original

| Criterio | Original | Recomendada |
|---|---|---|
| Probabilidad de demo funcionando | ~48% (7 etapas @90%) | **~73%** (3 etapas @90%) |
| Diferenciación vs Lovable/Bolt/v0 | ❌ Ninguna articulada | ✅ Atestación — nadie la ofrece |
| Necesidad genuina de blockchain | ⚠ Contabilidad interna | ✅ **Pago-contra-prueba es cumplimiento** |
| Consecuencia del fallo | Dinero real perdido | Números en un log |
| Encaje con criterios de la hackathon | Parcial | ✅ Los cuatro |
| Encaje con el SCF Integration Track | Débil | ✅ **Integra building blocks existentes** [R18] |

### 10.3 Secuencia de 11 días

```
D1–2   Rediseño a 3 agentes. Criterios EARS escritos (PRD §18).
       EXPERIMENTO H2 corriendo desde el día 1 — el dato llega antes del pitch.
D3–5   Bucle build→verify. Gate de convergencia. Sembrar vulnerabilidades y medir detección (H3).
D6–7   Integración MPP en testnet. Wallets con reservas patrocinadas (saldo 0).
       Pago liberado solo contra evidencia. Medir H4 con el gate on/off.
D8–9   Boletín de evidencia legible. Grabar ejecución de respaldo.
D10    Congelar. 5 ejecuciones desde cero. Registrar la tasa de convergencia real.
D11    Pitch con el número de convergencia adentro, no escondido.
```

> **Presentar la tasa de convergencia como parte de la demo convierte el fallo parcial en evidencia
> en lugar de en vergüenza.** *"Esto converge 4 de cada 5 veces; acá está dónde falla y por qué"* es
> una demostración más creíble de ingeniería seria que una ejecución perfecta e irrepetible.

### 10.4 Condición de muerte — escribir antes de empezar

[S031]: *"**Los equipos que escriben la condición de muerte antes de lanzar son los que realmente
matan la feature cuando se alcanza el umbral. Los que se saltan ese paso siempre encuentran una
razón para seguir 'iterando'.**"* ⚠ Experiencia del autor, no medido.

> **Si al 27 de septiembre la cadena no produce un proyecto que pase los criterios EARS en al menos
> 3 de 5 ejecuciones desde cero, la arquitectura multi-agente se declara no demostrada, y la
> siguiente iteración se hace con un agente único más verificación — no con más agentes.**

### 10.5 Las tres decisiones que hay que tomar esta semana

1. **¿Se acepta la reposición a capa de verificación?** Todo el PRD depende de esto.
2. **¿La economía entre agentes es cumplimiento o contabilidad?** Si es contabilidad, Stellar es
   opcional y el pitch pierde su ancla. La recomendación es tratarla como **cumplimiento**, y eso
   exige que el verificador sea independiente del constructor.
3. **¿P1 (fundador) o P2 (PyME)?** La recomendación es **P1** para el MVP. P2 es el mercado grande
   y requiere despliegue gestionado.

---

## 11. Preguntas abiertas

| # | Pregunta | Estado |
|---|---|---|
| Q1 | ¿Cómo se organiza un equipo de software multi-agente? | ❌ **Ninguna fuente.** Es lo que Brújula construye |
| Q2 | ¿Más especificación previa gana a dirección conversacional con agentes? | ❌ **Todo el movimiento SDD lo asume. No existe comparación controlada** |
| Q3 | ¿Cuál es la tasa de defectos a largo plazo del código escrito por agentes? | ❌ No medido |
| Q4 | ¿Cuánto cuesta realmente una ejecución extremo a extremo? | ❌ Sin modelo de costo. **Y con 3–10x de tokens [R16], es material** |
| Q5 | ¿Modelo de negocio: por ejecución, suscripción, o comisión sobre el pago? | ❌ **La KB no cubre pricing.** Gap declarado |
| Q6 | ¿Marketplace de dos lados? | ❌ **La KB no cubre marketplaces** |
| Q7 | ¿Qué proyectos del ecosistema Stellar ya trabajan en esto? | ⚠ **Investigación parcial.** Revisar "AI Real World Payment Agents" [R17] y las entregas de Stellar Hacks: Agents antes de aplicar al SCF |
| Q8 | ¿Cuántas PyMEs argentinas sin sistema de gestión? | ❌ **No se encontró estadística.** Se buscó y no existe públicamente |
| Q9 | Accesibilidad del producto generado | ❌ Ausente de la KB entera |

---

## Registro de investigación

| ID | Fuente | Tipo | Fiabilidad |
|---|---|---|---|
| **R01** | CoinDesk — organismo de estándares de pagos agénticos, jul 2026 | Prensa especializada | ⚠ B |
| **R02** | **stellar.org** — *x402 on Stellar: unlocking payments for the new agent economy* | **Oficial SDF** | 🟢 A (proveedor) |
| **R03** | **developers.stellar.org** — Lumens, reservas base; CAP-33 reservas patrocinadas | **Documentación oficial** | 🟢 A |
| **R04** | **developers.stellar.org/docs/build/agentic-payments/x402** | **Documentación oficial** | 🟢 A |
| **R05** | **developers.stellar.org/docs/build/agentic-payments/mpp** | **Documentación oficial** | 🟢 A |
| **R06** | mpprouter.dev — MPP vs x402; MPP Router (446 rutas / 20 servicios, mainnet 9 jul 2026) | Proveedor del ecosistema | ⚠ B |
| **R07** | Comparativas de AI app builders 2026 | Blogs de proveedores | ⚠ C |
| **R08** | **TechCrunch** — Lovable Serie B US$330M @ US$6,6B (18 dic 2025); Serie C US$400M @ US$13,3B (12 ago 2026); US$500M ARR jun 2026 | **Prensa tecnológica primaria** | 🟢 A |
| **R09** | Informes de tendencias de vibe coding 2026 (92% adopción / 29% confianza) | Blogs de proveedores | ⚠ C |
| **R10** | **VibeEval** — escaneo pasivo de 30.998 apps, 12–14 ago 2026; 57% Supabase lectura anónima (2.096/3.680); 1.332 apps con secretos | Proveedor de seguridad — **declara su interés comercial y publica su metodología** | ⚠ B |
| **R11** | Symbiotic Security — 42,3 vulns/repo IA vs 9,6 humano; 1.967 repos + 1.072 apps, 10 escáneres | Proveedor — **"asistido por IA" inferido de metadatos; leer como direccional** | ⚠ C |
| **R12** | **Georgia Tech SSLab** (Hanqing Zhao) — *Vibe Security Radar*; 43.000 advisories, 74 casos confirmados; 18 casos/7 meses 2025 → 56/3 meses 2026 | **Investigación académica** | 🟢 A |
| **R13** | Veracode — 45% de muestras con OWASP Top 10, 100+ modelos | Proveedor de seguridad | ⚠ B |
| **R14** | Guías de costos de desarrollo Argentina 2026 — US$20–60/h; app simple ~ARS 1,5M; mantenimiento 15–20%/año | Software factories argentinas | ⚠ C |
| **R15** | **a16z crypto / Artemis**, 30 ago 2026 — 94% del volumen cripto en pesos es stablecoins; ~1 de cada 5 argentinos; inflación 25,5% → 2,1% | **Investigación de fondo + firma de analítica** | 🟢 A |
| **R16** | **Anthropic** — *When to use multi-agent systems (and when not to)*, **23 ene 2026**, Cara Phillips et al. | **Guía primaria del proveedor** | 🟢 A (proveedor) |
| **R17** | communityfund.stellar.org — proyecto *AI Real World Payment Agents* | Listado oficial | ⚠ no investigado |
| **R18** | **stellar.gitbook.io/scf-handbook** — Build Award hasta US$150k, tracks Open/Integration/RFP, tramos 10/20/30/40%, mainnet en ~4 meses, KYC obligatorio | **Handbook oficial** | 🟢 A |

### Fuentes descartadas

| Fuente | Motivo |
|---|---|
| *"Mercado de US$4.700M, 63% usuarios no desarrolladores"* | **La página original no contiene esos números ni cita fuente alguna.** Es el blog de un competidor. Descartada |

### Método de producto

`pm-knowledge-base` v1.1.0 — [S025] [S031] [S052] [S054] [S065] [S074] [S081] [S084] [S085] [S087]
[S090] [S106] [S127] · [E006] [E007] [E008] [E011] [E012] [E014]

---

*Documento 1 de 2. Continúa en `02-product-requirements-document.md`.*

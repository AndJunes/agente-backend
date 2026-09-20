# Análisis de Producto — Brújula

**Documento analizado:** `brujula-vision-hackathon-target.md` — *Brújula — Vision & Hackathon Target*
**Analista:** PM Agent operando sobre `pm-knowledge-base` v1.1.0
**Fecha:** 16 de septiembre de 2026
**Propósito doble:** (1) analizar la idea de producto; (2) **probar si la Knowledge Base funciona**
como fuente de un PM Agent. La §14 evalúa lo segundo.

---

## Cómo leer este informe

Cada afirmación lleva el ID de su fuente. Dos registros separados, deliberadamente:

| Marca | Significado |
|---|---|
| `[Snnn]` | Fuente del **corpus original** (143 PDFs) — resolver en `SOURCES.md` |
| `[Ennn]` | Fuente de **investigación externa Fase 2** — registro aparte en `SOURCES.md` |
| **[CORPUS]** | La relación la afirma una fuente |
| **[SÍNTESIS]** | Inferencia de la KB combinando fuentes — **ninguna fuente lo dice sola** |
| **[INFERENCIA]** | Conclusión trazada entre fuentes **que no fueron diseñadas para sostenerla** — más débil que [SÍNTESIS] |
| **[JUICIO DEL PM]** | Mi valoración, **no respaldada por la KB**. Separada explícitamente |
| ⚠ | Disputado, no verificado, o gap documentado |
| ❌ | **La KB no puede responder esto.** No se rellena desde memoria |

> **Regla aplicada en todo el informe** (`README.md` §Rules, reglas 4 y 6): donde la KB no tiene
> material, lo digo. *"Esta base de conocimiento no cubre X"* es una respuesta correcta y útil, y
> es mejor que una respuesta ensamblada desde tres menciones de pasada.

---

## 1. Clasificación del documento: qué es y qué no es

Antes de analizar el contenido hay que saber **qué tipo de artefacto es**, porque de eso depende
qué se le puede exigir.

### 1.1 El diagnóstico de [S090]

> *"El fallo: muchos equipos **confunden un plan de producto con una estrategia de producto**...
> la gente cae en la trampa de pensar que **el plan de cómo van a construir algo nuevo es en sí
> mismo una estrategia de producto. Esto es especialmente común en compañías en etapa temprana o
> en equipos sin liderazgo de producto fuerte.**"* [S090]

La KB deriva de ahí un test **[SÍNTESIS]**:

> *Si el documento responde **qué construiremos y cuándo**, es un plan. Si responde **por qué
> esto, para quién y por qué nosotros**, se acerca a una estrategia. Un plan que no puede explicar
> por qué se rechazaron las alternativas es una lista.*

### 1.2 Resultado del test

| Pregunta que exige una estrategia [S090] | ¿La responde el documento? |
|---|---|
| **¿Quiénes son tus clientes?** | ⚠ Parcial — *"personas que pueden pagar tecnología pero no tienen el conocimiento técnico"*. Es una **categoría**, no un segmento (ver §2.1) |
| **¿Qué problemas resolverá tu producto?** | ✅ Sí, implícito: no poder construir software sin equipo técnico |
| **¿Qué oportunidades y amenazas enfrentas?** | ❌ **No aparecen** |
| **¿Qué harás diferente?** | ⚠ Se describe la **arquitectura** (agentes que se contratan y pagan), no el diferencial para el usuario |
| **¿Cómo destacarás en un mercado saturado?** | ❌ **No aparece.** No hay una sola mención de competidores ni de alternativas |

[S040] exige que una estrategia válida enuncie: *"los **usuarios y clientes** que se beneficiarán,
las **necesidades** que atenderá, los **beneficios de negocio** que ofrecerá, y las
**características distintivas** que la separarán de las ofertas competidoras."* El documento
cubre la primera parcialmente y la última en términos técnicos, no competitivos.

### 1.3 Y la sección "Core vision" tampoco es una visión

[S094] (Marty Cagan, SVPG — la fuente más autorizada del corpus en esto) abre corrigiendo
exactamente este error:

> *"La mayoría de la gente que conozco, cuando me enseña su 'visión de producto', **lo que
> realmente me está enseñando es su declaración de misión.** Están **confundiendo un eslogan
> sobre su propósito con una visión de producto.**"* [S094]

La sección *Core vision* del documento —"Human provides the intention. Brújula provides the
expertise. Agents perform the work..."— son **nueve eslóganes**. Encaja exactamente en la
descripción de [S094].

Lo que [S094] dice que una visión de producto sí debe hacer:

| Función de una visión [S094] | ¿Presente? |
|---|---|
| *"Mantenernos **enfocados en el cliente**"* | ❌ El cliente aparece una vez, en abstracto |
| *"Servir de **North Star** para la organización de producto"* | ✅ Sí — esto sí lo logra |
| *"Mostrar **por qué este trabajo es significativo. Una lista de features en un roadmap no es significativa. Cómo puedes impactar positivamente la vida de usuarios y clientes sí lo es.**"* | ⚠ El documento es, estructuralmente, una lista de capacidades |
| *"Ilustrar **cómo planeamos aprovechar tendencias y tecnologías** para resolver problemas de formas que **apenas ahora son posibles**"* | ✅ **Muy bien** — es su punto más fuerte |
| *"Dar a ingeniería suficiente claridad para asegurar **una arquitectura que pueda servir la necesidad**"* | ✅ Sí, explícitamente |

### 1.4 Veredicto de clasificación

**El documento es una visión técnica + un plan de hackathon.** Es un buen documento de su tipo: la
arquitectura es clara, el objetivo del hackathon es concreto y la demo final es falsable.

**Lo que falta no es detalle. Es la capa de estrategia**: para quién exactamente, por qué eso, y
por qué esta forma y no otra.

> **[JUICIO DEL PM]** Esto **no es un defecto para un hackathon**. Es un defecto si este documento
> se usa después para decidir qué construir en el trimestre siguiente. La recomendación de §13
> separa esos dos usos.

---

## 2. Discovery: el problema y el usuario

Fuente principal: [S081] (proceso de 6 pasos), [S030], [S087], [S028].

### 2.1 Paso 1 de [S081] — "define y enmarca la oportunidad"

[S081] exige tres cosas en este paso. El documento cumple una.

| Requisito [S081] | Estado |
|---|---|
| Escribir un **enunciado del problema** con formato *"[Quién] tiene dificultad con [qué] porque [causa] lo cual impacta [consecuencia]"* | ❌ **Ausente.** Hay una descripción de solución, no de problema |
| Identificar **precisamente quién** lo experimenta — *"siendo tan específico y estrecho como sea posible"* | ❌ **La definición actual es lo contrario de estrecha** |
| Clarificar **por qué es estratégicamente importante** | ⚠ Implícito |

**El usuario declarado**, literal: *"people who may be able to pay for technology but do not have
the technical knowledge to build it themselves."*

> **[JUICIO DEL PM] — esta es la debilidad más grande del documento, y no es la que parece.**
> Esa frase describe a una dueña de restaurante, a un director de una ONG, a un abogado con una
> idea, a un product manager no técnico, a un fundador buscando prototipo para inversores, y a un
> departamento de marketing de una empresa grande. **Son mercados distintos con disposiciones a
> pagar, tolerancias al riesgo y definiciones de "terminado" incompatibles.**
>
> El abogado quiere algo que funcione y no le importa el código. El fundador quiere algo que pueda
> entregar a un CTO después. Marketing necesita que pase revisión de seguridad corporativa. **La
> misma ZIP no sirve para los tres.**

### 2.2 Redacción propuesta del enunciado de problema

Siguiendo el formato de [S081]. **Tres candidatos, para elegir uno — no los tres:**

```
A) Los fundadores no técnicos en etapa pre-semilla no pueden producir un prototipo
   funcional para validar su idea con usuarios o inversores, porque contratar
   desarrollo cuesta entre X y Y y tarda semanas, lo que hace que abandonen o
   validen con mockups que no prueban nada.

B) Los dueños de pequeños negocios con un proceso manual costoso (agendamiento,
   inventario, notificaciones) no pueden encargar software a medida porque el
   coste mínimo de una agencia excede el valor anual del problema, lo que les
   obliga a seguir con hojas de cálculo y WhatsApp.

C) Los equipos de producto no técnicos dentro de empresas medianas no pueden
   obtener herramientas internas porque IT tiene lista de espera de meses, lo
   que produce shadow IT y procesos en hojas de cálculo.
```

> **[JUICIO DEL PM]** Recomiendo **(B)**. Es el único donde el "do nothing competitor" (§3.2) es
> visible y medible, donde el resultado esperado es un sistema pequeño y acotado —el ejemplo del
> propio documento, *"reservar citas y recibir notificaciones"*, es exactamente eso— y donde la
> ausencia de un CTO que revise el código es una **característica** y no un riesgo oculto.
>
> **Esto es juicio mío, no de la KB.** [S081] es explícito en su limitación: *"No hay guía sobre
> umbrales. Ninguna fuente dice qué resultado debería disparar un **no**."*

### 2.3 ¿Aplica hacer un opportunity assessment completo?

[S081] trata el método como **condicional**, y esa tabla es lo más valioso que aporta:

| Situación | ¿Corresponde? |
|---|---|
| **"Construir un producto nuevo desde cero"** → sí, evita *"lanzar un producto que nadie necesita"* | ✅ **Aplica directamente** |
| **"Un iniciativa de bajo esfuerzo o 'construir para aprender'"** → no, *"sobreanalizar un prototipo desechable desperdicia la ventaja de velocidad de la experimentación rápida"* | ✅ **También aplica** — es un hackathon |

**Ambos aplican, y a cosas distintas.** Esa es la resolución:

> **[SÍNTESIS], derivada de [S081]:** *la profundidad de la validación debe escalar con el tamaño
> y la reversibilidad de la apuesta.*
>
> - **El hackathon es una apuesta reversible y barata** → no requiere assessment. Construir.
> - **La decisión de convertir Brújula en producto es una apuesta grande e irreversible** →
>   requiere el assessment completo, y **debe hacerse con lo que el hackathon enseñe**, no antes.

### 2.4 Mapa de supuestos

Método: **Assumption Mapping** de [S087] — *"revela las creencias ocultas detrás de las ideas de
producto y las grafica por **importancia** e **incertidumbre**. Los supuestos que son a la vez
críticos e inciertos se vuelven prioridad máxima de validación."*

Cuadrante operativo: **alta importancia + alta incertidumbre**.

| # | Supuesto extraído del documento | Importancia | Incertidumbre | Cuadrante |
|---|---|---|---|---|
| **A1** | Existe gente no técnica dispuesta a **pagar** por software encargado a agentes | 🔴 Crítica | 🔴 Alta | **VALIDAR PRIMERO** |
| **A2** | Una cadena de agentes especializados produce mejor resultado que **un solo agente capaz** | 🔴 Crítica | 🔴 Alta | **VALIDAR PRIMERO** |
| **A3** | La verificación automática es suficiente para que **ningún humano revise** el código | 🔴 Crítica | 🔴 Alta | **VALIDAR PRIMERO** |
| **A4** | El **pago agente-a-agente** es necesario para el valor, no solo contabilidad interna | 🔴 Crítica | 🔴 Alta | **VALIDAR PRIMERO** |
| **A5** | Un usuario no técnico puede expresar la intención **con suficiente precisión** | 🔴 Crítica | 🟠 Media-alta | **VALIDAR PRIMERO** |
| **A6** | El destinatario puede **desplegar y mantener** la ZIP que recibe | 🔴 Crítica | 🟠 Media | Validar |
| **A7** | "Arquitectura profesional" es un criterio que **se puede evaluar automáticamente** | 🟠 Alta | 🔴 Alta | Validar |
| **A8** | Los agentes con RAG especializado superan a los agentes con solo prompt | 🟠 Alta | 🟠 Media | Investigar si es barato |
| **A9** | La infraestructura de wallets se puede construir en el tiempo del hackathon | 🟠 Alta | 🟠 Media | Investigar si es barato |
| **A10** | El mercado no será capturado antes por un incumbente | 🟠 Alta | 🔴 Alta | Monitorear — no controlable |

> **A4 es el supuesto que más me interesa desafiar, y lo trato en §5.**

### 2.5 Advertencia sobre qué cuenta como validación

La KB contiene material que socava la validación ingenua, y aplica aquí:

- **El interés declarado es actitudinal** [S081], [S074]. Una landing page mide un clic, no una
  compra. Para A1 esto importa: *"¿pagarías por esto?"* no es evidencia.
- [S074]: *"**Tanto los datos cualitativos como los cuantitativos pueden mentir. Los números no
  siempre dicen la verdad, pero los clientes tampoco.**"*
- [S081] fija un mínimo operativo: **"Apunta a un mínimo de 8–10 conversaciones de calidad para
  identificar patrones claros."** ⚠ La KB marca esta cifra como *"declarada sin justificación"*.

---

## 3. Mercado y competencia

Fuente: [S025], [S054], [S005]. **Esta sección existe porque el documento no la tiene en absoluto.**

### 3.1 Lo que exige [S025]

> *"**Selecciona de cinco a siete competidores** entre las categorías directa, indirecta y
> sustituta."* [S025]

El documento nombra **cero**.

### 3.2 La categoría que el documento omite y que [S025] llama la más importante

> *"Parte de la **competencia más fuerte** viene de herramientas o flujos de trabajo que
> **reemplazan la necesidad de un producto dedicado.** Estos sustitutos incluyen a menudo **hojas
> de cálculo, dashboards internos, hilos de correo, documentos compartidos o procesos manuales de
> coordinación.**
>
> **En muchos casos, el verdadero competidor es el flujo de trabajo existente, no otro producto de
> software.** Entender **por qué los usuarios siguen con sus métodos actuales** ayuda a
> identificar barreras de adopción."* [S025]

Esto converge exactamente con [S054] (JTBD): *"la competencia más significativa para un producto
no es otro producto similar sino **el statu quo**."*

### 3.3 El mapa competitivo que falta

**[JUICIO DEL PM] — las categorías, con la advertencia de §3.4:**

| Categoría | Quién compite realmente | Por qué el usuario los elegiría |
|---|---|---|
| **Statu quo / no hacer nada** | Seguir con hojas de cálculo y WhatsApp | Coste cero, riesgo cero, ya funciona |
| **Sustituto humano** | Un freelancer, una agencia | Alguien responsable si falla. **Una persona a quien reclamar** |
| **Sustituto no-code** | Herramientas de construcción visual | No produce código que haya que mantener |
| **Agente único** | Un asistente de código capaz, usado directamente | **Menos piezas, menos fallos compuestos** (ver §6) |
| **Plataforma incumbente** | Un proveedor grande añadiendo esto como feature | Ya tiene la distribución y la confianza |

> **La pregunta competitiva que el documento nunca responde, y que es la más importante:**
>
> ### ¿Por qué una red de agentes especializados que se contratan y se pagan, en lugar de un solo agente capaz con buenas herramientas?
>
> El documento **asume** que la especialización y la economía entre agentes son mejores. No lo
> argumenta. [S090] exige exactamente esto: *"¿Qué harás diferente?"* — y la respuesta actual
> describe **cómo está construido por dentro**, que es una respuesta de arquitectura, no de
> producto.
>
> **Un usuario no técnico no puede percibir la diferencia entre siete agentes y uno.** Solo puede
> percibir el resultado. Si la arquitectura multi-agente no produce un resultado observablemente
> mejor, es **coste sin valor percibido**.

### 3.4 ⚠ Límite estricto de esta sección

> **La KB no contiene ningún nombre de competidor en esta categoría, ningún dato de mercado,
> ninguna estimación de tamaño.** [S081] menciona TAM pero la KB registra explícitamente:
> *"la estimación de TAM se nombra pero no se enseña; el corpus no tiene tratamiento de método de
> dimensionamiento de mercado (TAM/SAM/SOM, top-down vs bottom-up). Registrado como gap."*
>
> Además [S057]/[S031] traen afirmaciones de tendencia de 2026 que la KB marca como **caducables**:
> *"El método es duradero; los hallazgos no."*
>
> **Las categorías de §3.3 son estructura, no inteligencia de mercado.** Rellenarlas con nombres y
> cifras requiere investigación que no está hecha.

---

## 4. Estrategia: propuesta de valor y PMF

### 4.1 La propuesta de valor, tal como está

Extraída del documento: *"reunir el conocimiento, contexto, herramientas, documentación, sistemas
RAG y mecanismos de verificación que normalmente requerirían acceso a todo un equipo de
especialistas técnicos."*

**Es una propuesta de valor por sustitución de coste**: reemplazas un equipo. Eso es fuerte y
claro.

**Lo que no dice**, y [S040] lo exige: los **beneficios de negocio**. ¿Cuánto más barato? ¿Cuánto
más rápido? ¿Con qué garantía? Sin eso, no es comparable contra el freelancer de §3.3.

### 4.2 El test del 40%

[S005] ofrece el único test operativo del corpus:

> *Pregunta a los usuarios: **"¿Cómo te sentirías si ya no pudieras usar este producto?"**
> **Si el 40% responde "muy decepcionado" respecto a tu beneficio principal, tienes el
> product-market fit correcto.**"* [S005]

⚠ **Advertencias que deben viajar con este número**, según la propia KB: *"el corpus no contiene
evidencia primaria del umbral del 40%, ninguna información sobre requisitos de muestra, ninguna
discusión sobre a qué usuarios encuestar, y ninguna validación de que el umbral prediga algo. Es
una heurística ampliamente usada con un originador nombrado — no una constante medida."*

**No es aplicable todavía a Brújula** (requiere usuarios existentes), pero **sí define qué habría
que medir después del hackathon**, y es lo más cercano a un criterio de PMF que la KB ofrece.

### 4.3 ⚠ PMF es un gap declarado de la KB

> *"Product-market fit se referencia constantemente a lo largo del corpus y **no está definido
> apropiadamente en ninguna parte.** Ninguna fuente lo trata directamente."*
>
> Las cuatro definiciones disponibles **son incompatibles entre sí**: ¿es un umbral que cruzas,
> un grado de solapamiento, o una condición de mercado que mides? El corpus usa los tres sentidos
> indistintamente.

**No puedo decirte si Brújula tiene camino a PMF.** La KB no tiene el material para responderlo.

### 4.4 Lo que sí aporta [S111]

El encuadre estructural más útil disponible: PMF como **etapa**, no como propiedad.

```
Pre-PMF          → encontrar un mercado que quiera el producto      ← BRÚJULA ESTÁ AQUÍ
PMF inicial      → el umbral
  ├─ trabajo de features   ├─ trabajo de crecimiento   └─ trabajo de escalado
Saturación       → el crecimiento se ralentiza
Expansión de PMF → subir el techo de forma no incremental
```

> **La consecuencia que [S111] permite extraer**: *el tipo de trabajo de producto apropiado depende
> de dónde esté el producto en esta secuencia.* **Tácticas de crecimiento aplicadas pre-PMF
> aceleran el churn.**
>
> Brújula está en **pre-PMF**. La implicación operativa: el hackathon no debe optimizar
> pulido, escala ni onboarding. Debe optimizar **aprender si A1–A5 son ciertos**.

---

## 5. El componente que más necesita ser desafiado: la economía agente-a-agente

Trato esto aparte porque es donde el análisis produce la recomendación más concreta.

### 5.1 Lo que el documento afirma

> *"Un hito clave del hackathon es tener una **capa de pagos funcional** donde fondos reales
> puedan entrar al sistema y distribuirse automáticamente entre agentes."*

Y en la visión: *"Wallets provide the economic layer. Agent-to-agent payments enable autonomous
collaboration."*

### 5.2 La pregunta que la KB obliga a hacer

[S090]: *"**Las features individuales son una forma en que podrías lograr la estrategia de
producto**"* — no son la estrategia.

**¿Qué problema del usuario resuelve el pago entre agentes?**

Recorriendo el documento: **ninguno que esté enunciado.** El usuario financia Brújula una vez. Lo
que pasa después entre agentes es invisible para él. La frase *"agent-to-agent payments enable
autonomous collaboration"* es una afirmación de arquitectura.

Hay dos lecturas posibles, y son muy distintas:

| Lectura | Implicación |
|---|---|
| **(a) Es contabilidad interna** — atribuir coste por agente para saber qué es caro | **Un ledger interno lo resuelve.** No requiere fondos reales, ni wallets, ni blockchain |
| **(b) Es el producto** — un mercado abierto donde agentes de terceros ofertan y cobran | **Entonces Brújula no es un generador de software, es un marketplace**, y todo el análisis cambia: los usuarios son los proveedores de agentes tanto como los solicitantes |

> **[JUICIO DEL PM]** El documento no elige entre (a) y (b), y **esa indecisión es cara**. Si es
> (a), la capa de pagos es un detalle de implementación que está consumiendo presupuesto de
> hackathon como si fuera un hito. Si es (b), falta toda la mitad del análisis —los agentes
> proveedores son un lado del mercado y el documento no los menciona como stakeholders.

### 5.3 Aplicando el marco de decisión de [S106]

[S106] (Ravi Mehta, ex-CPO de Tinder) — la matriz de **probabilidad × consecuencia del fallo**:

| | Consecuencia baja | Consecuencia alta |
|---|---|---|
| **Probabilidad alta** | **Tolerable** | ⚠ **TEMERARIO** |
| **Probabilidad baja** | **Seguro** | **Calculado** |

**Fondos reales + agentes autónomos + sin humano en el bucle + código de hackathon:**

- **Consecuencia del fallo: alta.** Dinero real mal distribuido, potencialmente irreversible.
- **Probabilidad del fallo: alta.** Software nuevo, sin auditar, en el plazo de un hackathon.

→ **Cuadrante temerario.**

> [S106] señala exactamente la salida: *"normalmente no puedes cambiar la **consecuencia** del
> fallo, pero a menudo puedes cambiar su **probabilidad**... el entrenamiento ayuda a mover la
> decisión de temeraria a calculada."*

**Traducción operativa — la recomendación más fuerte de este informe:**

> **Demostrar la capa económica con un ledger contabilizado y fondos simulados, con un único punto
> de liquidación real y manual al final.** La demo se ve idéntica al espectador. La consecuencia
> del fallo cae de "dinero perdido" a "números mal calculados en un log". **Mueve la decisión de
> temeraria a calculada sin perder nada de la demostración.**

### 5.4 Y el gate que no es negociable

[S050] combinado con [S031], en la síntesis de la KB:

> *"**Seguridad y privacidad son restricciones de compuerta, no features negociables.** [S031] hace
> el mismo punto en términos de priorización: seguridad, privacidad y cumplimiento son **una
> compuerta dura — trátala como una precondición, no como un atributo negociable. Si la compuerta
> falla, ningún puntaje te saca de ahí.**"*

Un sistema que (1) mueve dinero real, (2) ejecuta código generado y (3) entrega artefactos
desplegables **cruza tres compuertas a la vez**. La KB es inequívoca: ninguna se compensa con
velocidad de demo.

---

## 6. Ejecución: el hallazgo central

Esta es la sección donde la KB aporta algo que el documento no tiene y que **cambia el diseño del
sistema**, no solo su evaluación.

### 6.1 La aritmética de las cadenas

[E011] (Anthropic, *Demystifying evals for AI agents*, 9 enero 2026) distingue dos métricas:

| Métrica | Mide [E011] |
|---|---|
| **pass@k** | Probabilidad de **al menos un** éxito en *k* intentos |
| **pass^k** | Probabilidad de que **todos** los *k* intentos tengan éxito |

Ejemplo trabajado de [E011]: con **75% de éxito por intento en 3 intentos, pass^3 ≈ 42%.**

### 6.2 Aplicación a Brújula — **[INFERENCIA], no afirmación de [E011]**

> ⚠ **Marca de procedencia obligatoria.** [E011] describe *k intentos repetidos de la misma tarea*.
> Brújula tiene *n etapas distintas encadenadas*. **Es una estructura matemáticamente análoga pero
> no es lo que [E011] midió.** Lo presento como inferencia, con su debilidad declarada: los
> intentos reales **no son independientes** —un fallo temprano contamina los siguientes— por lo que
> el número real puede ser **peor**, no mejor.

El flujo del documento tiene **9 etapas secuenciales**: planificar → identificar especialistas →
contratar → trabajar con RAG/tools → colaborar → verificar → pagar → integrar → empaquetar.

Tomando 7 como lectura conservadora (agrupando las administrativas):

| Fiabilidad por etapa | Éxito extremo a extremo (7 etapas) | (9 etapas) |
|---|---|---|
| **95%** | **≈ 70%** | ≈ 63% |
| **90%** | **≈ 48%** | ≈ 39% |
| **85%** | **≈ 32%** | ≈ 23% |
| **75%** | **≈ 13%** | ≈ 7,5% |

> ### El resultado que importa
>
> **Un sistema donde cada agente acierta el 90% de las veces —lo cual sería excelente— entrega un
> proyecto completo menos de la mitad de las veces.**
>
> Y el corolario que contradice la intuición del documento: **añadir un agente especializado más
> no mejora el sistema, lo empeora**, a menos que ese agente reduzca la tasa de fallo de otros más
> de lo que añade la suya. **Cada especialista es un multiplicando adicional menor que 1.**

### 6.3 Por qué esto **rescata** la propuesta en lugar de hundirla

La verificación no es una etapa más de la cadena. **Es lo que convierte pass^k en pass@k.**

Si una etapa falla y se **detecta** y se **reintenta**, esa etapa deja de ser un multiplicando
frágil y pasa a ser un bucle con reintentos. [E012] (GitHub `spec-kit`) implementa exactamente
esto:

> *"Repite implement → converge hasta que la convergencia reporte **Converged**."* [E012]

`/speckit-converge` es *"verificar que la implementación coincide con la especificación"* — un paso
de verificación **de primera clase, nombrado y repetido, con condición de terminación.** La KB
señala que el desarrollo tradicional no tiene equivalente: esa función está repartida entre code
review, QA y aceptación.

> **[SÍNTESIS] — la conclusión de diseño más importante de este informe:**
>
> **La verificación no es la sexta característica de Brújula. Es el producto.** Todo lo demás
> —especialización, RAG, wallets— es coste. Lo único que hace que la cadena de agentes sea viable
> en lugar de aritméticamente condenada es que **cada etapa pueda detectar su propio fallo y
> reintentar.**
>
> El documento lo trata como un paso al final del flujo (*Agent output → Verification → Evidence →
> Payment*). **Debería estar dentro de cada etapa, no al final de todas.**

### 6.4 Quién verifica al verificador

[E011] da los tres tipos de evaluador y sus compromisos:

| Evaluador | Fortalezas [E011] | Debilidades [E011] |
|---|---|---|
| **Basado en código** | Rápido, barato, objetivo, reproducible, fácil de depurar | **Frágil ante variaciones válidas**; sin matiz |
| **Basado en modelo** (LLM como juez) | Flexible, escalable, capta matiz, maneja tareas abiertas | **No determinista, caro, necesita calibración** |
| **Humano** | Calidad de referencia | Caro, lento, requiere experto |

El documento implica evaluación **basada en modelo** sin mencionar calibración.

> La KB advierte: *"Un evaluador basado en modelo no es un atajo que evite al humano; es una forma
> de **amortizar** el juicio del humano, y tiene que ser contrastado contra ese juicio
> periódicamente."*

**Para Brújula esto es literal:** el verificador es otro agente. Si nadie calibra al verificador
contra juicio humano, **el sistema puede converger con confianza a resultados equivocados** — y
lo hará silenciosamente, porque el usuario no técnico no puede detectarlo. Por construcción.

### 6.5 Y el modelo del queso suizo

> *"**Ninguna capa de evaluación individual atrapa todos los problemas. Con múltiples métodos
> combinados, los fallos que se escapan de una capa son atrapados por otra.**"* [E011]

Capas que [E011] nombra: evals en CI/CD · monitoreo en producción · A/B testing · muestreo de
transcripciones.

> **La implicación incómoda**: el modelo del queso suizo admite que **no apuntas a cero escapes,
> apuntas a capas no correlacionadas.** El documento dice *"Verification provides trust"* —
> singular. Un PM que pregunte *"¿cómo garantizamos que esto es correcto?"* está haciendo una
> pregunta que el modelo dice que no tiene respuesta.

### 6.6 Los seis errores de [E011], como checklist

| Error [E011] | Aplicación a Brújula |
|---|---|
| **1. Especificaciones de tarea ambiguas** | 🔴 **Presente.** Ver §7 — "arquitectura profesional" es exactamente esto |
| **2. Estado compartido entre intentos** | ⚠ Riesgo alto — los agentes comparten contexto de proyecto por diseño |
| **3. Evaluación demasiado rígida** que penaliza alternativas válidas | ⚠ Riesgo si se verifica contra una arquitectura esperada |
| **4. Conjuntos de evaluación desbalanceados** | ❓ No evaluable desde el documento |
| **5. Aislamiento insuficiente del entorno** | ⚠ Relevante — agentes que ejecutan código |
| **6. Bugs en el evaluador** y exigir reproducibilidad estricta a tareas estocásticas | ⚠ Relevante |

> **Los errores 1 y 3 son propiedad del PM**, no de ingeniería.

---

## 7. Requisitos: los criterios de aceptación son infalsables

### 7.1 El problema

El documento lista lo que debe tener el proyecto generado:

> *Arquitectura profesional · Código funcional · Dependencias correctas · Estructura clara ·
> Configuración de entorno · Setup de base de datos · Tests · Documentación · Configuración de
> despliegue · **Sin placeholders críticos** · **Un camino claro a producción**.*
>
> *"La experiencia debería **sentirse como si el trabajo lo hubiera producido un equipo
> experimentado de ingeniería de software**."*

**Ninguno de estos es verificable por una máquina.** Y el sistema está diseñado para que una
máquina los verifique.

### 7.2 EARS — la corrección

[E014] (Alistair Mavin y colegas, **Rolls-Royce plc, publicado 2009**) — notación de requisitos
pre-IA que las herramientas de SDD adoptaron.

**Plantilla genérica:** *"While `<precondición>`, when `<disparador>`, the `<sistema>` shall
`<respuesta>`."*

| Patrón | Sintaxis [E014] |
|---|---|
| **Ubicuo** | The `<sistema>` **shall** `<respuesta>` |
| **Dirigido por estado** | **While** `<precondición>`, the `<sistema>` **shall** `<respuesta>` |
| **Dirigido por evento** | **When** `<disparador>`, the `<sistema>` **shall** `<respuesta>` |
| **Feature opcional** | **Where** `<feature incluida>`, the `<sistema>` **shall** `<respuesta>` |
| **Comportamiento no deseado** | **If** `<disparador>`, **then** the `<sistema>` **shall** `<respuesta>` |

> **El patrón de comportamiento no deseado es el que los PMs más omiten.** Un implementador humano
> pregunta qué debería pasar cuando el caso falla; **un agente elige algo plausible.**

### 7.3 Reescritura propuesta

| Criterio actual (infalsable) | Reescrito en EARS (verificable) |
|---|---|
| *"Código funcional"* | The system **shall** produce a project where `npm install && npm run build` exits with code 0 in a clean container |
| *"Dependencias correctas"* | The system **shall** produce a lockfile in which every declared dependency resolves, and **shall** report zero high-or-critical advisories from the audit tool |
| *"Tests / validación donde aplique"* | **Where** the project contains business logic, the system **shall** produce an executable test suite in which all tests pass |
| *"Sin placeholders críticos"* | The system **shall** produce no file containing `TODO`, `FIXME`, `<YOUR_`, or `lorem ipsum` outside of `.env.example` and `README` |
| *"Configuración de entorno"* | The system **shall** produce `.env.example` declaring every variable read by the code, and **shall** produce no committed secret |
| *"Setup de base de datos"* | **Where** the project requires persistence, the system **shall** produce migrations that apply successfully against an empty database |
| *"Camino claro a producción"* | The system **shall** produce deployment configuration that completes a dry-run against the target platform |
| *"Arquitectura profesional"* | ❌ **No traducible.** Descomponer en propiedades medibles o **eliminar del contrato** |
| *"Se siente como un equipo experimentado"* | ❌ **No traducible.** Es una hipótesis a medir con usuarios, no un criterio de aceptación |
| **(ausente)** | **If** any verification step fails three consecutive times, **then** the system **shall** halt, **shall not** release payment, and **shall** report which criterion failed |

> **La última fila es la más importante y no está en el documento.** Es el patrón de comportamiento
> no deseado de [E014] aplicado al fallo del sistema completo. Sin él, no está definido qué pasa
> cuando la cadena no converge — y por §6.2, eso pasará la mayoría de las veces al principio.

### 7.4 Definition of Done ≠ criterios de aceptación

⚠ **Corrección que la KB aplica desde textos primarios** (`disputed-information.md` §6.1):

| | Alcance | Pregunta que responde |
|---|---|---|
| **Criterios de aceptación** | **Este ítem** | *¿Construimos lo correcto?* |
| **Definition of Done** | **El equipo o el producto** | *¿Es publicable?* |

[E001] (Scrum Guide 2020): la DoD es *"una descripción formal del estado del Incremento cuando
cumple las medidas de calidad requeridas para el producto"*, y **el trabajo no forma parte del
Incremento si no la cumple**. [E003] (Kanban) llega al mismo lugar independientemente: es una
**política explícita**.

> **Para Brújula esto tiene una traducción directa:** la lista de §7.1 no son criterios de
> aceptación de una feature. Es **la Definition of Done del artefacto que Brújula produce** — una
> política permanente que aplica a toda salida. Eso es exactamente lo que [E012] llama la
> **constitución** del proyecto: principios establecidos **una vez por proyecto** y aplicados a
> cada feature.
>
> [E003] añade la advertencia que corresponde: las políticas explícitas deben ser *"escasas,
> simples, bien definidas, visibles, **siempre aplicadas y fácilmente modificables**"* — y esas dos
> últimas van juntas. **Una constitución que se fosiliza es peor que ninguna.**

---

## 8. Alcance y priorización

### 8.1 Lo que falta: la sección "lo que no vamos a hacer"

Tres fuentes independientes del corpus tratan el enunciado negativo como un artefacto con nombre
propio, no como un apéndice. **Esta convergencia es la señal más fuerte del corpus en este tema:**

| Fuente | Nombre de la sección | Instrucción |
|---|---|---|
| [S138] | **"What we're not doing"** | *"Mantén al equipo enfocado señalando claramente lo que no estás haciendo"* |
| [S113] | **"Features Out"** | *"Qué has decidido explícitamente no hacer **y por qué**"* |
| [S084] | (dentro de Features) | *"ítems fuera de alcance"* |

> **Por qué funciona** [SÍNTESIS de la KB]: *"Una exclusión no enunciada es indistinguible de un
> descuido. Escribir 'no vamos a hacer X, porque Y' convierte una omisión silenciosa en una
> decisión registrada — lo que significa que puede ser cuestionada, revisada o citada después, en
> lugar de re-litigarse silenciosamente cada vez que alguien nota que falta X."*

[S113] añade el requisito del **"por qué"**, que los otros dos omiten. *"Mantener la justificación
es lo que hace la exclusión duradera: sin ella, el ítem vuelve en cuanto la persona que tomó la
decisión sale de la conversación."*

**El documento de Brújula no tiene esta sección.** Para un hackathon con siete tipos de agente,
wallets, pagos, verificación y empaquetado, es la omisión más costosa del documento.

### 8.2 El tope del 60% de MoSCoW

[S031] rescata una regla atribuida a los creadores del framework:

> *"**DSDM es explícito sobre una barrera que casi todo el mundo ignora: los ítems Must-have no
> deberían consumir más de ~60% del esfuerzo, con una reserva sana (a menudo ~20%) para
> Could-haves como contingencia de entrega.**
>
> La mayoría de equipos que veo inflan los Musts al 90%+ y pierden toda la contingencia. Cuando
> llega la sorpresa inevitable a mitad de sprint, lo único que queda por cortar es algo ya
> etiquetado como crítico de misión, que es **cómo el proceso de priorización se devora a sí
> mismo.**"*

⚠ **NO VERIFICADO** contra la documentación de DSDM, que no está en el corpus. La KB lo marca como
*"una afirmación específica y falsable sobre una fuente nombrada, lo que la hace digna de
verificar en lugar de descartar."*

**Aplicado a Brújula:** el documento marca **todo** como necesario para el hackathon. Musts al
100%, contingencia 0%.

### 8.3 MoSCoW propuesto para el hackathon

**[JUICIO DEL PM]**, respetando el tope del 60%:

| Bucket | Ítems | Justificación |
|---|---|---|
| **MUST (~60%)** | Agente PM que planifica y descompone · **2–3** agentes especialistas (no 7) · Bucle de verificación **dentro** de cada etapa · Ledger contabilizado (simulado) · ZIP que pasa los criterios EARS de §7.3 | Es el mínimo que **prueba o refuta A2, A3 y A5** — los supuestos críticos |
| **SHOULD (~20%)** | RAG por especialista · Los 4–5 agentes restantes · Manejo de fallo de convergencia | Mejora el resultado; no prueba nada nuevo |
| **COULD (~20% — contingencia)** | Liquidación real de fondos en un único punto manual · Reintentos entre agentes · UI pulida | **Reserva deliberada.** Se recorta primero cuando llegue la sorpresa |
| **WON'T (declarado)** | Mercado abierto de agentes de terceros · Despliegue automático a producción · Multi-usuario · Facturación · **Cualquier movimiento autónomo de dinero real** | §5.3 y §5.4. **Declarado, con motivo** |

> **El movimiento clave es reducir de 7 especialistas a 2–3.** Por §6.2, siete especialistas con
> 90% de fiabilidad cada uno dan ~48% de éxito extremo a extremo. **Tres dan ~73%.** Una demo que
> funciona tres de cada cuatro veces se puede enseñar; una que funciona una de cada dos, no.
>
> Y demuestra exactamente lo mismo: que un PM Agent puede contratar especialistas, que colaboran,
> que se verifican y que se liquida el pago. **El número siete no aporta evidencia adicional de
> nada.**

### 8.4 La condición de muerte

[S031] hace su afirmación más fuerte aquí:

> *"**Los equipos que escriben la condición de muerte antes de lanzar son también los equipos que
> efectivamente matan la feature después cuando se alcanza el umbral. Cuando los equipos se saltan
> ese paso, siempre encuentran una razón para seguir 'iterando' en lugar de tirar del enchufe.**"*
>
> La KB lo matiza: *"Se presenta como experiencia del autor, no como algo medido. Pero el mecanismo
> —pre-compromiso contra la racionalización futura— es reconocible y comprobable."*

**Condición de muerte propuesta para el hackathon, a escribir antes de empezar:**

> *Si al final del hackathon la cadena completa no produce un proyecto que pase los criterios EARS
> de §7.3 en **al menos 3 de 5 ejecuciones desde cero**, entonces la arquitectura multi-agente se
> declara no demostrada, y la siguiente iteración se hace con un solo agente más el bucle de
> verificación — no con más agentes.*

---

## 9. Métricas

### 9.1 ⚠ Este es un gap declarado de la KB

`README.md` §Rules, regla 5: **MVP y diseño de métricas siguen siendo gaps. No responder desde
aquí.**

**No puedo darte un plan de medición.** La KB lista explícitamente lo que no cubre: cómo elegir
métricas, indicadores adelantados vs rezagados, análisis de cohortes, diseño de A/B tests,
significancia estadística, taxonomía de eventos, ley de Goodhart, benchmarks.

### 9.2 Lo que sí aporta — y encaja notablemente bien

[S031] argumenta que los productos usados por humanos y por agentes necesitan **dos conjuntos de
métricas separados**:

| Flujo | Unidad de valor [S031] |
|---|---|
| **Humano** | Tiempo hasta primer uso, uso repetido, profundidad de uso, tasa de abandono por paso, lift de retención |
| **Agente** | **Completitud de tarea** — tasa de resolución de intención, precisión de llamada a herramientas, éxito de autenticación, latencia, **tasa de fallback, tasa de intervención humana** |

Su advertencia: *"**cuando un agente llama a una herramienta 50 veces en 30 segundos en lugar de
hacer clic en un botón una vez, el dashboard silenciosamente sub-reporta.**"*

⚠ **Fuente única, vendor, 2026, no verificada.**

> **Para Brújula esto es inusualmente directo: Brújula *es* el flujo de agente.** Las seis métricas
> de la fila inferior son literalmente el instrumento correcto, y **"tasa de intervención humana"
> es la métrica del producto entero** — porque la promesa es que sea cero.

### 9.3 Y lo que aporta [E011]

Dos tipos de eval con **objetivos de tasa de acierto opuestos**:

| Tipo | Pregunta | Tasa objetivo |
|---|---|---|
| **Capability evals** | ¿Qué hace bien el agente? Tareas **difíciles** | **Debe empezar BAJA** |
| **Regression evals** | ¿Sigue haciendo lo que ya hacía? | **Cerca del 100%** |

*"A medida que los capability evals se saturan, se gradúan al conjunto de regresión."* [E011]

Y el consejo de arranque, que contradice cómo la mayoría de equipos se atasca:

> *"**Empieza con 20–50 tareas simples extraídas de fallos reales** — no esperes a tener cientos.
> Tamaños de muestra pequeños detectan cambios significativos al inicio del desarrollo."* [E011]

Saturación: *un eval al 100% ya no señala mejora.* [E011] marca **>80%** como el punto donde la
relación señal-ruido se degrada.

### 9.4 Instrumentación mínima propuesta

**[JUICIO DEL PM]**, construido sobre [S031] y [E011]:

| Qué medir | Por qué | Fuente |
|---|---|---|
| **Tasa de convergencia extremo a extremo** (ejecuciones que producen ZIP válida / ejecuciones totales) | Es la métrica de §6.2. Todo lo demás es secundario | [INFERENCIA] |
| **Tasa de fallo por etapa** | Localiza qué multiplicando está rompiendo la cadena | [S031] |
| **Tasa de intervención humana** | La promesa del producto es que sea cero | [S031] |
| **Reintentos hasta convergencia, por etapa** | Distingue "falla y se recupera" de "falla" | [E012] |
| **Suite de regresión de 20–50 proyectos** extraídos de fallos reales | [E011] | [E011] |
| **Tasa de aceptación humana de la ZIP** — un humano técnico revisa una muestra y dice si la usaría | **Calibra al verificador** (§6.4). Sin esto no sabes si el sistema converge a lo correcto | [E011] |

---

## 10. Registro de riesgos

Método: taxonomía de 16 ítems de [S087], aplicada como checklist. Es *"posiblemente su uso más
práctico"*.

### 10.1 La distinción que hay que tener presente

> *"**No siempre involucra bugs o averías. A veces el producto funciona perfectamente, solo que no
> de la forma en que la gente lo necesita.**"* [S087]

Y la consecuencia: **un proyecto puede tener éxito mientras el producto fracasa.** Entregado a
tiempo, en presupuesto, según especificación — y sin usar. *"La gestión de riesgo de proyecto no
atrapa eso."*

### 10.2 El registro

| # | Riesgo [S087] | ¿Aplica? | Evaluación para Brújula |
|---|---|---|---|
| 1 | **Product-market fit pobre** | 🔴 | A1 sin validar. El segmento no está definido (§2.1) |
| 2 | **Estrategia de lanzamiento débil** | 🟠 | El documento no tiene GTM |
| 3 | **Necesidades de usuario poco claras** | 🔴 | *"Cuando **los supuestos guían las decisiones de producto en lugar de insights reales de usuarios**"* — literal |
| 4 | **Sobreingeniería** | 🔴 | *"**Construir más de lo necesario** para un problema añade complejidad y retrasos."* Siete agentes + wallets + pagos, para un flujo que §6.2 dice que empeora con cada pieza |
| 5 | **Subestimar deuda técnica** | 🟠 | ❌ **La KB no cubre deuda técnica.** Solo puedo nombrarlo |
| 6 | **Expectativas de stakeholders desalineadas** | 🟡 | No evaluable desde el documento |
| 7 | **Integraciones clave faltantes** | 🟠 | El destinatario necesita desplegar en algún sitio (A6) |
| 8 | **Onboarding inadecuado** | 🔴 | ❌ **La KB no cubre onboarding.** Pero un usuario no técnico que recibe una ZIP **es exactamente el caso**. Ver §10.4 |
| 9 | **Bucles de feedback tardíos** | 🟠 | Mitigado por el formato hackathon |
| 10 | **Mal juicio de escalabilidad** | 🟡 | Prematuro |
| 11 | **Desajuste de precio** | 🟠 | ❌ **La KB no cubre pricing.** Y Brújula tiene coste marginal real por ejecución — el modelo de precio no es opcional aquí |
| 12 | **Sorpresas regulatorias o de cumplimiento** | 🔴 | **Dinero real + código generado + despliegue.** §5.4 |
| 13 | **Prioridades de compañía cambiantes** | 🟡 | No evaluable |
| 14 | **Métricas o analítica débiles** | 🔴 | El documento no define ninguna. *"Riesgas celebrar métricas de vanidad mientras te pierdes señales de problemas reales"* |
| 15 | **Brechas de capacidad del equipo** | 🟠 | [S087] nombra literalmente *"**agentes de IA**, modelado de datos, UX móvil"* como ejemplos |
| 16 | **Dependencia de una sola plataforma o socio** | 🔴 | Dependencia total de proveedores de modelos. *"**Crea un riesgo estructural que no puedes controlar del todo**"* |

**Seis rojos. Cuatro de ellos son gaps donde la KB puede nombrar el riesgo pero no tratarlo.**

### 10.3 El riesgo que el documento no tiene categoría para expresar

**[INFERENCIA], y lo marco como tal porque encadena tres estudios que no fueron diseñados para
encadenarse:**

- [E006] (METR, RCT julio 2025): los desarrolladores **aceptaron menos del 44%** de las
  generaciones de IA; una mayoría reportó **hacer cambios mayores para limpiar el código de IA**;
  **~9%** del tiempo total se fue en revisar y limpiar salidas de IA.
- [E008] (DORA 2025, n≈5.000): la adopción de IA **aumenta la inestabilidad de entrega**, y
  **el 30% reporta poca o ninguna confianza en el código generado por IA**.
- [E009]/[E010]: el *"impuesto de verificación"* como una de las tres causas de la curva J.

> **La inferencia:** si el volumen generado sube mientras la tasa de aceptación se mantiene muy por
> debajo del 100%, **la restricción se mueve de producir a verificar** — y verificar es el paso que
> menos obviamente escala añadiendo más agentes.

⚠ **Límite estricto, que la propia KB impone.** [E006] estudió **edición asistida por IA en
repositorios grandes y maduros por mantenedores experimentados**. Brújula genera proyectos
**greenfield pequeños**. Son condiciones distintas y **la generación greenfield podría ser
sustancialmente más fácil**. La KB advierte explícitamente contra generalizar [E006]. **La cifra
del 44% no es un pronóstico para Brújula; es la única medición disponible de la forma del
problema.**

Y [E007] (METR, 24 febrero 2026) añade que los propios autores creen que *"es probable que los
desarrolladores estén más acelerados por herramientas de IA ahora — a principios de 2026 —
comparado con nuestras estimaciones de principios de 2025"*, aunque *"por los efectos de selección
en nuestro experimento, nuestros datos son solo evidencia muy débil del tamaño de este aumento"*.

### 10.4 El riesgo que más me preocupa, y que no está en ninguna lista

**[JUICIO DEL PM].** El ejemplo trabajado de [S087] es una app de notas con edición en tiempo real
que *"funcionaba perfectamente en pruebas. Técnicamente, sólido como una roca"* — y fracasó porque
*"los usuarios no entienden cuándo ni por qué deberían usarla"*.

> **El análogo de Brújula:** el sistema entrega una ZIP técnicamente correcta a alguien que **no
> puede desplegarla, no puede evaluarla, y no puede mantenerla cuando se rompa.**
>
> La promesa es *"un camino claro a producción"*. Para el usuario definido —no técnico— **una ZIP
> no es un camino a producción. Es un obstáculo con formato de entregable.**
>
> Esto no es un fallo de la tecnología. Es un fallo de **dónde se corta el alcance**. Y es
> exactamente el riesgo #8 de [S087] (*"Un gran producto puede aún fracasar si los usuarios no
> logran averiguar cómo obtener valor"*), que la KB **no puede tratar** porque no tiene material
> sobre onboarding.

### 10.5 Respuestas al riesgo

Estrategias de [S065] (PMI, vía socio de formación autorizado):

| Riesgo | Estrategia | Acción concreta |
|---|---|---|
| **Fondos reales mal distribuidos** | **EVITAR** — *"eliminar la amenaza"* | Ledger simulado + un punto de liquidación manual (§5.3). ⚠ [S065]: *"Evitar normalmente cuesta otra cosa"* — aquí cuesta impacto de demo, y es barato |
| **La cadena no converge** | **MITIGAR** — *"disminuir probabilidad o impacto"* | Reducir de 7 a 3 especialistas (§8.3). ⚠ **Riesgo residual**: sigue fallando a veces. [S065]: *"Como se reduce, no se elimina, puede haber riesgo residual"* |
| **El verificador aprueba trabajo malo** | **MITIGAR** | Calibración humana de una muestra (§9.4). Riesgo residual: no detectado entre muestras |
| **El usuario no puede desplegar la ZIP** | **TRANSFERIR** o **ACEPTAR** | Transferir = integrar despliegue con un proveedor. ⚠ [S065] avisa: *"Si el proveedor no cumple los requisitos, **el riesgo se transfiere de vuelta**"*. Aceptar = declarar explícitamente que el destinatario es semi-técnico, lo que **cambia el segmento** |
| **Dependencia de proveedor de modelos** | **ACEPTAR** | [S065]: aceptar es *"una decisión, no una omisión"*. Registrarlo y revisarlo |

---

## 11. Lanzamiento

Aplicando [S106] paso 2 y 3 — **analizar éxito y fracaso por separado**:

> *"**El fallo más común en el pensamiento estratégico es asumir que el éxito y el fracaso son
> iguales y opuestos. Nuestros cerebros son perezosos así que nos gusta inferir una respuesta de
> la otra.**"* [S106]
>
> *"Una baja probabilidad de fracaso puede no significar una alta probabilidad de éxito. Una
> consecuencia significativa del fracaso puede no estar contrabalanceada por recompensas
> significativas."* [S106]

### 11.1 Caso de éxito del hackathon
Una persona no técnica describe una idea; Brújula produce una ZIP que compila, pasa sus tests y
se despliega; el público ve el ledger de agentes distribuyendo pagos.
**Probabilidad:** media-baja con 7 agentes (§6.2 dice ~48% por ejecución); **media-alta con 3.**
**Consecuencia:** validación fuerte de A2 y A3, base para levantar recursos.

### 11.2 Caso de fracaso — analizado **independientemente**
La cadena no converge en la demo en vivo. **Probabilidad: significativa** — y hay que decirlo,
porque la aritmética de §6.2 no la conoce el público pero sí la conoce el sistema.
**Consecuencia:** baja **si** hay una ejecución grabada de respaldo y la narrativa incluye la tasa
de convergencia como hallazgo. **Alta si** la demo se presenta como producto terminado.

> **[JUICIO DEL PM]** Presentar la tasa de convergencia **como parte de la demo** convierte el
> fracaso parcial en evidencia en lugar de en vergüenza. *"Esto converge 3 de cada 5 veces hoy;
> aquí está dónde falla y por qué"* es una demostración más creíble de ingeniería seria que una
> ejecución perfecta e irrepetible.

### 11.3 ⚠ Límite
La KB tiene material de GTM y lanzamiento ([11-lifecycle-and-launch/]) pero **está orientado a
lanzamiento de producto en mercado, no a demos de hackathon.** No lo fuerzo.

---

## 12. Lo que la Knowledge Base **no** puede responder sobre Brújula

Esta sección es obligatoria por diseño. `open-questions-ai-and-pm.md` existe precisamente para que
*"no lo sé, y esto es lo que tendría que ser cierto para saberlo"* sea una respuesta recuperable,
en lugar de la ausencia de una.

| # | Pregunta que Brújula necesita responder | Estado en la KB |
|---|---|---|
| 1 | **¿Cómo se organiza un equipo de software multi-agente** — roles, handoffs, orquestación, escalado? | ❌ **§B1. No se encontró ninguna fuente.** Es literalmente lo que Brújula está construyendo |
| 2 | ¿Más especificación previa produce mejores resultados con agentes que la dirección conversacional iterativa? | ❌ **§A2. El movimiento SDD entero lo asume. No existe comparación controlada** |
| 3 | ¿A qué tamaño de feature deja de compensar el sobrecoste de especificar? | ❌ **§A3. No cuantificado en ninguna parte** |
| 4 | ¿Puede automatizarse la verificación lo suficiente, y con qué riesgo residual? | ❌ **§B3. Los bucles `converge` lo asumen. Ninguna medición de tasas de escape** |
| 5 | ¿Cuál es la tasa de defectos y la mantenibilidad a largo plazo del código escrito por agentes? | ❌ **§C1. No medido en ninguna fuente consultada** |
| 6 | ¿Cuánto cuesta realmente, extremo a extremo, una feature implementada por agentes? | ❌ **§C3. Ninguna fuente aporta modelo de coste** |
| 7 | ¿Cuáles son los modos de fallo específicos de la implementación por agentes? | ❌ **§C4. No se encontró taxonomía** |
| 8 | **Seguridad, licencias, privacidad y cumplimiento del código generado por agentes** | ❌ **§C5. Completamente fuera de todas las fuentes consultadas** |
| 9 | ¿Siguen aplicando Scrum y Kanban tal como están escritos? | ❌ **§B6. [E001] presupone Developers humanos; [E003] presupone personas auto-organizándose** |
| 10 | **Accesibilidad** | ❌ **§C6. Ausente de la KB entera** |
| 11 | ¿Cómo debería un PM hacer aceptación de una feature implementada por un agente? | ❌ *"No se encontró plantilla, ni ejemplo trabajado, ni reporte de campo. Es un gap genuino, no una omisión"* |
| 12 | Definición rigurosa de PMF, MVP, y diseño de medición | ❌ **Gaps Priority 1 y 2 del backlog** |

### La lectura de esto que sí es útil

> **Brújula no tiene un manual que copiar. Y tampoco hay literatura que diga que no funciona.**
>
> La KB dice explícitamente (`pm-with-ai-implementers.md`): *"**Ninguna fuente consultada estudia el
> trabajo del product manager bajo implementación por agentes.** Ni una."*
>
> **[JUICIO DEL PM]** Esto es, a la vez, el mayor riesgo del proyecto y su mayor oportunidad. Un
> equipo que **instrumente** lo que construye —tasa de convergencia por etapa, tasa de
> intervención humana, tasa de aceptación humana calibrada— estaría produciendo **datos que no
> existen públicamente.** La pregunta §B2 de la KB (*¿es la revisión el nuevo cuello de botella?*)
> es medible hoy con el aparato de flujo de [E003] —lead time descompuesto por etapa, con revisión
> aislada— y la KB la señala como *"la contribución real más barata disponible"*.
>
> **Brújula es, accidentalmente, un experimento sobre la pregunta abierta más importante de su
> propio campo.** Vale la pena instrumentarlo como tal.

---

## 13. Veredicto y recomendaciones

### 13.1 Lo único que la KB sí establece empíricamente sobre esto

De todo el dominio 13, **un hallazgo toca directamente la función de producto** — [E008], DORA
2025, n≈5.000:

> *"**En ausencia de un foco centrado en el usuario, la adopción de IA tiene un impacto negativo
> en el rendimiento del equipo.**"*
>
> *"**Sin un foco centrado en el usuario, es improbable que la adopción de IA ayude a los equipos.
> Incluso puede dañarlos.**"*

Es un resultado de **moderación**: el foco en el usuario no solo suma al beneficio de la IA,
**determina su signo**.

⚠ **Límites que viajan con él**: transversal, autorreportado, ejecutado por un proveedor,
correlacional. Identifica una relación moderadora, **no un mecanismo causal**.

Y la tesis central de [E008]:

> *"El papel primario de la IA en el desarrollo de software es el de **amplificador**. Magnifica
> las fortalezas de las organizaciones de alto rendimiento y las disfunciones de las que tienen
> problemas."*

> **La traducción para Brújula es directa e incómoda.** Brújula es una apuesta a que la
> implementación acelerada sustituye a un equipo. [E008] dice que la aceleración **amplifica** lo
> que ya hay. Si lo que hay del lado del usuario es una intención vaga y ninguna capacidad de
> evaluar el resultado, **lo que se amplifica es eso.**
>
> Lo cual, leído al derecho, convierte al **agente PM en el componente más importante del sistema**
> —no al de pagos, no a los especialistas—. Es el único que puede introducir foco en el usuario en
> una cadena que por lo demás solo produce.

### 13.2 Veredicto

**[JUICIO DEL PM] — mío, no de la KB. [S081] registra que el corpus no da reglas de umbral.**

| | Veredicto |
|---|---|
| **¿Vale la pena construir el hackathon?** | **Sí.** Es una apuesta reversible y barata sobre supuestos que ninguna cantidad de investigación resolvería, porque §12 dice que la literatura no existe. [S081]: construir para aprender es exactamente el caso donde *no* se hace assessment completo |
| **¿Vale la pena construirlo tal como está especificado?** | **No.** Tres cambios (§13.3) mejoran materialmente la probabilidad de éxito sin reducir lo que demuestra |
| **¿Es esto un producto?** | **Desconocido, y honestamente desconocido.** A1 no está validado, el segmento no está definido, no hay análisis competitivo y PMF es un gap de la KB. **El hackathon puede responder A2, A3 y A5. No puede responder A1** — eso requiere hablar con 8–10 personas [S081] |

### 13.3 Las tres recomendaciones que cambian el resultado

> #### 1. De siete especialistas a tres
> **Por qué:** §6.2. Siete agentes al 90% dan ~48% de éxito extremo a extremo; tres dan ~73%.
> Demuestra exactamente lo mismo. **El número siete no aporta evidencia adicional de nada.**
> **Coste:** ninguno de demostración. **Beneficio:** la demo funciona.

> #### 2. La verificación va dentro de cada etapa, no al final del flujo
> **Por qué:** §6.3. Es lo único que convierte `pass^k` en `pass@k`. El patrón de [E012] —*repite
> implement → converge hasta Converged*— es la diferencia entre una cadena que se degrada
> multiplicativamente y una que se recupera.
> **Coste:** es rediseño, no trabajo extra. **Beneficio:** es lo que hace viable la arquitectura.

> #### 3. Ledger simulado, un único punto de liquidación real y manual
> **Por qué:** §5.3. [S106]: mueve la decisión de **temeraria** a **calculada** cambiando la
> probabilidad del fallo, ya que la consecuencia no se puede cambiar. §5.4: cruza tres compuertas
> duras a la vez [S050], [S031].
> **Coste:** cero de impacto visual. **Beneficio:** el fallo cuesta un log mal calculado en lugar
> de dinero.

### 13.4 Lo que debería añadirse al documento antes de empezar

| Sección | Fuente que la exige |
|---|---|
| **Enunciado de problema y segmento estrecho** | [S081] paso 1 |
| **"Lo que no vamos a hacer", con el porqué** | [S138], [S113], [S084] — convergencia de tres fuentes |
| **Criterios de aceptación en EARS**, incluido el comportamiento no deseado | [E014], §7.3 |
| **La condición de muerte, escrita antes de empezar** | [S031], §8.4 |
| **Instrumentación mínima** | [S031], [E011], §9.4 |
| **MoSCoW con tope del 60% de Musts** | [S031], §8.3 |

### 13.5 Y una pregunta abierta para el equipo

**§5.2 no se resolvió y no la puedo resolver yo:** ¿la economía agente-a-agente es contabilidad
interna, o es el producto?

Si es lo segundo, **Brújula es un marketplace de dos lados** y falta la mitad del análisis: quiénes
son los agentes proveedores, por qué se unirían, y cómo se garantiza la calidad de un agente de
terceros. Eso no es un ajuste al documento actual — es otro documento.

---

## 14. ¿Funcionó la Knowledge Base?

Esta era la pregunta real. Evaluación honesta.

### 14.1 Dónde funcionó bien

| Aportación | Origen | Valor |
|---|---|---|
| **La aritmética `pass^k`** | [E011] vía §6 | 🟢 **Alto.** Cambia el diseño del sistema, no solo su evaluación. Un PM sin esto no tiene forma de argumentar contra "añadamos un agente más" |
| **El test plan/estrategia/visión** | [S090], [S094] | 🟢 **Alto.** Clasificar el documento antes de analizarlo evitó exigirle cosas que no le tocan |
| **La taxonomía de 16 riesgos** | [S087] | 🟢 **Alto.** Funcionó exactamente como checklist mecánica; produjo 6 rojos en minutos |
| **"El verdadero competidor es el flujo existente"** | [S025], [S054] | 🟢 **Alto.** Es la pregunta que el documento más necesitaba y menos tenía |
| **La matriz temerario/calculado** | [S106] | 🟢 **Alto.** Produjo la recomendación más accionable del informe (§5.3) |
| **EARS** | [E014] | 🟢 **Alto.** Convirtió 11 criterios infalsables en 8 verificables y 2 honestamente descartados |
| **El tope del 60% de MoSCoW** | [S031] | 🟡 Medio. Útil y ⚠ **no verificado** — la KB lo dice |
| **"Lo que no vamos a hacer"** | [S138], [S113], [S084] | 🟢 Alto. La convergencia de tres fuentes independientes le dio peso |
| **Los flujos de métricas humano/agente** | [S031] | 🟢 Alto — y es suerte: encaja con Brújula por accidente |
| **La distinción DoD / criterios de aceptación** | [E001], [E003] | 🟡 Medio. Corrigió un error que yo habría cometido |

### 14.2 Dónde la KB me dejó sin respuesta — correctamente

**La KB se negó a responder 12 preguntas** (§12) y en cada caso dijo por qué. Eso es el
comportamiento correcto, y es lo que más me costaba confiar antes de probarlo:

- **No inventó** organización de equipos multi-agente. Dijo: no hay fuente.
- **No inventó** una definición de PMF. Dijo: cuatro definiciones incompatibles, es un gap.
- **No dejó** que citara "19% más lento" de [E006] sin sus condiciones de alcance, y **no me dejó
  aplicarlo a Brújula sin decir que el escenario es distinto**.
- **No dejó** que usara las cifras de ROI de DORA — marcadas `VENDOR PROJECTION`, no citables.
- **Me obligó a etiquetar** la aritmética de §6.2 como **[INFERENCIA]**, no como hallazgo de
  [E011], porque [E011] mide intentos repetidos y yo estoy encadenando etapas distintas.

> **Esa última es la prueba más dura que pasó el sistema.** La cadena `pass^k` es el argumento más
> persuasivo del informe. La KB me forzó a debilitarlo y a declarar por qué. Un sistema que solo
> disciplina las afirmaciones que no te importan no está disciplinando nada.

### 14.3 Dónde la KB falló o quedó corta

| Problema | Severidad | Detalle |
|---|---|---|
| **Onboarding no existe en la KB** | 🔴 | §10.4 es el riesgo que más me preocupa y **solo pude nombrarlo**. [S087] lo lista como riesgo #8 y la KB no tiene material para tratarlo |
| **Pricing no existe** | 🔴 | Brújula tiene coste marginal real por ejecución. El modelo de precio no es opcional. La KB no puede ayudar |
| **Diseño de métricas no existe** | 🔴 | §9 es la sección más débil del informe, y es por el gap, no por el análisis |
| **Dimensionamiento de mercado no existe** | 🟠 | §3 quedó como estructura sin datos |
| **Sesgo comercial del corpus (~85%)** | 🟠 | Las fuentes más útiles del análisis ([S031], [S087], [S081]) son **todas vendors o formadores** |
| **Nada sobre marketplaces de dos lados** | 🟠 | §13.5 quedó como pregunta abierta porque la KB no tiene el material |
| **El dominio 13 es demasiado nuevo para tener profundidad** | 🟡 | Aporta la aritmética y la evidencia; **no aporta práctica**. Lo dice de sí mismo |

### 14.4 Lo que este ejercicio revela sobre el propio backlog

**Recomiendo reordenar `RESEARCH_BACKLOG.md` con base en esta prueba:**

| Gap | Prioridad actual | Propuesta | Motivo |
|---|---|---|---|
| **Onboarding y activación** | No está en el backlog | **Subir a Priority 1** | Apareció como riesgo rojo y la KB no tenía nada. Es el gap que más dolió |
| **Pricing** | Priority 2 | **Subir a Priority 1** | Cualquier producto con coste marginal por uso lo necesita antes que un roadmap |
| **Diseño de métricas (1.3)** | Priority 1 | **Mantener — es correcto** | Confirmado en la práctica |
| **Organización de equipos multi-agente (§B1)** | Sin fuentes | **Convertir en instrumentación propia** | §12. Si Brújula se construye e instrumenta, **genera** la evidencia que falta |
| **MVP (1.2)** | Priority 1 | **Bajar a Priority 2** | No hizo falta ni una vez en este análisis. Sospecho que se sobreestimó |

### 14.5 Veredicto sobre el sistema

**Funciona, y funciona por la razón menos obvia.**

El valor no estuvo en tener las respuestas. Estuvo en **tener las preguntas en un orden fijo, con
fuentes atadas, y en negarse a rellenar los huecos.** Un análisis desde memoria habría producido
un informe parecido en forma, más fluido, con cifras plausibles — y yo no habría sabido cuáles eran
reales.

Las tres recomendaciones de §13.3 son trazables hasta sus fuentes y **contradicen el documento
original en puntos concretos**. Ninguna salió de una opinión.

**El punto débil es previsible y está bien documentado:** ~85% del corpus es contenido comercial,
y los gaps que más molestaron —onboarding, pricing, métricas— son exactamente donde el contenido
de vendors es más escaso, porque nadie regala lo que vende.

---

## Trazabilidad — fuentes usadas en este análisis

### Corpus `[Snnn]` — 20 fuentes

| ID | Publicación | Usado para |
|---|---|---|
| S005 | Lean/Osterwalder value proposition | Test del 40%, PMF |
| S025 | Competitive analysis | Sustitutos, "do nothing", 5–7 competidores |
| S028 | Discovery workshops | Mapeo de supuestos, priorización por riesgo |
| S030 | Evaluating ideas and opportunities | Ideas vs oportunidades, embudo de cribado |
| S031 | Userpilot — *Feature Prioritization Matrix 2026* | Tope 60% MoSCoW, condición de muerte, compuerta dura, métricas humano/agente |
| S040 | Roman Pichler — *Outcome-Based Roadmaps* | Qué debe enunciar una estrategia |
| S048 | Notion — *How to write a PRD* | Alcance, criterios de release |
| S050 | Hyperproof — IT/security risk | NIST, riesgo de seguridad |
| S054 | Jobs to be Done | El statu quo como competidor |
| S065 | PMI ATP — risk response | Las cinco estrategias, riesgo residual |
| S066 | Atlassian — prioritization frameworks | MoSCoW, debilidades |
| S074 | Datos cualitativos y cuantitativos | "Ambos pueden mentir" |
| S081 | Product School — *Opportunity Assessment* | Proceso de 6 pasos, cuándo correrlo/saltarlo, 8–10 entrevistas |
| S084 | PRD components | Supuestos, restricciones, dependencias |
| S087 | Product School — *Product Risk* | Taxonomía de 16 riesgos, assumption mapping, risk/evidence grid |
| S090 | Aha! — *Product Strategy* | Qué es y qué no es estrategia; la trampa del plan |
| S094 | **Marty Cagan (SVPG)** — *Product Vision* | Visión vs misión; funciones de una visión |
| S106 | **Ravi Mehta** — *Strategic Thinking* | Decisión buena vs correcta, matriz temerario/calculado, éxito y fracaso independientes |
| S111 | Reforge | PMF como etapa; expansión de PMF |
| S113 | PRD — *Features Out* | La exclusión con su porqué |
| S138 | PRD colaborativo | "What we're not doing"; requisitos evolutivos |

### Investigación externa `[Ennn]` — 8 fuentes

| ID | Fuente | Procedencia | Usado para |
|---|---|---|---|
| **E001** | **The Scrum Guide**, Schwaber & Sutherland, nov 2020 | `PRIMARY` | Definition of Done como compromiso del Incremento |
| **E003** | **Anderson & Carmichael — *Essential Kanban Condensed*, 2016** | `PRIMARY` | Políticas explícitas; aparato de flujo para §12 |
| **E006** | **METR — RCT, julio 2025** | `EMPIRICAL` | Tasa de aceptación <44%, ~9% de tiempo en revisión |
| **E007** | **METR — actualización de diseño, feb 2026** | `EMPIRICAL / CORRECCIÓN` | Caveat de vigencia sobre [E006] |
| **E008** | **DORA — *State of AI-assisted Software Development* 2025**, n≈5.000 | `EMPIRICAL` (autorreporte) | Foco en usuario como moderador; IA como amplificador; inestabilidad de entrega |
| **E009/E010** | DORA ROI 2026 vía InfoQ | ⚠ `VENDOR PROJECTION` / `SECONDARY` | Impuesto de verificación, curva J. **Cifras de ROI no citadas** |
| **E011** | **Anthropic — *Demystifying evals for AI agents*, 9 ene 2026** | `PRACTICE` | pass@k / pass^k, tipos de evaluador, saturación, queso suizo, seis errores |
| **E012** | **GitHub `spec-kit`** (MIT) | `PRIMARY (tool)` | Constitución; el bucle `converge` |
| **E014** | **EARS — Mavin et al., Rolls-Royce, 2009** | `PRIMARY` | Los cinco patrones; comportamiento no deseado |

### Fuentes cuyo uso se rechazó deliberadamente

| Fuente | Por qué no se usó |
|---|---|
| **[E009] cifras de ROI** (39% ROI, 727% a tres años) | ⚠ `UNVERIFIED — VENDOR PROJECTION`. Proyecciones modeladas por una empresa que vende herramientas de IA, leídas a través de una fuente secundaria. La KB prohíbe citarlas como evidencia |
| **[E006] "19% más lento"** como hecho general | Sus propios autores publican una tabla de malas lecturas. No es un pronóstico para Brújula |
| **Memoria del modelo** | Cero uso. Donde no hubo fuente, dice ❌ |

---

*Informe generado por un PM Agent operando sobre `pm-knowledge-base` v1.1.0 (88 documentos,
13 dominios, 143 fuentes de corpus + 14 externas). Las 12 preguntas de §12 que la KB no puede
responder están registradas en `13-ai-agent-collaboration/open-questions-ai-and-pm.md` junto con
qué evidencia resolvería cada una.*

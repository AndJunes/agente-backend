# Product Requirements Document — Brújula

| | |
|---|---|
| **Producto** | Brújula |
| **Versión** | 1.0 |
| **Fecha** | 16 de septiembre de 2026 |
| **Autor** | PM Agent · método `pm-knowledge-base` v1.1.0 |
| **Deriva de** | [`01-product-discovery-report.md`](01-product-discovery-report.md) |
| **Estado** | Listo para desarrollo |
| **Ventana de entrega** | **11 días** — congelar 26/09, entregar 27/09/2026 |
| **Audiencia** | Agentes de desarrollo y equipo humano |

---

## Cómo está escrito este documento

Los **criterios de aceptación están en EARS** (Easy Approach to Requirements Syntax, Alistair Mavin
et al., Rolls-Royce, 2009 [E014]) porque el implementador es un agente:

| Patrón | Sintaxis |
|---|---|
| Ubicuo | The `<sistema>` **shall** `<respuesta>` |
| Dirigido por estado | **While** `<precondición>`, the `<sistema>` **shall** `<respuesta>` |
| Dirigido por evento | **When** `<disparador>`, the `<sistema>` **shall** `<respuesta>` |
| Feature opcional | **Where** `<feature>`, the `<sistema>` **shall** `<respuesta>` |
| **Comportamiento no deseado** | **If** `<disparador>`, **then** the `<sistema>` **shall** `<respuesta>` |

> **El patrón de comportamiento no deseado es el que más se omite** y el que más importa acá: un
> implementador humano pregunta qué hacer cuando algo falla; **un agente elige algo plausible.**

Marcas: `[Snnn]`/`[Ennn]` método · `[Rnn]` investigación (registro en el Discovery) · ❌ sin
resolver · ⚠ no verificado.

---

## 1. Product Overview

### 1.1 Qué es

> **Brújula es la capa de verificación y liquidación del software generado por IA.** Toma una
> intención en lenguaje natural, la construye con agentes, **verifica cada etapa contra criterios
> explícitos**, y **libera el pago únicamente contra evidencia** — nunca contra la afirmación de un
> agente de que terminó.
>
> El entregable no es solo código. Es **código más una atestación verificable de qué se comprobó,
> qué pasó y qué no**, anclada en Stellar.

### 1.2 Qué no es

| No es | Por qué se declara |
|---|---|
| Un generador de aplicaciones que compite con Lovable/Bolt/v0 | Ese mercado tiene un líder a **US$13.300M y US$500M de ARR** [R08]. Brújula no compite ahí |
| Un marketplace abierto de agentes de terceros | Requiere el lado dos del mercado. Fuera de alcance — Discovery §2.5 |
| Una plataforma de despliegue gestionado | Requiere operación continua. Fuera de alcance — Discovery §2.4 |
| Un escáner de seguridad | Los escáneres reportan a ingenieros. Brújula **atesta para no-ingenieros y condiciona el pago** |

### 1.3 La frase de posicionamiento

> **Lovable te da una aplicación. Brújula te da una aplicación y la prueba de que se puede usar.**

### 1.4 Por qué Stellar, en una línea

Porque **el pago es el mecanismo de cumplimiento de la verificación**, y eso requiere un riel de
pagos programable, de liquidación rápida y de costo casi nulo. Stellar publica x402 y MPP como
building blocks oficiales para pagos entre agentes [R04][R05], y **MPP ya está en mainnet con
canales de pago** [R05][R06].

---

## 2. Problem Statement

> **Quien encarga software generado por IA no tiene forma de saber si lo que recibió es seguro,
> completo y desplegable — y precisamente quien más necesita esa garantía es quien menos capacidad
> tiene de evaluarla.**

### 2.1 Evidencia

| Dato | Fuente |
|---|---|
| **57%** de las apps con Supabase alcanzables permitían **lectura no autenticada de tablas** (2.096 de 3.680, sobre 30.998 apps escaneadas pasivamente en agosto 2026) | [R10] ⚠ |
| **1 de cada 23** apps publica secretos en el bundle (1.332 apps) | [R10] ⚠ |
| **92% de adopción diaria con 29% de confianza** | [R09] ⚠ |
| **42,3** vulnerabilidades por repo asistido por IA vs **9,6** humano | [R11] ⚠ |
| CVEs confirmados atribuibles a IA: **18 en 7 meses de 2025 → 56 en 3 meses de 2026** | [R12] 🟢 Georgia Tech |

⚠ [R10] y [R11] son proveedores de seguridad que declaran su interés comercial; [R11] infiere
"asistido por IA" de metadatos y su publicador dice leerlo como direccional. [R12] es académica pero
mide CVEs confirmados, no porcentaje de apps. **La tendencia es consistente; las magnitudes no son
constantes.**

### 2.2 Lo que hoy hace el usuario

Genera con una herramienta de IA, lo mira funcionar en la demo, y **asume** que está bien. No tiene
instrumento para saber lo contrario, y la herramienta no se lo da porque no es el producto que vende.

---

## 3. Goals & Objectives

### 3.1 Objetivo de producto

Que una persona que **ya generó software con IA** pueda obtener, sin conocimiento técnico, **una
respuesta defendible** a: *¿esto se puede poner en producción?*

### 3.2 Objetivos de la hackathon (11 días)

| # | Objetivo | Criterio de éxito medible |
|---|---|---|
| **G1** | Demostrar que el gate de verificación funciona | **≥3 de 5** ejecuciones desde cero producen un artefacto que pasa todos los criterios de §18 |
| **G2** | Demostrar que el pago se condiciona a evidencia | **0** pagos liberados sin bundle de evidencia válido, en 100% de las ejecuciones |
| **G3** | Demostrar detección real | **≥80%** de las vulnerabilidades sembradas deliberadamente son detectadas |
| **G4** | Producir el dato de H2 | Resultado del experimento A/B/C (Discovery §6.3) listo **antes** del pitch |
| **G5** | Integración Stellar sustantiva | Pagos MPP en testnet + hash de evidencia anclado en `MEMO_HASH` |

### 3.3 No-objetivos de esta fase

Escala · mainnet · múltiples categorías de aplicación · pulido de UI · multi-usuario · facturación ·
agentes de terceros.

### 3.4 Alineación con los criterios publicados de la hackathon

| Criterio | Cómo se responde |
|---|---|
| **Validación del problema** | §2 — 30.998 apps escaneadas, 57% expuestas |
| **Foco de negocio** | Mercado de generación a US$13,3B [R08]; la confianza es el cuello sin resolver |
| **Foco de producto** | El usuario recibe **un boletín reenviable**, no un dashboard |
| **Ejecución técnica** | MPP es building block oficial [R05]; la integración es el mecanismo, no decoración |

---

## 4. Target Users

### 4.1 Usuario primario del MVP

**P1 · Fundador técnico-adyacente en pre-semilla.** Ya generó software con IA. Sabe leer un README
y seguir instrucciones; no sabe auditar una policy de base de datos. Tiene una reunión con fecha
donde alguien va a mirar su producto en serio.

### 4.2 Fuera de alcance para el MVP

| Usuario | Por qué queda fuera |
|---|---|
| **P2 · PyME argentina** | Necesita despliegue y mantenimiento gestionados — **15–20% anual del costo de desarrollo** [R14]. Es el mercado grande; es otro producto |
| **P3 · Proveedor de agentes** | Requiere marketplace de dos lados. ❌ La KB no cubre marketplaces |

### 4.3 ⚠ Advertencia obligatoria

> **Se hicieron CERO entrevistas de usuario.** [S081] exige un mínimo de 8–10 conversaciones —
> ⚠ cifra que la propia fuente declara sin justificación. **P1 es una hipótesis de segmento, no un
> hallazgo.** Ver §22 · Q1.

---

## 5. User Personas

### P1 — Martín · 29 · Buenos Aires · fundador pre-semilla **[PRIMARIO]**

| Campo | |
|---|---|
| **Rol** | Fundador, perfil producto/comercial. No ingeniero |
| **Capacidad técnica** | Lee un README. Corre `npm install`. **No** audita permisos de base de datos |
| **Estado actual** | Tiene una app generada con Lovable o Bolt que funciona en demo |
| **Job to be Done** | *Cuando tengo que enseñarle mi producto a un inversor o a un cliente que va a cargar datos reales, quiero poder afirmar que es seguro sin mentir, para no quemar la relación cuando alguien lo mire en serio* |
| **Dolor** | No sabe si aguanta. No sabe cómo averiguarlo. No puede pagar una auditoría |
| **Define el éxito como** | **Un documento que puede reenviar.** No un dashboard que tiene que interpretar |
| **Frustración con lo actual** | Los escáneres le devuelven 200 hallazgos en jerga y ninguna conclusión |
| **Disposición a pagar** | ❌ **Sin medir.** Es H1 |
| **Hipótesis que lo invalida** | Que la velocidad le gane siempre hasta que algo se rompa |

### P2 — Carolina · 44 · Salta · PyME de servicios **[SECUNDARIO — NO MVP]**

| Campo | |
|---|---|
| **Contexto** | Centro de estética, 6 empleadas. Agenda por WhatsApp y planilla |
| **Job to be Done** | *Cuando pierdo un turno porque se me traspapeló un mensaje, quiero un sistema que lo maneje solo, para dejar de perder plata sin contratar a alguien que me lo mantenga* |
| **Barrera real** | **No puede desplegar ni mantener una ZIP.** Le cotizaron ARS 1,5M [R14] y no lo hizo |
| **Por qué se documenta** | Es el mercado grande y es literalmente el ejemplo del documento original ("turnos y notificaciones") |

---

## 6. User Stories

Formato: *Como `<rol>` quiero `<objetivo>` para `<beneficio>`* [S127]. **Épicas E1–E5; las marcadas
`[MVP]` entran en los 11 días.**

### E1 · Expresar la intención

| ID | Historia | Prioridad |
|---|---|---|
| **US-01** | Como Martín, quiero describir lo que necesito en lenguaje natural, para no tener que saber qué stack pedir | **[MVP] Must** |
| **US-02** | Como Martín, quiero que el sistema me pregunte lo que no dije y que importa, para no descubrir después que asumió algo equivocado | **[MVP] Must** |
| **US-03** | Como Martín, quiero ver el requisito interpretado antes de que se construya, para corregirlo barato | **[MVP] Must** |
| **US-04** | Como Martín, quiero subir un proyecto **ya generado** para que lo verifique sin reconstruirlo | Should — es la oportunidad O2 del Discovery |

### E2 · Construcción verificada

| ID | Historia | Prioridad |
|---|---|---|
| **US-05** | Como Martín, quiero ver en qué etapa va y qué pasó, para saber si está trabado | **[MVP] Must** |
| **US-06** | Como el orquestador, quiero que cada etapa se verifique antes de avanzar, para que un fallo no contamine las siguientes | **[MVP] Must** |
| **US-07** | Como el orquestador, quiero reintentar una etapa fallida hasta N veces y después **detenerme**, para no gastar presupuesto indefinidamente | **[MVP] Must** |
| **US-08** | Como Martín, quiero que si no converge me diga **qué criterio falló**, para decidir si simplifico | **[MVP] Must** |

### E3 · Evidencia y atestación

| ID | Historia | Prioridad |
|---|---|---|
| **US-09** | Como Martín, quiero un boletín legible por alguien no técnico, para reenviárselo a un inversor | **[MVP] Must** |
| **US-10** | Como Martín, quiero que el boletín diga qué **no** se verificó, para no afirmar de más | **[MVP] Must** |
| **US-11** | Como un tercero, quiero verificar que el boletín corresponde a ese código y no fue editado | **[MVP] Must** |
| **US-12** | Como Martín, quiero ver las vulnerabilidades encontradas explicadas en castellano, con qué pasa si no las arreglo | **[MVP] Should** |

### E4 · Economía entre agentes

| ID | Historia | Prioridad |
|---|---|---|
| **US-13** | Como el orquestador, quiero pagar a un agente **solo** cuando su trabajo pasó verificación | **[MVP] Must** |
| **US-14** | Como el orquestador, quiero un presupuesto máximo por ejecución que no se pueda exceder | **[MVP] Must** |
| **US-15** | Como Martín, quiero ver cuánto costó cada etapa, para entender el precio | **[MVP] Should** |
| **US-16** | Como un agente, quiero cobrar sin tener que mantener saldo de XLM | **[MVP] Must** — resuelto por fees patrocinadas [R05] y CAP-33 [R03] |

### E5 · Fuera del MVP

| ID | Historia | Prioridad |
|---|---|---|
| **US-17** | Como Martín, quiero desplegar con un clic | Won't (esta fase) |
| **US-18** | Como proveedor de agentes, quiero registrar mi agente y cobrar | Won't (esta fase) |
| **US-19** | Como Martín, quiero re-verificar tras cambios | Could |

---

## 7. Functional Requirements

Convención: `FR-n`. **Todos los MVP son verificables por máquina** (§18).

### FR-1 · Captura de intención
| ID | Requisito |
|---|---|
| FR-1.1 | The system **shall** accept a natural-language description of the desired application, up to 4.000 characters |
| FR-1.2 | The system **shall** produce a structured specification from that description containing: purpose, entities, user roles, core flows, and non-functional constraints |
| FR-1.3 | **When** the specification contains an unspecified error-handling case, the system **shall** generate an explicit clarifying question before building |
| FR-1.4 | The system **shall** present the interpreted specification to the user for confirmation **before** any build stage begins |
| FR-1.5 | **If** the user does not confirm the specification within the session, **then** the system **shall not** start any build stage |

> **FR-1.3 es el patrón de comportamiento no deseado de EARS aplicado al propio input.** Es la
> mitigación directa de H5 del Discovery.

### FR-2 · Orquestación
| ID | Requisito |
|---|---|
| FR-2.1 | The system **shall** decompose the specification into **vertical slices** (each slice delivering one complete user-facing capability end to end) |
| FR-2.2 | The system **shall not** decompose work by technical layer (frontend / backend / database) |
| FR-2.3 | The system **shall** assign each slice to exactly one Builder agent instance |
| FR-2.4 | **Where** two slices have no shared dependency, the system **shall** execute them concurrently |
| FR-2.5 | The system **shall** record, for each stage, the agent id, start time, end time, token count and outcome |

> **FR-2.2 es una restricción arquitectónica directa, no una preferencia.** Anthropic [R16]:
> *"**Descomposición por tipo de problema: dividir por tipo de trabajo (planificación,
> implementación, testing) crea sobrecarga de coordinación.**"* El documento original proponía
> exactamente eso con siete agentes.
>
> **FR-2.4 es la condición donde el multi-agente sí gana** [R16]: *"Paralelización: facetas
> independientes pueden explorarse simultáneamente."*

### FR-3 · Verificación
| ID | Requisito |
|---|---|
| FR-3.1 | The system **shall** run a Verifier agent against every Builder output before that output is accepted |
| FR-3.2 | The Verifier **shall** receive only the acceptance criteria and the produced artifact — **not** the Builder's reasoning, plan or transcript |
| FR-3.3 | The Verifier **shall** execute every check in §18 and **shall** record a pass/fail plus the raw tool output for each |
| FR-3.4 | **If** any check fails, **then** the system **shall** return the artifact to the Builder with the failing check identified, and **shall not** release payment |
| FR-3.5 | **If** a stage fails verification **three consecutive times**, **then** the system **shall** halt that stage, **shall not** release payment, and **shall** report which criterion failed |
| FR-3.6 | The Verifier **shall not** mark a check as passed on the basis of the Builder's own claim, self-report, or any statement in the Builder's output text |

> **FR-3.2 y FR-3.6 atacan el modo de fallo que [R16] nombra explícitamente: el "problema de la
> victoria temprana" — verificadores que marcan salidas como aprobadas tras pruebas mínimas.** Por
> eso [R16] especifica *caja negra* y *transferencia de contexto mínima*: un verificador que ve el
> razonamiento del constructor tiende a creerle.

### FR-4 · Evidencia
| ID | Requisito |
|---|---|
| FR-4.1 | The system **shall** produce an evidence bundle containing: the specification, every check with its result, the raw tool output, the artifact SHA-256, timestamps, and agent identities |
| FR-4.2 | The system **shall** compute a SHA-256 digest of the canonicalised evidence bundle |
| FR-4.3 | The system **shall** render a human-readable report **in Spanish** stating what passed, what failed, and **what was not checked at all** |
| FR-4.4 | The report **shall** state its own limitations explicitly and **shall not** claim the artifact is secure |
| FR-4.5 | The system **shall** allow any third party to recompute the digest from the bundle and compare it against the on-chain record |

> **FR-4.4 es una restricción legal y ética, no de producto.** Brújula atesta **qué comprobó**, no
> que el software sea seguro. La diferencia es la que separa un informe defendible de una
> declaración falsa.

### FR-5 · Pagos
| ID | Requisito |
|---|---|
| FR-5.1 | The system **shall** create one Stellar account per agent using sponsored reserves, with a starting balance of 0 XLM |
| FR-5.2 | The system **shall** release payment to a Builder **only** after the Verifier has recorded a full pass for that stage |
| FR-5.3 | Every release payment **shall** carry `MEMO_HASH` set to the SHA-256 digest of the evidence bundle for that stage |
| FR-5.4 | The system **shall** enforce a per-run budget cap, denominated in test USDC |
| FR-5.5 | **If** the cumulative spend of a run reaches the budget cap, **then** the system **shall** halt the run, **shall not** initiate further payments, and **shall** report the remaining work as unfunded |
| FR-5.6 | The system **shall** operate exclusively on **Stellar testnet** in this release |
| FR-5.7 | **If** a payment transaction fails to confirm, **then** the system **shall** retry up to 3 times, and **shall** mark the stage as *verified-unpaid* rather than reverting the verification |

> **FR-5.3 es el mecanismo central del producto.** La transacción de pago **es** la atestación:
> `MEMO_HASH` acepta exactamente **32 bytes** [R19] y SHA-256 produce exactamente 32 bytes. El
> ajuste es exacto y no requiere contrato adicional. **El pago y la prueba son el mismo objeto
> on-chain.**

### FR-6 · Entregable
| ID | Requisito |
|---|---|
| FR-6.1 | The system **shall** produce a ZIP containing the source, the evidence bundle (JSON) and the human-readable report (HTML + Markdown) |
| FR-6.2 | The ZIP **shall** contain a `VERIFICATION.md` at the root with the digest and the testnet transaction hash |
| FR-6.3 | **If** the run halted before completion, **then** the system **shall** still produce a ZIP containing everything completed and a report stating exactly what is missing |

> **FR-6.3 importa más de lo que parece.** Por la aritmética del Discovery §8.4, una fracción
> significativa de ejecuciones no completará. **Un fallo que entrega evidencia parcial es un
> producto; un fallo que no entrega nada es un crash.**

---

## 8. Non-Functional Requirements

[S085]: los no funcionales *"cubren **cómo** se desempeña el producto"*. [S084] advierte que son los
que más se dejan implícitos y se descubren tarde.

| ID | Requisito |
|---|---|
| **NFR-1 · Determinismo de la verificación** | Given the same artifact and criteria, the Verifier **shall** produce the same pass/fail set on repeated runs. **Code-based checks only in the MVP** |
| **NFR-2 · Aislamiento** | Every build and every check **shall** execute in a container with no network access except an explicit allowlist, and **shall not** share filesystem state with any other run |
| **NFR-3 · Latencia** | A complete run **shall** finish within **15 minutes** for the reference specification of §18.4 |
| **NFR-4 · Trazabilidad** | Every stage **shall** be reconstructible from the evidence bundle alone, with no access to the running system |
| **NFR-5 · Techo de costo** | A run **shall not** exceed its declared token budget. **Rationale: [R16] reports multi-agent using 3–10x the tokens of single-agent for equivalent tasks** |
| **NFR-6 · Idioma** | The user-facing report **shall** be in Spanish. Code, commits and logs **shall** be in English |
| **NFR-7 · Ausencia de secretos** | The system **shall not** write any credential into the produced artifact, the evidence bundle or the report |
| **NFR-8 · Degradación** | **If** any external dependency is unavailable, **then** the system **shall** halt with a named cause and **shall not** produce an evidence bundle claiming checks that did not run |

> **NFR-1 es una decisión deliberada y costosa.** [E011] da los tres tipos de evaluador:
> basado en código (*"rápido, barato, objetivo, reproducible"* pero *"frágil ante variaciones
> válidas"*), basado en modelo (*"flexible... **no determinista, caro, necesita calibración**"*) y
> humano (*"calidad de referencia"* pero caro y lento).
>
> **El MVP usa solo evaluadores basados en código.** Un evaluador basado en modelo sin calibración
> es precisamente cómo se produce la victoria temprana. [E011]: *"un evaluador basado en modelo no
> es un atajo que evite al humano; es una forma de **amortizar** su juicio, y hay que contrastarlo
> contra ese juicio periódicamente."* Sin tiempo para calibrar, no se usa.

---

## 9. Product Features

| # | Feature | Descripción | MoSCoW |
|---|---|---|---|
| **F1** | **Captura y clarificación de intención** | Lenguaje natural → especificación estructurada, con preguntas sobre los casos de error no especificados | **MUST** |
| **F2** | **Orquestación por cortes verticales** | Descompone por capacidad completa, no por capa técnica | **MUST** |
| **F3** | **Gate de verificación por etapa** | Verificador caja negra, contexto mínimo, reintentos con tope duro | **MUST** |
| **F4** | **Bundle de evidencia + digest** | JSON canónico, SHA-256 | **MUST** |
| **F5** | **Pago condicionado a evidencia** | MPP testnet, `MEMO_HASH` = digest | **MUST** |
| **F6** | **Boletín legible en castellano** | Lo que pasó, lo que falló, **lo que no se comprobó** | **MUST** |
| **F7** | **Wallets de agente con saldo 0** | Reservas patrocinadas CAP-33 | **MUST** |
| **F8** | **Tope de presupuesto por ejecución** | Corte duro, no advertencia | **MUST** |
| **F9** | **Explicación de vulnerabilidades en castellano** | Qué es, qué pasa si no lo arreglás | **SHOULD** |
| **F10** | **Panel de costo por etapa** | Transparencia de precio | **SHOULD** |
| **F11** | **Canales de pago MPP** | Sesiones off-chain para alta frecuencia [R05] | **COULD** — contingencia |
| **F12** | **Verificar proyecto subido** | Oportunidad O2 del Discovery | **COULD** |
| **F13** | **Smart wallet con passkey** | Onboarding sin frase semilla [R20] | **COULD** |
| **F14** | **Liquidación en mainnet** | Un punto manual, post-hackathon | **WON'T** |
| **F15** | **Agentes de terceros** | Marketplace de dos lados | **WON'T** |
| **F16** | **Despliegue gestionado** | Requiere operación continua | **WON'T** |

---

## 10. User Flows

### 10.1 Flujo principal — feliz

```
1  Martín describe: "sistema de turnos con notificaciones por email"
2  Brújula devuelve la especificación interpretada
   └─ y 3 preguntas: ¿qué pasa si el turno se solapa?
                     ¿qué pasa si el email rebota?
                     ¿qué pasa si el usuario cancela con 5 minutos?     ← FR-1.3
3  Martín responde. Confirma.                                            ← FR-1.4
4  Orquestador descompone en cortes verticales:
      S1 · crear y listar turnos
      S2 · notificación por email
      S3 · cancelación                                                   ← FR-2.1
5  PARA CADA corte:
      Builder construye
      Verifier corre TODOS los checks de §18, en caja negra              ← FR-3.2
      ├─ pasa  → evidencia → digest → pago con MEMO_HASH=digest          ← FR-5.3
      └─ falla → vuelve al Builder con el check que falló
                 (máximo 3 intentos → alto duro)                         ← FR-3.5
6  Integrator une los cortes. Corre el conjunto completo de checks.
7  ZIP: código + evidencia + VERIFICATION.md + boletín en castellano
8  Martín abre el boletín. Dice qué pasó, qué falló y QUÉ NO SE COMPROBÓ  ← FR-4.3
```

### 10.2 Flujo de no convergencia — **el que más importa**

```
Corte S2 falla verificación 3 veces
      ↓
Sistema DETIENE S2                                                       ← FR-3.5
Sistema NO paga S2                                                       ← FR-3.4
Sistema conserva S1 (verificado y pagado)
      ↓
ZIP contiene: S1 completo + evidencia de S1
              S2 incompleto + los 3 intentos y el check que falló
              boletín: "2 de 3 capacidades verificadas. Falta: notificación
                        por email. Falló en: el envío no se completa
                        contra el servidor SMTP de prueba."               ← FR-6.3
```

> **Este flujo se especifica con el mismo detalle que el feliz, deliberadamente.** Por la aritmética
> del Discovery §8.4, va a ocurrir. Un sistema que entrega evidencia parcial y nombra el criterio
> que falló es útil; uno que se cae, no.

### 10.3 Flujo de agotamiento de presupuesto

```
Gasto acumulado alcanza el tope
      ↓
Alto inmediato. Ningún pago nuevo.                                       ← FR-5.5
ZIP con lo completado + boletín declarando trabajo sin financiar
```

### 10.4 Flujo de verificación por un tercero

```
Un inversor recibe el ZIP
      ↓
Abre VERIFICATION.md → digest + hash de transacción testnet
      ↓
Recalcula SHA-256 del bundle de evidencia
      ↓
Consulta la transacción en testnet → lee MEMO_HASH
      ↓
Coinciden → la evidencia no fue alterada después del pago               ← FR-4.5
```

> **Este flujo es el producto.** Todo lo demás lo habilita.

---

## 11. Business Rules

| ID | Regla | Origen |
|---|---|---|
| **BR-1** | **Ningún pago se libera sin un bundle de evidencia con todos los checks en verde.** Sin excepciones, sin override manual en el MVP | Tesis del producto |
| **BR-2** | El Verifier **nunca** ve el razonamiento del Builder | [R16] — victoria temprana |
| **BR-3** | Máximo **3 intentos** por etapa. Al cuarto fallo, alto duro | FR-3.5 |
| **BR-4** | El tope de presupuesto es **duro**, no una advertencia | [S106] — controlar la probabilidad del fallo |
| **BR-5** | **Testnet únicamente.** Ningún fondo real | Discovery §8.3 |
| **BR-6** | El boletín **nunca** afirma que el software es seguro. Afirma **qué se comprobó** | FR-4.4 |
| **BR-7** | Seguridad y privacidad son **compuerta dura**, no atributos puntuables | [S031]: *"si la compuerta falla, ningún puntaje te saca de ahí"* |
| **BR-8** | Un agente que falla verificación **no cobra**, incluso si su salida es parcialmente utilizable | Sin esto, el mecanismo económico no existe |
| **BR-9** | La evidencia es **inmutable** una vez anclada. Una corrección genera un bundle nuevo | Integridad de la atestación |
| **BR-10** | Toda ejecución produce un ZIP, incluso si falla | FR-6.3 |

---

## 12. Technical Considerations

### 12.1 Arquitectura de agentes — **y por qué esta y no la original**

```
┌─────────────────────────────────────────────────────────┐
│  ORCHESTRATOR                                           │
│  · interpreta la intención                              │
│  · descompone en CORTES VERTICALES  (no en capas)       │
│  · administra presupuesto y reintentos                  │
└────────────┬────────────────────────────────────────────┘
             │
     ┌───────┴────────┬──────────────┐
     ▼                ▼              ▼
┌─────────┐      ┌─────────┐    ┌─────────┐
│BUILDER  │      │BUILDER  │    │BUILDER  │   ← paralelos SOLO si los
│ corte 1 │      │ corte 2 │    │ corte 3 │     cortes son independientes
└────┬────┘      └────┬────┘    └────┬────┘     (FR-2.4)
     │                │              │
     ▼                ▼              ▼
┌──────────────────────────────────────────┐
│  VERIFIER  (caja negra, contexto mínimo) │  ← recibe SOLO criterios + artefacto
│  · checks basados en código              │
│  · emite evidencia, no opinión           │
└────────────┬─────────────────────────────┘
             ▼
┌──────────────────────────────────────────┐
│  INTEGRATOR                              │
│  · une cortes verificados                │
│  · corre el conjunto completo de checks  │
└──────────────────────────────────────────┘
```

**Cuatro roles, no siete. La justificación es de fuente primaria** [R16], Anthropic, 23 ene 2026:

| Guía de [R16] | Cómo la cumple esta arquitectura |
|---|---|
| ✅ *"**Paralelización**: facetas independientes pueden explorarse simultáneamente"* | Cortes verticales independientes → FR-2.4 |
| ✅ *"El enfoque multi-agente **más confiable** usa un **agente de verificación dedicado que prueba la salida como caja negra** contra criterios explícitos, minimizando la transferencia de contexto"* | El Verifier es exactamente eso → FR-3.2 |
| ✅ *"**Protección de contexto**: cuando las subtareas generan alto volumen pero la mayoría es irrelevante"* | Cada Builder solo ve su corte |
| ❌ Evitado: *"**dividir por tipo de trabajo (planificación, implementación, testing) crea sobrecarga de coordinación**"* | **FR-2.2 lo prohíbe explícitamente** |
| ❌ Evitado: *"**traspasos pierden contexto por efecto teléfono descompuesto**"* | Un corte = un Builder, extremo a extremo |

> **⚠ Y el costo declarado:** *"las implementaciones multi-agente típicamente usan **3–10x más
> tokens** que los enfoques de un solo agente para tareas equivalentes"* [R16]. **Por eso NFR-5
> existe y por eso el experimento del Discovery §6.3 corre desde el día 1.** Si el brazo de un solo
> agente iguala al de tres, esta arquitectura no se justifica y hay que decirlo.

### 12.2 Elección de protocolo de pago: **MPP, no x402**

| Criterio | **MPP** | x402 |
|---|---|---|
| Firma requerida | **Cualquier keypair de Stellar** | Wallets de navegador (Freighter, Albedo, Hana…) |
| Canales de pago | **Sí** — depósito único, compromisos off-chain, un cierre | **No** en Stellar — un transfer firmado por request |
| Fees | **El servidor puede patrocinar vía `feePayer`; el agente nunca toca XLM** | El facilitador paga el gas |
| Mainnet | **Vivo** | Facilitador OpenZeppelin en mainnet; Coinbase limitado a testnet |
| Paquetes | `@stellar/mpp`, `mppx`, `@stellar/stellar-sdk` | `x402-stellar` |

> **Decisión: MPP.** Los agentes no son wallets de navegador — son procesos con keypairs. Y los
> pagos entre agentes son **alta frecuencia**, que es justo para lo que existen las sesiones de MPP.
> Fuente: [R05] documentación oficial de Stellar, [R06] comparación técnica.
>
> ⚠ [R06] reporta **un bug conocido en las constantes de USDC publicadas** de MPP. **Verificar los
> contratos contra la doc oficial antes de integrar.**

### 12.3 Wallets de agente — reservas patrocinadas

| Hecho | Dato | Fuente |
|---|---|---|
| Reserva base | **0,5 XLM** | [R03] |
| Mínimo de cuenta | **2 reservas base = 1 XLM**, más 0,5 por subentrada | [R03] |
| Sin patrocinio, 4 agentes + trustlines USDC | ≥ 6 XLM inmovilizados por ejecución | cálculo |
| **Con CAP-33** | Cuenta creada con `startingBalance` **0**; el patrocinador carga las reservas | [R03] |

> **`BeginSponsoringFutureReservesOp` y `EndSponsoringFutureReservesOp` deben aparecer ambas en la
> transacción de patrocinio**, garantizando que ambas cuentas consienten [R03]. Sin esto, cada
> wallet de agente cuesta dinero inmovilizado por ejecución.

### 12.4 Anclaje de la evidencia

| Tipo de memo | Tamaño | Uso acá |
|---|---|---|
| MEMO_TEXT | 28 bytes | ❌ insuficiente |
| MEMO_ID | entero 64-bit | ❌ |
| **MEMO_HASH** | **hash de 32 bytes** | ✅ **SHA-256 = exactamente 32 bytes** |

Fuente: [R19], documentación oficial de Stellar.

> **No hace falta un contrato Soroban para el MVP.** El pago lleva la prueba. Menos superficie,
> menos fallos, y la verificación por terceros es una consulta a Horizon.

### 12.5 Restricciones técnicas declaradas

| # | Restricción |
|---|---|
| TC-1 | **Testnet únicamente.** BR-5 |
| TC-2 | **Una sola categoría de aplicación** — la de referencia de §18.4 |
| TC-3 | **Solo checks basados en código.** NFR-1 |
| TC-4 | Sin RAG por especialista en el MVP — H8 sin investigar |
| TC-5 | Sin persistencia entre ejecuciones más allá de los artefactos |
| TC-6 | Sin autenticación de usuario en el MVP — una sola sesión |

---

## 13. Integrations

| # | Integración | Propósito | Estado | MVP |
|---|---|---|---|---|
| **I1** | **Stellar Testnet (Horizon + RPC)** | Liquidación y anclaje | Estable | ✅ |
| **I2** | **`@stellar/mpp` + `mppx` + `@stellar/stellar-sdk`** | Pagos entre agentes | Publicados [R05] | ✅ |
| **I3** | **USDC testnet** — emisor `GBBD47IF6LWK7P7MDEVSCWR7DPUWV3NY3DTQEVFL4NAT4AQH3ZLLFLA5`, contrato SEP-41 `CBIELTK6YBZJU5UP2WWQEUCYKLPU6AUNZ2BQ4WWFEIE3USCIHMXQDAMA` | Denominación | Publicado [R04] | ✅ |
| **I4** | **Friendbot testnet** | Fondeo del patrocinador | Estándar | ✅ |
| **I5** | **Proveedor de LLM** | Constructores y orquestador | — | ✅ |
| **I6** | **Escáner de seguridad** (Semgrep/Trivy o equivalente) | Checks de §18 | — | ✅ |
| **I7** | **Runtime de contenedores** | Aislamiento NFR-2 | — | ✅ |
| **I8** | **MPP Router** — 446 rutas, 20 servicios, mainnet desde 9 jul 2026 | **Pagar el uso de LLM con USDC de Stellar** | Vivo [R06] | ⚠ **Should** |
| **I9** | **Facilitador OpenZeppelin x402** | Alternativa de pago | Testnet y mainnet [R04] | ❌ |
| **I10** | **Raven MCP Server / Stellar Skills** | Contexto de Stellar para los agentes | Documentado [R21] | ⚠ **Could** |

> **I8 merece atención particular.** El punto 4 del documento original —*"los agentes pagan por su
> uso de LLM"*— **ya existe desplegado en mainnet**: MPP Router permite pagar OpenAI, Anthropic,
> DeepSeek, Perplexity, Exa, Firecrawl y Tavily con USDC de Stellar [R06]. **No hay que
> construirlo.** Integrarlo convierte una afirmación de visión en una demostración real y refuerza
> la historia de integración ante el SCF.

---

## 14. Data Requirements

### 14.1 Entidades

```
Run
├─ id, created_at, status {running|converged|halted_failed|halted_budget}
├─ intent_text, specification (JSON), budget_cap, spend_total
└─ Slice[]
    ├─ id, run_id, name, status, attempt_count
    ├─ Artifact       · sha256, path, size_bytes
    ├─ CheckResult[]  · check_id, result{pass|fail}, raw_output, duration_ms
    ├─ EvidenceBundle · digest, canonical_json, created_at
    └─ Payment        · agent_account, amount, tx_hash, memo_hash, status

Agent
└─ id, role {orchestrator|builder|verifier|integrator}
   stellar_account, sponsored_by
```

### 14.2 Bundle de evidencia — esquema canónico

```json
{
  "schema_version": "1.0",
  "run_id": "uuid",
  "slice_id": "uuid",
  "specification_sha256": "hex",
  "artifact_sha256": "hex",
  "checks": [
    { "id": "AC-01", "statement": "...", "result": "pass",
      "tool": "npm", "raw_output": "...", "duration_ms": 8421 }
  ],
  "not_checked": [
    "Comportamiento bajo carga concurrente",
    "Accesibilidad",
    "Corrección del modelo de datos frente a la intención del negocio"
  ],
  "agents": [ { "role": "builder", "account": "G..." } ],
  "created_at": "ISO-8601"
}
```

| ID | Requisito de datos |
|---|---|
| **DR-1** | The evidence bundle **shall** be serialised with sorted keys and no insignificant whitespace before hashing |
| **DR-2** | The `not_checked` array **shall never** be empty |
| **DR-3** | Raw tool output **shall** be stored verbatim, not summarised |
| **DR-4** | The system **shall not** persist the user's intent text beyond the run |
| **DR-5** | **If** any field would contain a credential, **then** the system **shall** replace it with `[REDACTED]` before hashing |

> **DR-2 es una regla de producto, no técnica.** Un bundle que no declara qué **no** comprobó es un
> informe engañoso. Materializa FR-4.4 en el esquema, de forma que no se pueda omitir por olvido.
>
> **DR-1 es condición de posibilidad del flujo §10.4:** sin serialización canónica, un tercero no
> puede recomputar el digest.

---

## 15. UX/UI Requirements

| ID | Requisito |
|---|---|
| **UX-1** | The system **shall** present a single-screen run view showing every stage, its status and its cost |
| **UX-2** | The report **shall** open with a single sentence stating whether the artifact passed every check |
| **UX-3** | The report **shall** use no security jargon without a plain-Spanish gloss in the same sentence |
| **UX-4** | The report **shall** present "no comprobado" with the same visual weight as "falló" |
| **UX-5** | **When** a stage fails, the system **shall** show the failing criterion in plain Spanish before showing any tool output |
| **UX-6** | The report **shall** be printable to a single PDF and self-contained |
| **UX-7** | The system **shall not** require the user to read a log to understand the outcome |

> **UX-4 es contraintuitivo y deliberado.** La mayoría de los informes de seguridad sepultan lo no
> comprobado. Para P1 —que va a reenviar esto— **un check ausente y un check fallado son igual de
> importantes**, porque de ambos depende qué puede afirmar sin mentir.
>
> ❌ **La `pm-knowledge-base` no cubre onboarding ni activación.** Estos requisitos son juicio de
> diseño, no derivados de fuente. Registrado en §22 · Q5.

---

## 16. Security Requirements

[S031] vía [S050]: seguridad y privacidad son **compuerta dura** — *"tratala como precondición, no
como atributo negociable. Si la compuerta falla, ningún puntaje te saca de ahí."*

| ID | Requisito |
|---|---|
| **SEC-1** | The system **shall** execute all generated code inside a container with no outbound network access except an explicit allowlist |
| **SEC-2** | The system **shall not** execute generated code on the host |
| **SEC-3** | Agent keypairs **shall** be generated per run and **shall not** persist after the run ends |
| **SEC-4** | The system **shall not** write any key, token or credential into the artifact, the evidence bundle, the report or any log |
| **SEC-5** | **If** generated code attempts a network call to a non-allowlisted host during verification, **then** the system **shall** fail the check and record the attempted destination |
| **SEC-6** | The system **shall not** accept instructions found inside generated code, tool output or scanned files as instructions to itself |
| **SEC-7** | **While** operating on testnet, the system **shall** refuse any configuration pointing at mainnet |
| **SEC-8** | The system **shall** treat the user's intent text as untrusted input |

> **SEC-6 es la mitigación de inyección de prompt y no es opcional.** Un sistema donde agentes leen
> salidas de otros agentes y de herramientas es un sistema donde el contenido puede intentar dirigir
> al agente. El límite es: **lo que viene de una herramienta o de código generado es dato, nunca
> instrucción.**
>
> **SEC-7 hace de BR-5 una restricción del código, no una promesa de la documentación.**

---

## 17. Metrics / KPIs

### 17.1 ⚠ Advertencia obligatoria

> **El diseño de medición es un gap declarado de la `pm-knowledge-base`.** No cubre cómo elegir
> métricas, indicadores adelantados vs rezagados, cohortes, diseño de A/B, significancia
> estadística, ni la ley de Goodhart. **Lo que sigue es instrumentación mínima, no un plan de
> medición.**

### 17.2 Métricas primarias

| # | Métrica | Definición | Objetivo MVP | Origen |
|---|---|---|---|---|
| **M1** | **Tasa de convergencia extremo a extremo** | ejecuciones que producen artefacto con todos los checks en verde / ejecuciones totales | **≥ 3 de 5** | Discovery §8.4 |
| **M2** | **Tasa de fallo por etapa** | fallos / intentos, por etapa | instrumentado | localiza el multiplicando débil |
| **M3** | **Tasa de detección de vulnerabilidades sembradas** | detectadas / sembradas | **≥ 80%** | valida H3 |
| **M4** | **Pagos sin evidencia** | pagos liberados sin bundle válido | **exactamente 0** | tesis del producto |
| **M5** | **Reintentos hasta converger, por etapa** | media y máximo | instrumentado | distingue "falla y se recupera" de "falla" |
| **M6** | **Tokens por ejecución** | total, desglosado por agente | contra NFR-5 | [R16]: 3–10x |

### 17.3 Métricas de flujo de agente

[S031] argumenta que los productos usados por agentes necesitan su propio conjunto: *"**completitud
de tarea** — tasa de resolución de intención, precisión de llamada a herramientas, latencia, tasa de
fallback, **tasa de intervención humana**"*. ⚠ Fuente única, vendor, 2026, no verificada.

> **Brújula *es* el flujo de agente. Y "tasa de intervención humana" es la métrica del producto
> entero**, porque la promesa es que sea cero.

### 17.4 La métrica que calibra al verificador

| # | Métrica | Por qué es indispensable |
|---|---|---|
| **M7** | **Tasa de acuerdo humano** — un humano técnico revisa una muestra y dice si coincide con el veredicto del Verifier | **Sin esto no sabés si el sistema converge a lo correcto.** [E011]: un evaluador amortiza el juicio humano, no lo reemplaza; hay que contrastarlo periódicamente. Es la única defensa contra la victoria temprana [R16] |

### 17.5 Prohibido medir

| Anti-métrica | Por qué |
|---|---|
| Líneas de código generadas | [E002] principio 7: *"el software que funciona es la medida primaria de progreso"* |
| Cantidad de agentes involucrados | Cada agente es costo. [R16]: 3–10x tokens |
| Velocidad de generación sin tasa de convergencia | Genera rápido y mal es el problema, no la solución |
| **Productividad autorreportada** | [E006] midió creer 20% más rápido y ser 19% más lento. **El autorreporte no es medición** |

---

## 18. Acceptance Criteria

**Esta sección es el contrato.** El Verifier ejecuta exactamente esto. Cada criterio es
verificable por máquina; los que no lo son están declarados como no verificables y **excluidos del
contrato** en lugar de simulados.

### 18.1 Del artefacto generado

| ID | Criterio (EARS) | Herramienta |
|---|---|---|
| **AC-01** | The system **shall** produce a project where `npm ci && npm run build` exits with code 0 in a clean container | npm |
| **AC-02** | The system **shall** produce a lockfile in which every declared dependency resolves | npm |
| **AC-03** | The system **shall** produce a project reporting **zero high or critical** advisories | `npm audit` |
| **AC-04** | **Where** the project contains business logic, the system **shall** produce an executable test suite in which all tests pass | test runner |
| **AC-05** | The system **shall** produce no file containing `TODO`, `FIXME`, `<YOUR_`, `CHANGEME` or `lorem ipsum` outside `.env.example` and `README.md` | grep |
| **AC-06** | The system **shall** produce `.env.example` declaring every environment variable read anywhere in the code | AST + grep |
| **AC-07** | The system **shall** produce no committed secret | secret scanner |
| **AC-08** | **Where** the project requires persistence, the system **shall** produce migrations that apply successfully against an empty database | migration runner |
| **AC-09** | **If** the project exposes an HTTP API, **then** every endpoint that reads or writes user data **shall** reject an unauthenticated request with 401 or 403 | integration test |
| **AC-10** | **If** the project uses a hosted database with row-level policies, **then** the system **shall** produce policies denying anonymous read and write by default | policy check |
| **AC-11** | The system **shall** produce a `README.md` containing runnable setup steps | structural check |
| **AC-12** | The system **shall** produce deployment configuration that completes a dry-run | platform CLI |

> **AC-09 y AC-10 son la razón de ser del producto.** Atacan directamente el hallazgo de [R10]: el
> **57%** de las apps con Supabase alcanzables permitían lectura no autenticada. **Si Brújula
> comprueba una sola cosa, es esa.**

### 18.2 Del sistema Brújula

| ID | Criterio (EARS) |
|---|---|
| **AC-20** | **When** a Builder output passes every check, the system **shall** emit an evidence bundle whose digest matches the `MEMO_HASH` of the resulting payment |
| **AC-21** | **If** any check fails, **then** the system **shall not** emit a payment for that stage |
| **AC-22** | **If** a stage fails three consecutive times, **then** the system **shall** halt, **shall not** pay, and **shall** name the failing criterion |
| **AC-23** | **If** cumulative spend reaches the budget cap, **then** the system **shall** halt and **shall not** initiate further payments |
| **AC-24** | The system **shall** produce a ZIP on every run, including halted runs |
| **AC-25** | A third party **shall** be able to recompute the evidence digest from the bundle and match it against the on-chain memo |
| **AC-26** | The evidence bundle **shall** contain a non-empty `not_checked` array |
| **AC-27** | **If** any configuration points at Stellar mainnet, **then** the system **shall** refuse to start |

### 18.3 Criterios que NO se pueden verificar — declarados, no simulados

| Del documento original | Por qué se excluye |
|---|---|
| *"Arquitectura profesional"* | ❌ **No traducible a una comprobación.** Descomponer o retirar del contrato |
| *"Se siente como un equipo experimentado"* | ❌ **Es una hipótesis a medir con usuarios**, no un criterio de aceptación |
| *"Un camino claro a producción"* | Parcialmente cubierto por AC-12. El resto es juicio |

> **Declararlos es más honesto que simular que se comprueban.** Un criterio infalsable dentro del
> contrato produce una atestación falsa, que es peor que ninguna.

### 18.4 Especificación de referencia

Todas las métricas de §17 se miden contra este enunciado fijo:

> *"Sistema de turnos donde un cliente reserva un horario y recibe una confirmación por email. El
> negocio ve la agenda del día. Un turno no puede solaparse con otro. El cliente puede cancelar
> hasta 2 horas antes."*

**Con tres vulnerabilidades sembradas deliberadamente** para medir M3: una tabla sin política de
lectura, una clave en el bundle del cliente, y un endpoint sin autenticación.

---

## 19. Risks & Constraints

### 19.1 Riesgos, con respuesta [S065]

| # | Riesgo | Evidencia | Respuesta | Riesgo residual |
|---|---|---|---|---|
| **RK-1** | **Victoria temprana del verificador** | [R16] lo nombra como el modo de fallo principal | **MITIGAR** — FR-3.2, FR-3.6, NFR-1, M7 | ⚠ **Alto.** Solo los checks basados en código son deterministas; lo que no está en §18 no se comprueba |
| **RK-2** | **La cadena no converge** | Discovery §8.4 | **MITIGAR** — 4 roles, verificación por etapa, FR-6.3 | ⚠ Sigue fallando a veces. Es aceptado y se reporta |
| **RK-3** | **El multi-agente no supera al agente único** | [R16]: 3–10x tokens; descomposición por tipo de trabajo contraindicada | **INVESTIGAR** — experimento del Discovery §6.3 desde el día 1 | ⚠ **Si el resultado es negativo, hay que decirlo.** Es un hallazgo |
| **RK-4** | **Fondos reales mal distribuidos** | [S106]: cuadrante temerario | **EVITAR** — BR-5, SEC-7, AC-27 | Ninguno en esta fase |
| **RK-5** | **El usuario no puede desplegar lo que recibe** | [R14]: 15–20% anual de mantenimiento | **ACEPTAR y declarar** — el MVP apunta a P1 | ⚠ Bloquea a P2 por completo |
| **RK-6** | **Sobreingeniería** | [S087]: *"construir más de lo necesario añade complejidad y retrasos"* | **EVITAR** — §20 | — |
| **RK-7** | **Dependencia de un proveedor de modelos** | [S087]: *"riesgo estructural que no podés controlar del todo"* | **ACEPTAR** — decisión registrada | ⚠ Sin plan de contingencia |
| **RK-8** | **Un incumbente añade verificación** | Replit Agent ya testea en navegador real [R07] | **MONITOREAR** | ⚠ La ventana es corta |
| **RK-9** | **Bug conocido en constantes USDC de MPP** | [R06] | **MITIGAR** — verificar contra doc oficial antes de integrar | — |
| **RK-10** | **Inyección de prompt vía código generado** | Riesgo estructural de sistemas multi-agente | **MITIGAR** — SEC-6 | ⚠ No hay defensa completa conocida |

### 19.2 Restricciones

| ID | Restricción |
|---|---|
| **C-1** | **11 días de construcción.** Congelar 26/09 |
| **C-2** | Equipo de 2 a 4 personas (regla de la hackathon) |
| **C-3** | Testnet únicamente |
| **C-4** | Una sola categoría de aplicación de referencia |
| **C-5** | Solo checks basados en código |
| **C-6** | Sin entrevistas de usuario antes del MVP |
| **C-7** | El presupuesto de tokens es finito y **3–10x** el de un agente único [R16] |

### 19.3 Supuestos [S084]

> *"Cualquier cosa que **esperás que esté en su lugar aunque no esté garantizada**."*

| ID | Supuesto | Cómo se valida |
|---|---|---|
| **A-1** | `@stellar/mpp` funciona en testnet como está documentado | **Spike técnico, día 1.** Es bloqueante |
| **A-2** | Las reservas patrocinadas permiten wallets de agente con saldo 0 | Spike técnico, día 1 |
| **A-3** | Los checks de §18 detectan las vulnerabilidades sembradas | M3 |
| **A-4** | El presupuesto de tokens alcanza para 5 ejecuciones completas | M6 |
| **A-5** | P1 valora una atestación lo suficiente como para pagarla | ❌ **Sin validar. Es H1.** Requiere entrevistas |

### 19.4 Dependencias [S084]

> *"Cualquier condición o ítem del que el producto **dependa**."*

Stellar testnet operativa · Horizon/RPC accesibles · Friendbot funcionando · disponibilidad del
proveedor de LLM · registro npm · runtime de contenedores en la máquina de la demo.

> **La demo depende de servicios de red externos.** Mitigación: **grabar una ejecución completa de
> respaldo** (D8–9 del plan).

---

## 20. MVP Scope

MoSCoW con el tope del 60% de Musts que [S031] atribuye a DSDM — ⚠ **no verificado** contra
documentación de DSDM:

> *"**Los Must-have no deberían consumir más del ~60% del esfuerzo, con ~20% reservado para
> Could-haves como contingencia.** La mayoría de los equipos infla los Musts al 90%+ y pierde toda
> la contingencia. Cuando llega la sorpresa, lo único que queda por cortar es algo ya etiquetado
> como crítico de misión, que es **cómo el proceso de priorización se devora a sí mismo.**"*

### MUST — ~60% del esfuerzo

| Feature | Requisitos |
|---|---|
| F1 · Captura y clarificación de intención | FR-1.1 … FR-1.5 |
| F2 · Orquestación por cortes verticales | FR-2.1 … FR-2.5 |
| F3 · Gate de verificación por etapa | FR-3.1 … FR-3.6 |
| F4 · Bundle de evidencia + digest | FR-4.1, FR-4.2, FR-4.5 |
| F5 · Pago condicionado a evidencia (MPP testnet) | FR-5.1 … FR-5.7 |
| F6 · Boletín en castellano | FR-4.3, FR-4.4, UX-1 … UX-7 |
| F7 · Wallets de agente con saldo 0 | FR-5.1 |
| F8 · Tope de presupuesto | FR-5.4, FR-5.5 |
| — · Checks AC-01 a AC-12 | §18.1 |
| — · Seguridad SEC-1 … SEC-8 | §16 |

### SHOULD — ~20%

F9 explicación de vulnerabilidades · F10 costo por etapa · I8 MPP Router para pagar LLMs ·
experimento A/B/C del Discovery §6.3

### COULD — ~20% de contingencia, se corta primero

F11 canales MPP · F12 verificar proyecto subido · F13 smart wallet con passkey · I10 Raven MCP

### WON'T — declarado, con motivo

| No se hace | Por qué |
|---|---|
| Los 7 agentes originales | [R16]: la descomposición por tipo de trabajo crea sobrecarga. Discovery §8.4: 7 etapas al 90% ≈ 48% de éxito |
| Fondos reales en mainnet | [S106]: cuadrante temerario. Consecuencia alta × probabilidad alta |
| Marketplace de agentes de terceros | Requiere lado dos del mercado. ❌ La KB no lo cubre |
| Despliegue gestionado | Requiere operación continua. Bloquea a P2, y es consciente |
| RAG por especialista | H8 sin investigar. No entra al camino crítico |
| Múltiples categorías de aplicación | Una categoría permite criterios de aceptación reales |
| Evaluadores basados en modelo | NFR-1. Sin tiempo para calibrar → victoria temprana |
| Multi-usuario y autenticación | TC-6 |

> **Esta sección es el artefacto más valioso del PRD.** Tres fuentes independientes del corpus
> —[S138] *"What we're not doing"*, [S113] *"Features Out"*, [S084] *"ítems fuera de alcance"*—
> tratan la exclusión declarada como sección con nombre propio. [S113] añade el requisito del
> **porqué**: *"sin la justificación, el ítem vuelve en cuanto la persona que tomó la decisión sale
> de la conversación."*

---

## 21. Future Scope

### Fase 2 · Sprint de Instaward (~30 días)

| # | Ítem | Precondición |
|---|---|---|
| 1 | **8–10 entrevistas de usuario** [S081] para validar H1 | **Bloqueante para todo lo demás** |
| 2 | Liquidación en mainnet, con un punto manual | Auditoría de la ruta de pagos |
| 3 | F12 · verificar proyectos subidos — **oportunidad O2** | Convierte competidores en canal |
| 4 | Ampliar §18 a más categorías | Un conjunto de checks por categoría |
| 5 | Evaluadores basados en modelo **con calibración humana** | M7 con línea base |
| 6 | Publicar la evidencia de H2 — **oportunidad O5** | El dato no existe públicamente |

### Fase 3 · SCF Build Award

**Requisitos verificados del handbook** [R18]:

| Requisito | Estado de Brújula |
|---|---|
| Hasta **US$150.000 en XLM** | — |
| Track **Integration** — *"equipos listos para construir que quieren incorporar un building block existente de Stellar"* | ✅ **MPP/x402 son building blocks. Es el track que corresponde** |
| *"equipos fuertes listos para entregar en **3–5 meses**"* | Planificar en consecuencia |
| **Mainnet en ~4 meses** desde el award | Fase 2 debe cerrar mainnet |
| Tramos **10% → 20% → 30% → 40%** | Estructurar hitos así |
| Entregar cada tramo **dentro de 90 días** del pago anterior, o se pierden los fondos | Restricción dura de planificación |
| **KYC obligatorio** para cada contribuyente individual | Preparar con antelación |
| Requisitos de la aplicación: roadmap técnico detallado, desglose de presupuesto por tramos, **tracción actual**, habilidades del equipo | **La tracción es el punto débil.** Ver abajo |
| Evaluación: valor para el ecosistema, factibilidad técnica, claridad del roadmap y capacidad del equipo. En Open Track **vota la comunidad verificada** | — |

> **La brecha más grande hacia el SCF es la tracción.** Se pide explícitamente. El MVP de la
> hackathon no la produce. **Las entrevistas y los primeros usuarios reales de la Fase 2 son el
> camino, no más features.**

### Fase 4 · Mercado

| # | Ítem |
|---|---|
| 1 | **P2 · PyME argentina** con despliegue gestionado — el mercado grande |
| 2 | Marketplace de agentes de terceros, **si** el lado dos se resuelve |
| 3 | Modelo de precio — ❌ **gap de la KB**, y Brújula tiene costo marginal real por ejecución |

---

## 22. Open Questions

| # | Pregunta | Bloquea | Cómo se resuelve |
|---|---|---|---|
| **Q1** | ¿Alguien **paga** por verificación de software generado? (H1) | Fase 2 | **8–10 entrevistas** [S081] |
| **Q2** | ¿El multi-agente supera al agente único acá? (H2) | La arquitectura entera | **Experimento del Discovery §6.3, desde el día 1** |
| **Q3** | ¿Modelo de precio: por ejecución, suscripción, o comisión? | Fase 2 | ❌ **La KB no cubre pricing** |
| **Q4** | ¿Cuánto cuesta realmente una ejecución extremo a extremo? | Unit economics | M6 lo instrumenta |
| **Q5** | ¿Cómo se activa a un usuario que recibe un ZIP? | P2 por completo | ❌ **La KB no cubre onboarding** |
| **Q6** | ¿Cómo se organiza un equipo de software multi-agente? | Escalar más allá de 4 roles | ❌ **Ninguna fuente publicada** |
| **Q7** | ¿Marketplace de dos lados? | Fase 4 | ❌ **La KB no cubre marketplaces** |
| **Q8** | ¿Qué hace *AI Real World Payment Agents* en el SCF? | Posicionamiento ante el SCF | **Investigar antes de aplicar** [R17] |
| **Q9** | ¿Qué entregaron los equipos de *Stellar Hacks: Agents*? | Diferenciación | Revisar entregas |
| **Q10** | Accesibilidad del producto generado | Completitud del contrato | ❌ **Ausente de la KB entera** |
| **Q11** | ¿La atestación tiene valor legal o solo reputacional? | Redacción de FR-4.4 | Consulta legal |

---

## Anexo A · Trazabilidad

### Requisitos ← evidencia

| Requisito | Se deriva de |
|---|---|
| FR-2.2 (no dividir por capa) | [R16] Anthropic, 23 ene 2026 |
| FR-3.2 / FR-3.6 (verificador caja negra) | [R16] — patrón del verificador dedicado + victoria temprana |
| FR-3.5 (tope de 3 intentos) | [E011] `pass^k` + [E012] bucle `converge` |
| FR-5.1 (wallets con saldo 0) | [R03] CAP-33 reservas patrocinadas |
| FR-5.3 (`MEMO_HASH` = digest) | [R19] MEMO_HASH = 32 bytes; SHA-256 = 32 bytes |
| FR-5.6 (testnet) | [S106] matriz temerario/calculado |
| NFR-1 (solo checks de código) | [E011] tipos de evaluador |
| NFR-5 (techo de tokens) | [R16] 3–10x |
| AC-09 / AC-10 (auth y RLS) | [R10] 57% con lectura anónima |
| §18 en EARS | [E014] Mavin et al., Rolls-Royce, 2009 |
| §20 tope del 60% | [S031] ⚠ no verificado contra DSDM |
| §20 exclusiones con motivo | [S138] [S113] [S084] — convergencia de tres fuentes |
| M7 (acuerdo humano) | [E011] calibración de evaluadores |
| §17.5 anti-métricas | [E002] principio 7 · [E006] brecha de percepción |
| DR-2 (`not_checked` no vacío) | FR-4.4 — honestidad de la atestación |

### Fuentes nuevas de este documento

| ID | Fuente | Tipo |
|---|---|---|
| **R19** | developers.stellar.org — tipos de memo; **MEMO_HASH = hash de 32 bytes** | 🟢 Documentación oficial |
| **R20** | developers.stellar.org / stellar.org — smart wallets con passkey, `__check_auth`, **firmantes de política con límites de gasto por período** | 🟢 Documentación oficial |
| **R21** | developers.stellar.org — Raven MCP Server, Stellar Skills, llms.txt | 🟢 Documentación oficial |

R01–R18 en el registro de `01-product-discovery-report.md`.

### Método

`pm-knowledge-base` v1.1.0 — [S031] [S050] [S084] [S085] [S087] [S106] [S113] [S127] [S138] ·
[E002] [E006] [E011] [E012] [E014]

---

## Anexo B · Lo que este PRD NO especifica

Declarado para que ningún agente lo invente:

| Área | Estado |
|---|---|
| **Stack tecnológico del propio Brújula** | ❌ Deliberadamente abierto. Decisión del equipo |
| **Prompts de los agentes** | ❌ Implementación |
| **Diseño visual** | ❌ Solo restricciones de UX en §15 |
| **Modelo de precio** | ❌ Q3 |
| **Términos legales de la atestación** | ❌ Q11 |
| **Accesibilidad** | ❌ Q10 |
| **Qué pasa si el usuario disputa un resultado** | ❌ No especificado. **Debería estarlo antes de mainnet** |

> **La última fila es una omisión consciente que hay que cerrar.** Un sistema que condiciona pagos a
> una verificación automática necesita un procedimiento de disputa antes de tocar dinero real.

---

*Documento 2 de 2. Deriva de [`01-product-discovery-report.md`](01-product-discovery-report.md).*

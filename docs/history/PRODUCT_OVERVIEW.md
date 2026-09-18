# Mirag

**Le das un problema. Mirag busca lo que sabe, propone una solución, la ejecuta, y te enseña
exactamente en qué se apoya para confiar en ella — y en qué no.**

## El problema que resuelve

Un asistente que escribe código te dice que funciona. No lo sabe: lo afirma. Y cuando te dice
"los tests pasan", normalmente lo que ha pasado es que un comando terminó con exit code 0.

Mirag separa tres cosas que casi todas las herramientas mezclan:

```
MODEL CLAIM      lo que el modelo dice que hizo
OBSERVED         lo que la máquina vio al ejecutarlo
VERIFIED         lo que queda demostrado al cruzar las dos
```

Esa separación no es un detalle de la interfaz: es el producto. Cada respuesta llega con un panel
de cuatro capas donde no se pueden confundir, porque no comparten sitio.

## Y ahora entrega proyectos, no archivos sueltos

```
Creá una API REST de libros con CRUD completo. Arquitectura por dominios:
separá router, service, repository, schemas y models. Agregá tests.
        ↓
libros-api · 14 archivos · VERIFICADO · 16/16 marcadores
[ Descargar ZIP ]
        ↓  descomprimir y ejecutar
Ran 9 tests in 0.520s — OK
```

El ZIP no es otra lógica: es la última representación del mismo artefacto que se verificó.
Entre el proyecto, el workspace donde se ejecuta, el manifiesto, el ZIP y lo que se
descarga hay **identidad comprobable por hashes**, y si en algún eslabón no cuadra no hay
descarga. Ver [PROJECT_ARTIFACT_INTEGRITY_REPORT.md](PROJECT_ARTIFACT_INTEGRITY_REPORT.md).

Y el CRUD no se da por bueno porque existan cinco funciones: **Mirag escribe su propio
arnés**, levanta el servidor del proyecto en un puerto libre y le pega por HTTP —
POST, GET, GET por id, PUT (comprobando que *persista*), DELETE y 404. Los identificadores
de esos marcadores llevan un nonce por ejecución, así que el modelo no puede fabricarlos.

## Cómo funciona

```
Pregunta → Plan → Recuperación → Contexto → Modelo → Herramienta → Verificación → Evidencia → Respuesta
```

- **Plan** — qué cajas del corpus tocar, si hace falta código, si hace falta mirar el repo. 0 llamadas.
- **Recuperación** — tres índices a la vez: conocimiento, anti-patrones y fallos conocidos. Cada
  fragmento conserva de dónde salió, en qué puesto y por qué métodos pasó.
- **Contexto** — un solo sitio decide qué entra al prompt: orden, deduplicación, techo de tokens.
- **Verificación** — el código se ejecuta de verdad, en un temporal, con lista blanca de intérpretes.
  El veredicto lo decide la **ejecución**, con cuatro estados posibles:

  | | |
  |---|---|
  | `verde` | hubo marcadores y todos pasaron |
  | `rojo` | se ejecutó y falló |
  | `sin evidencia` | terminó sin error y **no imprimió ni un marcador** — esto no es aprobar |
  | `no ejecutado` | ni llegó a correr |

  El tercero es el que más importa. Antes de arreglarlo, ese caso devolvía *"TESTS EN VERDE"*.

- **Evidencia** — cada propiedad que el modelo declaró, cruzada contra un marcador real.
- **Abstención** — si el corpus no cubre lo que preguntas, Mirag lo dice **antes** de responder.

## Qué está realmente activo

| | |
|---|---|
| BM25 sobre tres índices | **sí** — es el suelo del ranking |
| Reranker | **sí** — +0.082 MRR duro, medido sobre el camino real |
| Búsqueda de símbolos en el repo | **sí**, solo cuando la pregunta lo pide |
| Señal vectorial | **no** — se midió: −0.015 MRR y 13× más lento |
| Grafo | conectado, apagado: +8 fragmentos sin evidencia de que ayuden |
| Caché semántica, árbol, routing de modelos | **experimentales**, fuera del camino |

Nada está encendido por existir. `config.activar()` lee las mediciones, y **una etapa sin medir
nace apagada**.

## Sin dependencias en el núcleo

Python de biblioteca estándar. **Cero paquetes externos en los 30 módulos de producción**,
verificado recorriendo su AST. Un servidor que escucha solo en loopback y sirve exactamente dos
rutas de página, una de descarga y una de lectura JSON.

La única excepción es `blockchain/`, la capa de identidad Stellar: vive fuera de la cadena de
producción, tiene su propio entorno gestionado con `uv` y declara `stellar-sdk`. `import server`
sigue funcionando sin ese paquete instalado, y hay un test que lo comprueba.

## Limitaciones conocidas

Están aquí porque medirlas fue el trabajo, no a pesar de eso.

1. **No se sabe si los anti-patrones recuperados aplican.** El buscador devuelve un número fijo
   por consulta, relevantes o no, y los scores no separan: en una tarea de concurrencia, el más
   puntuado (10.63) no hablaba de concurrencia, y uno genuinamente relevante puntuaba 4.72. Por eso
   se etiquetan `RECOVERED` y no "aplica".
2. **Acotar la búsqueda por temas no demostró hacer mejor al agente.** Reduce el contexto un 21% y
   no mejora lo verificado. Con n=5 eso significa "no se demostró ganancia", no "es malo".
3. **El reranker empeora las paráfrasis** (0.490 → 0.427) aunque gane en el agregado. Está
   encendido con esa salvedad escrita.
4. **Pedir código no garantiza recibirlo**: el modelo a veces responde en prosa aunque se le
   ofrezca la herramienta. Observado 1 de 5 veces.
5. **En tareas de concurrencia difíciles**, de 10 ejecuciones con modelo real, 2 acabaron en verde.
   Mirag no las resuelve; lo que sí hace es **no mentir sobre las otras 8**.
6. **Un proyecto con dependencias que aquí no están** (FastAPI, por ejemplo) se genera y
   se valida, pero **nunca llega a `VERIFICADO`**: se queda en `VALIDADO` diciendo qué
   falta. El código puede estar bien; aquí no hay evidencia de que lo esté.
7. **El detector de "esto es un proyecto"** acierta 6 de 7 peticiones de proyecto, 10 de
   10 de archivo suelto y 49 de 49 consultas. La que falla —*"Armá un bot de Telegram con
   comandos y persistencia"*— es genuinamente ambigua.
8. **El modo `arquitecto` es experimental** y está etiquetado como tal: sus fases no pasan por la
   disciplina de evidencia del pipeline.

## Qué no es

No es un colección de técnicas de RAG. Cada pieza que está encendida se midió sobre el camino que
alimenta al modelo, y las que no se justificaron están apagadas y dicen por qué.

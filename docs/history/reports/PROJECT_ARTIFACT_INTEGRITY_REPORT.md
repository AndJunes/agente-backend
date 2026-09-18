# El ZIP que se descarga es el proyecto que se verificó

El defecto que recorrió todas las fases de este proyecto, en su forma nueva:

```
ProyectoArtefacto  ≠  workspace verificado  ≠  ZIP  ≠  árbol que ve el usuario
```

Este documento es la prueba de que esa cadena tiene identidad comprobable en cada eslabón.

## La cadena

```
árbol sellado (inmutable)
   │  materializar() con write_bytes — nunca write_text
   ▼
workspace del artefacto            artefactos/<id>/proyecto/
   │  skills.verificar_codigo ejecuta los tests y la sonda de CRUD
   ▼
certificado                        el estado sale de la ejecución, de nada más
   │  manifiesto: sha256 COMPLETO por archivo, DESPUÉS de verificar
   ▼
ZIP                                lista blanca: solo entra lo que el manifiesto declara
   │  se reabre, se extrae a un temporal y se RE-HASHEA
   ▼
descarga                           los MISMOS bytes en memoria, re-hasheados al servir
```

## Dos decisiones que sostienen la cadena

**El árbol se sella antes de verificar.** `Proyecto.sellar()` congela el dict: a partir de
ahí, cualquier intento de añadir revienta. Lo que se verifica es, por construcción, lo que
se empaqueta. Una reparación no muta el artefacto: produce uno nuevo.

**Los bytes se sirven de memoria.** `Paquete.datos` es la fuente de la descarga; el `.zip`
en disco es una copia de conveniencia que nadie lee para servir. Así no existe la ventana
entre *"el gate inspeccionó estos bytes"* y *"el servidor escribió estos otros"*. Y justo
antes de escribir la cabecera se re-hashea una vez más — ~1 ms sobre 8 KB.

**El hash es completo, no truncado.** `cache.py` trunca a 16 hex y hace bien: allí el hash
**detecta** cambios. Aquí el hash **es la prueba** de identidad entre dos estados de la
cadena, y truncar convertiría una prueba en una heurística.

## Dos criterios independientes, a propósito

| | cómo decide |
|---|---|
| el constructor | **lista blanca**: solo entra lo que está en el manifiesto |
| el inspector | **lista negra** de patrones + escaneo del contenido |

Si el inspector reutilizara el filtro del constructor, un solo bug pasaría las dos puertas
y el test saldría verde. Por eso `.env`, `__pycache__` y las trazas de Mirag no pueden
colarse *por construcción*, y además se rechazan *por contenido* si aparecieran.

## Las 13 comprobaciones

```
✅ cabe en el tope                          ✅ se reabre
✅ los CRC cuadran                          ✅ todo cuelga de una raíz única
✅ ninguna ruta se escapa                   ✅ ningún symlink
✅ nada de basura de Mirag ni secretos      ✅ no falta ningún archivo del manifiesto
✅ no sobra ningún archivo                  ✅ se puede extraer
✅ los hashes del ZIP == los del artefacto  ✅ ningún secreto en el contenido
✅ el manifiesto embebido coincide
```

El re-hash extrae de verdad a un temporal con `extractall`, no `z.read()`: es lo que hará
el usuario, y es donde aparecen los fallos de ruta.

## El gate caza

Un gate que nunca ha rechazado nada es decoración. Estos siete ataques se ejecutan en
`test_empaquetado.py`, manipulando el ZIP a mano:

| manipulación | qué comprobación la rechaza |
|---|---|
| un archivo con el contenido cambiado | los hashes del ZIP == los del artefacto |
| un archivo de más | no sobra ningún archivo |
| un archivo de menos | no falta ningún archivo del manifiesto |
| un `.env` colado dentro | nada de basura de Mirag ni secretos por nombre |
| un `__pycache__` colado | ídem |
| una ruta `../` que se escapa | ninguna ruta se escapa |
| un ZIP truncado / un byte cambiado | se reabre / los CRC cuadran |

Y el ZIP intacto sigue pasando.

## Determinismo, sin prometer de más

Mismo árbol y mismo intérprete dan los mismos bytes: `ZipInfo(date_time` fijo`)`, orden
alfabético, `create_system` fijo. Entre versiones de zlib eso **no está garantizado**, así
que lo que se afirma y se testea es la propiedad fuerte: **el conjunto de (nombre, CRC-32,
tamaño) es siempre el mismo**. Decir "reproducible byte a byte en cualquier máquina" sería
otra afirmación sin respaldo.

## El endpoint

`GET /descarga?id=<24 hex>`, añadido a una lista blanca que sigue siendo literal.

**La propiedad que no se puede relajar: el id nunca se concatena a un `Path`.** Se valida
contra una regex, se busca en un diccionario en memoria, y el artefacto trae su propia
carpeta. Si alguien escribe algún día `CARPETA / ident`, vuelve entero el agujero que la
lista blanca cerró.

| situación | respuesta |
|---|---|
| id mal formado | `400`, sin ecoar lo recibido |
| id desconocido o caducado | `410` |
| existe pero no pasó el gate | `409 ARTIFACT INTEGRITY ERROR` |
| todo bien | `200` + `X-Mirag-Sha256` para verificar la entrega desde fuera |

`HEAD /descarga` → `404`: HEAD no descarga.

## Un agujero vivo que apareció al tocar esto

Al añadir la segunda ruta apareció que **`do_HEAD` nunca se había cerrado**:

```
GET  /.env  → 404          HEAD /.env  → 200 · Content-Length: 93 · Last-Modified
GET  /server.py → 404      HEAD /server.py → 200
GET  /trazas_noche.jsonl → 404   HEAD /trazas_noche.jsonl → 200
```

`do_GET` estaba sobreescrito; `do_HEAD` seguía siendo el de `SimpleHTTPRequestHandler`,
que pasa por `translate_path()` y responde sobre el directorio entero. No filtraba el
cuerpo, pero sí **que el archivo existe, cuánto mide y cuándo se tocó** — justo lo que la
lista blanca dejó de decir. Y el docstring afirmaba *"Una sola ruta. Ni una más."*

**Sobrevivió a toda la auditoría porque los 15 tests de seguridad preguntaban con GET.**
Una prueba que solo usa un método solo demuestra ese método. Cerrado, con dos tests: uno
que recorre las rutas con los dos verbos, y otro que exige que GET y HEAD compartan la
misma lista.

## Aislamiento entre proyectos

Un id opaco (`secrets.token_hex(12)`, 96 bits) y una carpeta por artefacto. Nada de
"artefacto actual" a nivel de módulo, y `salida/` queda fuera de esto por completo —
`rapido.guardar` la vacía entera en cada petición, así que un botón que apuntara ahí
entregaría el proyecto de la otra pestaña.

Probado en `test_empaquetado.py`:

- **A, luego B, luego descargar A**: el ZIP de A llega íntegro con su sha anunciado.
- **Descargas concurrentes**: dos hilos bajando A y B a la vez, cada uno recibe el suyo.
- **20 hilos registrando a la vez**: 20 ids únicos, ninguno perdido.
- **Registrar uno nuevo no borra los anteriores** — es exactamente lo que hace
  `rapido.guardar`, y por eso no se usa aquí.

Un límite que se dice en voz alta: **la generación concurrente offline no se puede probar
hoy**, porque `dobles.usar` sustituye el global `agent.llm` y dos generaciones simultáneas
se roban el guion. Así que el test prueba lo que de verdad ocurre —la entrega concurrente—
y su docstring dice exactamente qué demuestra y qué no. Un test que *parece* probar
generación concurrente y en realidad la serializa sería la clase de mentira que esta suite
existe para no cometer.

## Una fuga que apareció al limpiar

Tras la sesión de desarrollo había **33 carpetas de artefactos huérfanas en disco**
(1,8 MB). El registro vive en memoria y muere con el proceso, así que `_caducar` nunca
alcanza las carpetas de ejecuciones anteriores: se acumulan para siempre.

`barrer_huerfanos()` corre al importar el módulo y borra lo que tiene **forma de
artefacto** (un id de 24 hex) y más de 24 h, saltándose lo vivo de este proceso. Tres
tests lo fijan, y el del medio es el que importa: **no toca lo que no es suyo**. Barrer
con un `iterdir()` a lo bruto es exactamente lo que hace `rapido.guardar` con `salida/`,
y es lo que se lleva por delante lo ajeno.

## Lo que ve el usuario sale del manifiesto

El árbol de la página se construye **desde `manifiesto.archivos`**, nunca reconstruido. El
estado sale del certificado. El botón usa `p.descarga` tal cual viene del backend: la
página **no compone la URL**, así que un fallo de integridad no puede acabar en un botón
que funciona por accidente. Cuando la integridad falla, `descarga` es `null` y no hay de
dónde sacar un enlace.

Hay un test que ejecuta `seccionProyecto` de verdad en node con tres fixtures —verificado,
parcial, integridad rota— y comprueba sobre el HTML producido que `VERIFICADO` solo
aparece en el primero y que el tercero no trae botón.

## Y se puede ver fallar

```bash
python3 demo_proyecto.py --romper hash      # un archivo cambiado
python3 demo_proyecto.py --romper entrada   # un archivo de más
python3 demo_proyecto.py --romper zip       # un ZIP truncado
```

Los tres enseñan la comprobación que falla, con su motivo real, y terminan en *"No hay
descarga"*. Un camino de fallo que nunca se ha visto en pantalla es un camino de fallo que
no existe.

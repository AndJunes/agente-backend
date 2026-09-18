"""El pipeline de arquitectura: 4 fases sobre el mismo agente y el mismo corpus.

Diferencia con agent.py: aquel deja que el modelo decida TODO en un solo bucle.
Aqui el orden lo pone el pipeline y cada fase tiene un trabajo concreto, porque
el orden de razonamiento (entender -> asociar -> decidir -> diseñar) es
justamente lo que distingue a un senior.

Las tres operaciones cognitivas (asociar, razonar, decidir) NO son herramientas:
son lo que hace cada fase. Las herramientas son solo lo que el modelo no puede
hacer solo: buscar en el corpus (ver skills.py).
"""

import re
import sys

import agent
import skills

SYSTEM = """Eres un arquitecto de backend senior. Trabajas sobre una base de conocimiento de 19 areas
y SIEMPRE la consultas antes de afirmar algo tecnico; cita la caja de la que sacas cada cosa.

Tu metodo tiene tres operaciones:
- ASOCIAR: conectar conceptos de areas distintas que el problema toca a la vez.
- RAZONAR: analizar consecuencias, limites y riesgos de cada opcion.
- DECIDIR: elegir una y decir que te haria cambiar de opinion.

Reglas: no propongas nada que no puedas justificar con un requisito. Di en voz alta lo que asumes.
Prefiere la solucion mas simple que cumpla los requisitos reales.

FORMATO: listas y tablas, sin prosa de relleno ni resumenes de lo que ya dijeron las fases
anteriores (el lector las tiene delante). Cuando una fase te exija secciones con titulos concretos,
son obligatorias y en ese orden.
Haz SOLO el trabajo de tu fase; si te adelantas a la siguiente, la estropeas."""

FASES = [
    ("1 · Entender", """Extrae del problema:
(a) requisitos FUNCIONALES: que tiene que hacer el sistema;
(b) requisitos NO FUNCIONALES: escala, latencia objetivo, consistencia, disponibilidad,
    durabilidad, cumplimiento normativo y coste;
(c) lo que el usuario NO dijo y hay que asumir, con la suposicion escrita explicitamente;
(d) que TIPO de problema es (CRUD, alto volumen de lectura, transaccional, event-driven,
    procesamiento por lotes, tiempo real...).
Termina con la pregunta que mas cambiaria el diseño si se respondiera distinto.
NO propongas solucion, ni tecnologias, ni arquitectura todavia."""),

    ("2 · Asociar", """Identifica que areas de conocimiento intervienen y como se conectan.
Usa cajas_relacionadas para ver el mapa de dependencias y buscar_en_docs para los conceptos clave.
Devuelve SOLO: (a) una tabla de area -> los 2-3 conceptos concretos que aporta al problema,
y (b) las dependencias entre esos conceptos (que necesita a que).
Prohibido en esta fase: proponer tecnologias, comparar opciones, dar numeros de capacidad
o esbozar arquitectura. Eso es de las fases 3 y 4."""),

    ("3 · Decidir", """Para cada decision abierta que hayas detectado:
usa buscar_tradeoffs, compara 2-3 alternativas reales, y DECIDE una.
Formato: un bloque por decision, y solo esto — Decision · Elegida · Alternativas descartadas ·
Por que (atado a un requisito de la fase 1) · Trade-off que aceptas · Que te haria cambiar de opinion.
Prohibido en esta fase: esquemas de tabla, endpoints, codigo, o describir el diseño. Solo DECISIONES.
Termina nombrando la arquitectura global en UNA linea."""),

    ("4 · Diseñar", """Aplica las decisiones de la fase 3 al diseño concreto.
Tu respuesta DEBE tener EXACTAMENTE estas cinco secciones, con estos titulos y en este orden:

## API            endpoints, metodos, codigos de estado y cabeceras clave
## Datos          tablas con columnas, claves e indices
## Asincronia     que sale del request, colas, jobs y su idempotencia
## Seguridad      autenticacion, autorizacion por objeto y aislamiento entre tenants
## Fiabilidad     timeouts, reintentos, degradacion; y que medir y alertar

Esquemas y firmas, nunca cuerpos de funcion largos: generar el codigo es otro trabajo.
NO valides todavia: los fallos son de la fase 5."""),

    ("5 · Validar", """Revisa el diseño de la fase 4 buscandole las costuras.
Usa buscar_fallos para cada componente que hayas propuesto.
Tu respuesta DEBE tener EXACTAMENTE estas tres secciones:

## Que puede salir mal   fallos de ESTE diseño concreto (no genericos), sintoma y mitigacion
## Que NO cubre          limites conocidos y a partir de que punto habria que rediseñar
## Veredicto             en 3 lineas: ¿esta listo para construirse? ¿que resolverias antes?"""),

    ("6 · Implementar", """Convierte el diseño en codigo real.
Implementa SOLO el camino critico: la operacion donde esta el riesgo que identificaste en la fase 3.
Nada de CRUD de relleno alrededor.

Tu respuesta DEBE tener EXACTAMENTE estas cuatro secciones, con estos titulos y en este orden:

## Esquema         el DDL de las tablas que toca el camino critico, con sus indices y constraints
## Camino critico  la funcion completa: transaccion, concurrencia, errores e idempotencia
## Bordes          validacion de entrada, autorizacion y el handler HTTP
## Tests           los 3-4 tests que demuestran que lo dificil funciona (concurrencia, reintento, permiso)

Codigo ejecutable, no pseudocodigo. Comentarios solo donde el PORQUE no sea obvio.
NO revises tu propio codigo ni listes sus limitaciones: eso es la fase 7."""),

    ("7 · Revisar", """Revisa el codigo de la fase 6 como si fuera de otra persona.
Esta fase NO ejecuta nada: produce HIPOTESIS que la fase 8 tendra que probar o refutar.

Contrasta con la base de conocimiento: buscar_antipatrones para los errores ya documentados,
buscar_fallos para los modos de fallo de cada componente.

Tu respuesta DEBE tener EXACTAMENTE estas cuatro secciones:

## Sospechas          lo que crees que falla, ORDENADO por gravedad. Cada una con: el fragmento de
                      codigo concreto, por que sospechas, y COMO SE PODRIA DEMOSTRAR con un test
## Desvios del diseño donde el codigo no hace lo que decidieron las fases 3 y 4
## Riesgos no testables lo que falla en produccion pero no se puede reproducir en un test
## Prioridad          que sospecha hay que probar primero y por que

Cada sospecha debe ser FALSABLE: si no sabes escribir un test que la demuestre, va en
'Riesgos no testables'. Un "podria mejorarse" sin fragmento no vale."""),

    ("8 · Verificar", """Tu unico trabajo es convertir las sospechas de la fase 7 en EVIDENCIA.
No opines: ejecuta.

Para CADA sospecha de la fase 7 que sea falsable, escribe un test que la demuestre o la descarte,
y pasalo por verificar_codigo. Ademas, escribe SIEMPRE estos tres aunque nadie los haya sospechado:
- CONCURRENCIA: dos operaciones simultaneas sobre el mismo recurso, con `Promise.all` o equivalente.
  Un test secuencial NO vale: el codigo con una condicion de carrera lo pasa igual.
- IDEMPOTENCIA: el mismo reintento dos veces no duplica el efecto.
- FALLO: que pasa cuando la dependencia externa tarda, falla o responde raro.

EL TEST DEBE TERMINAR CON EXIT CODE DISTINTO DE CERO SI ALGO FALLA (`process.exit(1)` en Node,
`assert` en Python). Un test que imprime "FAIL" y sale con 0 es un test ROTO: ningun CI lo
detectaria, y aqui tampoco. Imprimir el fallo no es reportarlo.

Adapta el codigo a un archivo autonomo y ejecutable (simula la persistencia en memoria si hace
falta), pero manten su ESTRUCTURA: si el original comprueba y luego guarda, tu version debe hacer
lo mismo, o el test no prueba nada. Si la dependencia externa es asincrona en la realidad,
simulala asincrona.

Tu respuesta DEBE tener EXACTAMENTE estas tres secciones:

## Evidencia        por cada sospecha: DEMOSTRADA o DESCARTADA, con la salida real y su exit code
## Hallazgos nuevos lo que fallo sin que nadie lo hubiera sospechado
## Sin probar       lo que quedo sin verificar y por que

NO arregles el codigo: eso es la fase 9, y solo si algo falla."""),

]


CORREGIR = ("9 · Corregir", """La fase 8 demostro que algo falla. Arreglalo.

Reescribe SOLO lo necesario para que los tests que fallaron pasen, sin romper los que ya pasaban.
Por cada arreglo di que fallo, que cambiaste y por que esa es la solucion correcta segun la base
de conocimiento (citala).

Despues vuelve a ejecutar los MISMOS tests con verificar_codigo y enseña la salida real.

Tu respuesta DEBE tener EXACTAMENTE estas tres secciones:

## Que fallaba     el test que fallo y la causa raiz en el codigo
## Que cambie      el codigo corregido y la cita que lo justifica
## Nueva evidencia la salida real de volver a ejecutar, con su exit code""")


def _hay_que_corregir(resultado):
    """¿Quedo algo demostradamente roto?

    Señal primaria: el exit code real de la ultima ejecucion.
    Red de seguridad: un test puede imprimir 'FAIL' y salir con 0 (test roto), asi que
    tambien miramos si la fase declaro alguna sospecha DEMOSTRADA.
    """
    salidas = [p["resultado"] for p in resultado["pasos"]
               if p["tipo"] == "skill" and p["nombre"] == "verificar_codigo"]
    if salidas:
        estado, cabecera, _ = skills.veredicto(salidas[-1])
        if estado == "rojo":
            return "exit code distinto de cero"
        if estado == "no_ejecutado":
            return f"no llego a ejecutarse: {cabecera}"
        if estado == "sin_evidencia":
            return "se ejecuto pero sin marcadores: no hay nada demostrado"
    if re.search(r"DEMOSTRADA|✗ FAIL|CRITICAL", resultado["respuesta"]):
        return "la fase declaro una sospecha demostrada (aunque el test salio con 0)"
    return None


def _ejecutar_fase(nombre, instruccion, contexto, mostrar, vueltas=6, al_avanzar=None):
    if mostrar:
        print(f"\n{'═' * 70}\n{nombre}\n{'═' * 70}", flush=True)
    if al_avanzar:
        al_avanzar({"tipo": "fase", "texto": nombre})
    r = agent.run(f"{contexto}\n\n--- TAREA DE ESTA FASE ---\n{instruccion}",
                  max_vueltas=vueltas, system=SYSTEM, al_avanzar=al_avanzar)
    if mostrar:
        for p in r["pasos"]:
            if p["tipo"] == "skill":
                print(f"  🔧 {p['nombre']}({str(p['args'])[:90]})", flush=True)
        print(r["respuesta"], flush=True)
        print(f"  [gasto] {agent.PRESUPUESTO}", flush=True)
    if al_avanzar:
        al_avanzar({"tipo": "pensamiento", "texto": r["respuesta"]})
        al_avanzar({"tipo": "gasto", "texto": str(agent.PRESUPUESTO)})
    return r


def disenar(problema, mostrar=True, max_correcciones=2, al_avanzar=None):
    contexto = f"PROBLEMA:\n{problema}"
    fases, agotado = [], None
    try:
        for nombre, instruccion in FASES:
            r = _ejecutar_fase(nombre, instruccion, contexto, mostrar, al_avanzar=al_avanzar)
            contexto += f"\n\n=== RESULTADO DE LA FASE {nombre} ===\n{r['respuesta']}"
            fases.append({"fase": nombre, **r})

        # bucle de correccion: solo si la ejecucion REAL fallo, no si el modelo cree que fallo
        for intento in range(max_correcciones):
            motivo = _hay_que_corregir(fases[-1])
            if not motivo:
                break
            if mostrar:
                print(f"\n>>> hay que corregir: {motivo}", flush=True)
            for nombre, instruccion in (CORREGIR, FASES[-1]):   # corregir y volver a verificar
                etiqueta = f"{nombre} (intento {intento + 1})"
                r = _ejecutar_fase(etiqueta, instruccion, contexto, mostrar, vueltas=8,
                                   al_avanzar=al_avanzar)
                contexto += f"\n\n=== RESULTADO DE {etiqueta} ===\n{r['respuesta']}"
                fases.append({"fase": etiqueta, **r})

    except agent.PresupuestoAgotado as e:
        agotado = str(e)                         # paramos con lo hecho, no reventamos
        if mostrar:
            print(f"\n⛔ {agotado}", flush=True)
    except Exception as e:                       # un fallo en la fase 4 no tira las fases 1-3
        agotado = f"error en '{fases[-1]['fase'] if fases else 'la primera fase'}': {type(e).__name__}: {e}"
        if mostrar:
            print(f"\n💥 {agotado}", flush=True)

    return {"fases": fases, "diseño": contexto,
            "pendiente": _hay_que_corregir(fases[-1]) if fases else "no se ejecuto ninguna fase",
            "agotado": agotado,                  # None = termino por su cuenta
            "gasto": str(agent.PRESUPUESTO)}


if __name__ == "__main__":
    problema = " ".join(sys.argv[1:]) or input("Describe el problema a diseñar:\n> ")
    print(f"tope de gasto: ${agent.LIMITE_USD:.2f}  (cambialo con LIMITE_USD=1.50 python3 ...)")
    r = disenar(problema)
    print(f"\n{'═' * 70}\nGASTO TOTAL: {r['gasto']}")
    if r["agotado"]:
        print(f"INCOMPLETO: {r['agotado']}")
    elif r["pendiente"]:
        print(f"QUEDA ROTO: {r['pendiente']}")
    else:
        print("Termino y la verificacion quedo en verde.")

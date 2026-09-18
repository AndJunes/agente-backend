"""La cadena que convierte un proyecto generado en un proyecto con evidencia.

    GENERADO -> VALIDADO -> EJECUTADO -> PROBADO -> VERIFICADO
                                                 \\-> PARCIAL
                                                 \\-> FALLIDO

EL UNICO SITIO QUE DECIDE EL ESTADO

    `derivar_estado()` es la unica funcion del proyecto que devuelve estos literales, y
    no recibe nada del modelo: recibe fases, marcadores y hallazgos. Es deliberado.
    `skills.veredicto` existe porque el "verde" estaba re-derivado en ocho sitios y un
    TIMEOUT era "error" en una linea y "verde" catorce mas abajo. No se repite.

LA DISTINCION QUE LO SOSTIENE TODO

    Una dependencia externa ausente NO hunde el estado: le pone un TECHO. Un proyecto
    FastAPI bien escrito se queda en VALIDADO y dice por que, en vez de llamarse FALLIDO.
    Un import interno roto si es un error, y se repara.
"""

import time
from typing import NamedTuple

import dependencias
import proyecto as P
import rapido
import skills
import sondas
from skills import SKILLS

GENERADO, VALIDADO, EJECUTADO = "GENERADO", "VALIDADO", "EJECUTADO"
PROBADO, VERIFICADO = "PROBADO", "VERIFICADO"
PARCIAL, FALLIDO = "PARCIAL", "FALLIDO"

MAXIMAS_REPARACIONES = 2       # el archivo suelto permite 1; un proyecto tiene mas superficie


class Fase(NamedTuple):
    nombre: str
    estado: str                 # ok | fallo | limitado | omitido
    detalle: str
    ms: float = 0.0
    salida: str = ""            # la salida CRUDA cuando ejecuto algo


class Certificado(NamedTuple):
    estado: str
    por_que: str
    fases: tuple
    hallazgos: tuple
    marcas: dict
    evidencia: tuple = ()
    reparaciones: tuple = ()
    interprete: str = ""

    @property
    def ok(self):
        return self.estado == VERIFICADO

    def resumen(self):
        pasan = sum(1 for v in self.marcas.values() if v == "PASS")
        return f"{self.estado} · {pasan}/{len(self.marcas)} marcadores · {self.por_que}"


def _entrypoint(proy):
    """El modulo que expone `crear_servidor`. Se busca en el codigo, no se supone."""
    for archivo in proy.listar():
        if archivo.ruta.endswith(".py") and "def crear_servidor" in archivo.texto:
            return archivo.modulo
    return ""


def validar_estructura(proy):
    """Lo que tiene que existir para que lo demas signifique algo."""
    problemas = []
    if not proy.listar():
        problemas.append("el proyecto no tiene archivos")
    if not any(a.ruta.startswith("tests/") or "test" in a.ruta.split("/")[-1]
               for a in proy.listar()):
        problemas.append("no hay ningun archivo de tests")
    codigo = [a for a in proy.listar() if a.ruta.endswith((".py", ".js"))]
    if not codigo:
        problemas.append("no hay ningun archivo de codigo")
    # paquetes de Python sin __init__.py: funciona ejecutando desde la raiz y falla fuera
    paquetes = {"/".join(a.ruta.split("/")[:-1]) for a in proy.listar()
                if a.ruta.endswith(".py") and "/" in a.ruta}
    for paquete in sorted(paquetes):
        if paquete.startswith("tests"):
            continue
        if not proy.obtener(f"{paquete}/__init__.py"):
            problemas.append(f"{paquete}/ no tiene __init__.py")
    return problemas


def certificar(proy, comando_test=None, al_avanzar=None, reparador=None):
    """Recorre la cadena entera y devuelve un `Certificado`. No llama al modelo salvo
    que se le pase un `reparador`, y aun asi como mucho `MAXIMAS_REPARACIONES` veces."""
    fases, reparaciones = [], []
    reloj = time.perf_counter

    def anota(fase):
        fases.append(fase)
        if al_avanzar:
            al_avanzar(fase)
        return fase

    # ── 1. estructura ───────────────────────────────────────────────────────
    t = reloj()
    problemas = validar_estructura(proy)
    anota(Fase("estructura", "fallo" if problemas else "ok",
               "; ".join(problemas) or f"{proy.totales['archivos']} archivos, "
               f"{proy.totales['directorios']} directorios",
               (reloj() - t) * 1000))
    if problemas:
        return Certificado(FALLIDO, f"estructura incompleta: {problemas[0]}",
                           tuple(fases), (), {})

    # ── 2. sintaxis ─────────────────────────────────────────────────────────
    t = reloj()
    error = rapido._comprobar_sintaxis(proy.planos())
    anota(Fase("sintaxis", "fallo" if error else "ok",
               error or "todos los archivos compilan", (reloj() - t) * 1000))
    if error:
        return Certificado(FALLIDO, f"no compila: {error[:120]}", tuple(fases), (), {})

    # ── 3. imports y dependencias ───────────────────────────────────────────
    t = reloj()
    _imports, hallazgos = dependencias.analizar(proy)
    errores = [h for h in hallazgos if h.gravedad == dependencias.ERROR]
    limites = [h for h in hallazgos if h.gravedad == dependencias.LIMITE]
    anota(Fase("importaciones", "fallo" if errores else ("limitado" if limites else "ok"),
               (f"{len(errores)} imports rotos" if errores else
                f"{len(limites)} dependencias no instaladas aqui" if limites else
                "el grafo de imports resuelve entero"),
               (reloj() - t) * 1000))

    if errores and reparador:
        for intento in range(1, MAXIMAS_REPARACIONES + 1):
            t = reloj()
            nuevo, cambiados, causa = reparador(proy, errores, "", intento)
            reparaciones.append({"intento": intento, "archivos": list(cambiados),
                                 "causa": causa, "motivo": "imports"})
            anota(Fase(f"reparacion:{intento}", "ok" if cambiados else "fallo",
                       f"{len(cambiados)} archivos tocados por imports rotos",
                       (reloj() - t) * 1000))
            if not cambiados:
                break
            proy = nuevo
            _imports, hallazgos = dependencias.analizar(proy)
            errores = [h for h in hallazgos if h.gravedad == dependencias.ERROR]
            limites = [h for h in hallazgos if h.gravedad == dependencias.LIMITE]
            if not errores:
                break

    if errores:
        return Certificado(FALLIDO,
                           f"quedan {len(errores)} imports rotos: {errores[0].detalle}",
                           tuple(fases), tuple(hallazgos), {},
                           reparaciones=tuple(reparaciones))

    # Con una dependencia externa ausente no se puede ejecutar nada, y eso NO es un fallo
    # del proyecto. Es un techo: VALIDADO, diciendo exactamente por que.
    if limites:
        faltan = sorted({h.detalle.split("'")[1] for h in hallazgos
                         if h.clase == "dependencia_ausente"})
        anota(Fase("ejecucion", "limitado",
                   f"no se ejecuta aqui: falta {', '.join(faltan)}"))
        return Certificado(
            VALIDADO,
            f"el codigo compila y su grafo de imports resuelve, pero no se pudo ejecutar: "
            f"{', '.join(faltan)} no esta instalado en esta maquina. El proyecto puede "
            f"estar bien; aqui no hay evidencia de que lo este.",
            tuple(fases), tuple(hallazgos), {}, reparaciones=tuple(reparaciones),
            interprete=_binario())

    # Las secciones 4 y 5 son las UNICAS que ejecutan el proyecto. Si la ejecucion esta
    # apagada no se anota ninguna de sus fases, y eso es deliberado, no pereza:
    # `derivar_estado` devuelve EJECUTADO en cuanto EXISTE una fase llamada "tests", con
    # el motivo "el comando de tests corrio y no imprimio un solo marcador". Con la
    # ejecucion apagada eso seria falso — no corrio nada. Sin esas fases cae en GENERADO,
    # "hay archivos y nada se ha llegado a ejecutar", que es justo lo que ha pasado.
    #
    # Lo de arriba (estructura, sintaxis con ast, imports) NO se toca: es analisis
    # estatico, no ejecuta nada, y sigue siendo lo que caza los fallos de verdad.
    impedimento = skills.impedimento_de_ejecucion()
    marcas, ids_crud = {}, ()
    if impedimento:
        anota(Fase("ejecucion", "omitido", impedimento.split(". ")[0], 0.0))
    else:
        # ── 4. tests del proyecto ───────────────────────────────────────────────
        # SIEMPRE por la sonda. Si se usara el comando del proyecto a secas, `unittest` no
        # imprime marcadores y la fase sale "SIN EVIDENCIA" — y ese silencio quedaba tapado
        # por los marcadores del CRUD, dando un VERIFICADO falso. La sonda emite uno por
        # test, asi que la evidencia no depende de que al modelo se le ocurra imprimirla.
        t = reloj()
        extra = sondas.tests("tests")
        salida_tests = SKILLS["verificar_codigo"]({**proy.planos(), **extra},
                                                  "python3 _sonda_tests.py")
        ejec = skills.resultado_de(salida_tests)
        anota(Fase("tests", {"verde": "ok", "rojo": "fallo"}.get(ejec.estado, "limitado"),
                   ejec.cabecera, (reloj() - t) * 1000, salida_tests))
        marcas = dict(ejec.marcas)

        # Y aparte, el comando que el README le dice al usuario que ejecute. Si ese falla,
        # da igual que la sonda vaya bien: lo que el usuario escriba no le va a funcionar.
        if comando_test:
            t = reloj()
            salida_doc = SKILLS["verificar_codigo"](proy.planos(), comando_test)
            doc = skills.resultado_de(salida_doc)
            # Aqui NO se piden marcadores: un `unittest` normal no los imprime y no tiene por
            # que. Lo que se comprueba es que el comando del README funcione, porque es el
            # que va a escribir quien descomprima el ZIP.
            roto = doc.estado in ("rojo", "no_ejecutado")
            anota(Fase("comando documentado", "fallo" if roto else "ok",
                       (f"`{comando_test}` falla: {doc.cabecera}" if roto
                        else f"`{comando_test}` corre sin errores"),
                       (reloj() - t) * 1000, salida_doc))

        if ejec.estado == "rojo" and reparador:
            for intento in range(len(reparaciones) + 1, MAXIMAS_REPARACIONES + 1):
                t = reloj()
                nuevo, cambiados, causa = reparador(proy, [], salida_tests, intento)
                reparaciones.append({"intento": intento, "archivos": list(cambiados),
                                     "causa": causa, "motivo": "tests en rojo"})
                anota(Fase(f"reparacion:{intento}", "ok" if cambiados else "fallo",
                           f"{len(cambiados)} archivos tocados por tests en rojo",
                           (reloj() - t) * 1000))
                if not cambiados:
                    break
                proy = nuevo
                salida_tests = SKILLS["verificar_codigo"]({**proy.planos(), **extra},
                                                          "python3 _sonda_tests.py")
                ejec = skills.resultado_de(salida_tests)
                anota(Fase("tests (tras arreglo)",
                           {"verde": "ok", "rojo": "fallo"}.get(ejec.estado, "limitado"),
                           ejec.cabecera, 0.0, salida_tests))
                marcas = dict(ejec.marcas)
                if ejec.estado == "verde":
                    break

        # ── 5. CRUD real, si el proyecto expone el contrato ─────────────────────
        entrypoint = _entrypoint(proy)
        ids_crud = ()
        if entrypoint:
            t = reloj()
            marca = sondas.nonce()
            ids_crud = sondas.ids_crud(marca)
            salida_crud = SKILLS["verificar_codigo"](
                {**proy.planos(), **sondas.crud(entrypoint, marca)}, "python3 _sonda_crud.py")
            crud = skills.resultado_de(salida_crud)
            anota(Fase("crud", {"verde": "ok", "rojo": "fallo"}.get(crud.estado, "limitado"),
                       crud.cabecera, (reloj() - t) * 1000, salida_crud))
            marcas.update(crud.marcas)
        else:
            anota(Fase("crud", "omitido",
                       "el proyecto no expone crear_servidor(): no hay API que ejercitar"))

    evidencia = rapido._evidencia(
        [{"riesgo": f"la operacion {i.split('_')[1]} no funciona de verdad",
          "propiedad": f"{i.split('_')[1]} responde por HTTP", "test_id": i}
         for i in ids_crud],
        "\n".join(f"TEST:{k}:{v}" for k, v in marcas.items()), ejecutado=bool(marcas))

    estado, por_que = derivar_estado(tuple(fases), marcas, tuple(hallazgos), ids_crud)
    return Certificado(estado, por_que, tuple(fases), tuple(hallazgos), marcas,
                       tuple(evidencia), tuple(reparaciones), _binario())


def _binario():
    import shutil
    return shutil.which("python3") or ""


def derivar_estado(fases, marcas, hallazgos, ids_crud=()):
    """El ESTADO, derivado solo de lo observado. El unico sitio que lo decide.

    Se lee de arriba abajo: la primera condicion que se cumple manda.
    """
    por_nombre = {f.nombre.split(":")[0]: f for f in fases}
    errores = [h for h in hallazgos if h.gravedad == dependencias.ERROR]
    limites = [h for h in hallazgos if h.gravedad == dependencias.LIMITE]
    pasan = [k for k, v in marcas.items() if v == "PASS"]
    fallan = [k for k, v in marcas.items() if v == "FAIL"]

    if por_nombre.get("estructura", Fase("", "ok", "")).estado == "fallo":
        return FALLIDO, "la estructura del proyecto esta incompleta"
    if por_nombre.get("sintaxis", Fase("", "ok", "")).estado == "fallo":
        return FALLIDO, "hay archivos que no compilan"
    if errores:
        return FALLIDO, f"quedan {len(errores)} imports internos rotos"
    if not marcas:
        if limites:
            return VALIDADO, "compila y resuelve, pero aqui falta una dependencia externa"
        if por_nombre.get("tests"):
            return EJECUTADO, ("el comando de tests corrio y no imprimio un solo marcador: "
                               "eso no es aprobar, es que nadie sabe que se probo")
        return GENERADO, "hay archivos y nada se ha llegado a ejecutar"
    if fallan:
        return (PARCIAL if pasan else FALLIDO), \
            f"{len(fallan)} de {len(marcas)} marcadores en FAIL"
    if ids_crud and not set(ids_crud) <= set(marcas):
        faltan = sorted(set(ids_crud) - set(marcas))
        return PARCIAL, (f"los tests pasan, pero el CRUD no se pudo ejercitar entero: "
                         f"faltan {len(faltan)} operaciones")
    if limites:
        return PARCIAL, "lo ejecutable pasa; parte del proyecto no se puede probar aqui"
    if not pasan:
        return EJECUTADO, "no hubo ni un marcador en PASS"
    # Una fase que CORRIO y no produjo evidencia no puede quedar tapada por otra que si.
    # Paso: los 9 tests del proyecto salieron "SIN EVIDENCIA" y los 7 marcadores del CRUD
    # arrastraron el estado a VERIFICADO. Eso es exactamente lo que no puede ocurrir.
    mudas = [f.nombre for f in fases
             if f.estado == "limitado" and f.nombre in ("tests", "crud")]
    if mudas:
        return PARCIAL, (f"la fase '{mudas[0]}' se ejecuto y no produjo ni un marcador: "
                         f"no hay forma de saber que probo")
    rotas = [f.nombre for f in fases if f.estado == "fallo"]
    if rotas:
        return PARCIAL, f"la fase '{rotas[0]}' fallo"
    return VERIFICADO, (f"los {len(pasan)} marcadores pasan"
                        + (f", incluido el CRUD completo por HTTP" if ids_crud else ""))


if __name__ == "__main__":
    print("estados posibles:", GENERADO, VALIDADO, EJECUTADO, PROBADO, VERIFICADO,
          PARCIAL, FALLIDO)
    casos = [
        ("todo verde con CRUD", (Fase("estructura", "ok", ""), Fase("sintaxis", "ok", ""),
                                 Fase("tests", "ok", "")),
         {"a": "PASS", "crud_crear_x": "PASS"}, (), ("crud_crear_x",)),
        ("un marcador en FAIL", (Fase("estructura", "ok", ""), Fase("sintaxis", "ok", ""),
                                 Fase("tests", "fallo", "")),
         {"a": "PASS", "b": "FAIL"}, (), ()),
        ("exit 0 sin marcadores", (Fase("estructura", "ok", ""), Fase("sintaxis", "ok", ""),
                                   Fase("tests", "limitado", "")), {}, (), ()),
        ("falta fastapi", (Fase("estructura", "ok", ""), Fase("sintaxis", "ok", "")), {},
         (dependencias.Hallazgo("dependencia_ausente", dependencias.LIMITE, "a.py", 1,
                                "'fastapi' no esta instalado"),), ()),
        ("import roto", (Fase("estructura", "ok", ""), Fase("sintaxis", "ok", "")), {},
         (dependencias.Hallazgo("import_interno_roto", dependencias.ERROR, "a.py", 1, "x"),), ()),
    ]
    print()
    for nombre, fases, marcas, hallazgos, ids in casos:
        estado, por_que = derivar_estado(fases, marcas, hallazgos, ids)
        print(f"  {estado:<10} {nombre:<24} {por_que[:64]}")

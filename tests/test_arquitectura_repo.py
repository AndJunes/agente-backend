"""La dirección de dependencias, comprobada en vez de prometida.

    producción  ←  tests · demos · benchmarks · experimental

Producción no puede conocer sus tests, sus demos ni sus bancos. Si algún día alguien
importa un fixture desde el pipeline, esto se pone rojo el mismo día y no seis meses
después, cuando ya no se sabe por qué está ahí.

    python3 tests/test_arquitectura_repo.py
"""

import sys as _sys
from pathlib import Path as _Path
_RAIZ_REPO = _Path(__file__).resolve().parent.parent
# La raiz (produccion) y las dos carpetas cuyos modulos se importan por nombre desnudo:
# `test_cache` importa `cache` (experimental/) y `test_plan` importa `eval` (benchmarks/).
for _d in (_RAIZ_REPO, _RAIZ_REPO / "experimental", _RAIZ_REPO / "benchmarks"):
    _sys.path.insert(0, str(_d))

import ast
import sys
from pathlib import Path

RAIZ = _RAIZ_REPO
CARPETAS = ("tests", "demos", "benchmarks", "experimental")
# `blockchain/` es un PAQUETE (carpeta con __init__.py), no archivos sueltos. Se lista
# aparte porque `_de()` hace glob de un nivel y no lo veria; y porque es la unica carpeta
# del repo con dependencias externas, cosa que un test de aqui abajo comprueba.
PAQUETES = ("blockchain",)
casos = []

# La única inversión permitida, y por qué. Si crece, este test lo enseña.
EXCEPCIONES = {
    ("server", "demos"): "el modo offline (por defecto) elige el guion de la demo",
    ("server", "dobles"): "el modo offline sustituye agent.llm por un doble",
    ("dobles", "fixture_proyecto"): "el guion del proyecto necesita su codigo",
    ("pipeline", "dobles"): "solo bajo __main__, para el self-test del modulo",
    ("server", "blockchain"): "la ruta /api/blockchain/agent, con import PEREZOSO dentro "
                              "del handler: sin el paquete el servidor arranca igual",
}


def probar(nombre, fn):
    try:
        fn(); casos.append((True, nombre, ""))
    except AssertionError as e:
        casos.append((False, nombre, str(e) or "assert"))
    except Exception as e:
        casos.append((False, nombre, f"{type(e).__name__}: {e}"))


def _importa(archivo, nombres_locales):
    """Los módulos locales que importa, incluidos los imports dentro de funciones."""
    try:
        arbol = ast.parse(archivo.read_text())
    except SyntaxError:
        return set()
    salida = set()
    for nodo in ast.walk(arbol):
        mods = ([a.name for a in nodo.names] if isinstance(nodo, ast.Import)
                else [nodo.module] if isinstance(nodo, ast.ImportFrom) and nodo.module else [])
        for m in mods:
            raiz = (m or "").split(".")[0]
            if raiz in nombres_locales:
                salida.add(raiz)
    return salida


def _produccion():
    return sorted(p for p in RAIZ.glob("*.py"))


def _de(carpeta):
    return sorted((RAIZ / carpeta).glob("*.py"))


def hay_produccion_que_escanear():
    """Si esto falla, todo lo de abajo estaria comprobando el vacio."""
    prod = _produccion()
    assert len(prod) >= 20, f"solo {len(prod)} modulos en la raiz: ¿se movio produccion?"
    for carpeta in CARPETAS:
        assert (RAIZ / carpeta).is_dir(), f"falta {carpeta}/"
        assert _de(carpeta), f"{carpeta}/ esta vacia"


def produccion_no_importa_lo_de_fuera():
    """El corazón de este archivo."""
    fuera = {p.stem: carpeta for carpeta in CARPETAS for p in _de(carpeta)}
    fuera.update({nombre: nombre + "/" for nombre in PAQUETES})
    malas = []
    for archivo in _produccion():
        for importado in _importa(archivo, set(fuera)):
            if (archivo.stem, importado) in EXCEPCIONES:
                continue
            malas.append(f"{archivo.name} importa {importado} (de {fuera[importado]}/)")
    assert not malas, "produccion depende de lo que esta fuera:\n  " + "\n  ".join(malas)


def las_excepciones_son_reales_y_estan_justificadas():
    """Una excepcion que ya no ocurre es una excusa que sobra en la lista."""
    locales = ({p.stem for p in _produccion()} | {p.stem for c in CARPETAS for p in _de(c)}
               | set(PAQUETES))
    vivas = set()
    for archivo in _produccion():
        for importado in _importa(archivo, locales):
            if (archivo.stem, importado) in EXCEPCIONES:
                vivas.add((archivo.stem, importado))
    muertas = set(EXCEPCIONES) - vivas
    assert not muertas, f"excepciones declaradas que ya no ocurren: {sorted(muertas)}"
    assert all(EXCEPCIONES[e] for e in vivas), "hay una excepcion sin motivo escrito"


def los_tests_si_pueden_importar_produccion():
    """La flecha va en un solo sentido, pero va."""
    produccion = {p.stem for p in _produccion()}
    tocan = set()
    for archivo in _de("tests"):
        tocan |= _importa(archivo, produccion)
    assert len(tocan) >= 15, f"los tests solo tocan {len(tocan)} modulos de produccion"


def nadie_importa_los_tests():
    """Ni produccion ni las demas carpetas."""
    nombres = {p.stem for p in _de("tests")}
    malas = []
    for archivo in _produccion() + [p for c in ("demos", "benchmarks", "experimental")
                                    for p in _de(c)]:
        for importado in _importa(archivo, nombres):
            malas.append(f"{archivo.name} importa el test {importado}")
    assert not malas, malas


def lo_experimental_no_lo_toca_produccion():
    """`config.ESTADO_FLAGS` los declara EXPERIMENTAL; si produccion los importara,
    la etiqueta seria mentira."""
    import config
    nombres = {p.stem for p in _de("experimental")}
    for archivo in _produccion():
        assert not _importa(archivo, nombres), \
            f"{archivo.name} importa un modulo experimental"
    for flag in ("SEMANTIC_CACHE", "KNOWLEDGE_TREE", "MODEL_ROUTING"):
        estado, _motivo = config.ESTADO_FLAGS[flag]
        assert estado == config.EXPERIMENTAL, f"{flag} dice {estado}"


def lo_conectado_sigue_en_la_raiz():
    """grafo y vectores NO son experimentales: config los declara CONECTADO y
    pipeline/hibrido los importan. Moverlos a experimental/ seria etiquetar mal."""
    import config
    for flag, modulo in (("GRAPH_RETRIEVAL", "grafo"), ("VECTOR_SIGNAL", "vectores")):
        estado, _ = config.ESTADO_FLAGS[flag]
        assert estado == config.CONECTADO, f"{flag} dice {estado}"
        assert (RAIZ / f"{modulo}.py").exists(), \
            f"{modulo}.py esta declarado CONECTADO y no esta en la raiz"


def la_documentacion_esta_separada_de_los_informes():
    """docs/ = como se usa Mirag. reports/ = como llegamos hasta aqui."""
    docs = {p.name for p in (RAIZ / "docs").glob("*.md")}
    reports = {p.name for p in (RAIZ / "reports").glob("*.md")}
    assert docs and reports and not (docs & reports)
    assert "DEMO.md" in docs and "RELEASE_REPORT.md" in reports
    # En la raiz solo los tres que describen el repositorio en si. Todo lo demas tiene
    # que estar clasificado en docs/ o en reports/.
    EN_LA_RAIZ = {"README.md", "REPOSITORY_STRUCTURE.md", "RELOCATION_EXCEPTIONS.md"}
    sueltos = {p.name for p in RAIZ.glob("*.md")}
    assert sueltos <= EN_LA_RAIZ, f"hay .md sin clasificar en la raiz: {sueltos - EN_LA_RAIZ}"


def la_raiz_es_exactamente_la_cerradura_de_server():
    """El criterio de la reorganizacion, comprobado en vez de prometido.

    «Un archivo es produccion si esta en la cadena transitiva de `server.py`». Escrito asi
    la frase no cuesta nada; lo que cuesta es que siga siendo verdad. Este caso falla en
    los dos sentidos: si queda un modulo en la raiz que nadie alcanza desde server (basura
    que habria que haber movido) y si produccion empieza a importar algo que no esta ahi.
    """
    en_raiz = {p.stem for p in _produccion()}
    assert len(en_raiz) >= 20, f"solo {len(en_raiz)} modulos: ¿se movio produccion?"
    vistos, pendientes = set(), ["server"]
    while pendientes:
        modulo = pendientes.pop()
        if modulo in vistos or modulo not in en_raiz:
            continue
        vistos.add(modulo)
        pendientes += _importa(RAIZ / f"{modulo}.py", en_raiz)
    huerfanos = en_raiz - vistos
    assert not huerfanos, \
        f"en la raiz y fuera de la cadena de server.py: {sorted(huerfanos)}"
    # Y al reves. Sin esto el caso pasaba en vacio: al quitar skills.py de la raiz, el
    # `skills` que importa pipeline dejaba de ser «local», el recorrido lo saltaba, y los
    # dos conjuntos encogian a la vez. Comprobado sacando skills.py de verdad.
    # Mirag no tiene ninguna dependencia externa: un import que no es stdlib y no esta en
    # la raiz ni en las carpetas clasificadas es un modulo que falta.
    fuera = {p.stem for c in CARPETAS for p in _de(c)} | set(PAQUETES)
    colgados = []
    for archivo in _produccion():
        for nodo in ast.walk(ast.parse(archivo.read_text())):
            nombres = ([a.name for a in nodo.names] if isinstance(nodo, ast.Import)
                       else [nodo.module] if isinstance(nodo, ast.ImportFrom)
                       and nodo.module and nodo.level == 0 else [])
            for nombre in nombres:
                raiz_mod = (nombre or "").split(".")[0]
                if raiz_mod and raiz_mod not in sys.stdlib_module_names \
                        and raiz_mod not in en_raiz and raiz_mod not in fuera:
                    colgados.append(f"{archivo.name} importa {raiz_mod}, que no existe")
    assert not colgados, "produccion importa modulos que no estan:\n  " + "\n  ".join(colgados)


def los_bancos_escriben_donde_produccion_lee():
    """`ganancias.json` lo escribe un banco y lo LEE produccion (`config.activar`).

    Al mudarse a benchmarks/, los cuatro scripts seguian colgando un "benchmarks" de su
    propio `__file__`: escribian en benchmarks/benchmarks/ y la medicion se guardaba donde
    nadie la busca. Nada fallaba — simplemente el dato dejaba de llegar.
    """
    import config
    banco = RAIZ / "benchmarks"
    assert config.GANANCIAS.parent.resolve() == banco.resolve(), config.GANANCIAS
    assert config.GANANCIAS.exists(), "produccion lee un ganancias.json que no existe"
    assert not (banco / "benchmarks").exists(), \
        "hay un benchmarks/benchmarks/: alguien volvio a colgar la carpeta de __file__"
    malas = [p.name for p in _de("benchmarks")
             if '__file__).parent / "benchmarks"' in p.read_text()]
    assert not malas, f"calculan su destino como si siguieran en la raiz: {malas}"


def _externas_de(archivos, locales):
    """Los imports que no son stdlib y no resuelven a nada local."""
    fuera = set()
    for archivo in archivos:
        for nodo in ast.walk(ast.parse(archivo.read_text())):
            nombres = ([a.name for a in nodo.names] if isinstance(nodo, ast.Import)
                       else [nodo.module] if isinstance(nodo, ast.ImportFrom)
                       and nodo.module and nodo.level == 0 else [])
            for nombre in nombres:
                raiz = (nombre or "").split(".")[0]
                if raiz and raiz not in sys.stdlib_module_names and raiz not in locales:
                    fuera.add(raiz)
    return fuera


def el_nucleo_sigue_sin_dependencias_externas():
    """Lo que el README promete de los 30 modulos de la raiz. Sin matices."""
    locales = ({p.stem for p in _produccion()} | {p.stem for c in CARPETAS for p in _de(c)}
               | set(PAQUETES))
    externas = _externas_de(_produccion(), locales)
    assert not externas, f"produccion importa paquetes externos: {sorted(externas)}"


def la_capa_blockchain_solo_usa_lo_que_declara():
    """Una dependencia que nadie declaro es una que nadie instala ni audita.

    Escanea RECURSIVAMENTE, que es justo lo que el test de la raiz no hace: mientras
    `blockchain/` fue invisible, un `import loquesea` ahi dentro pasaba en verde.
    """
    capa = RAIZ / "blockchain"
    assert capa.is_dir(), "falta blockchain/"
    archivos = [p for p in sorted(capa.rglob("*.py")) if ".venv" not in p.parts]
    assert len(archivos) >= 8, f"el escaneo no ve la capa: {len(archivos)} archivos"

    locales = ({p.stem for p in _produccion()} | set(PAQUETES)
               | {p.stem for p in archivos} | {d.name for d in capa.iterdir() if d.is_dir()})
    usadas = _externas_de(archivos, locales)

    proyecto = (capa / "pyproject.toml").read_text()
    # De "stellar-sdk>=16.1.0" al nombre del modulo: guion -> guion bajo.
    declaradas = {linea.strip().strip('",').split(">=")[0].split("==")[0].replace("-", "_")
                  for linea in proyecto.splitlines()
                  if linea.strip().startswith('"') and linea.strip().endswith(('",', '"'))}
    assert declaradas, "blockchain/pyproject.toml no declara ninguna dependencia"
    sin_declarar = usadas - declaradas
    assert not sin_declarar, f"usa sin declarar: {sorted(sin_declarar)}"
    sin_usar = declaradas - usadas
    assert not sin_usar, f"declara y no usa: {sorted(sin_usar)}"


def el_claim_de_dependencias_dice_la_verdad():
    """La frase que ve el usuario, atada a la medicion.

    `estado.py` se lo cuenta a la pagina y a quien pregunte de que esta hecho Mirag. Si
    `blockchain/` tiene dependencias externas, esa frase NO puede afirmar cero a secas.
    Este caso existe porque la version anterior decia "cero dependencias externas" y
    seguia en verde el dia que dejo de ser cierto: el unico test que lo vigilaba escaneaba
    `RAIZ.glob("*.py")` y una carpeta le era invisible.
    """
    capa = RAIZ / "blockchain"
    archivos = [p for p in sorted(capa.rglob("*.py")) if ".venv" not in p.parts]
    locales = ({p.stem for p in _produccion()} | set(PAQUETES) | {p.stem for p in archivos}
               | {d.name for d in capa.iterdir() if d.is_dir()})
    hay_externas = bool(_externas_de(archivos, locales))

    texto = (RAIZ / "estado.py").read_text()
    afirmaciones = [l.strip() for l in texto.splitlines()
                    if "dependencias externas" in l and not l.strip().startswith("#")]
    assert afirmaciones, "estado.py ya no dice nada sobre dependencias: ¿se perdio el claim?"
    for linea in afirmaciones:
        if not hay_externas:
            continue
        assert ("nucleo" in linea or "núcleo" in linea or "blockchain" in linea),             f"estado.py afirma cero dependencias sin decir donde vale: {linea}"


def produccion_no_lee_de_reports_ni_de_docs():
    """Ningun modulo de produccion puede depender de un informe historico."""
    malas = []
    for archivo in _produccion():
        texto = archivo.read_text()
        for carpeta in ("reports/", "docs/"):
            if carpeta in texto and "#" not in texto.split(carpeta)[0].splitlines()[-1]:
                malas.append(f"{archivo.name} menciona {carpeta}")
    assert not malas, malas


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if callable(fn) and getattr(fn, "__module__", "") == "__main__" \
                and not nombre.startswith(("probar", "_")):
            probar(nombre.replace("_", " "), fn)
    for ok, nombre, error in casos:
        print(f"  {'✅' if ok else '❌'} {nombre}" + (f"  → {error}" if error else ""))
    fallos = sum(1 for ok, _, _ in casos if not ok)
    print(f"\n{len(casos)} casos · {'TODO OK' if not fallos else f'{fallos} FALLOS'}")
    sys.exit(1 if fallos else 0)

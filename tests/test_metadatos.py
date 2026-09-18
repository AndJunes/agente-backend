"""Metadatos derivados y filtrado con aviso.

Lo que mas importa aqui no es que el filtro acierte, es que CUENTE lo que hizo:
el filtro anterior caia al corpus entero en silencio y nadie se enteraba.

    python3 test_metadatos.py
"""

import sys as _sys
from pathlib import Path as _Path
# Este archivo vive en una subcarpeta y produccion sigue en la raiz. Sin esto, ejecutarlo
# directamente (`python3 tests/test_x.py`) pone la subcarpeta en sys.path[0] y no la raiz,
# asi que `import pipeline` no encontraria nada. Mismo patron que usan las sondas.
_RAIZ_REPO = _Path(__file__).resolve().parent.parent
# La raiz (produccion) y las dos carpetas cuyos modulos se importan por nombre desnudo:
# `test_cache` importa `cache` (experimental/) y `test_plan` importa `eval` (benchmarks/).
for _d in (_RAIZ_REPO, _RAIZ_REPO / "experimental", _RAIZ_REPO / "benchmarks"):
    _sys.path.insert(0, str(_d))
import sys

import metadatos as M
import plan
import rag

casos = []


def probar(nombre, fn):
    try:
        fn()
        casos.append((True, nombre, ""))
    except AssertionError as e:
        casos.append((False, nombre, str(e) or "assert"))
    except Exception as e:
        casos.append((False, nombre, f"{type(e).__name__}: {e}"))


def trozo(titulo):
    return next(t for t in rag.TROZOS if t.titulo == titulo)


# ── lo que se deriva ─────────────────────────────────────────────────────────

def dominio_es_la_caja():
    m = M.de(trozo("Índices"))
    assert m.domain == "04" and m.domain_nombre == "Databases", m


def subdominio_sale_del_temario():
    m = M.de(trozo("Índices"))
    assert "indexing" in m.subdomains, m.subdomains
    declaradas = M._temario()["04"]
    assert all(s in declaradas for s in m.subdomains), \
        "no se puede asignar una subcategoria que la caja no declara"


def tecnologia_por_palabras():
    assert "PostgreSQL" in M.de(trozo("Índices")).technologies
    assert "Kubernetes" in M.de(trozo("Kubernetes")).technologies


def lenguaje_de_los_bloques():
    con_lenguaje = [t for t in rag.TROZOS if M.de(t).languages]
    assert con_lenguaje, "ningun trozo tiene lenguaje: el parseo de ``` esta roto"
    for t in con_lenguaje[:5]:
        assert all(l.isalpha() for l in M.de(t).languages), M.de(t).languages


def tipos_de_artefacto():
    tipos = M.de(trozo("Índices")).artifact_types
    assert "concepto" in tipos and "ficha" in tipos, tipos


def lo_que_no_existe_vale_none():
    """Declarado, sin fuente: mejor None explicito que un valor inventado."""
    m = M.de(trozo("Índices"))
    assert m.difficulty is None and m.status is None and m.version is None


def cobertura_es_honesta():
    c = M.cobertura()
    assert c["con_subdominio"] <= c["trozos"]
    assert c["subcategorias_asignadas_a_algun_trozo"] <= c["subcategorias_declaradas"], \
        "no se pueden asignar mas subcategorias de las declaradas"
    assert "difficulty" in c["sin_fuente_en_el_corpus"]


def todos_los_trozos_tienen_metadatos():
    for t in rag.TROZOS:
        m = M.de(t)
        assert m.domain.isdigit() and len(m.domain) == 2, (t.caja, m.domain)


# ── el filtro ────────────────────────────────────────────────────────────────

def sin_filtro_no_toca_nada():
    r, fallback, motivo = M.filtrar(rag.TROZOS)
    assert len(r) == len(rag.TROZOS) and not fallback
    assert "sin filtro" in motivo, motivo


def filtro_por_caja():
    r, fallback, motivo = M.filtrar(rag.TROZOS, cajas=["04"])
    assert not fallback, motivo
    assert r and all(t.caja.startswith("04") for t in r), "se colaron trozos de otra caja"
    assert len(r) < len(rag.TROZOS), "el filtro no filtro nada"
    assert "04" in motivo and str(len(r)) in motivo, motivo


def filtro_por_varias_cajas():
    r, _, _ = M.filtrar(rag.TROZOS, cajas=["04", "08"])
    cajas = {t.caja.split("·")[0].strip() for t in r}
    assert cajas == {"04", "08"}, cajas


def filtro_por_tecnologia():
    r, fallback, _ = M.filtrar(rag.TROZOS, tecnologias=["Kubernetes"])
    assert not fallback
    assert all("Kubernetes" in M.de(t).technologies for t in r)


def excluir_una_caja():
    r, _, motivo = M.filtrar(rag.TROZOS, cajas=["04", "08"], excluir=["08"])
    assert all(t.caja.startswith("04") for t in r), motivo


# ── y lo importante: que AVISE cuando no puede filtrar ───────────────────────

def filtro_vacio_avisa_y_sigue():
    r, fallback, motivo = M.filtrar(rag.TROZOS, tecnologias=["CobolEnLaNube"])
    assert fallback is True, "un filtro que deja 0 trozos tiene que marcarse como fallback"
    assert len(r) == len(rag.TROZOS), "pero hay que seguir buscando, no devolver nada"
    assert "no dejo ningun trozo" in motivo, motivo


def filtro_casi_vacio_tambien_avisa():
    """Dos trozos no son un corpus: mejor buscar en todo y decirlo."""
    r, fallback, motivo = M.filtrar(rag.TROZOS, cajas=["04"], tecnologias=["Stripe"])
    if len(r) == len(rag.TROZOS):
        assert fallback and "muy poco" in motivo or "no dejo" in motivo, motivo


def el_motivo_siempre_se_puede_enseñar():
    for kwargs in ({}, {"cajas": ["04"]}, {"tecnologias": ["NoExiste"]},
                   {"tipos": ["ficha"]}, {"cajas": ["99"]}):
        _, _, motivo = M.filtrar(rag.TROZOS, **kwargs)
        assert motivo and len(motivo) > 10, (kwargs, motivo)


def filtro_desde_un_plan():
    p = plan.leer('{"domains":["04","08"],"needs_code":false}', "reservas concurrentes")
    r, fallback, motivo = M.filtrar(rag.TROZOS, plan=p)
    assert not fallback, motivo
    assert {t.caja.split("·")[0].strip() for t in r} == {"04", "08"}


def caja_inexistente_no_revienta():
    r, fallback, motivo = M.filtrar(rag.TROZOS, cajas=["99"])
    assert fallback and len(r) == len(rag.TROZOS), motivo


def indice_vacio_no_revienta():
    r, fallback, motivo = M.filtrar([], cajas=["04"])
    assert r == [] and isinstance(motivo, str)


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if callable(fn) and not nombre.startswith(("probar", "trozo", "_")) \
                and getattr(fn, "__module__", "") == "__main__":
            probar(nombre.replace("_", " "), fn)
    for ok, nombre, error in casos:
        print(f"  {'✅' if ok else '❌'} {nombre}" + (f"  → {error}" if error else ""))
    fallos = sum(1 for ok, _, _ in casos if not ok)
    print(f"\n{len(casos)} casos · {'TODO OK' if not fallos else f'{fallos} FALLOS'}")
    sys.exit(1 if fallos else 0)

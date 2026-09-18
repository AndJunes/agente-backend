"""La ÚNICA fuente de recuperación y de contexto. Producción y banco consumen esto.

POR QUE EXISTE ESTE MODULO

    Antes había dos stacks. `pipeline` llamaba a `hibrido.recuperar()` y luego tiraba su
    resultado: el contexto del modelo se reconstruía aparte con `rapido.recuperar()`, que
    hace tres `rag.buscar*` sueltos. El banco medía el primero y el modelo recibía el
    segundo. Se demostró con el SHA del contexto: idéntico con el reranker encendido y
    apagado, porque el reranker mejoraba un ranking que nadie leía.

    Aquí hay una sola función. La consumen `pipeline` y `banco_recuperacion`, sobre los
    mismos tres índices y con la misma configuración.

DOS INVARIANTES QUE NO SE PUEDEN ROMPER

    1. Toda métrica de retrieval que decida activar una capacidad tiene que estar medida
       sobre el MISMO pipeline que consume el modelo. Si no, se repite el desastre del
       reranker: +0.0441 MRR que jamás llegó al prompt.

    2. benchmark(query, config) y production(query, config) tienen que pasar por esta
       misma función y obtener los mismos trozos. Hay un test que lo comprueba
       comparando los datos, no la forma.

LOS TRES INDICES SE MANTIENEN SEPARADOS
    No se mezclan: cada uno tiene una semántica distinta en el prompt y el modelo los
    lee de forma distinta. Lo que cambia es que ahora los tres pasan por el mismo
    ranking (filtro de metadatos → BM25 → vector? → RRF → reranker?) en vez de por
    `rag.buscar*` a pelo.
"""

import hashlib
import time
from typing import NamedTuple

import config
import hibrido
import rag

# nombre lógico · índice · cuántos trozos · cómo se separan en el prompt
# Los k son los que ya usaba el contexto anterior (rag.buscar=3, antipatrones=6,
# fallos=5): se conservan para no cambiar dos cosas a la vez.
INDICES = (
    ("conocimiento", "TROZOS", 3, "\n\n---\n\n"),
    ("antipatrones", "ANTIPATRONES", 6, "\n\n"),
    ("fallos", "FALLOS", 5, "\n\n"),
)

ETIQUETAS = {
    "conocimiento": "=== CONOCIMIENTO RECUPERADO ===",
    "antipatrones": "=== ANTI-PATRONES (cubrir con un test CADA UNO) ===",
    "fallos": "=== MODOS DE FALLO CONOCIDOS ===",
}

LIMITE_CONTEXTO = 24_000      # caracteres. ~6k tokens: techo duro para que no crezca solo


class TrozoRecuperado(NamedTuple):
    """Un trozo y de dónde salió. La procedencia es la mitad del valor."""
    trozo: object                 # rag.Trozo
    indice: str                   # conocimiento | antipatrones | fallos
    puntuacion: float
    puesto: int                   # 1 = el mejor de su índice
    metodos: tuple                # ("bm25",) o ("bm25", "vector", "rrf", "reranker")

    @property
    def id(self):
        """Identidad estable de un trozo, para poder rastrearlo hasta el prompt."""
        return f"{self.indice}:{self.trozo.caja.split('·')[0].strip()}:{self.trozo.titulo}"


class RetrievalResult(NamedTuple):
    query: str
    plan: object
    por_indice: dict              # nombre -> [TrozoRecuperado]
    etapas: list                  # hibrido.Etapa, con nombre por índice
    fallbacks: list               # [(etapa, motivo)]
    filtros: str
    metricas: dict

    @property
    def seleccionados(self):
        return [t for nombre, _, _, _ in INDICES for t in self.por_indice.get(nombre, ())]

    @property
    def antipatrones(self):
        """Se expone aparte a propósito.

        El corpus dice que los anti-patrones son de cubrimiento OBLIGATORIO, y hoy
        NADIE lo comprueba: `_evidencia` cruza los test_id que declaró el modelo, nunca
        los anti-patrones recuperados. Aquí se preserva la identidad y la procedencia
        para que la fase de evidencia pueda cerrarlo. NO se finge que ya están cubiertos.
        """
        return list(self.por_indice.get("antipatrones", ()))

    def ids(self):
        return [t.id for t in self.seleccionados]

    def resumen(self):
        partes = [f"{n}:{len(self.por_indice.get(n, ()))}" for n, _, _, _ in INDICES]
        return " · ".join(partes)


def _indice_real(nombre_atributo):
    return getattr(rag, nombre_atributo)


def recuperar(consulta, plan=None, familia="general", vector=None, reranker=None,
              limite_por_indice=None):
    """LA función. Recupera de los tres índices con el mismo ranking y devuelve la
    procedencia de cada trozo.

    vector/reranker: None = decide config.activar(); True/False = forzar (para medir).
    """
    t0 = time.perf_counter()
    por_indice, etapas, fallbacks, filtros = {}, [], [], []

    for nombre, atributo, k, _sep in INDICES:
        k = (limite_por_indice or {}).get(nombre, k)
        r = hibrido.recuperar(consulta, indice=_indice_real(atributo), plan=plan, k=k,
                              familia=familia, vector=vector, reranker=reranker)
        metodos = tuple(e.nombre for e in r.etapas if e.usada)
        por_indice[nombre] = [
            TrozoRecuperado(trozo=t, indice=nombre, puntuacion=round(p, 4),
                            puesto=i, metodos=metodos)
            for i, (t, p) in enumerate(r.trozos, 1)]
        # los nombres de etapa van por índice: tres llamadas producían tres pasos
        # 'bm25' idénticos y cualquier búsqueda por nombre se quedaba con el primero
        etapas += [e._replace(nombre=f"{e.nombre}:{nombre}") for e in r.etapas]
        fallbacks += [(f"{et}:{nombre}", motivo) for et, motivo in r.fallbacks]
        filtros += [e.detalle for e in r.etapas if e.nombre == "filtro"]

    metricas = {
        "ms": round((time.perf_counter() - t0) * 1000, 2),
        "candidatos": {n: len(v) for n, v in por_indice.items()},
        "total_seleccionados": sum(len(v) for v in por_indice.values()),
        "metodos": sorted({m for v in por_indice.values() for t in v for m in t.metodos}),
    }
    return RetrievalResult(query=consulta, plan=plan, por_indice=por_indice, etapas=etapas,
                           fallbacks=fallbacks, filtros=" | ".join(filtros), metricas=metricas)


def construir_contexto(resultado, peticion=None, simbolos=(), aviso_cobertura=None,
                       instrucciones_extra=None, limite=LIMITE_CONTEXTO):
    """El ÚNICO sitio donde se decide qué entra al prompt.

    Ningún otro módulo puede volver a llamar a rag.buscar* para armar el contexto de una
    petición que ya pasó por aquí. Si hace falta más conocimiento, se pide en el
    RetrievalResult, no por un segundo camino.
    """
    peticion = peticion if peticion is not None else resultado.query
    bloques = [f"PETICION DEL USUARIO:\n{peticion}"]
    vistos = set()                     # dedup por identidad, no por texto
    descartados = []

    for nombre, _atributo, _k, separador in INDICES:
        textos = []
        for tr in resultado.por_indice.get(nombre, ()):
            clave = (tr.trozo.caja, tr.trozo.titulo)
            if clave in vistos:        # el mismo trozo puede salir en dos índices
                descartados.append((tr.id, "duplicado"))
                continue
            vistos.add(clave)
            textos.append(tr.trozo.texto)
        bloques.append(f"{ETIQUETAS[nombre]}\n" + (separador.join(textos) or "Sin resultados."))

    if simbolos:
        bloques.append("=== CODIGO DEL PROYECTO ===\n" + "\n".join(
            f"{s.archivo}:{s.linea}  {s.firma}" for s, _ in simbolos))
    if aviso_cobertura:
        bloques.append("=== AVISO DE COBERTURA ===\n" + aviso_cobertura
                       + "\nNo inventes lo que falte: di que el corpus no lo cubre.")
    if instrucciones_extra:
        bloques.append(instrucciones_extra)

    contexto = "\n\n".join(bloques)
    if len(contexto) > limite:
        # Recortar por el FINAL del conocimiento, nunca de los anti-patrones ni de los
        # fallos: esos son las restricciones, y son lo primero que el modelo se salta.
        contexto = contexto[:limite] + "\n\n[contexto recortado en el limite]"
        descartados.append(("(cola del contexto)", f"limite de {limite} caracteres"))
    return contexto, {"chars": len(contexto), "tokens_aprox": len(contexto) // 4,
                      "incluidos": len(vistos), "descartados": descartados,
                      "sha": hashlib.sha256(contexto.encode()).hexdigest()[:16]}


if __name__ == "__main__":
    import plan as P
    q = "como evito un race condition al reservar una plaza en postgres"
    r = recuperar(q, plan=P.deducir(q))
    print(f"{q}\n\n  {r.resumen()} · {r.metricas['ms']} ms · metodos: {r.metricas['metodos']}")
    for tr in r.seleccionados[:6]:
        print(f"    [{tr.indice:<13} #{tr.puesto}] {tr.puntuacion:7.3f}  {tr.trozo.titulo[:44]}")
    ctx, m = construir_contexto(r)
    print(f"\n  contexto: {m['chars']:,} chars · ~{m['tokens_aprox']:,} tokens · "
          f"{m['incluidos']} trozos · sha {m['sha']}")
    print(f"  anti-patrones preservados para la fase de evidencia: {len(r.antipatrones)}")

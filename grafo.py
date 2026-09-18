"""El grafo de referencias, pero por TROZO en vez de por caja.

QUE CAMBIA RESPECTO A rag.GRAFO
    rag._grafo() corre el mismo regex `[NN]` sobre cada trozo y despues AGREGA todo
    en la caja del trozo: se queda con "04 referencia a 09" y tira la informacion de
    que fue la seccion "Índices" la que lo dijo. Aqui se guarda el origen exacto.
    Mismo corpus, mismo regex, cero cambios de formato: solo no tirar lo que ya habia.

        rag.GRAFO      19 nodos, 182 aristas caja->caja
        construir()   247 nodos, 407 aristas trozo->caja   (los numeros los mide test_)

LO QUE EL CORPUS NO DA, Y NO SE INVENTA
    Las marcas `[NN]` apuntan a CAJAS, nunca a secciones. No existe ningun destino
    a nivel de trozo en todo el corpus. Asi que este grafo es trozo -> caja y punto:
    para traer trozos concretos de la caja destino hay que elegirlos con una heuristica,
    y esa eleccion se declara en el camino (ver expandir).

EL GRAFO ES MUY DENSO, Y ESO LIMITA LOS SALTOS
    Las 19 cajas tienen salidas y a 2 saltos casi cualquiera alcanza a 17-18 de las 19.
    "Vecino a 2 saltos" por tanto NO acota nada por si solo: lo que acota es el orden
    (distancia primero, peso despues) y el `limite`. Un multi-hop sin tope aqui es
    equivalente a no filtrar.

POR QUE TODO LLEVA CAMINO
    Sin el camino, "graph retrieval" es magia: aparecen trozos y nadie sabe por que.
    expandir() devuelve una explicacion por cada trozo traido, incluida la parte
    heuristica ("no habia enlace de vuelta, se cogio el primero de la caja").
"""

import re
from collections import Counter, deque
from functools import lru_cache

import rag

# El mismo patron que usa rag._grafo(). Se repite a proposito: si el corpus cambia de
# formato, los dos sitios tienen que fallar a la vez y no en silencio uno de ellos.
PATRON = r"`\[([0-9,\s]+)\]`"


def _numero(caja):
    """'04 · Databases' -> '04'. Tambien acepta un numero ya suelto."""
    return str(caja).split("·")[0].strip().zfill(2)


def referencias(trozo) -> list:
    """Las cajas que ESE trozo cita, en orden de aparicion y sin repetir.

    Devuelve numeros de dos digitos ('09'), no nombres: es lo que hay en el texto.
    Un trozo sin marcas devuelve [] — 19 de los 247 estan en ese caso (las secciones
    'Preguntas de entrevista y trade-offs' no llevan linea '> **Relacionado:**').
    """
    texto = getattr(trozo, "texto", "") or ""
    salida = []
    for grupo in re.findall(PATRON, texto):
        for n in grupo.split(","):
            if n.strip():
                salida.append(n.strip().zfill(2))
    return list(dict.fromkeys(salida))


@lru_cache(maxsize=1)
def construir() -> dict:
    """El indice completo. Se calcula una vez (lru_cache) y se reutiliza.

    Claves:
        cajas       numeros ordenados
        nombres     '04' -> '04 · Databases'
        citas       lista paralela a rag.TROZOS: las cajas que cita cada trozo
        por_caja    '04' -> [indices de sus trozos en rag.TROZOS]
        salidas     '04' -> Counter({'09': cuantos trozos de 04 citan a 09})
        entradas    lo mismo al reves
        aristas_trozo_caja / aristas_caja_caja   para poder comparar con rag.GRAFO
    """
    nombres, por_caja, citas = {}, {}, []
    salidas, entradas = {}, {}
    aristas_trozo_caja = 0

    for i, t in enumerate(rag.TROZOS):
        n = _numero(t.caja)
        nombres[n] = t.caja
        por_caja.setdefault(n, []).append(i)
        refs = [r for r in referencias(t) if r != n]   # no hay autocitas, pero por si acaso
        citas.append(tuple(refs))
        aristas_trozo_caja += len(refs)
        for destino in refs:
            salidas.setdefault(n, Counter())[destino] += 1
            entradas.setdefault(destino, Counter())[n] += 1

    return {
        "cajas": sorted(por_caja),
        "nombres": nombres,
        "citas": citas,
        "por_caja": por_caja,
        "salidas": salidas,
        "entradas": entradas,
        "aristas_trozo_caja": aristas_trozo_caja,
        "aristas_caja_caja": sum(len(c) for c in salidas.values()),
    }


def _resolver(caja):
    """Acepta '04', 4, '04 · Databases' o 'databases'. None si no existe."""
    g = construir()
    clave = _numero(caja)
    if clave in g["por_caja"]:
        return clave
    texto = rag._normalizar(str(caja))
    if len(texto) >= 3:
        for n, nombre in g["nombres"].items():
            if texto in rag._normalizar(nombre):
                return n
    return None


def vecinos(caja, saltos=1) -> dict:
    """BFS acotado sobre el grafo caja->caja derivado de los trozos.

    Devuelve {caja: distancia}, sin la caja de partida. El grafo se recorre DIRIGIDO
    (A cita a B): es lo unico que el corpus afirma. Una caja inexistente devuelve {}
    en vez de reventar — la llama el modelo y se equivoca de nombre a menudo.
    """
    origen = _resolver(caja)
    if origen is None or saltos < 1:
        return {}
    salidas = construir()["salidas"]
    distancia, cola = {origen: 0}, deque([origen])
    while cola:
        actual = cola.popleft()
        if distancia[actual] >= saltos:
            continue
        for destino in salidas.get(actual, ()):
            if destino not in distancia:
                distancia[destino] = distancia[actual] + 1
                cola.append(destino)
    distancia.pop(origen, None)
    return distancia


def _candidatas(origenes, saltos):
    """Cajas alcanzables desde las de partida, ordenadas por (distancia, -peso).

    El peso es cuantos trozos de la caja de origen citan la destino. A distancia 1 es
    una cuenta real; a distancia >1 no hay peso directo y vale 0, por eso la distancia
    manda en el orden.
    """
    salidas = construir()["salidas"]
    mejor = {}
    for origen in origenes:
        for destino, dist in vecinos(origen, saltos).items():
            if destino in origenes:
                continue
            peso = salidas.get(origen, {}).get(destino, 0)
            anterior = mejor.get(destino)
            if anterior is None or (dist, -peso) < (anterior[0], -anterior[1]):
                mejor[destino] = (dist, peso, origen)
    return sorted(mejor.items(), key=lambda x: (x[1][0], -x[1][1], x[0]))


def _ruta_corta(origen, destino, saltos):
    """Reconstruye un camino origen->destino para poder enseñarlo. [] si no hay."""
    salidas = construir()["salidas"]
    previo, cola = {origen: None}, deque([origen])
    while cola:
        actual = cola.popleft()
        if actual == destino:
            break
        if len(_desde(previo, actual)) - 1 >= saltos:
            continue
        for siguiente in salidas.get(actual, ()):
            if siguiente not in previo:
                previo[siguiente] = actual
                cola.append(siguiente)
    return _desde(previo, destino) if destino in previo else []


def _desde(previo, nodo):
    camino = []
    while nodo is not None:
        camino.append(nodo)
        nodo = previo.get(nodo)
    return list(reversed(camino))


def expandir(trozos, saltos=1, limite=8):
    """Trae trozos de las cajas relacionadas con las que ya se recuperaron.

    Devuelve (trozos_extra, camino_explicado), donde camino_explicado tiene UNA
    entrada por cada trozo extra: (caja_origen, trozo_traido, motivo). El motivo
    incluye la ruta de cajas y como se eligio ese trozo dentro de la caja destino.

    LA PARTE HEURISTICA, DICHA EN VOZ ALTA
        El corpus no dice QUE seccion de la caja destino es la relevante, solo la caja.
        Asi que se prefiere un trozo que cite de vuelta a la caja de origen (enlace
        reciproco = relacion de verdad, no de pasada) y, si no lo hay, el primero de la
        caja, diciendolo. Sin query no se puede hacer mejor sin inventarse una señal.

    El reparto es por turnos entre cajas: con limite=8 y 5 cajas candidatas salen
    trozos de las 5, no 8 de la primera.
    """
    trozos = list(trozos or ())
    if not trozos or limite < 1:
        return [], []

    g = construir()
    origenes = list(dict.fromkeys(_numero(t.caja) for t in trozos if getattr(t, "caja", None)))
    origenes = [o for o in origenes if o in g["por_caja"]]
    if not origenes:
        return [], []

    ya = {(t.caja, t.titulo) for t in trozos}
    candidatas = _candidatas(origenes, saltos)

    # una cola de trozos por caja candidata, ya ordenada por la heuristica
    colas = []
    for destino, (dist, peso, origen) in candidatas:
        reciprocos, resto = [], []
        for i in g["por_caja"][destino]:
            t = rag.TROZOS[i]
            if (t.caja, t.titulo) in ya:
                continue
            (reciprocos if origen in g["citas"][i] else resto).append(t)
        colas.append((origen, destino, dist, peso, deque(reciprocos), deque(resto)))

    extra, camino = [], []
    while colas and len(extra) < limite:
        quedan = []
        for origen, destino, dist, peso, reciprocos, resto in colas:
            if len(extra) >= limite:
                quedan.append((origen, destino, dist, peso, reciprocos, resto))
                continue
            if reciprocos:
                t, como = reciprocos.popleft(), "cita de vuelta a la caja de origen"
            elif resto:
                t, como = resto.popleft(), "sin enlace de vuelta: siguiente trozo de la caja"
            else:
                continue
            ruta = _ruta_corta(origen, destino, saltos) or [origen, destino]
            flecha = " → ".join(ruta)
            peso_txt = (f"{peso} trozo de {origen} lo cita" if peso == 1 else
                        f"{peso} trozos de {origen} lo citan" if peso else
                        f"{dist} saltos")
            camino.append((g["nombres"].get(origen, origen), t,
                           f"{flecha} ({peso_txt}) · {t.titulo}: {como}"))
            extra.append(t)
            quedan.append((origen, destino, dist, peso, reciprocos, resto))
        colas = [c for c in quedan if c[4] or c[5]]
        if not any(c[4] or c[5] for c in colas):
            break
    return extra, camino


def comparar_con_rag() -> dict:
    """Cuanta informacion recupera este grafo frente al rag.GRAFO agregado.

    Se mide, no se afirma: es el unico argumento a favor de este modulo.
    """
    g = construir()
    return {
        "nodos_trozo_caja": len(rag.TROZOS),
        "aristas_trozo_caja": g["aristas_trozo_caja"],
        "nodos_caja_caja": len(rag.GRAFO),
        "aristas_caja_caja_rag": sum(len(c) for c in rag.GRAFO.values()),
        "aristas_caja_caja_propias": g["aristas_caja_caja"],
        "trozos_con_referencias": sum(1 for c in g["citas"] if c),
        "trozos_sin_referencias": sum(1 for c in g["citas"] if not c),
    }


if __name__ == "__main__":
    c = comparar_con_rag()
    print(f"trozo→caja : {c['nodos_trozo_caja']:>4} nodos · {c['aristas_trozo_caja']:>4} aristas")
    print(f"caja→caja  : {c['nodos_caja_caja']:>4} nodos · {c['aristas_caja_caja_rag']:>4} aristas"
          f"  (rag.GRAFO)")
    print(f"  trozos con referencias: {c['trozos_con_referencias']}"
          f" · sin ellas: {c['trozos_sin_referencias']}")
    print()
    for caja in ("04", "07", "18"):
        uno, dos = vecinos(caja, 1), vecinos(caja, 2)
        print(f"  {caja}: {len(uno)} cajas a 1 salto → {len(dos)} a 2 saltos")

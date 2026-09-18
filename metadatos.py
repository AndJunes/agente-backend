"""Metadatos por trozo, y el filtrado que decide donde se busca.

LO QUE HAY Y LO QUE NO (medido sobre el corpus, no supuesto)

    domain          SI    es la caja. 19 valores.
    subdomain       DERIVADO  la linea "Cubre del temario" existe en 19/19 archivos y
                              declara el vocabulario; la asignacion trozo -> subcategoria
                              la hace este modulo por coincidencia de palabras. No la
                              escribio nadie a mano: mira cobertura() antes de fiarte.
    technology      DERIVADO  por diccionario de palabras clave. En el corpus NO existe
                              ningun campo 'technology': 0 ocurrencias.
    language        PARCIAL   de las etiquetas de los bloques ```: 65 etiquetados y 144
                              sin etiquetar, asi que muchos trozos no tienen lenguaje.
    artifact_type   DERIVADO  de en que indice cae el trozo y de que contiene.
    difficulty      NO HAY    0 ocurrencias en el corpus.
    status          NO HAY    0 ocurrencias como campo.
    version         NO HAY    0 ocurrencias como campo.

Los tres ultimos se declaran en la estructura y valen None a proposito: es mas util
saber que no existen que rellenarlos con algo inventado.

EL FILTRO AVISA CUANDO FALLA
    rag._filtrar caia al indice completo en silencio cuando el filtro no dejaba nada.
    Aqui se devuelve (resultados, hubo_fallback, motivo) para que la traza y la UI
    puedan decir "se busco en todo el corpus porque el filtro se quedo sin trozos".
"""

import re
from functools import lru_cache
from typing import NamedTuple

import rag

# ── vocabulario de tecnologias ───────────────────────────────────────────────
# Lista a mano y corta: cada entrada se comprobo contra el corpus. Esto NO es
# deteccion semantica, es buscar palabras.
TECNOLOGIAS = {
    "PostgreSQL": r"postgres|postgresql|psql",
    "MySQL": r"\bmysql\b|mariadb",
    "Redis": r"\bredis\b",
    "MongoDB": r"\bmongo",
    "Kafka": r"\bkafka\b",
    "RabbitMQ": r"rabbitmq|\bamqp\b",
    "Elasticsearch": r"elasticsearch|opensearch",
    "Docker": r"\bdocker\b|dockerfile",
    "Kubernetes": r"kubernetes|\bk8s\b|kubectl",
    "S3": r"\bs3\b|object storage",
    "Stripe": r"\bstripe\b",
    "JWT": r"\bjwt\b|json web token",
    "OAuth": r"oauth|openid",
    "gRPC": r"\bgrpc\b",
    "GraphQL": r"graphql",
    "Terraform": r"terraform",
    "Prometheus": r"prometheus",
    "OpenTelemetry": r"opentelemetry|\botel\b",
    "Nginx": r"\bnginx\b",
    "Python": r"\bpython\b",
    "Node.js": r"node\.js|nodejs|\bnpm\b",
}

# ── puente de las subcategorias (inglés) a los titulos (español) ─────────────
# Tambien a mano. Solo donde la palabra no coincide sola.
SINONIMOS = {
    "indexing": ("indice", "index"), "transactions": ("transaccion", "acid", "lock"),
    "queries": ("query", "consulta", "join"), "caching": ("cache", "redis"),
    "scaling": ("escalad", "sharding", "replica"), "modeling": ("modelado", "data model"),
    "authentication": ("autenticacion", "sesion", "token", "password", "mfa"),
    "authorization": ("autorizacion", "rbac", "permiso", "rol"),
    "attacks": ("owasp", "injection", "vulnerabilidad", "ataque"),
    "cryptography": ("encryption", "cifrado", "hashing", "secret"),
    "failure_modes": ("como falla", "fallo", "incidente"),
    "tradeoffs": ("trade-off", "preguntas de entrevista"),
    "implementations": ("implementacion",), "concepts": (),
    "webhooks": ("webhook",), "refunds": ("refund", "chargeback", "disputa"),
    "subscriptions": ("subscription", "billing", "suscripcion"),
    "checkout": ("carrito", "pedido", "pago"), "providers": ("stripe", "proveedor"),
    "idempotency": ("idempot",), "state_machines": ("maquina de estado", "state machine"),
    "messaging": ("cola", "queue", "broker", "evento"),
    "observability": ("observabilidad",), "metrics": ("metrica",),
    "tracing": ("traza", "tracing", "correlation"), "logging": ("log",),
    "alerting": ("alert",), "deployment": ("despliegue", "deploy", "canary"),
    "rollback": ("rollback",), "cicd": ("ci/cd", "pipeline"), "git": ("git",),
    "containers": ("docker", "contenedor", "kubernetes"),
    "storage": ("almacenamiento", "volumen", "s3"),
    "uploads": ("upload", "subida", "presigned", "multipart"),
    "networking": ("red", "dns", "tcp", "tls"), "protocols": ("http", "protocolo"),
    "headers": ("header",), "streaming": ("streaming", "sse", "websocket"),
    "search": ("busqueda", "filtering", "sorting"),
    "profiling": ("profiling", "perfilad"), "optimization": ("optimizacion",),
    "bottlenecks": ("cuello de botella",), "capacity": ("estimacion", "capacity"),
    "load": ("carga", "load balancing", "load testing"),
    "recovery": ("backup", "disaster", "failover"), "reliability": ("fiabilidad",),
    "rag": ("rag", "retrieval"), "embeddings": ("embedding",),
    "reranking": ("rerank",), "llms": ("llm", "modelo"), "agents": ("agente",),
    "prompting": ("prompt",), "evals": ("eval",), "guardrails": ("guardrail",),
    "tool_calling": ("tool calling", "structured output"),
    "vector_databases": ("vector",), "mcp": ("mcp",),
    "multi_tenancy": ("tenant", "multi-tenancy", "organization"),
    "permissions": ("permiso", "rol"), "audit": ("audit",),
    "workflows": ("workflow", "flujo"), "entities": ("entidad", "agregado"),
    "notifications": ("notification", "notificacion", "email"),
    "external_apis": ("api de tercero", "integracion", "externa"),
    "email": ("email", "correo"), "oauth": ("oauth",),
    "unit": ("unit test",), "integration": ("integration test",), "e2e": ("e2e",),
    "contract": ("contract test", "contrato"), "requirements": ("requisito",),
    "decisions": ("adr", "decision"), "diagrams": ("diagrama",),
    "architecture": ("arquitectura", "layered", "hexagonal", "solid", "ddd", "cqrs"),
    "patterns": ("patron", "pattern"), "boundaries": ("boundary", "frontera", "coupling"),
    "dependencies": ("dependenc",), "linux": ("linux",), "cloud": ("nube", "cloud", "serverless"),
    "iam": ("iam", "permiso"), "infrastructure": ("infraestructura", "terraform"),
    "secrets": ("secret",), "security": ("seguridad", "security"),
    "orchestration": ("orquesta", "saga"), "processing": ("procesamiento", "background"),
    "failure_scenarios": ("escenario de fallo", "adversarial"),
    "dashboards": ("dashboard",), "constraints": ("limite", "constraint", "cumplimiento"),
    "events": ("evento", "event"),
}


class Metadatos(NamedTuple):
    domain: str                    # "04"
    domain_nombre: str             # "Databases"
    subdomains: tuple = ()         # derivado; ver cobertura()
    technologies: tuple = ()       # derivado por palabras clave
    languages: tuple = ()          # de las etiquetas ```; parcial
    artifact_types: tuple = ()     # derivado
    # declarados a proposito, sin fuente en el corpus:
    difficulty: str = None
    status: str = None
    version: str = None


@lru_cache(maxsize=1)
def _temario():
    """Las subcategorias que cada caja DECLARA cubrir. 19/19 archivos la tienen."""
    salida = {}
    for archivo in sorted(rag.CARPETA.glob("[0-9]*.md")):
        contenido = archivo.read_text()
        caja = contenido.split("\n", 1)[0].lstrip("# ").split("·")[0].strip()
        if (m := re.search(r"\*\*Cubre del temario:\*\*(.+)$", contenido, re.M)):
            salida[caja] = tuple(re.findall(r"`([a-z_]+)`", m.group(1)))
    return salida


def _subdominios(trozo, declaradas):
    """Asigna el trozo a las subcategorias de su caja que de verdad aparecen en el."""
    texto = rag._normalizar(trozo.titulo + " " + trozo.texto[:1200])
    encontradas = []
    for sub in declaradas:
        agujas = (sub.replace("_", " "),) + SINONIMOS.get(sub, ())
        if any(rag._normalizar(a) in texto for a in agujas if a):
            encontradas.append(sub)
    # 'concepts' es el cajon generico del temario: no tiene palabra propia que buscar,
    # asi que se usa para lo que no encaja en ninguna otra. No es un acierto, es el resto.
    if not encontradas and "concepts" in declaradas:
        return ("concepts",)
    return tuple(encontradas)


@lru_cache(maxsize=4096)
def _de_texto(caja, titulo, texto):
    tecnologias = tuple(n for n, patron in TECNOLOGIAS.items()
                        if re.search(patron, texto, re.I))
    lenguajes = tuple(dict.fromkeys(re.findall(r"^```([a-z]+)", texto, re.M)))
    tipos = ["concepto"]
    if re.search(r"^> \*\*Ficha\*\*", texto, re.M):
        tipos.append("ficha")
    if "```" in texto:
        tipos.append("implementacion")
    if re.search(r"^\|.*\|", texto, re.M):
        tipos.append("tabla")
    if titulo.startswith(rag.TITULOS_DE_FALLO):
        tipos.append("fallo")
    if "Anti-patrón" in texto:
        tipos.append("antipatron")
    return tecnologias, lenguajes, tuple(tipos)


def de(trozo):
    """Los metadatos de un trozo. Todo derivado, nada inventado."""
    numero, _, nombre = trozo.caja.partition("·")
    numero, nombre = numero.strip(), nombre.strip()
    tecnologias, lenguajes, tipos = _de_texto(trozo.caja, trozo.titulo, trozo.texto)
    return Metadatos(domain=numero, domain_nombre=nombre,
                     subdomains=_subdominios(trozo, _temario().get(numero, ())),
                     technologies=tecnologias, languages=lenguajes, artifact_types=tipos)


def filtrar(indice, plan=None, cajas=None, tecnologias=None, tipos=None, excluir=None):
    """Acota el indice. Devuelve (resultados, hubo_fallback, motivo).

    El motivo va a la traza: si el filtro deja el indice vacio hay que seguir
    buscando, pero el usuario tiene derecho a saber que su filtro no sirvio.
    """
    if plan is not None:
        cajas = cajas or list(plan.domains or ())
        tecnologias = tecnologias or list(plan.technologies or ())
        tipos = tipos or [t for t in (plan.artifact_types or ())
                          if t in ("ficha", "fallo", "antipatron", "concepto", "implementacion")]
        excluir = excluir or list(plan.exclude or ())

    if not any((cajas, tecnologias, tipos, excluir)):
        return list(indice), False, "sin filtro: se busca en todo el corpus"

    filtrado, aplicados = list(indice), []
    if cajas:
        claves = {str(c).split("·")[0].strip().zfill(2) if str(c).strip().isdigit()
                  else rag._normalizar(str(c)) for c in cajas}
        filtrado = [t for t in filtrado
                    if t.caja.split("·")[0].strip() in claves
                    or any(k in rag._normalizar(t.caja) for k in claves if not k.isdigit())]
        aplicados.append("cajas " + ",".join(sorted(str(c) for c in cajas)))
    if excluir:
        fuera = {str(c).zfill(2) for c in excluir}
        filtrado = [t for t in filtrado if t.caja.split("·")[0].strip() not in fuera]
        aplicados.append("excluyendo " + ",".join(sorted(fuera)))
    if tecnologias:
        quiere = {t.lower() for t in tecnologias}
        filtrado = [t for t in filtrado
                    if any(x.lower() in quiere for x in de(t).technologies)]
        aplicados.append("tecnologias " + ",".join(sorted(tecnologias)))
    if tipos:
        quiere = {t.lower() for t in tipos}
        filtrado = [t for t in filtrado if quiere & {x.lower() for x in de(t).artifact_types}]
        aplicados.append("tipo " + ",".join(sorted(tipos)))

    detalle = " · ".join(aplicados)
    if not filtrado:
        return (list(indice), True,
                f"el filtro ({detalle}) no dejo ningun trozo: se busca en todo el corpus")
    if len(filtrado) < 3:
        return (list(indice), True,
                f"el filtro ({detalle}) dejo solo {len(filtrado)} trozos, muy poco: "
                f"se busca en todo el corpus")
    return filtrado, False, f"{detalle} → {len(filtrado)} de {len(indice)} trozos"


def cobertura():
    """Cuanto de la asignacion trozo->subcategoria funciona de verdad.

    Se reporta en vez de afirmarse: AUDITORIA.md dice '157/157 subcategorias
    cubiertas' y eso es a nivel de caja, no de trozo. Esto mide lo segundo.
    """
    total = len(rag.TROZOS)
    con_sub = sum(1 for t in rag.TROZOS if de(t).subdomains)
    con_tec = sum(1 for t in rag.TROZOS if de(t).technologies)
    con_len = sum(1 for t in rag.TROZOS if de(t).languages)
    declaradas = {s for subs in _temario().values() for s in subs}
    asignadas = {s for t in rag.TROZOS for s in de(t).subdomains}
    return {
        "trozos": total,
        "con_subdominio": con_sub, "con_tecnologia": con_tec, "con_lenguaje": con_len,
        "subcategorias_declaradas": len(declaradas),
        "subcategorias_asignadas_a_algun_trozo": len(asignadas),
        "nunca_asignadas": sorted(declaradas - asignadas),
        "sin_fuente_en_el_corpus": ["difficulty", "status", "version"],
    }


if __name__ == "__main__":
    c = cobertura()
    print(f"{c['trozos']} trozos\n")
    for campo, n in (("subdominio", c["con_subdominio"]), ("tecnologia", c["con_tecnologia"]),
                     ("lenguaje", c["con_lenguaje"])):
        print(f"  con {campo:<12} {n:>4}/{c['trozos']}  ({100*n//c['trozos']}%)")
    print(f"\n  subcategorias declaradas en el temario: {c['subcategorias_declaradas']}")
    print(f"  asignadas a algun trozo:                {c['subcategorias_asignadas_a_algun_trozo']}")
    if c["nunca_asignadas"]:
        print(f"  nunca asignadas ({len(c['nunca_asignadas'])}): {', '.join(c['nunca_asignadas'])}")
    print(f"\n  sin fuente en el corpus (valen None): {', '.join(c['sin_fuente_en_el_corpus'])}")

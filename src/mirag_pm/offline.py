"""The PM agent's deterministic double.

`mirag` has had one since the beginning — `offline/scripts.py` and the books project — and
this half had none. With the lock on it answered 502: *"The PM agent has no model: these
operations need one — there is no scripted demo for this corpus."* True, and the reason the
whole flow could not be exercised without a key and without spending: the very first step of
every run is a PM call.

WHAT IS SIMULATED AND WHAT IS NOT

Only the model's DECISION. The corpus is really loaded, the retrieval really runs, the skill
is really fetched, the citation audit really inspects the text. What is scripted is the answer
a model would have given — which is why anything this proves is labelled simulated.

The plan below is deliberately ORDINARY: one entity with four scalar fields and a REST
resource. That is the shape the backend agent's CRUD probe exercises, so a run that starts
here can be followed all the way to a verified project without a network.
"""

from __future__ import annotations

import json
from typing import Any

SUMMARY = (
    "Entendí que querés una API REST para gestionar reservas de salas de reunión, con el "
    "ciclo completo: crear, listar, consultar, modificar y borrar. Antes de proponer una "
    "estructura necesito cerrar algunas decisiones que no están en lo que escribiste."
)

QUESTIONS = [
    {"id": "users", "text": "¿Quién lo usa día a día y con qué soltura técnica?"},
    {"id": "scale", "text": "¿Cuántas reservas por semana, y una sede o varias?"},
    {"id": "pain", "text": "¿Qué falla hoy — se pisan las reservas, no hay visibilidad, otra cosa?"},
    {"id": "outcome", "text": "¿Qué haría que esto valiera la pena?"},
]

PLAN = {
    "purpose": (
        "Una herramienta para que una recepcionista registre y consulte las reservas de las "
        "salas de reunión, de modo que dejen de pisarse y se vea de un vistazo qué hay hoy."
    ),
    "entities": [
        {"name": "Reserva",
         "description": "una sala apartada por una persona, con fecha y hora de inicio",
         "fields": []},
        {"name": "Sala", "description": "el espacio que se reserva", "fields": []},
    ],
    "roles": [{"name": "Recepcionista", "can": []}],
    "flows": [
        {"name": "Registrar una reserva",
         "steps": ["elegir la sala", "elegir fecha y hora", "anotar quién reserva", "guardar"]},
        {"name": "Ver las reservas del día",
         "steps": ["abrir el listado", "filtrar por fecha", "ver sala, persona y hora"]},
        {"name": "Corregir o cancelar",
         "steps": ["encontrar la reserva", "modificarla o borrarla", "comprobar que quedó así"]},
    ],
    "constraints": [
        {"kind": "compatibility", "statement": "Datos en SQLite, biblioteca estándar de Python"},
        {"kind": "performance", "statement": "Una sede, decenas de reservas por semana"},
    ],
    "openQuestions": [
        "El modelo de datos exacto y los tipos de cada campo: los deriva quien lo implemente.",
        "Qué pasa con dos reservas que se solapan — si se rechaza o se avisa — no está decidido.",
        "No hay autenticación en esta versión y eso es una decisión, no un olvido.",
    ],
}


def _call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """A message shaped exactly like the provider's, so nothing downstream can tell."""
    return {"role": "assistant", "content": None, "tool_calls": [
        {"id": "call_1", "type": "function",
         "function": {"name": name, "arguments": json.dumps(arguments, ensure_ascii=False)}}]}


def script_for(operation: str) -> list[dict[str, Any]]:
    """The scripted answers for one PM operation, in the order it will ask for them.

    `analyze` folds its summary into the tool call because the real one does: asked for prose
    AND a call in the same turn, models reliably do one or the other.

    Each list carries a second copy of the same answer. `plan` and `revise` go through
    `_attempt`, which retries once when the first answer cannot be used — and a script that
    runs out mid-retry would fail for a reason that has nothing to do with what is being
    tested.
    """
    if operation == "analyze":
        answer = _call("ask_questions", {"summary": SUMMARY, "reason":
                       "Estas cuatro cambian la forma del trabajo y no se deducen de la idea.",
                       "questions": QUESTIONS})
    elif operation == "plan":
        answer = _call("deliver_plan", PLAN)
    elif operation == "revise":
        answer = _call("deliver_plan", {**PLAN, "purpose": PLAN["purpose"] + " (revisado)"})
    else:  # pragma: no cover - the container only registers the three
        answer = _call("deliver_plan", PLAN)
    return [answer, answer]

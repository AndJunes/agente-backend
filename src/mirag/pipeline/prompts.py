"""Prompts and tool schemas of the production path.

Prompts are written in English for every locale; a language directive (from the locale's
messages) tells the model which language to answer in.
"""

from __future__ import annotations

from mirag.llm.messages import function_tool

SYSTEM_PROMPT = (
    "You are a backend tutor. Consult the documents before answering technical questions and say "
    "which document each claim comes from. If it is not in the documents, say so. Use the calculator "
    "for arithmetic. Be brief. When you run tests, each case must print an exact line "
    "TEST:<id>:PASS or TEST:<id>:FAIL. It is the only thing read to know what was proved. Do NOT "
    "claim that a test passed if you do not see its marker in the real output: an exit 0 only proves "
    "that the command did not crash, not that it tested anything."
)

REPAIR_SYSTEM_PROMPT = "Fix the CAUSE, not the test."

MEASUREMENT_INSTRUCTIONS = (
    "=== HOW WHAT YOU DELIVER IS MEASURED ===\n"
    "Each test prints an EXACT line TEST:<id>:PASS or TEST:<id>:FAIL, with the same <id> you put in "
    "properties[].test_id. A property whose test_id does not appear in the output is marked UNVERIFIED, "
    "whatever you say. The test must exit with a non-zero code if something fails: printing FAIL is "
    "not reporting it."
)


def deliver_tool(interpreters: str):
    return function_tool(
        "deliver_implementation",
        "Deliver the code and its tests. Call it ONCE, with everything inside.",
        {
            "type": "object",
            "properties": {
                "files": {"type": "object", "additionalProperties": {"type": "string"},
                          "description": "path -> content. The code AND the tests, runnable."},
                "test_command": {"type": "string",
                                 "description": f"How to run the tests. It starts with one of: {interpreters}"},
                "decisions": {"type": "string", "description": "what you decided and why, citing the boxes"},
                "properties": {
                    "type": "array",
                    "description": "What is going to be PROVED. One entry per risk, with the falsifiable "
                                   "property and the id of the test that proves it.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "risk": {"type": "string", "description": "what can go wrong"},
                            "property": {"type": "string",
                                         "description": "a checkable claim, e.g. 'successes <= 1'"},
                            "test_id": {"type": "string",
                                        "description": "exact id the test prints in TEST:<id>:PASS"},
                        },
                    },
                },
                "uncovered": {"type": "array", "items": {"type": "string"},
                              "description": "risks you could NOT test. Be honest: this is published."},
            },
            "required": ["files", "test_command", "decisions", "properties", "uncovered"],
        },
    )

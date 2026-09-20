"""Skills, which are files rather than functions.

A skill is a named operation the agent can carry out: a trigger, the inputs it needs, an
ordered method composed from the knowledge base, the artifact it produces, and — the part
that matters most here — the claims it is not allowed to make.

**Why markdown and not Python.** Fifty-six operations came out of reading the corpus. As
functions that is a module nobody can hold in their head, every new skill is a code change and
a redeploy, and the link back to the documents a method came from lives in a comment, if
anywhere. As files: adding a skill is writing a file, the ``draws_on`` field makes the link
machine-checkable, and the same retrieval machinery that finds knowledge finds the procedure
for using it.

``draws_on`` is the load-bearing field. ``mirag-pm coverage`` reads it across every skill and
fails if any document in the corpus is named by none of them. That is what turns "no part of
this knowledge base gets discarded" from an intention into something CI can enforce.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from mirag.retrieval.corpus import Chunk

from mirag_pm.frontmatter import FrontmatterError, parse

SKILL_BOX = "SK · Skills"
"""Skills retrieve alongside knowledge, so they need a box like anything else. Not a number,
because they are not a domain of the corpus — they are how it gets used."""

REQUIRED = ("skill", "domain", "trigger", "draws_on")


class SkillError(ValueError):
    """A malformed skill card. Loud, because a skill that fails to load is an operation the
    agent simply stops being able to do, with nothing on screen to say so."""


@dataclass(frozen=True, slots=True)
class Skill:
    name: str
    domain: str
    purpose: str
    trigger: tuple[str, ...]
    inputs: tuple[str, ...]
    outputs: str
    draws_on: tuple[str, ...]
    refuses: tuple[str, ...]
    confidence: str
    body: str
    path: Path

    @property
    def text(self) -> str:
        """What the model is shown when this skill is retrieved."""
        lines = [f"[{SKILL_BOX}] {self.name} — {self.purpose}".rstrip(" —")]
        if self.trigger:
            lines.append(f"Use when: {'; '.join(self.trigger)}")
        if self.inputs:
            lines.append(f"Needs: {', '.join(self.inputs)}")
        if self.outputs:
            lines.append(f"Produces: {self.outputs}")
        if self.refuses:
            # Carried into the prompt, not left in the frontmatter, because a refusal the
            # model never sees is a refusal that does not happen.
            lines.append(f"Must NOT claim: {'; '.join(self.refuses)}")
        lines.append(f"Grounded in: {', '.join(self.draws_on)}")
        return "\n".join(lines) + "\n\n" + self.body.strip()

    def chunk(self) -> Chunk:
        return Chunk.of(self.text, SKILL_BOX, self.name)


class SkillLibrary:
    """Every skill card under one directory."""

    def __init__(self, skills: tuple[Skill, ...]) -> None:
        self._skills = skills

    def __len__(self) -> int:
        return len(self._skills)

    def __iter__(self) -> Iterator[Skill]:
        return iter(self._skills)

    @classmethod
    def load(cls, directory: Path) -> SkillLibrary:
        if not directory.exists():
            return cls(())
        skills: list[Skill] = []
        seen: dict[str, Path] = {}
        for path in sorted(directory.rglob("*.md")):
            if path.name.startswith("_") or path.name == "README.md":
                continue
            try:
                doc = parse(path.read_text(encoding="utf-8"), source=str(path))
            except FrontmatterError as error:
                raise SkillError(str(error)) from error
            if missing := [field for field in REQUIRED if field not in doc.meta]:
                raise SkillError(f"{path}: missing {', '.join(missing)}")
            name = doc.text("skill")
            if name in seen:
                raise SkillError(f"{path}: skill {name!r} is already defined in {seen[name]}")
            seen[name] = path
            skills.append(
                Skill(
                    name=name,
                    domain=doc.text("domain"),
                    purpose=doc.text("purpose"),
                    trigger=doc.list("trigger"),
                    inputs=doc.list("inputs"),
                    outputs=doc.text("outputs"),
                    draws_on=doc.list("draws_on"),
                    refuses=doc.list("refuses"),
                    confidence=doc.text("confidence", "medium"),
                    body=doc.body,
                    path=path,
                )
            )
        return cls(tuple(skills))

    # ── what coverage asks ───────────────────────────────────────────────────

    def documents_reached(self) -> set[str]:
        return {document for skill in self._skills for document in skill.draws_on}

    def skills_naming(self, document: str) -> list[str]:
        return [skill.name for skill in self._skills if document in skill.draws_on]

    # ── what retrieval asks ──────────────────────────────────────────────────

    def chunks(self) -> tuple[Chunk, ...]:
        return tuple(skill.chunk() for skill in self._skills)

    def by_name(self, name: str) -> Skill | None:
        return next((skill for skill in self._skills if skill.name == name), None)

    def by_domain(self, domain: str) -> tuple[Skill, ...]:
        return tuple(skill for skill in self._skills if skill.domain == domain)

"""Request validation. Every input is checked here before any use case sees it."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

MAX_BODY_BYTES = 64 * 1024
MAX_QUESTION_CHARS = 8_000


class ChatMode(StrEnum):
    PIPELINE = "pipeline"
    """Production: retrieve, generate, execute and verify."""
    ARCHITECT = "architect"
    """EXPERIMENTAL: ordered design phases, without the pipeline's evidence discipline."""


class ValidationError(ValueError):
    """The request is malformed. The message is safe to show: it never echoes the input."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class ChatRequest:
    question: str
    mode: str
    locale: str | None

    @classmethod
    def parse(cls, raw: bytes) -> ChatRequest:
        try:
            data: Any = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValidationError("invalid_json", "the body is not valid UTF-8 JSON") from exc
        if not isinstance(data, dict):
            raise ValidationError("invalid_body", "the body must be a JSON object")
        question = data.get("question")
        if not isinstance(question, str) or not question.strip():
            raise ValidationError("missing_question", "'question' is required and must be a non-empty string")
        if len(question) > MAX_QUESTION_CHARS:
            raise ValidationError("question_too_long", f"'question' exceeds {MAX_QUESTION_CHARS} characters")
        mode = data.get("mode", ChatMode.PIPELINE.value)
        if not isinstance(mode, str):
            raise ValidationError("invalid_mode", "'mode' must be a string")
        locale = data.get("locale")
        if locale is not None and not isinstance(locale, str):
            raise ValidationError("invalid_locale", "'locale' must be a string")
        return cls(question=question.strip(), mode=mode, locale=locale)

"""Turning pipeline records into what the reader sees: markdown and JSON panels.

Everything here is localised through the request's :class:`~mirag.i18n.MessageCatalog`.
Nothing here decides a status: presenters only read what the pipeline recorded.
"""

from mirag.presentation.answers import AnswerFormatter
from mirag.presentation.panels import (
    CostPresenter,
    EvidencePanelPresenter,
    StepSerializer,
    TimelinePresenter,
)

__all__ = ["AnswerFormatter", "CostPresenter", "EvidencePanelPresenter", "StepSerializer", "TimelinePresenter"]

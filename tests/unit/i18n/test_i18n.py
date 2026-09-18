"""The i18n layer, and the parity of the two locales."""

from __future__ import annotations

import json
import re
import string
from pathlib import Path

import pytest

from mirag.i18n.catalog import MessageCatalog, flatten
from mirag.i18n.registry import SUPPORTED_LOCALES, I18n, parse_accept_language
from mirag.paths import LOCALES_DIR, PACKAGE_ROOT


def _flat(locale: str, name: str) -> dict[str, str]:
    return flatten(json.loads((LOCALES_DIR / locale / name).read_text(encoding="utf-8")))


def _placeholders(template: str) -> set[str]:
    return {field for _, field, _, _ in string.Formatter().parse(template) if field}


# ── catalogs ─────────────────────────────────────────────────────────────────

def test_translates_and_formats() -> None:
    catalog = MessageCatalog("en", {"greet": "Hello {name}"})
    assert catalog.t("greet", name="Ana") == "Hello Ana"


def test_missing_params_stay_visible_instead_of_raising() -> None:
    catalog = MessageCatalog("en", {"greet": "Hello {name}"})
    assert catalog.t("greet", other=1) == "Hello {name}"


def test_falls_back_to_the_fallback_catalog_and_then_to_the_key() -> None:
    fallback = MessageCatalog("en", {"only.en": "english"})
    catalog = MessageCatalog("es", {"both": "ambos"}, fallback)
    assert catalog.t("both") == "ambos"
    assert catalog.t("only.en") == "english"
    assert catalog.t("nowhere") == "nowhere"


def test_plural_forms() -> None:
    catalog = MessageCatalog("en", {"files.one": "{count} file", "files.other": "{count} files"})
    assert catalog.plural("files", 1) == "1 file"
    assert catalog.plural("files", 3) == "3 files"


# ── locale resolution ────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    ("header", "expected"),
    [
        ("es-AR,es;q=0.9,en;q=0.8", "es"),
        ("fr-FR,fr;q=0.9,en;q=0.5", "en"),
        ("en;q=0.2,es;q=0.9", "es"),
        ("de", None),
        ("", None),
        (None, None),
    ],
)
def test_accept_language(header: str | None, expected: str | None) -> None:
    assert parse_accept_language(header) == expected


def test_explicit_locale_wins_over_the_header_and_the_default() -> None:
    i18n = I18n("en")
    assert i18n.resolve("ES", "en") == "es"
    assert i18n.resolve("es_AR") == "es"
    assert i18n.resolve(None, "es-MX") == "es"
    assert i18n.resolve("fr", None) == "en"


def test_unknown_default_falls_back_to_english() -> None:
    assert I18n("fr").default_locale == "en"


def test_unknown_locale_is_rejected_when_loading() -> None:
    with pytest.raises(KeyError):
        I18n().catalog("fr")


# ── parity between locales ───────────────────────────────────────────────────

def test_each_locale_has_its_own_folder_with_the_same_resources() -> None:
    for locale in SUPPORTED_LOCALES:
        names = sorted(p.name for p in (LOCALES_DIR / locale).glob("*.json"))
        assert names == ["corpus.json", "lexicon.json", "messages.json", "ui.json"]
        assert (PACKAGE_ROOT / "knowledge" / locale).is_dir()


@pytest.mark.parametrize("resource", ["messages.json", "corpus.json"])
def test_locales_have_identical_keys(resource: str) -> None:
    en, es = _flat("en", resource), _flat("es", resource)
    assert set(en) == set(es)


def test_messages_have_the_same_placeholders_in_every_locale() -> None:
    en, es = _flat("en", "messages.json"), _flat("es", "messages.json")
    mismatched = {key for key in en if _placeholders(en[key]) != _placeholders(es[key])}
    assert not mismatched


def test_no_message_is_empty() -> None:
    for locale in SUPPORTED_LOCALES:
        assert all(value.strip() for value in _flat(locale, "messages.json").values())


def test_lexicons_define_the_same_sections_and_every_pattern_compiles(i18n: I18n) -> None:
    raw = {loc: json.loads((LOCALES_DIR / loc / "lexicon.json").read_text(encoding="utf-8"))
           for loc in SUPPORTED_LOCALES}
    sections = {loc: {k: set(v) if isinstance(v, dict) else None for k, v in data.items() if not k.startswith("_")}
                for loc, data in raw.items()}
    assert sections["en"].keys() == sections["es"].keys()
    for section in ("intent", "project_state", "claims", "demos", "model_routing", "stopwords"):
        assert sections["en"][section] == sections["es"][section], section
    for locale in SUPPORTED_LOCALES:
        lexicon = i18n.lexicon(locale)
        for dotted in ("intent.code_verbs", "intent.question_start", "claims.success",
                       "project_state.work_verbs", "demos.project"):
            assert lexicon.pattern(dotted).pattern


def _keys_used_in_code() -> set[str]:
    """Literal keys passed to a catalog in the package sources."""
    pattern = re.compile(r"""(?:\bt|_t|catalog\.t|catalog|self\._t)\(\s*["']([a-z_]+(?:\.[a-z_A-Z]+)+)["']""")
    keys: set[str] = set()
    for path in PACKAGE_ROOT.rglob("*.py"):
        keys |= set(pattern.findall(path.read_text(encoding="utf-8")))
    return keys


def test_every_literal_key_used_by_the_code_exists_in_every_locale() -> None:
    used = _keys_used_in_code()
    assert len(used) > 100  # the scan really found the calls
    for locale in SUPPORTED_LOCALES:
        missing = sorted(used - set(_flat(locale, "messages.json")))
        assert not missing, f"{locale}: {missing}"


@pytest.mark.parametrize("family", [
    "features.reason.{}", "evidence.status.{}", "obligation.status.{}", "obligation.label.{}",
    "sufficiency.grade.{}", "plan.need.{}", "project.status.{}", "phase.{}", "claims.{}.title",
    "claims.{}.body", "state.title.{}", "architect.phase.{}", "pipeline.delivery.{}",
])
def test_dynamic_key_families_are_complete(family: str) -> None:
    """Keys built at runtime (``f"evidence.status.{value}"``) must exist for every value."""
    from mirag.agent.architect import FIX, PHASES
    from mirag.evidence.obligations import ObligationStatus
    from mirag.evidence.properties import PropertyStatus
    from mirag.projects.certification import ProjectStatus
    from mirag.retrieval.sufficiency import Grade

    values = {
        "features.reason.{}": ["not_implemented", "experimental", "experimental_forced_on", "forced_on",
                               "core_always_on", "forced_off", "off_by_default", "unreadable_measurement",
                               "not_measured", "below_threshold", "not_worth_cost", "measured_gain"],
        "evidence.status.{}": [s.value for s in PropertyStatus],
        "obligation.status.{}": [s.value for s in ObligationStatus],
        "obligation.label.{}": [s.value for s in ObligationStatus],
        "sufficiency.grade.{}": [g.value for g in Grade],
        "plan.need.{}": ["project", "code", "graph", "symbols"],
        "project.status.{}": [s.value for s in ProjectStatus],
        "phase.{}": ["structure", "syntax", "imports", "repair", "execution", "tests", "tests_after_repair",
                     "documented_command", "crud"],
        "claims.{}.title": ["contradicted", "not_executed", "no_markers", "nothing_ran", "no_property_proved"],
        "claims.{}.body": ["contradicted", "not_executed", "no_markers", "nothing_ran", "no_property_proved"],
        "state.title.{}": ["model", "modes", "tools", "corpus_size", "boxes", "output_location", "structure"],
        "architect.phase.{}": [key for key, _ in (*PHASES, FIX)],
        "pipeline.delivery.{}": ["no_call", "invalid_json", "no_files"],
    }[family]
    for locale in SUPPORTED_LOCALES:
        flat = _flat(locale, "messages.json")
        missing = [family.format(v) for v in values if family.format(v) not in flat]
        assert not missing, f"{locale}: {missing}"


def test_the_knowledge_folders_mirror_each_other() -> None:
    en = sorted(p.name for p in (PACKAGE_ROOT / "knowledge" / "en").glob("*.md"))
    es = sorted(p.name for p in (PACKAGE_ROOT / "knowledge" / "es").glob("*.md"))
    assert en == es
    assert len([n for n in en if n[0].isdigit()]) == 19


def test_ui_catalog_is_served_per_locale(i18n: I18n) -> None:
    en, es = i18n.ui_messages("en"), i18n.ui_messages("es")
    assert isinstance(en, dict) and isinstance(es, dict)
    assert Path(LOCALES_DIR / "en" / "ui.json").is_file()

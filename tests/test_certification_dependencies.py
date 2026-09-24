"""The gate that turns "it does not run here" into a project whose tests actually ran.

The ceiling is not being removed — it is being asked a second time, after installing. These
tests pin both halves: that the ceiling lifts when the install works, and that it is exactly
where the run lands when it does not.
"""

from __future__ import annotations

import re
from dataclasses import replace

from conftest import (
    INSTALLED_AT,
    FakeAnalyzer,
    FakeInstaller,
    FakeRunner,
    failed,
    make_project,
    succeeded,
)
from mirag.execution.syntax import SyntaxChecker
from mirag.i18n.catalog import MessageCatalog
from mirag.paths import LOCALES_DIR
from mirag.projects.certification import PhaseStatus, ProjectCertifier, ProjectStatus


def certifier(runner: FakeRunner, analyzer: FakeAnalyzer, installer: object) -> ProjectCertifier:
    return ProjectCertifier(runner, SyntaxChecker(runner), analyzer, installer=installer)  # type: ignore[arg-type]


def phase(certificate, name: str):
    return next((p for p in certificate.phases if p.name == name), None)


def phases_named(certificate, name: str) -> list:
    return [p for p in certificate.phases if p.name == name]


# ── the ceiling lifts ────────────────────────────────────────────────────────

def test_an_installed_dependency_lets_the_tests_run(catalog, interpreters) -> None:
    runner = FakeRunner(interpreters)
    analyzer = FakeAnalyzer(interpreters, present_at=INSTALLED_AT)
    installer = FakeInstaller(succeeded())

    certificate = certifier(runner, analyzer, installer).certify(make_project(), catalog)

    assert certificate.status is not ProjectStatus.VALIDATED, certificate.reason
    assert phase(certificate, "dependencies").status is PhaseStatus.OK
    assert installer.projects, "the installer was never asked"


def test_the_analyzer_is_asked_again_and_with_the_volume(catalog, interpreters) -> None:
    """The install is worth nothing if the second question is asked of the bare interpreter."""
    runner = FakeRunner(interpreters)
    analyzer = FakeAnalyzer(interpreters, present_at=INSTALLED_AT)

    certifier(runner, analyzer, FakeInstaller(succeeded())).certify(make_project(), catalog)

    assert analyzer.asked[0] == "", "the first question is about the bare machine"
    assert INSTALLED_AT in analyzer.asked[1:], "the second must carry the dependency volume"


def test_every_probe_after_the_install_is_given_the_volume(catalog, interpreters) -> None:
    """A probe run without the volume fails on the very import the install just fixed."""
    runner = FakeRunner(interpreters)
    analyzer = FakeAnalyzer(interpreters, present_at=INSTALLED_AT)

    certifier(runner, analyzer, FakeInstaller(succeeded())).certify(
        make_project(), catalog, test_command="python3 -m unittest")

    assert runner.calls, "nothing ran at all"
    assert set(runner.volumes) == {INSTALLED_AT}


def test_the_imports_phase_is_re_noted_after_a_successful_install(catalog, interpreters) -> None:
    """The first row said LIMITED and that row is what the verdict reads.

    Without the second one a project whose dependencies were installed and whose tests pass
    still comes out capped, because of a phase that is no longer true.
    """
    runner = FakeRunner(interpreters)
    analyzer = FakeAnalyzer(interpreters, present_at=INSTALLED_AT)

    certificate = certifier(runner, analyzer, FakeInstaller(succeeded())).certify(
        make_project(), catalog)

    rows = phases_named(certificate, "imports")
    assert len(rows) == 2
    assert rows[0].status is PhaseStatus.LIMITED
    assert rows[1].status is PhaseStatus.OK
    assert "after installing" in rows[1].detail


def test_the_certificate_says_what_was_installed(catalog, interpreters) -> None:
    """"The tests passed" means something different when the packages were installed for this
    run, and a reader should not have to infer that from the phase rows."""
    runner = FakeRunner(interpreters)
    analyzer = FakeAnalyzer(interpreters, present_at=INSTALLED_AT)

    certificate = certifier(runner, analyzer, FakeInstaller(succeeded())).certify(
        make_project(), catalog)

    assert certificate.installation is not None
    assert certificate.installation.installed == ("fastapi==0.115.0",)


# ── the ceiling stays ────────────────────────────────────────────────────────

def test_a_failed_install_lands_exactly_where_the_run_used_to(catalog, interpreters) -> None:
    runner = FakeRunner(interpreters)
    analyzer = FakeAnalyzer(interpreters, present_at="")  # never importable

    certificate = certifier(runner, analyzer, FakeInstaller(failed())).certify(
        make_project(), catalog)

    assert certificate.status is ProjectStatus.VALIDATED
    assert "fastapi" in certificate.reason
    assert phase(certificate, "dependencies").status is PhaseStatus.LIMITED
    assert "no network" in phase(certificate, "dependencies").detail
    assert runner.calls == [], "nothing may run when the dependency is still missing"


def test_a_failed_install_keeps_its_log(catalog, interpreters) -> None:
    """The ceiling was always honest about WHAT was missing. Now it also says why it could
    not be fixed."""
    runner = FakeRunner(interpreters)
    analyzer = FakeAnalyzer(interpreters, present_at="")

    certificate = certifier(runner, analyzer, FakeInstaller(failed())).certify(
        make_project(), catalog)

    assert "pypi.org" in phase(certificate, "dependencies").output


def test_an_install_that_only_half_worked_still_caps_the_project(catalog, interpreters) -> None:
    """The install reported success and the package is STILL not importable — a wheel for
    another platform, a name that does not match its import root. The analyzer is the
    authority, not the installer's own exit code."""
    runner = FakeRunner(interpreters)
    analyzer = FakeAnalyzer(interpreters, present_at="mirag-deps-someothervolume")

    certificate = certifier(runner, analyzer, FakeInstaller(succeeded())).certify(
        make_project(), catalog)

    assert certificate.status is ProjectStatus.VALIDATED
    assert phase(certificate, "dependencies").status is PhaseStatus.OK
    assert phases_named(certificate, "imports")[-1].status is PhaseStatus.LIMITED


def test_a_switched_off_installer_changes_nothing(catalog, interpreters) -> None:
    runner = FakeRunner(interpreters)
    analyzer = FakeAnalyzer(interpreters, present_at="")
    installer = FakeInstaller(succeeded(), enabled=False)

    certificate = certifier(runner, analyzer, installer).certify(make_project(), catalog)

    assert certificate.status is ProjectStatus.VALIDATED
    assert phase(certificate, "dependencies") is None
    assert installer.projects == []


def test_nothing_is_installed_when_execution_is_off(catalog, interpreters) -> None:
    """Installing so that nothing can run is a download for no reason."""
    runner = FakeRunner(interpreters, enabled=False)
    analyzer = FakeAnalyzer(interpreters, present_at="")
    installer = FakeInstaller(succeeded())

    certifier(runner, analyzer, installer).certify(make_project(), catalog)

    assert installer.projects == []


def test_refused_requirement_lines_are_named_in_the_trace(catalog, interpreters) -> None:
    runner = FakeRunner(interpreters)
    analyzer = FakeAnalyzer(interpreters, present_at=INSTALLED_AT)
    installer = FakeInstaller(
        replace(succeeded(), refused=("--index-url https://evil.invalid",)))

    certificate = certifier(runner, analyzer, installer).certify(make_project(), catalog)

    row = phase(certificate, "dependencies:refused")
    assert row is not None
    assert "evil.invalid" in row.detail


# ── the project that never needed any of this ────────────────────────────────

def test_a_project_whose_imports_all_resolve_never_calls_the_installer(catalog,
                                                                      interpreters) -> None:
    runner = FakeRunner(interpreters)
    analyzer = FakeAnalyzer(interpreters, present_at="")
    installer = FakeInstaller(succeeded())
    stdlib_only = make_project(**{
        "app/main.py": "import json\n\n\ndef create_thing():\n    return json\n",
        "requirements.txt": "",
    })

    certificate = certifier(runner, analyzer, installer).certify(stdlib_only, catalog)

    assert installer.projects == []
    assert phase(certificate, "dependencies") is None
    assert certificate.status is ProjectStatus.VERIFIED, certificate.reason


# ── the messages exist in both languages ─────────────────────────────────────

MESSAGE_KEY = re.compile(r"""\bt\(\s*["']([a-z_]+(?:\.[a-z_]+)+)["']""")


def test_every_message_the_certifier_can_emit_exists_in_both_locales() -> None:
    """A missing key renders as the key itself — `cert.dependencies.installed` in front of a
    user — because `MessageCatalog.template` falls back to it rather than raising. Nothing
    else in the code base would ever notice."""
    from mirag.projects import certification

    source = (LOCALES_DIR.parent / "projects" / "certification.py").read_text(encoding="utf-8")
    keys = {key for key in MESSAGE_KEY.findall(source) if key.split(".")[0] in ("cert", "derive")}
    assert "cert.dependencies.installed" in keys, "the scan found nothing; the regex broke"

    for locale in ("en", "es"):
        catalog = MessageCatalog.from_file(locale, LOCALES_DIR / locale / "messages.json")
        missing = sorted(key for key in keys if not catalog.has(key))
        assert missing == [], f"{locale} is missing {missing}"

    assert certification.MAX_REPAIRS >= 1

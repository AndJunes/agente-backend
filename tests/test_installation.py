"""The installer: what it refuses to install, and where it puts what it does.

Two halves. The first is about `requirements.txt` being untrusted input written by a model,
where every line is a potential pip flag. The second is about the packages landing inside the
sandbox and nowhere else — not in the interpreter running Mirag, not in this checkout, not on
the host at all.

Docker itself is replaced by a double that records argv and answers from a script. What is
under test is the decisions and the commands, which is what can be wrong; that `docker run`
runs is Docker's problem, and `scripts/check_installation.py` does that for real.
"""

from __future__ import annotations

import subprocess
from collections.abc import Sequence

import pytest

from mirag.projects.installation import (
    FINGERPRINT_LABEL,
    LABEL,
    MARKER,
    NO_SANDBOX_REASON,
    OFF_REASON,
    VOLUME_PREFIX,
    DockerInstaller,
    NullInstaller,
    Requirement,
    fingerprint,
    parse_requirements,
    requirements_of,
    run_argv,
    volume_for,
)
from mirag.projects.model import Project


def project_with(requirements: str) -> Project:
    return Project.from_mapping("demo", {"app/main.py": "x = 1\n",
                                         "requirements.txt": requirements})


# ── what a requirements line is allowed to be ────────────────────────────────

@pytest.mark.parametrize(("line", "expected"), [
    ("fastapi", Requirement("fastapi")),
    ("fastapi==0.115.0", Requirement("fastapi", "", "==0.115.0")),
    ("uvicorn[standard]>=0.30", Requirement("uvicorn", "[standard]", ">=0.30")),
    ("python-dotenv~=1.0", Requirement("python-dotenv", "", "~=1.0")),
    ("httpx>=0.27,<1.0", Requirement("httpx", "", ">=0.27,<1.0")),
    ("Django === 4.2", Requirement("Django", "", "===4.2")),
])
def test_an_ordinary_pinned_package_is_accepted(line: str, expected: Requirement) -> None:
    accepted, refused = parse_requirements(line)
    assert accepted == (expected,)
    assert refused == ()


@pytest.mark.parametrize("line", [
    "-r other-requirements.txt",
    "--index-url https://example.invalid/simple",
    "--extra-index-url https://example.invalid/simple",
    "-e .",
    "-e git+ssh://git@example.invalid/x.git#egg=x",
    "git+https://github.com/example/pkg.git",
    "./local-wheel",
    "/etc/passwd",
    "https://example.invalid/pkg.whl",
    "pkg @ https://example.invalid/pkg.whl",
    "--trusted-host example.invalid",
])
def test_anything_that_is_not_a_plain_package_is_refused_by_name(line: str) -> None:
    """Refused, and quoted back. Silently dropping these is how a person ends up reading a
    trace that says an install failed with no way to tell that a line was never sent."""
    accepted, refused = parse_requirements(line)
    assert accepted == ()
    assert refused == (line,)


def test_the_file_is_never_handed_to_pip_whole() -> None:
    """The reason this module parses at all: `-r requirements.txt` makes every line a flag.

    What reaches pip is a list of arguments built from the lines that passed, so a file that
    is half legitimate installs its legitimate half and names the rest.
    """
    accepted, refused = parse_requirements(
        "fastapi==0.115.0\n--index-url https://evil.invalid/simple\nhttpx>=0.27\n")
    assert [r.argument for r in accepted] == ["fastapi==0.115.0", "httpx>=0.27"]
    assert refused == ("--index-url https://evil.invalid/simple",)


def test_comments_blank_lines_and_markers_are_handled() -> None:
    accepted, refused = parse_requirements(
        "# the web framework\n\nfastapi==0.115.0  # pinned\n"
        'tomli==2.0 ; python_version < "3.11"\n')
    assert [r.argument for r in accepted] == ["fastapi==0.115.0", "tomli==2.0"]
    assert refused == ()


def test_a_duplicate_name_is_taken_once() -> None:
    accepted, _refused = parse_requirements("fastapi==0.115.0\nFastAPI==0.116.0\n")
    assert len(accepted) == 1


def test_an_absurdly_long_line_is_refused() -> None:
    accepted, refused = parse_requirements("pkg==" + "9" * 400)
    assert accepted == ()
    assert len(refused) == 1


def test_the_number_of_packages_is_capped() -> None:
    accepted, _refused = parse_requirements("\n".join(f"pkg{n}" for n in range(200)))
    assert len(accepted) == 30


def test_a_project_without_requirements_declares_nothing() -> None:
    assert requirements_of(Project.from_mapping("demo", {"app/main.py": "x = 1\n"})) == ((), ())


# ── the import root a distribution provides ──────────────────────────────────

@pytest.mark.parametrize(("name", "module"), [
    ("fastapi", "fastapi"),
    ("python-dotenv", "dotenv"),
    ("beautifulsoup4", "bs4"),
    ("PyYAML", "yaml"),
    ("some-new-package", "some_new_package"),
])
def test_the_import_root_is_guessed_from_the_distribution_name(name: str, module: str) -> None:
    assert Requirement(name).module == module


# ── which volume ─────────────────────────────────────────────────────────────

def test_the_same_requirements_name_the_same_volume() -> None:
    """What makes the second project asking for FastAPI install nothing at all."""
    one = [Requirement("fastapi", "", "==0.115.0"), Requirement("httpx")]
    other = [Requirement("httpx"), Requirement("fastapi", "", "==0.115.0")]
    assert volume_for(one) == volume_for(other)


def test_a_different_version_names_a_different_volume() -> None:
    assert fingerprint([Requirement("fastapi", "", "==0.115.0")]) != fingerprint(
        [Requirement("fastapi", "", "==0.116.0")])


def test_a_volume_name_is_a_name_and_not_a_path() -> None:
    """The whole property this module exists to have: there is no host directory to hand
    anybody, so there is nothing for a caller to accidentally mount, copy or serve."""
    name = volume_for([Requirement("fastapi")])
    assert name.startswith(VOLUME_PREFIX)
    assert "/" not in name
    assert "\\" not in name
    assert ":" not in name


# ── the install, with Docker replaced by a script ────────────────────────────

class FakeDocker:
    """Answers each `docker` call from a script and remembers every argv it was given."""

    def __init__(self, *outcomes: int | str) -> None:
        self.outcomes = list(outcomes)
        self.calls: list[list[str]] = []

    def __call__(self, argv: Sequence[str], timeout_s: int) -> subprocess.CompletedProcess[str] | str:
        self.calls.append(list(argv))
        outcome = self.outcomes.pop(0) if self.outcomes else 0
        if isinstance(outcome, str):
            return outcome
        return subprocess.CompletedProcess(list(argv), outcome, stdout="pip said things",
                                           stderr="")

    def argv_of(self, word: str) -> list[str]:
        """The one call containing ``word``. Fails loudly when there is not exactly one."""
        found = [argv for argv in self.calls if word in argv]
        assert len(found) == 1, f"{word!r} appears in {len(found)} calls"
        return found[0]

    @property
    def kinds(self) -> list[str]:
        """What each call was, in order: `volume`, `check`, `install` or `seal`."""
        kinds = []
        for argv in self.calls:
            if "volume" in argv:
                kinds.append("volume")
            elif "pip" in argv:
                kinds.append("install")
            elif any(MARKER in part and "sys.exit" in part for part in argv):
                kinds.append("check")
            else:
                kinds.append("seal")
        return kinds


def installer(*outcomes: int | str, enabled: bool = True) -> tuple[DockerInstaller, FakeDocker]:
    docker = FakeDocker(*outcomes)
    return DockerInstaller(enabled=enabled, execute=docker), docker


COLD = (0, 1, 0, 0)
"""volume create: ok, check: 1 (not sealed), install: ok, seal: ok."""


def test_a_successful_install_names_the_volume_it_went_into() -> None:
    pip, docker = installer(*COLD)

    report = pip.install(project_with("fastapi==0.115.0\n"))

    assert report.ok, report.detail
    assert report.volume == volume_for([Requirement("fastapi", "", "==0.115.0")])
    assert report.installed == ("fastapi==0.115.0",)
    assert docker.kinds == ["volume", "check", "install", "seal"]


def test_the_volume_is_created_before_anything_mounts_it() -> None:
    """`docker run -v name:/…` auto-creates a missing volume, silently and WITHOUT labels.

    So asking "is it sealed?" first brings the volume into existence unlabelled, and the
    `create` that follows is a no-op on something that already exists — leaving a working
    install in a volume no `--filter label=…` can find, which is the same as one that cannot
    be cleaned up. Found on a real Docker run; the order is the fix.
    """
    pip, docker = installer(*COLD)
    pip.install(project_with("fastapi\n"))

    assert docker.kinds[0] == "volume"
    assert "create" in docker.calls[0]


def test_pip_is_given_the_parsed_arguments_and_not_the_file() -> None:
    pip, docker = installer(*COLD)
    pip.install(project_with("fastapi==0.115.0\n--index-url https://evil.invalid\n"))

    argv = docker.argv_of("pip")
    assert argv[-1] == "fastapi==0.115.0"
    assert "-r" not in argv
    assert not any("evil.invalid" in part for part in argv)


def test_the_packages_go_into_a_volume_and_never_a_host_path() -> None:
    """The point of the rework. A bind mount here would put third-party code chosen by a
    model inside the checkout, which is what this must not do."""
    pip, docker = installer(*COLD)
    report = pip.install(project_with("fastapi\n"))

    mounts = [argv[index + 1]
              for argv in docker.calls
              for index, part in enumerate(argv) if part == "-v"]
    assert mounts, "nothing was mounted at all"
    for mount in mounts:
        source = mount.split(":")[0]
        assert source == report.volume
        assert "/" not in source and "\\" not in source


def test_only_the_install_container_has_a_network() -> None:
    """It holds no project code, which is why giving it one is safe. The others do."""
    pip, docker = installer(*COLD)
    pip.install(project_with("fastapi\n"))

    for argv in docker.calls:
        if "pip" in argv:
            assert "--network" not in argv, "the install is the one step that needs a network"
        elif "run" in argv:
            assert argv[argv.index("--network") + 1] == "none"


def test_every_container_drops_its_capabilities() -> None:
    pip, docker = installer(*COLD)
    pip.install(project_with("fastapi\n"))

    for argv in (call for call in docker.calls if "run" in call):
        assert "--cap-drop" in argv
        assert "no-new-privileges" in argv


def test_the_volume_is_labelled_so_it_can_be_found_and_removed() -> None:
    pip, docker = installer(*COLD)
    report = pip.install(project_with("fastapi\n"))

    argv = docker.argv_of("create")
    assert LABEL in argv
    assert any(part.startswith(f"{FINGERPRINT_LABEL}=") for part in argv)
    assert argv[-1] == report.volume


def test_a_sealed_volume_is_reused_and_nothing_is_downloaded() -> None:
    pip, docker = installer(0, 0)  # create: ok, check: "already sealed"

    report = pip.install(project_with("fastapi==0.115.0\n"))

    assert report.ok
    assert report.reused
    assert docker.kinds == ["volume", "check"]


def test_a_failing_install_is_not_sealed_so_the_next_run_tries_again() -> None:
    """A half-filled volume with a marker on it is worse than none: the next run would trust
    it and import half a package."""
    pip, docker = installer(0, 1, 1)  # create: ok, check: cold, install: fails

    report = pip.install(project_with("fastapi\n"))

    assert not report.ok
    assert report.volume == ""
    assert "exit 1" in report.detail
    assert "pip said things" in report.log
    assert "seal" not in docker.kinds


def test_a_seal_that_fails_is_reported_rather_than_called_success() -> None:
    """pip succeeded and the packages are there, but without the marker the next run installs
    them again and without the chmod the tests may not be able to read them."""
    pip, _docker = installer(0, 1, 0, 1)

    report = pip.install(project_with("fastapi\n"))

    assert not report.ok
    assert "could not be sealed" in report.detail


def test_a_volume_that_cannot_be_created_stops_it_there() -> None:
    pip, docker = installer(1)

    report = pip.install(project_with("fastapi\n"))

    assert not report.ok
    assert "volume could not be created" in report.detail
    assert "install" not in docker.kinds


def test_docker_not_being_installed_is_reported_and_not_raised() -> None:
    pip, _docker = installer("the 'docker' command is not installed on this machine")

    report = pip.install(project_with("fastapi\n"))

    assert not report.ok
    assert "not installed on this machine" in report.detail


def test_a_project_that_declares_only_refused_lines_says_so() -> None:
    pip, docker = installer(*COLD)

    report = pip.install(project_with("-r other.txt\n--index-url https://x.invalid\n"))

    assert not report.ok
    assert "declares nothing this can install" in report.detail
    assert len(report.refused) == 2
    assert docker.calls == [], "nothing may be run when every line was refused"


def test_a_project_with_no_requirements_file_says_so() -> None:
    pip, docker = installer(*COLD)
    report = pip.install(Project.from_mapping("demo", {"app/main.py": "x = 1\n"}))

    assert not report.ok
    assert "no requirements.txt" in report.detail
    assert docker.calls == []


def test_a_switched_off_installer_runs_nothing() -> None:
    pip, docker = installer(*COLD, enabled=False)
    report = pip.install(project_with("fastapi\n"))

    assert not report.ok
    assert report.detail == OFF_REASON
    assert docker.calls == []


# ── the deployment with no sandbox ───────────────────────────────────────────

def test_without_a_sandbox_there_is_no_install_and_it_says_why() -> None:
    """The host backend runs probes as subprocesses on this machine. Installing a model's
    chosen dependencies there is exactly what must not happen, so nothing is installed and
    the project keeps the ceiling it had."""
    report = NullInstaller(NO_SANDBOX_REASON).install(project_with("fastapi\n"))

    assert not report.ok
    assert "inside the execution sandbox" in report.detail
    assert "MIRAG_EXECUTION_BACKEND=docker" in report.detail


def test_the_null_installer_is_off() -> None:
    assert not NullInstaller().enabled
    assert NullInstaller().install(project_with("fastapi\n")).detail == OFF_REASON


# ── the default executor ─────────────────────────────────────────────────────

def test_a_command_that_does_not_exist_comes_back_as_a_sentence() -> None:
    """`run_argv` never raises: a failure to START is a string the report can carry."""
    assert run_argv(["mirag-no-such-binary"], 5) == (
        "the 'docker' command is not installed on this machine")


def test_a_real_command_comes_back_as_a_process() -> None:
    import sys

    completed = run_argv([sys.executable, "-c", "print('hi')"], 30)
    assert not isinstance(completed, str)
    assert completed.returncode == 0
    assert "hi" in completed.stdout

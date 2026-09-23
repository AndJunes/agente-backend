"""What language a project is written in, and everything that follows from it.

Until this existed the pipeline assumed Python in four unrelated places: the plan was completed
with `unittest` files, the structure check wanted a `.py` under `tests/`, the test phase ran a
Python probe, and the file allow-list knew `.py` and `.js` and nothing else. A Node.js project
therefore came out with its own JavaScript tests ignored and a Python test file it could never
pass injected beside them — `unittest_loader__FailedTest_tests_test_HTTPServer`, verdict FAILED.

The fix is one table instead of four assumptions. A language is a row; adding one is a line, not
a change to the pipeline. What a row buys depends on whether Mirag can RUN that language here:

    harness == "python" / "node"   the tests are executed and every test becomes a marker
    harness == ""                  the tests are generated in the right language and delivered,
                                   and the verdict says they were not run — which is what it is

A language that is not in the table is not rejected: its tests are recognised by convention
(a `tests/` directory, `*_test.*`, `*.spec.*`, `FooTest.*`) and nothing is injected on its
behalf, because guessing another language's test file layout is how Python got injected into a
Node project in the first place.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any


@dataclass(frozen=True, slots=True)
class Language:
    name: str
    aliases: tuple[str, ...]
    """What a model writes in `language`, lower-cased. Whole tokens only."""
    extensions: tuple[str, ...]
    """Source-file suffixes. Also what the project file allow-list accepts."""
    framework: str
    """Its own standard test framework, in the words the contract tells the model."""
    test_command: str
    """The usual command, written in the README. Only RUN when `harness` says it can be."""
    harness: str = ""
    """``python`` | ``node`` — languages Mirag executes here. Empty: delivered, not run."""
    test_files: tuple[str, ...] = ()
    """What is added when the plan has no tests at all. Empty: nothing is guessed."""
    hints: tuple[str, ...] = ()
    """Frameworks and runtimes that imply the language. Weaker than `aliases`, and asked last:
    "Kotlin (Spring Boot)" is Kotlin, and only Java's `spring` hint would say otherwise."""


LANGUAGES: tuple[Language, ...] = (
    Language("python", ("python", "python3"), (".py",),
             "unittest", "python3 -m unittest discover -s tests -t .", harness="python",
             test_files=("tests/__init__.py", "tests/test_{entity}.py"),
             hints=("flask", "django", "fastapi")),
    # TypeScript before JavaScript: "Node.js with TypeScript" is a TypeScript project, and it
    # cannot be run here without a transpile step Mirag does not have.
    Language("typescript", ("typescript", "ts"), (".ts", ".tsx"),
             "vitest (or jest, whichever package.json declares)", "npx vitest run",
             hints=("deno", "nestjs")),
    Language("javascript", ("javascript", "js", "ecmascript"),
             (".js", ".mjs", ".cjs"), "the built-in node:test runner with node:assert/strict",
             "node --test tests/", harness="node", test_files=("tests/{entity}.test.js",),
             hints=("node", "node.js", "nodejs", "express", "express.js", "fastify", "koa")),
    Language("go", ("go", "golang"), (".go",), "the standard `testing` package (files named *_test.go)",
             "go test ./..."),
    Language("java", ("java",), (".java",), "JUnit 5", "mvn test",
             hints=("spring", "springboot", "maven", "gradle")),
    Language("kotlin", ("kotlin",), (".kt", ".kts"), "JUnit 5 with kotlin.test", "gradle test",
             hints=("ktor",)),
    Language("rust", ("rust",), (".rs",),
             "the built-in `#[test]` harness (integration tests under tests/)", "cargo test",
             hints=("axum", "actix", "cargo")),
    Language("ruby", ("ruby",), (".rb",), "Minitest", "bundle exec rake test", hints=("rails", "sinatra")),
    Language("php", ("php",), (".php",), "PHPUnit", "vendor/bin/phpunit", hints=("laravel", "symfony")),
    Language("csharp", ("c#", "csharp"), (".cs",), "xUnit", "dotnet test",
             hints=(".net", "dotnet", "asp.net")),
    Language("cpp", ("c++", "cpp"), (".cpp", ".cc", ".cxx", ".hpp", ".hh"), "GoogleTest", "ctest"),
    Language("c", ("c",), (".c", ".h"), "plain assert-based tests", "make test"),
    Language("swift", ("swift",), (".swift",), "XCTest", "swift test", hints=("vapor",)),
    Language("dart", ("dart",), (".dart",), "package:test", "dart test", hints=("flutter",)),
    Language("elixir", ("elixir",), (".ex", ".exs"), "ExUnit", "mix test", hints=("phoenix",)),
    Language("scala", ("scala",), (".scala",), "ScalaTest", "sbt test", hints=("akka",)),
    Language("haskell", ("haskell",), (".hs",), "HUnit or Hspec", "stack test", hints=("yesod",)),
    Language("clojure", ("clojure",), (".clj", ".cljs"), "clojure.test", "lein test"),
    Language("lua", ("lua",), (".lua",), "busted", "busted"),
    Language("perl", ("perl",), (".pl", ".pm"), "Test::More", "prove -r t"),
    Language("r", ("r",), (".r",), "testthat", "Rscript -e 'testthat::test_dir(\"tests\")'"),
    Language("julia", ("julia",), (".jl",), "the built-in Test stdlib", "julia --project -e 'using Pkg; Pkg.test()'"),
)

BUILD_EXTENSIONS = frozenset({".jsx", ".vue", ".svelte", ".xml", ".gradle", ".properties", ".csproj",
                              ".sln", ".props", ".mod", ".sum", ".lock", ".proto", ".graphql"})
"""Files that belong to a project in one of these languages without being source code in it."""

SOURCE_EXTENSIONS = frozenset(ext for language in LANGUAGES for ext in language.extensions)
"""Every suffix that is code in some language the table knows."""

_TEST_DIRS = frozenset({"tests", "test", "__tests__", "spec", "specs", "e2e"})
_TEST_NAME = re.compile(r"^test[_.-]|^Test[A-Z]|[_.-]tests?\.|[_.-]spec\.|Tests?\.[A-Za-z0-9]+$")
_TOKEN = re.compile(r"[a-z0-9#+.]+")


def looks_like_test(path: str) -> bool:
    """A test file by convention, in any language.

    Directory or name, because languages disagree about which one carries the signal: Python
    and Node put tests in `tests/`, Go puts `foo_test.go` beside `foo.go`, Java mirrors the
    source tree under `src/test/`, Ruby has `foo_spec.rb`.
    """
    pure = PurePosixPath(path)
    return any(part in _TEST_DIRS for part in pure.parts[:-1]) or bool(_TEST_NAME.search(pure.name))


def _match(text: object) -> Language | None:
    """Languages by their own name first, by the frameworks that imply them only after."""
    tokens = set(_TOKEN.findall(str(text or "").lower()))
    by_name = next((lang for lang in LANGUAGES if tokens & set(lang.aliases)), None)
    return by_name or next((lang for lang in LANGUAGES if tokens & set(lang.hints)), None)


def detect(spec: Mapping[str, Any] | None, paths: Iterable[str] = ()) -> Language | None:
    """The language of a project, or ``None`` when it cannot be told.

    What the blueprint SAYS comes first — `language`, then `framework` — because the model
    chose it on purpose. The files are the fallback and the tiebreaker for a blueprint that
    left it blank: whichever known language owns the most non-test source files.
    """
    declared = spec or {}
    for field in ("language", "framework"):
        if found := _match(declared.get(field)):
            return found
    counts: dict[str, int] = {}
    for path in paths:
        if looks_like_test(path):
            continue
        suffix = PurePosixPath(path).suffix.lower()
        for language in LANGUAGES:
            if suffix in language.extensions:
                counts[language.name] = counts.get(language.name, 0) + 1
                break
    if not counts:
        return None
    best = max(counts.values())
    return next(lang for lang in LANGUAGES if counts.get(lang.name) == best)


def is_source(path: str) -> bool:
    return PurePosixPath(path).suffix.lower() in SOURCE_EXTENSIONS


def has_tests(paths: Iterable[str], language: Language | None) -> bool:
    """Whether there is a test file the project's language can use.

    Where Mirag runs the tests, the answer is strict on purpose: the harness looks in `tests/`
    and only there, so a `test_api.py` at the root is not "tests", it is a file nothing will
    ever execute — two places disagreeing about where tests live was the bug that made a
    project whose tests never ran read as one whose tests were silent. Everywhere else it is the
    convention that decides, and the language's own extensions keep a stray `tests/notes.md`
    from counting.
    """
    for path in paths:
        suffix = PurePosixPath(path).suffix.lower()
        if language is not None and language.harness:
            if path.startswith("tests/") and suffix in language.extensions:
                return True
        elif looks_like_test(path) and (language is None or suffix in language.extensions or not suffix):
            return True
    return False


def slug(entity: object) -> str:
    """The entity as something that can sit in a file name."""
    return re.sub(r"[^A-Za-z0-9_]+", "_", str(entity or "")).strip("_") or "api"

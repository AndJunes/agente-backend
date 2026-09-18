"""The symbol index: what there is in a Python repository and where.

The corpus search looks in prose. This looks in CODE, and code has structure prose does
not: a function has a name, a signature, a docstring, a file, an enclosing class and the
names it calls. It is read with ``ast``, Python's own parser, so nothing is guessed with
regular expressions. Deterministic and local: no dependencies, no network, no model.
"""

from __future__ import annotations

import ast
import re
import threading
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from mirag.core.text import normalize_words
from mirag.i18n.lexicon import Lexicon

IGNORED_DIRS = frozenset({
    "__pycache__", ".git", ".venv", "venv", "node_modules", "site-packages",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "build", "dist",
})

# How much each signal is worth, from most to least reliable: the name is what the author
# chose, the docstring is written in passing, the file is almost geography.
# (direct, via synonym): synonyms weigh less because they are a guessed translation.
EXACT = 100.0
W_NAME = (10.0, 6.0)
W_CALLS = (4.0, 2.5)
W_TEXT = (3.0, 2.0)
W_FILE = (1.5, 1.0)
TEST_WEIGHT = 0.5
"""A test mentions what it tests, but it is not where it is done."""

_DEFS = (ast.FunctionDef, ast.AsyncFunctionDef)
_PARTS = re.compile(r"[A-Z]+(?![a-z])|[A-Z][a-z]+|[a-z0-9]+")


@dataclass(frozen=True, slots=True)
class Symbol:
    name: str
    kind: str
    """``function`` | ``method`` | ``class`` | ``module`` | ``test``."""
    file: str
    """Path relative to the indexed root, POSIX style."""
    line: int
    signature: str
    doc: str
    """First line of the docstring, or ``""``."""
    parent: str
    """Enclosing class, or ``""``."""
    calls: tuple[str, ...]
    imports: tuple[str, ...]

    def describe(self) -> str:
        return f"{self.file}:{self.line}  {self.signature or self.name}"


def split_identifier(name: str) -> list[str]:
    """``verifyJWT`` -> ``["verify", "jwt"]``; ``validate_token`` -> ``["validate", "token"]``."""
    return [p.lower() for p in _PARTS.findall(str(name))]


def is_test_file(relative: str | Path) -> bool:
    """Convention, not magic: test_x.py, x_test.py, or anything under tests/.

    The RELATIVE path is checked, not the absolute one: otherwise a project stored under
    ``~/tests/whatever/`` would have every symbol marked as a test just by where it lives.
    """
    path = Path(relative)
    return (path.stem.startswith("test_") or path.stem.endswith("_test")
            or any(p in ("test", "tests") for p in path.parts[:-1]))


class SymbolIndexer:
    """Builds the symbol list of a directory tree."""

    @staticmethod
    def _first_doc_line(node: ast.AST) -> str:
        doc = ast.get_docstring(node) or ""  # type: ignore[arg-type]
        return doc.strip().split("\n")[0].strip()

    @staticmethod
    def _signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
        return f"{node.name}({ast.unparse(node.args)}){returns}"

    @staticmethod
    def _class_signature(node: ast.ClassDef) -> str:
        bases = [ast.unparse(b) for b in node.bases] + [ast.unparse(k) for k in node.keywords]
        return f"class {node.name}({', '.join(bases)})" if bases else f"class {node.name}"

    @staticmethod
    def _calls(node: ast.AST, into_defs: bool = True) -> tuple[str, ...]:
        """Who this node calls, in order. ``self.repo.save(x)`` -> ``"save"``."""
        seen: list[str] = []
        pending = list(ast.iter_child_nodes(node))
        while pending:
            child = pending.pop(0)
            if isinstance(child, (*_DEFS, ast.ClassDef)) and not into_defs:
                continue
            if isinstance(child, ast.Call):
                func = child.func
                name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
                if name and name not in seen:
                    seen.append(name)
            pending.extend(ast.iter_child_nodes(child))
        return tuple(seen)

    @staticmethod
    def _imports(tree: ast.AST) -> tuple[str, ...]:
        modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module.split(".")[0])
        return tuple(sorted(modules))

    def _symbols_of(self, path: Path, relative: str, tree: ast.Module) -> list[Symbol]:
        imports = self._imports(tree)
        test = is_test_file(relative)

        def make(name: str, kind: str, line: int, signature: str, doc: str, parent: str,
                 calls: tuple[str, ...]) -> Symbol:
            return Symbol(name, kind, relative, line, signature, doc, parent, calls, imports)

        out = [make(path.stem, "module", 1, "", self._first_doc_line(tree), "",
                    self._calls(tree, into_defs=False))]
        for node in tree.body:
            if isinstance(node, _DEFS):
                out.append(make(node.name, "test" if test else "function", node.lineno,
                                self._signature(node), self._first_doc_line(node), "", self._calls(node)))
            elif isinstance(node, ast.ClassDef):
                out.append(make(node.name, "class", node.lineno, self._class_signature(node),
                                self._first_doc_line(node), "", self._calls(node, into_defs=False)))
                for child in node.body:  # one level: nested functions are internal detail
                    if isinstance(child, _DEFS):
                        out.append(make(child.name, "test" if test else "method", child.lineno,
                                        self._signature(child), self._first_doc_line(child),
                                        node.name, self._calls(child)))
        return out

    def index(self, root: Path | str) -> list[Symbol]:
        """Every symbol of the ``.py`` files under ``root``, in file order.

        Tolerant on purpose: a file with broken syntax (or odd encoding) is skipped and the
        rest is indexed. An indexer that dies on a half-written file is useless exactly when
        it is most needed.
        """
        root = Path(root)
        if not root.is_dir():
            return []
        out: list[Symbol] = []
        for path in sorted(root.rglob("*.py")):
            if IGNORED_DIRS & set(path.parts):
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except (SyntaxError, ValueError, UnicodeDecodeError, OSError, RecursionError):
                continue
            out += self._symbols_of(path, path.relative_to(root).as_posix(), tree)
        return out

    @staticmethod
    def summary(symbols: Sequence[Symbol]) -> dict[str, int]:
        """The figures that say at a glance whether the index makes sense."""
        kinds = [s.kind for s in symbols]
        return {
            "files": len({s.file for s in symbols}),
            "modules": kinds.count("module"),
            "classes": kinds.count("class"),
            "functions": kinds.count("function") + kinds.count("method"),
            "tests": kinds.count("test"),
            "imported": len({m for s in symbols for m in s.imports}),
        }


class SymbolSearcher:
    """Deterministic, explainable scoring: name > name words > calls > signature/doc > file."""

    def __init__(self, lexicon: Lexicon) -> None:
        self._stopwords = lexicon.words("stopwords.symbols")
        self._synonyms = lexicon.mapping("code_synonyms")

    @staticmethod
    def _matches(a: str, b: str) -> bool:
        """Equal, or one a prefix of the other with at least 4 letters (a poor man's stemmer)."""
        short, long = sorted((a, b), key=len)
        return short == long or (len(short) >= 4 and long.startswith(short))

    def _terms(self, query: str) -> tuple[list[str], list[str]]:
        direct = [w for w in normalize_words(query).split() if len(w) >= 3 and w not in self._stopwords]
        expanded: set[str] = set()
        for word in direct:
            for key, values in self._synonyms.items():
                if self._matches(word, key):
                    expanded.update(values)
        expanded = {e for e in expanded if not any(self._matches(e, d) for d in direct)}
        return direct, sorted(expanded)

    def _points(self, target: list[str], direct: list[str], expanded: list[str], weights: tuple[float, float]) -> float:
        """Counts once per query term, not per target word: long names must not win by repetition."""
        if not target:
            return 0.0
        w_direct, w_synonym = weights
        score = sum(w_direct for t in direct if any(self._matches(t, o) for o in target))
        return score + sum(w_synonym for e in expanded if any(self._matches(e, o) for o in target))

    def score(self, symbol: Symbol, query: str) -> float:
        direct, expanded = self._terms(query)
        if not direct:
            return 0.0
        q = normalize_words(query)
        name = normalize_words(symbol.name)
        if q == name or q.replace(" ", "") == name.replace(" ", ""):
            return EXACT
        name_words = split_identifier(symbol.name)
        calls = [w for c in symbol.calls for w in split_identifier(c)]
        text = split_identifier(symbol.signature) + normalize_words(symbol.doc).split()
        file_words = split_identifier(symbol.file.replace("/", " ").removesuffix(".py"))
        total = (self._points(name_words, direct, expanded, W_NAME)
                 + self._points(calls, direct, expanded, W_CALLS)
                 + self._points(text, direct, expanded, W_TEXT)
                 + self._points(file_words, direct, expanded, W_FILE))
        return total * (TEST_WEIGHT if symbol.kind == "test" else 1.0)

    def search(self, symbols: Sequence[Symbol], query: str, k: int = 5) -> list[tuple[Symbol, float]]:
        """The best ``k`` symbols. Zero-scored ones are NOT returned: if nothing matches, the
        right answer is the empty list. Padding the top-k is how invented answers sneak in."""
        scored = [(s, self.score(s, query)) for s in symbols]
        scored.sort(key=lambda pair: (-pair[1], pair[0].file, pair[0].line))
        return [(s, p) for s, p in scored[:k] if p > 0]


class SymbolIndexCache:
    """Indexing a few hundred symbols costs ~100 ms and repeated on EVERY request.

    Cached by (root, newest mtime of the .py files): when the code changes, the index is
    rebuilt. A stale index would be worse than a slow one - the agent indexes its own
    repository, which changes while people work on it.
    """

    def __init__(self, indexer: SymbolIndexer | None = None) -> None:
        self._indexer = indexer or SymbolIndexer()
        self._cache: dict[tuple[str, float], list[Symbol]] = {}
        self._lock = threading.Lock()

    def get(self, root: Path) -> list[Symbol]:
        stamp = max((f.stat().st_mtime for f in root.rglob("*.py")), default=0.0)
        key = (str(root), stamp)
        with self._lock:
            if key not in self._cache:
                self._cache.clear()  # only the current version is kept
                self._cache[key] = self._indexer.index(root)
            return self._cache[key]

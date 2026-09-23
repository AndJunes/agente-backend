"""``mirag-pm doctor`` and ``mirag-pm coverage``: what CI runs in place of the deleted tests.

Neither needs a model, a network or a key, which is the point — they are cheap enough to run
on every push and they check the two things that fail silently: an index that quietly empties,
and a document that no skill can reach.
"""

from __future__ import annotations

import argparse
import sys

from mirag.i18n.corpus_format import CorpusFormat
from mirag_pm.corpus import DOMAIN_FOLDER, PmCorpus, domain_counts
from mirag_pm.paths import DOCUMENTS_LOCALE, KNOWLEDGE_DIR, LOCALES_DIR, SKILLS_DIR

EXPECTED_DOMAINS = 14
MINIMUM = {"knowledge": 700, "cards": 80, "failures": 50, "anti_patterns": 80}
"""Floors, not targets. They exist to catch a load that collapses — a parser change that
stops seeing sections, a corpus copied in half — not to pin the exact counts, which move
whenever the knowledge base is edited and should be free to."""


def _corpus(locale: str = DOCUMENTS_LOCALE):
    fmt = CorpusFormat.from_file(locale, LOCALES_DIR / locale / "corpus.json")
    return PmCorpus.load_with_report(KNOWLEDGE_DIR / locale, fmt, locale)


def doctor(_: argparse.Namespace) -> int:
    """Load the corpus and complain about anything that looks like a silent failure."""
    corpus, report = _corpus()
    print("\n".join(report.lines()))
    print("\nper domain:")
    for box, count in sorted(domain_counts(corpus).items()):
        print(f"  {box:<36} {count:>4}")

    problems: list[str] = []
    for name, floor in MINIMUM.items():
        found = report.counts[name]
        if found < floor:
            problems.append(f"index {name!r} has {found} chunks, below the floor of {floor}")
    if len(report.domains) != EXPECTED_DOMAINS:
        problems.append(f"{len(report.domains)} domains, expected {EXPECTED_DOMAINS}")
    if missing := [n for n in ("INDEX.md", "SOURCES.md", "GLOSSARY.md") if n not in report.lookups]:
        problems.append(f"lookup tables missing: {', '.join(missing)}")

    # Every locale the process serves must reach documents. A locale with no tree of its own
    # falls back, and the fallback has to be exercised, not assumed.
    for locale in sorted(p.name for p in LOCALES_DIR.iterdir() if p.is_dir()):
        try:
            _, other = _corpus(locale)
        except (ValueError, OSError) as error:
            problems.append(f"locale {locale!r}: {error}")
            continue
        if other.counts["knowledge"] == 0:
            problems.append(f"locale {locale!r} loads an empty corpus")

    print()
    for problem in problems:
        print(f"  !! {problem}")
    print("doctor: ok" if not problems else f"doctor: {len(problems)} problem(s)")
    return 1 if problems else 0


def coverage(args: argparse.Namespace) -> int:
    """Every document reachable by at least one skill.

    This is the check behind the rule that no part of the knowledge base gets discarded. A
    skill declares the documents it draws on in its ``draws_on`` frontmatter; anything no
    skill names is knowledge that shipped and can never be retrieved deliberately.
    """
    from mirag_pm.skills import SkillLibrary  # local: skills are optional while being written

    root = KNOWLEDGE_DIR / DOCUMENTS_LOCALE
    # The meta files count. `SOURCES.md` is what makes a citation resolvable and
    # `RESEARCH_BACKLOG.md` is what a refusal points at, so a skill naming them is naming real
    # knowledge — leaving them out of the denominator would let them rot unreferenced.
    documents = sorted(
        [f"{path.parent.name}/{path.name}" for path in root.glob("*/*.md")
         if DOMAIN_FOLDER.match(path.parent.name)]
        + [path.name for path in root.glob("*.md")]
    )
    library = SkillLibrary.load(SKILLS_DIR)
    reached = library.documents_reached()

    orphans = [name for name in documents if name not in reached]
    unknown = sorted(reached - set(documents))

    print(f"documents: {len(documents)} · skills: {len(library)} · reached: {len(documents) - len(orphans)}")
    if unknown:
        print(f"\n  !! {len(unknown)} skill reference(s) point at documents that do not exist:")
        for name in unknown:
            print(f"      {name}  ({', '.join(library.skills_naming(name))})")
    if orphans:
        print(f"\n  !! {len(orphans)} document(s) no skill reaches:")
        for name in orphans:
            print(f"      {name}")
    else:
        print("\n  every document is reachable")

    if args.by_domain:
        print("\nby domain:")
        groups: dict[str, list[str]] = {}
        for name in documents:
            folder, _, _ = name.rpartition("/")
            groups.setdefault(folder or "(meta files)", []).append(name)
        for folder, names in sorted(groups.items()):
            covered = sum(1 for n in names if n in reached)
            mark = " " if covered == len(names) else "!"
            print(f"  {mark} {folder:<30} {covered:>3}/{len(names)}")

    return 1 if (orphans or unknown) else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mirag-pm", description="The PM agent's corpus and skills.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="load the corpus and report anything that looks wrong").set_defaults(run=doctor)
    cov = sub.add_parser("coverage", help="check that every document is reachable by a skill")
    cov.add_argument("--by-domain", action="store_true", help="also break the result down by domain")
    cov.set_defaults(run=coverage)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.run(args))


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

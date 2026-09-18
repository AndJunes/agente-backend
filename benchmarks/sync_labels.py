"""Derive the chunk labels of one locale's retrieval set from another's. 0 model calls.

The Spanish set is the one that was labelled (and checked) by hand. The English set holds the
same questions translated; its chunk labels are COMPUTED, never typed: the i-th ``##`` section
of box NN is the same section in both corpora.

    python -m benchmarks.sync_labels                 # rewrite en expectations from es
    python -m benchmarks.sync_labels --check         # exit 1 if they are out of sync
    python -m benchmarks.sync_labels --source en --target es

Only the ``expected`` field of the target file changes; its queries are left alone.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from benchmarks.cases import (
    DATASETS_DIR,
    RetrievalDataset,
    align_titles,
    aligned_expectations,
    dump_dataset,
)
from benchmarks.harness import utf8_console
from mirag.i18n.registry import I18n
from mirag.retrieval.corpus import KnowledgeCorpus


def load_corpus(i18n: I18n, locale: str) -> KnowledgeCorpus:
    return KnowledgeCorpus.load(i18n.knowledge_dir(locale), i18n.corpus_format(locale), locale)


def synced(source: RetrievalDataset, target: RetrievalDataset, i18n: I18n) -> RetrievalDataset:
    """The target dataset with its expectations recomputed from the source one."""
    mapping = align_titles(load_corpus(i18n, source.locale), load_corpus(i18n, target.locale))
    labels = aligned_expectations(source, target, mapping)
    cases = tuple(type(case)(case.family, case.query, expected)
                  for case, expected in zip(target.cases, labels, strict=True))
    return RetrievalDataset(target.locale, cases, target.uncovered, target.description, target.source)


def main(argv: Sequence[str] | None = None) -> int:
    utf8_console()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", default="es", help="the hand-labelled locale (default: es)")
    parser.add_argument("--target", default="en", help="the locale whose labels are derived (default: en)")
    parser.add_argument("--check", action="store_true", help="only report; exit 1 if out of sync")
    args = parser.parse_args(argv)

    i18n = I18n()
    source = RetrievalDataset.load(args.source)
    target = RetrievalDataset.load(args.target)
    fresh = synced(source, target, i18n)
    changed = [(old, new) for old, new in zip(target.cases, fresh.cases, strict=True) if old != new]
    for old, new in changed:
        print(f"  {old.query}\n    {[str(x) for x in old.expected]}\n -> {[str(x) for x in new.expected]}")
    if args.check:
        print(f"{len(changed)} case(s) out of sync" if changed else "in sync")
        return 1 if changed else 0
    if changed:
        path = RetrievalDataset.path_for(args.target, DATASETS_DIR)
        path.write_text(dump_dataset(fresh.as_dict()), encoding="utf-8")
        print(f"rewrote {len(changed)} case(s) in {path}")
    else:
        print("already in sync: nothing written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

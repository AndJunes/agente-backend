"""Command line interface.

    mirag serve                      start the web server (http://127.0.0.1:8000)
    mirag ask "question" [--locale]  run one question through the pipeline and print it
    mirag demo [name|all] [--locale] run the canonical demos and check their contracts
    mirag features                   show the state of every feature flag
    mirag traces [-n 20]             show the latest trace lines
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from mirag import __version__


def _container():  # imported lazily: `mirag --version` must not load the corpus
    from mirag.container import build_container

    return build_container()


def _serve(args: argparse.Namespace) -> int:
    from dataclasses import replace

    from mirag.api.server import serve

    container = _container()
    if args.port is not None or args.host is not None:
        container.settings = replace(container.settings, port=args.port or container.settings.port,
                                     host=args.host or container.settings.host)
    serve(container)
    return 0


def _ask(args: argparse.Namespace) -> int:
    from mirag.presentation.answers import AnswerFormatter

    container = _container()
    locale = container.i18n.resolve(args.locale)
    demo = None
    if container.settings.offline:
        demo, script = container.demos(locale).script_for(args.question)
        gateway = container.gateways.create(script=script)
    else:
        gateway = container.gateways.create()
    run = container.pipeline.run(args.question, gateway, locale, persist=not args.dry_run)
    print(run.render())
    print()
    print(AnswerFormatter(container.i18n.catalog(locale)).pipeline_answer(run, demo))
    print(f"\n[cost] {gateway.budget}")
    return 0


def _demo(args: argparse.Namespace) -> int:
    from mirag.offline.contracts import DemoContractRunner

    container = _container()
    locale = container.i18n.resolve(args.locale)
    runner = DemoContractRunner(container)
    keys = runner.keys() if args.name in (None, "all") else [args.name]
    failures = 0
    for key in keys:
        report = runner.run(key, locale)
        mark = "OK " if report.fulfils else "FAIL"
        print(f"[{mark}] {key:<13} {report.question[:70]}")
        for field_, value in report.observed.items():
            print(f"        {field_:<22} {value}")
        for problem in report.problems:
            print(f"        !! {problem}")
        failures += not report.fulfils
    return 1 if failures else 0


def _features(args: argparse.Namespace) -> int:
    container = _container()
    catalog = container.i18n.catalog(container.i18n.resolve(args.locale))
    print(f"vector backend: {container.settings.vector_backend}\n")
    for name, decision in container.gate.summary().items():
        print(f"  {'ON ' if decision.enabled else 'off'}  {name:<18} {decision.explain(catalog)}")
    return 0


def _traces(args: argparse.Namespace) -> int:
    container = _container()
    rows = container.traces.read()
    if not rows:
        print("No traces yet.")
        return 0
    for row in rows[-args.n:]:
        print(f"{row['at']:20} {row['version']:10} {row['status']!s:12} {row['calls']:>3} calls "
              f"${row['cost_usd']:.4f} {row['seconds']:>6.1f}s  {row['task'][:50]}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mirag", description="Mirag backend engineering agent")
    parser.add_argument("--version", action="version", version=f"mirag {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="start the web server")
    serve.add_argument("--host")
    serve.add_argument("--port", type=int)
    serve.set_defaults(handler=_serve)

    ask = sub.add_parser("ask", help="run one question through the pipeline")
    ask.add_argument("question")
    ask.add_argument("--locale")
    ask.add_argument("--dry-run", action="store_true", help="write nothing to disk")
    ask.set_defaults(handler=_ask)

    demo = sub.add_parser("demo", help="run the canonical demos and check their contracts")
    demo.add_argument("name", nargs="?", default="all")
    demo.add_argument("--locale")
    demo.set_defaults(handler=_demo)

    features = sub.add_parser("features", help="show the state of every feature flag")
    features.add_argument("--locale")
    features.set_defaults(handler=_features)

    traces = sub.add_parser("traces", help="show the latest trace lines")
    traces.add_argument("-n", type=int, default=20)
    traces.set_defaults(handler=_traces)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    sys.exit(main())

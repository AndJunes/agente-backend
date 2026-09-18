"""The benches: their datasets are sound, and they measure the production code without spending.

A benchmark that measures a parallel implementation is how the original audit started, so
these tests pin that the benches go through ``RetrievalService.retrieve`` and
``QuestionPipeline.run``, force stages only through arguments, and write nothing unless asked.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from benchmarks import calibrate_stages, project_bench, retrieval_eval, task_bench
from benchmarks.cases import (
    EASY,
    FAMILIES,
    DatasetError,
    Label,
    RetrievalDataset,
    align_titles,
    aligned_expectations,
)
from benchmarks.harness import RESULTS_DIR, RankMetrics, benchmark_environment

from mirag.container import Container
from mirag.features.flags import FeatureGate
from mirag.i18n.registry import I18n
from mirag.paths import FEATURE_GAINS_FILE
from mirag.retrieval.corpus import Chunk, KnowledgeCorpus
from mirag.retrieval.engine import RetrievalEngineFactory
from mirag.retrieval.service import RetrievalService

LOCALES = ("en", "es")
GAIN_KEYS = {"delta_mrr", "normalized_cost", "measured_on", "measured_over", "baseline", "corpus_locale"}


def snapshot_outputs() -> tuple[bytes | None, list[str]]:
    """The production policy and the results folder: what a bench must not touch by itself."""
    policy = FEATURE_GAINS_FILE.read_bytes() if FEATURE_GAINS_FILE.exists() else None
    results = sorted(p.name for p in RESULTS_DIR.iterdir()) if RESULTS_DIR.exists() else []
    return policy, results


# ── datasets ─────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("locale", LOCALES)
def test_the_retrieval_dataset_loads_with_every_family(locale: str) -> None:
    dataset = RetrievalDataset.load(locale)

    assert dataset.locale == locale
    assert dataset.families == FAMILIES
    assert all(not label.is_chunk for case in dataset.easy for label in case.expected)  # easy: by box
    assert all(any(label.is_chunk for label in case.expected) for case in dataset.hard)  # hard: by chunk
    assert {case.grade for case in dataset.uncovered} == {"mentioned", "absent"}


@pytest.mark.parametrize("locale", LOCALES)
def test_every_expected_label_exists_in_the_corpus_of_its_locale(
    engines: RetrievalEngineFactory, locale: str
) -> None:
    assert RetrievalDataset.load(locale).problems(engines.get(locale).corpus) == []


def test_english_chunk_labels_are_the_spanish_ones_aligned_by_position(engines: RetrievalEngineFactory) -> None:
    spanish, english = RetrievalDataset.load("es"), RetrievalDataset.load("en")
    mapping = align_titles(engines.get("es").corpus, engines.get("en").corpus)

    expected = aligned_expectations(spanish, english, mapping)

    assert [case.expected for case in english.cases] == expected
    assert [case.query for case in english.cases] != [case.query for case in spanish.cases]


def test_the_english_set_keeps_realistic_typos_and_mixed_language_queries() -> None:
    english = RetrievalDataset.load("en")
    typos = " ".join(case.query for case in english.of_family("typos"))
    mixed = " ".join(case.query for case in english.of_family("mixed"))

    assert "postgress" in typos
    assert any(word in mixed.split() for word in ("de", "para", "sin", "necesito", "hacer"))


def test_a_label_is_a_box_or_a_box_and_a_title() -> None:
    assert Label.parse("04") == Label("04")
    assert Label.parse("04 · Indexes") == Label("04", "Indexes")
    assert str(Label("04", "Indexes")) == "04 · Indexes"
    for bad in ("4", "04 ·", "Indexes", 4):
        with pytest.raises(DatasetError):
            Label.parse(bad)


@pytest.mark.parametrize("case", [
    {"family": "unknown", "query": "q", "expected": ["04"]},
    {"family": "easy", "query": "", "expected": ["04"]},
    {"family": "easy", "query": "q", "expected": []},
    {"family": "easy", "query": "q", "expected": ["04"], "extra": 1},
])
def test_a_malformed_case_is_rejected(case: dict[str, Any]) -> None:
    with pytest.raises(DatasetError):
        RetrievalDataset.from_dict({"locale": "en", "cases": [case]})


def test_alignment_refuses_corpora_whose_boxes_are_out_of_step(i18n: I18n) -> None:
    def corpus(locale: str, titles: list[str]) -> KnowledgeCorpus:
        chunks = tuple(Chunk.of(f"## {title}", "04 · Databases", title) for title in titles)
        return KnowledgeCorpus(locale, i18n.corpus_format(locale), chunks, (), (), (), {})

    assert align_titles(corpus("es", ["Índices"]), corpus("en", ["Indexes"])) == {("04", "Índices"): "Indexes"}
    with pytest.raises(DatasetError):
        align_titles(corpus("es", ["Índices", "Locks"]), corpus("en", ["Indexes"]))


def test_the_task_datasets_hold_the_same_tasks_in_both_locales() -> None:
    names = {locale: [task.name for task in task_bench.load_tasks(locale)] for locale in LOCALES}

    assert names["en"] == names["es"]
    assert len(names["en"]) == 5


# ── metrics and environment ──────────────────────────────────────────────────


def test_rank_metrics_count_the_first_hit_within_the_depth() -> None:
    metrics = RankMetrics.of([1, 2, 5, None, 12], k=10)

    assert (metrics.n, metrics.hits_at_1, metrics.hits_at_3, metrics.hits_at_k) == (5, 1, 2, 3)
    assert metrics.mrr == round((1 + 1 / 2 + 1 / 5) / 5, 4)


def test_the_bench_environment_isolates_the_data_dir_and_can_force_the_lock(tmp_path: Path) -> None:
    env = benchmark_environment(tmp_path, offline=True, base={"MIRAG_OFFLINE": "0", "MIRAG_DATA_DIR": "/repo/var"})

    assert env["MIRAG_DATA_DIR"] == str(tmp_path)
    assert env["MIRAG_OFFLINE"] == "1"


# ── retrieval eval ───────────────────────────────────────────────────────────


@pytest.mark.parametrize("locale", LOCALES)
def test_the_eval_scores_a_subset_offline_with_mrr_between_zero_and_one(
    engines: RetrievalEngineFactory, locale: str
) -> None:
    dataset = RetrievalDataset.load(locale).subset(1)

    report = retrieval_eval.RetrievalEvaluator(engines, locale).run(dataset)

    assert set(report.by_family()) == set(FAMILIES)
    assert all(0.0 <= metrics.mrr <= 1.0 for metrics in report.by_family().values())
    assert 0.0 <= report.total.mrr <= 1.0
    assert all(o.context_tokens > 0 for o in report.outcomes)
    assert [o.observed for o in report.uncovered]


def test_the_eval_ranks_exactly_what_production_retrieves(engines: RetrievalEngineFactory) -> None:
    case = RetrievalDataset.load("en").of_family("multi_hop")[0]
    engine = engines.get("en")

    outcome = retrieval_eval.RetrievalEvaluator(engines, "en").evaluate_case(case)
    production = engine.service.retrieve(case.query, plan=engine.deducer.deduce(case.query), family="general",
                                         per_index_limit={"knowledge": retrieval_eval.DEPTH})

    assert outcome.positions == case.hit_positions(rc.chunk for rc in production.by_index["knowledge"])


def test_the_eval_cli_saves_only_where_it_is_told(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    before = snapshot_outputs()
    target = tmp_path / "eval.json"

    assert retrieval_eval.main(["--locale", "es", "--per-family", "1", "--save", str(target)]) == 0

    saved = json.loads(target.read_text(encoding="utf-8"))
    assert saved["model_calls"] == 0
    assert 0.0 <= saved["total"]["mrr"] <= 1.0
    assert snapshot_outputs() == before
    assert "HARD SET" in capsys.readouterr().out


# ── calibration ──────────────────────────────────────────────────────────────


def test_calibration_forces_stages_only_through_the_retrieval_service(
    engines: RetrievalEngineFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[bool | None, bool | None]] = []
    original = RetrievalService.retrieve

    def spy(self: RetrievalService, query: str, plan: Any = None, family: str = "general",
            vector: bool | None = None, rerank: bool | None = None, per_index_limit: Any = None) -> Any:
        calls.append((vector, rerank))
        return original(self, query, plan=plan, family=family, vector=vector, rerank=rerank,
                        per_index_limit=per_index_limit)

    monkeypatch.setattr(RetrievalService, "retrieve", spy)
    dataset = RetrievalDataset.load("en").subset(1)

    arms = calibrate_stages.StageCalibrator(engines, "en", warmup=False).measure_arms(dataset)

    assert len(calls) == len(calibrate_stages.ARMS) * len(dataset.cases)
    assert set(calls) == {(arm.vector, arm.rerank) for arm in calibrate_stages.ARMS}
    assert all(set(arm.candidates) == {"knowledge", "anti_patterns", "failures"} for arm in arms)


def test_the_calibration_baseline_is_reproducible(engines: RetrievalEngineFactory) -> None:
    calibrator = calibrate_stages.StageCalibrator(engines, "es", warmup=False)
    dataset = RetrievalDataset.load("es").subset(2)

    first = calibrator.measure(calibrate_stages.BASELINE, dataset)
    second = calibrator.measure(calibrate_stages.BASELINE, dataset)

    assert first.families == second.families
    assert first.hard == second.hard


def test_the_gains_table_follows_the_policy_schema_and_the_gate_can_read_it(
    engines: RetrievalEngineFactory,
) -> None:
    calibrator = calibrate_stages.StageCalibrator(engines, "en", warmup=False)
    dataset = RetrievalDataset.load("en").subset(1)
    base, *_ = arms = calibrator.measure_arms(dataset)
    by_name = {arm.spec.name: arm for arm in arms}

    table = calibrate_stages.gains_table(
        base, {stage: by_name[spec.name] for stage, spec in calibrate_stages.STAGE_ARMS.items()}, "en")

    assert set(table) == {"reranker", "vector_signal"}
    for entry in table.values():
        assert set(entry) == {*FAMILIES, "general"}
        assert all(set(row) == GAIN_KEYS and row["corpus_locale"] == "en" for row in entry.values())
    decision = FeatureGate({}).decide("reranker", "general", gains=table)
    assert decision.code in {"measured_gain", "below_threshold", "not_worth_cost"}


def test_normalized_cost_makes_one_second_or_one_cent_worth_one_mrr_point() -> None:
    assert calibrate_stages.normalized_cost(1000.0) == 1.0
    assert calibrate_stages.normalized_cost(0.0, 0.01) == 1.0
    assert calibrate_stages.normalized_cost(-50.0) == 0.0  # being faster is not a gain in MRR


def test_calibration_writes_nothing_unless_asked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    before = snapshot_outputs()

    assert calibrate_stages.main(["--locale", "en", "--per-family", "1", "--no-warmup"]) == 0

    assert snapshot_outputs() == before
    assert list(tmp_path.iterdir()) == []
    assert "policy not written" in capsys.readouterr().out


def test_calibration_refuses_to_write_a_policy_measured_on_a_sample(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        calibrate_stages.main(["--per-family", "1", "--write", str(tmp_path / "gains.json")])
    assert not (tmp_path / "gains.json").exists()


@pytest.mark.slow
def test_calibration_writes_the_gains_where_it_is_told(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    before = snapshot_outputs()
    target = tmp_path / "gains.json"

    assert calibrate_stages.main(["--locale", "en", "--no-warmup", "--write", str(target)]) == 0

    table = json.loads(target.read_text(encoding="utf-8"))
    assert set(table) == {"reranker", "vector_signal"}
    assert all(set(row) == GAIN_KEYS for entry in table.values() for row in entry.values())
    assert snapshot_outputs() == before  # the production policy was NOT the target
    capsys.readouterr()


# ── pipeline benches ─────────────────────────────────────────────────────────


@pytest.mark.slow
def test_a_dry_project_bench_run_reaches_verified(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    before = snapshot_outputs()
    target = tmp_path / "project_bench.json"

    assert project_bench.main(["1", "--dry", "--output", str(target)]) == 0

    report = json.loads(target.read_text(encoding="utf-8"))
    run = report["runs"][0]
    assert report["dry"] is True
    assert run["status"] == "VERIFIED"
    assert run["fulfils_contract"] is True
    assert run["cost_usd"] == 0.0
    assert snapshot_outputs() == before
    capsys.readouterr()


def test_the_task_baseline_narrows_nothing_but_keeps_the_intent(shared_container: Container) -> None:
    bench = task_bench.TaskBench(shared_container, "en", dry=False)
    request = task_bench.load_tasks("en")[0].request

    baseline = bench.plan_for(task_bench.Arm.BASELINE, request)

    assert baseline is not None
    assert baseline.domains == () and baseline.origin == "disabled"
    assert baseline.needs_code is True  # otherwise the model would get no delivery tool
    assert bench.plan_for(task_bench.Arm.DEFAULT, request) is None


def test_the_task_comparison_needs_both_arms() -> None:
    lines = task_bench.compare({"baseline": {"rows": [], "dry": True, "locale": "en"}})

    assert "Both arms are needed" in lines[0]


@pytest.mark.slow
def test_a_dry_task_bench_runs_both_arms_through_the_pipeline(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "task_bench.json"

    assert task_bench.main(["--dry", "--output", str(target)]) == 0

    arms = json.loads(target.read_text(encoding="utf-8"))["arms"]
    assert set(arms) == {"baseline", "default"}
    assert arms["baseline"]["rows"][0]["plan_origin"] == "disabled"
    assert arms["default"]["rows"][0]["plan_origin"] == "deduced"
    assert all(row["green"] and row["cost_usd"] == 0.0 for arm in arms.values() for row in arm["rows"])
    assert "verified success (GOOD)" in capsys.readouterr().out


def test_the_published_policy_uses_the_dataset_families() -> None:
    assert FAMILIES[0] == EASY
    assert set(json.loads(FEATURE_GAINS_FILE.read_text(encoding="utf-8"))["reranker"]) == {*FAMILIES, "general"}

"""The retrieval engine of one locale: every retrieval component, wired once and cached.

A request in Spanish is answered from the Spanish corpus with the Spanish lexicon and
messages; a request in English from the English ones. Nothing is shared between locales
except the stateless feature gate and the vector backend configuration.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass

from mirag.features.flags import FeatureGate
from mirag.i18n.catalog import MessageCatalog
from mirag.i18n.lexicon import Lexicon
from mirag.i18n.registry import I18n
from mirag.retrieval.context import ContextBuilder
from mirag.retrieval.corpus import KnowledgeCorpus
from mirag.retrieval.graph import ChunkGraph
from mirag.retrieval.hybrid import HybridRetriever, VectorIndexCache
from mirag.retrieval.metadata import MetadataExtractor, MetadataFilter
from mirag.retrieval.plan import IntentClassifier, PlanDeducer, PlanParser
from mirag.retrieval.ranking import Bm25Ranker, Ranker
from mirag.retrieval.reranker import HeuristicReranker
from mirag.retrieval.search import KnowledgeSearch
from mirag.retrieval.service import RetrievalService
from mirag.retrieval.sufficiency import SufficiencyEvaluator
from mirag.retrieval.symbols import SymbolSearcher
from mirag.retrieval.vectors import VectorStoreFactory


@dataclass(frozen=True, slots=True)
class RetrievalEngine:
    locale: str
    catalog: MessageCatalog
    lexicon: Lexicon
    corpus: KnowledgeCorpus
    ranker: Ranker
    metadata: MetadataExtractor
    metadata_filter: MetadataFilter
    retriever: HybridRetriever
    service: RetrievalService
    context: ContextBuilder
    classifier: IntentClassifier
    deducer: PlanDeducer
    plan_parser: PlanParser
    sufficiency: SufficiencyEvaluator
    graph: ChunkGraph
    search: KnowledgeSearch
    symbols: SymbolSearcher


class RetrievalEngineFactory:
    """Builds (once) and returns the engine of each locale. Thread safe."""

    def __init__(self, i18n: I18n, gate: FeatureGate, vector_factory: VectorStoreFactory) -> None:
        self._i18n = i18n
        self._gate = gate
        self._vector_factory = vector_factory
        self._engines: dict[str, RetrievalEngine] = {}
        self._lock = threading.Lock()

    @property
    def gate(self) -> FeatureGate:
        return self._gate

    def get(self, locale: str) -> RetrievalEngine:
        with self._lock:
            if locale not in self._engines:
                self._engines[locale] = self._build(locale)
            return self._engines[locale]

    def _build(self, locale: str) -> RetrievalEngine:
        catalog = self._i18n.catalog(locale)
        lexicon = self._i18n.lexicon(locale)
        corpus = KnowledgeCorpus.load(self._i18n.knowledge_dir(locale), self._i18n.corpus_format(locale), locale)
        ranker = Bm25Ranker()
        metadata = MetadataExtractor(corpus, lexicon)
        metadata_filter = MetadataFilter(metadata, catalog)
        retriever = HybridRetriever(
            ranker, metadata_filter, HeuristicReranker(metadata),
            VectorIndexCache(self._vector_factory), self._gate, catalog,
        )
        classifier = IntentClassifier(lexicon)
        deducer = PlanDeducer(corpus, ranker, classifier)
        return RetrievalEngine(
            locale=locale,
            catalog=catalog,
            lexicon=lexicon,
            corpus=corpus,
            ranker=ranker,
            metadata=metadata,
            metadata_filter=metadata_filter,
            retriever=retriever,
            service=RetrievalService(corpus, retriever),
            context=ContextBuilder(),
            classifier=classifier,
            deducer=deducer,
            plan_parser=PlanParser(deducer),
            sufficiency=SufficiencyEvaluator(corpus, lexicon, catalog),
            graph=ChunkGraph(corpus, catalog),
            search=KnowledgeSearch(corpus, ranker, catalog),
            symbols=SymbolSearcher(lexicon),
        )

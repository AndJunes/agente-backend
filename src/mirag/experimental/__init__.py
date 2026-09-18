"""Experimental modules: working, tested, and deliberately OFF the production path.

Nothing in production imports this package - not the container, not the pipeline, not the
API. Each module here is behind an ``EXPERIMENTAL`` switch of the
:class:`~mirag.features.flags.FeatureGate` (``semantic_cache``, ``knowledge_tree``,
``model_routing``): it can be tried on purpose with ``MIRAG_<NAME>=on`` but it never switches
itself on, not even with a good measurement.

Why they are not wired, in one line each (the measured details live in each module):

``semantic_cache``
    The exact level is safe; the similarity level cannot tell two different questions that
    share most of their letters apart, so it is born off.
``knowledge_tree``
    Routing by the syllabus vocabulary is cheap, but it stays silent whenever the query does
    not use that vocabulary. It has to beat the BM25 baseline before it filters anything.
``model_routing``
    There is no measured cost, latency or verified success per model yet: the routing table
    is a declared preference, not a conclusion.

This file imports nothing on purpose: importing ``mirag.experimental`` must not load any of
its modules.
"""

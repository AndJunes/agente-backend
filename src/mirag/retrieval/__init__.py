"""Retrieval over the knowledge corpus: parsing, ranking, filtering, planning and context.

The only production entry point is :class:`mirag.retrieval.engine.RetrievalEngine`, built
per locale. Benchmarks and production consume the same :class:`RetrievalService`, so a
metric that decides whether a stage is switched on is always measured on the pipeline that
actually feeds the model.
"""

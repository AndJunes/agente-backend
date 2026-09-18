"""The production path, from the question to the evidence.

    question
       │
       ▼ project state ──→ already known? → answer. 0 calls, 0 retrieval.
       ▼ retrieval plan
       ▼ metadata routing
       ▼ BM25 (+ vector if measured) → RRF → reranker if measured
       ▼ symbols    if the plan asks for them
       ▼ graph      if the gate opens it
       ▼ SUFFICIENCY ──→ does the corpus cover this? if not, it is said.
       ▼ context
       ▼ model      (or its deterministic double)
       ▼ tools + verification by EXECUTION
       ▼ evidence
       ▼ trace

NO STAGE RUNS OUT OF HABIT
    Optional stages go through the feature gate, which reads what was measured. A stage
    nobody measured does not run. And when it does NOT run, it is recorded anyway with its
    reason: "Mirag did not use the graph because it is not measured" is useful information.

EVERY STEP SAYS WHERE WHAT IT CLAIMS COMES FROM
    source='execution' -> the computer did it and it can be repeated
    source='model'     -> the model (or its double) said it
    source='corpus'    -> it comes from the documents
"""

from mirag.pipeline.models import PipelineRun, Source, Step, StepStatus
from mirag.pipeline.orchestrator import QuestionPipeline

__all__ = ["PipelineRun", "QuestionPipeline", "Source", "Step", "StepStatus"]

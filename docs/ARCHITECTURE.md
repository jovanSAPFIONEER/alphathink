# Alpha Evolve: Architecture

A small, dependency-free RAG control loop that prefers refusal over hallucination.

## Components

- Retriever (`alpha_evolve/retrieval.py`):
  - SimpleFSRetriever builds a tiny in-memory index and ranks documents with a BM25-like score.
- Agent (`alpha_evolve/agent.py`):
  - Iteratively: retrieve → propose ideas → verify → refine; stops early on acceptance.
  - Multi-idea generation to diversify candidate drafts; optional trace logs; optional inline citations.
- Verifier (`alpha_evolve/verifier.py`):
  - KeywordCoverageVerifier blends unigram and bigram coverage of the query in the combined answer+citations.
  - Analyzer interface supports missing-term feedback to guide retrieval expansion.
- CLI (`alpha_evolve/cli.py`):
  - Flags: --iters, --ideas, --threshold, --trace, --corpus, --demo, --no-inline-citations.
- Eval (`alpha_evolve/eval.py`):
  - Runs a small dataset, outputs JSON report with acceptance, coverage, examples, and citations.

## Flow

1. Retrieve top-k evidence (BM25).
2. Propose N candidate drafts from top evidence.
3. Verify coverage and pick the best; accept if score ≥ threshold.
4. If not accepted, analyze missing terms and expand retrieval; repeat.
5. Refuse with an evidence-based message if threshold is not met.

## Trade-offs & limits

- Heuristic coverage and simple retrieval; performance depends on corpus quality.
- Conservative by design; prefers refusal over guessing.
- No external libraries—portable and inspectable.

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from .agent import AlphaEvolveAgent
from .retrieval import SimpleFSRetriever
from .verifier import KeywordCoverageVerifier
from .memory import RingMemory


def build_agent(corpus: Path, *, max_iters: int = 3, accept_threshold: float = 0.7, ideas: int = 2, trace: bool = False, inline_citations: bool = True) -> AlphaEvolveAgent:
    retriever = SimpleFSRetriever(corpus)
    verifier = KeywordCoverageVerifier()
    memory = RingMemory(maxlen=128)
    return AlphaEvolveAgent(
        retriever,
        verifier,
        memory,
        max_iters=max_iters,
        ideas_per_iter=ideas,
        accept_threshold=accept_threshold,
    trace=trace,
    inline_citations=inline_citations,
    )


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="alpha-evolve", description="Anti-hallucination agent demo")
    parser.add_argument("query", nargs="?", help="Question to ask the agent")
    parser.add_argument("--corpus", default=str(Path("data/corpus").absolute()), help="Path to text corpus directory")
    parser.add_argument("--iters", type=int, default=3, help="Max refinement iterations")
    parser.add_argument("--threshold", type=float, default=0.7, help="Acceptance threshold [0-1]")
    parser.add_argument("--ideas", type=int, default=2, help="Number of ideas (candidate drafts) per iteration")
    parser.add_argument("--demo", action="store_true", help="Use a built-in demo question if no query provided")
    parser.add_argument("--no-inline-citations", action="store_true", help="Disable inline [n] markers in the answer text")
    parser.add_argument("--trace", action="store_true", help="Print per-iteration trace diagnostics")

    args = parser.parse_args(argv)

    corpus = Path(args.corpus)
    agent = build_agent(
        corpus,
        max_iters=args.iters,
        accept_threshold=args.threshold,
        ideas=args.ideas,
        trace=args.trace,
        inline_citations=not args.no_inline_citations,
    )

    if args.demo and not args.query:
        args.query = "What is alpha evolve?"

    if not args.query:
        parser.print_help()
        return 1

    answer, citations, score = agent.ask(args.query)
    print(f"Score: {score:.2f}")
    print("Answer:")
    print(answer)
    if citations:
        print("\nCitations:")
        for i, c in enumerate(citations, 1):
            print(f"[{i}] {c.source}: {c.snippet[:120]}")
    if args.trace:
        trace = agent.get_trace()
        if trace:
            print("\nTrace:")
            for line in trace:
                print(f"- {line}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

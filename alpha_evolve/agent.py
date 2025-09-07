from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple, Optional, Protocol, Set, runtime_checkable


@dataclass
class Evidence:
    source: str
    snippet: str
    score: float = 1.0


@dataclass
class Draft:
    answer: str
    citations: List[Evidence]
    confidence: float


class Retriever:
    def search(self, query: str, k: int = 5) -> List[Evidence]:  # pragma: no cover - interface
        raise NotImplementedError


class Verifier:
    def score(self, query: str, draft: Draft) -> float:  # pragma: no cover - interface
        raise NotImplementedError


class Memory:
    def remember(self, q: str, a: str, ok: bool) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class AlphaEvolveAgent:
    """Iteratively proposes an answer and verifies it against evidence.

    If the verification score stays below a threshold, the agent refuses with
    an evidence-based message, avoiding hallucination.
    """

    _trace_enabled: bool
    _trace_log: List[str]
    _inline_citations: bool

    def __init__(self, retriever: Retriever, verifier: Verifier, memory: Optional[Memory] = None, *, max_iters: int = 3, ideas_per_iter: int = 2, accept_threshold: float = 0.7, trace: bool = False, inline_citations: bool = True) -> None:
        self.retriever = retriever
        self.verifier = verifier
        self.memory = memory
        self.max_iters = max(1, int(max_iters))
        self.ideas_per_iter = max(1, int(ideas_per_iter))
        self.accept_threshold = float(accept_threshold)
        self._trace_enabled = bool(trace)
        self._trace_log = []
        self._inline_citations = bool(inline_citations)

    def ask(self, query: str) -> Tuple[str, List[Evidence], float]:
        evidence = self.retriever.search(query, k=6)
        best: Optional[Draft] = None

        for step in range(self.max_iters):
            # generate multiple candidate drafts (ideas)
            candidates: List[Draft] = []
            for i in range(self.ideas_per_iter):
                draft = self._propose(query, evidence, variant=i)
                score = self.verifier.score(query, draft)
                draft.confidence = score
                candidates.append(draft)
                if best is None or score > best.confidence:
                    best = draft
            # early accept if any candidate meets threshold
            for d in candidates:
                if d.confidence >= self.accept_threshold:
                    if self._trace_enabled:
                        scores = ", ".join(f"{c.confidence:.2f}" for c in candidates)
                        self._trace_log.append(f"Iter {step+1}: accept early with scores [{scores}]")
                    if self.memory:
                        self.memory.remember(query, d.answer, True)
                    return d.answer, d.citations, d.confidence
            # refine: focus on top-evidence citations and expand for missing terms
            candidates.sort(key=lambda d: d.confidence, reverse=True)
            top = candidates[0]
            evidence = sorted(top.citations, key=lambda e: e.score, reverse=True)[:4]
            # attempt to expand retrieval using missing terms
            analyzer: Optional[Analyzer] = self.verifier if isinstance(self.verifier, Analyzer) else None
            missing: Set[str] = set()
            if analyzer is not None:
                try:
                    _score2, _covered, missing = analyzer.analyze(query, top)
                    for term in list(missing)[:2]:
                        extra = self.retriever.search(term, k=2)
                        evidence.extend(extra)
                except Exception:
                    pass
            if self._trace_enabled:
                scores = ", ".join(f"{c.confidence:.2f}" for c in candidates)
                miss = ", ".join(sorted(missing)) if missing else "-"
                self._trace_log.append(
                    f"Iter {step+1}: top={top.confidence:.2f} candidates=[{scores}] missing=[{miss}]"
                )
        assert best is not None
        if self.memory:
            self.memory.remember(query, best.answer, False)
        refusal = self._refusal(query, best)
        return refusal, best.citations, best.confidence

    def _propose(self, query: str, evidence: Iterable[Evidence], variant: int = 0) -> Draft:
        cites = list(evidence)[:4]
        if not cites:
            return Draft(
                answer=(
                    "I don’t have enough evidence to answer. Please provide more context "
                    "or allow me to consult additional sources."
                ),
                citations=[],
                confidence=0.0,
            )
        # Simple extractive synthesis
        summary_bits: List[str] = []
        for idx, ev in enumerate(cites):
            line = ev.snippet.strip().splitlines()[0]
            if self._inline_citations:
                line = f"{line} [{idx+1}]"
            # small variation in ordering selection per variant to diversify ideas
            if (idx + variant) % 2 == 0:
                summary_bits.append(line)
            else:
                summary_bits.insert(0, line)
        synthesis = " ".join(summary_bits)
        answer = f"Based on available evidence, {synthesis}"
        return Draft(answer=answer, citations=cites, confidence=0.0)

    def _refusal(self, query: str, draft: Draft) -> str:
        if not draft.citations:
            return (
                "I cannot answer confidently because I found no supporting evidence. "
                "I prefer to avoid guessing."
            )
        return (
            "I’m not fully confident in an answer grounded in evidence. "
            "Here’s what the sources suggest, but it may be incomplete: "
            + draft.answer
        )

    def get_trace(self) -> List[str]:
        """Return trace lines if tracing was enabled."""
        return list(self._trace_log)


@runtime_checkable
class Analyzer(Protocol):
    def analyze(self, query: str, draft: Draft) -> Tuple[float, Set[str], Set[str]]:
        ...

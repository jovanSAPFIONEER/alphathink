from __future__ import annotations

from typing import Set, Tuple

from .agent import Draft, Verifier


def _terms(text: str) -> Set[str]:
    return {t for t in (text.lower().split()) if t.isalnum() and len(t) > 2}


def _bigrams(text: str) -> Set[str]:
    toks = [t for t in text.lower().split() if t.isalnum() and len(t) > 2]
    return {f"{a} {b}" for a, b in zip(toks, toks[1:])}


class KeywordCoverageVerifier(Verifier):
    """Scores a draft by coverage of query terms in citations and answer."""

    def score(self, query: str, draft: Draft) -> float:
        # combine unigram and bigram coverage
        q1 = _terms(query)
        evidence_text = " \n".join(ev.snippet for ev in draft.citations)
        a_text = draft.answer + " " + evidence_text
        a1 = _terms(a_text)
        if not q1:
            return 0.0
        cov1 = len(q1.intersection(a1)) / max(1, len(q1))
        q2 = _bigrams(query)
        a2 = _bigrams(a_text)
        cov2 = (len(q2.intersection(a2)) / max(1, len(q2))) if q2 else 0.0
        # weight bigrams higher to reward phrasing alignment
        return min(1.0, 0.6 * cov2 + 0.4 * cov1)

    def analyze(self, query: str, draft: Draft) -> Tuple[float, Set[str], Set[str]]:
        """Return (score, covered_unigrams, missing_unigrams)."""
        q = _terms(query)
        evidence_text = " \n".join(ev.snippet for ev in draft.citations)
        a_text = draft.answer + " " + evidence_text
        a = _terms(a_text)
        covered_terms = q.intersection(a)
        missing_terms = q.difference(a)
        score = self.score(query, draft)
        return score, covered_terms, missing_terms

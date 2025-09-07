from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Dict, List, Tuple

from .agent import Evidence, Retriever


def _terms(text: str) -> List[str]:
    return [t for t in text.lower().split() if t.isalnum() and len(t) > 2]


class SimpleFSRetriever(Retriever):
    """BM25-like keyword retriever over .txt files in a directory (stdlib only)."""

    def __init__(self, corpus_dir: Path) -> None:
        self.corpus_dir = Path(corpus_dir)
        # index structures
        self._docs: Dict[str, Tuple[int, str]] = {}  # doc_id -> (length, first_line_snippet)
        self._tf: Dict[str, Dict[str, int]] = {}  # doc_id -> term -> freq
        self._df: Dict[str, int] = {}  # term -> document frequency
        self._num_docs: int = 0
        self._avgdl: float = 0.0
        self._idf: Dict[str, float] = {}
        self._build_index()

    def _build_index(self) -> None:
        if not self.corpus_dir.exists():
            return
        total_len = 0
        for root, _, files in os.walk(self.corpus_dir):
            for fn in files:
                if not fn.lower().endswith(".txt"):
                    continue
                p = str(Path(root) / fn)
                try:
                    text = Path(p).read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                toks = _terms(text)
                if not toks:
                    continue
                first_line = text.strip().splitlines()[0][:280] if text.strip() else ""
                self._docs[p] = (len(toks), first_line)
                total_len += len(toks)
                tfd: Dict[str, int] = {}
                for t in toks:
                    tfd[t] = tfd.get(t, 0) + 1
                self._tf[p] = tfd
                for t in set(toks):
                    self._df[t] = self._df.get(t, 0) + 1
        self._num_docs = len(self._docs)
        self._avgdl = (total_len / self._num_docs) if self._num_docs > 0 else 0.0
        # BM25 idf
        self._idf = {}
        if self._num_docs > 0:
            for t, df in self._df.items():
                # BM25+ style idf with 0.5 correction for stability
                self._idf[t] = math.log(1.0 + (self._num_docs - df + 0.5) / (df + 0.5))

    def search(self, query: str, k: int = 5) -> List[Evidence]:
        if self._num_docs == 0:
            return []
        q_terms = [t for t in _terms(query) if t in self._df]
        if not q_terms:
            return []
        k1 = 1.5
        b = 0.75
        scores: Dict[str, float] = {}
        for doc_id, (dl, _snippet) in self._docs.items():
            tfd = self._tf.get(doc_id, {})
            s = 0.0
            for t in q_terms:
                tf = tfd.get(t, 0)
                if tf == 0:
                    continue
                idf = self._idf.get(t, 0.0)
                denom = tf + k1 * (1 - b + b * (dl / (self._avgdl or 1.0)))
                s += idf * (tf * (k1 + 1)) / denom
            if s > 0:
                scores[doc_id] = s
        # sort and create Evidence
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
        results: List[Evidence] = []
        for doc_id, score in ranked:
            snippet = self._docs[doc_id][1]
            results.append(Evidence(source=doc_id, snippet=snippet, score=float(score)))
        return results

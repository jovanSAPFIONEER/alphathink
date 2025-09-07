from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from .agent import AlphaEvolveAgent, Draft
from .cli import build_agent
from .verifier import KeywordCoverageVerifier


def _load_dataset(p: Path) -> List[Dict[str, Any]]:
    if not p.exists():
        # built-in tiny dataset
        return [
            {
                "question": "What is alpha evolve?",
                "should_refuse": False,
            },
            {
                "question": "How to grow mangoes on Mars with lasers?",
                "should_refuse": True,
            },
        ]
    rows: List[Dict[str, Any]] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _terms(text: str) -> set[str]:
    return {t for t in text.lower().split() if t.isalnum() and len(t) > 2}


def _wilson_interval(successes: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    """Wilson score interval for a binomial proportion.

    Returns (low, high). Handles n=0 by returning (0.0, 0.0).
    """
    if n <= 0:
        return 0.0, 0.0
    phat = successes / n
    denom = 1 + (z * z) / n
    center = phat + (z * z) / (2 * n)
    margin = z * ((phat * (1 - phat) / n) + (z * z) / (4 * n * n)) ** 0.5
    low = max(0.0, (center - margin) / denom)
    high = min(1.0, (center + margin) / denom)
    return low, high


def evaluate(
    agent: AlphaEvolveAgent,
    data: Iterable[Dict[str, Any]],
    threshold: float,
) -> Dict[str, Any]:
    total = 0
    accepts = 0
    refusals = 0
    sum_score = 0.0
    sum_cov = 0.0
    examples: List[Dict[str, Any]] = []
    # Confusion matrix counts vs should_refuse ground truth
    tp_accept = 0  # accepted when should_refuse=False
    fp_accept = 0  # accepted when should_refuse=True (bad)
    tn_refuse = 0  # refused when should_refuse=True
    fn_refuse = 0  # refused when should_refuse=False (over-conservative)

    analyzer = agent.verifier if isinstance(agent.verifier, KeywordCoverageVerifier) else None

    for row in data:
        total += 1
        q = str(row.get("question") or row.get("query") or "")
        should_refuse = bool(row.get("should_refuse", False))
        ans, cites, score = agent.ask(q)

        accepted = score >= threshold
        accepts += 1 if accepted else 0
        refusals += 0 if accepted else 1
        sum_score += score
        # update confusion matrix
        if accepted and not should_refuse:
            tp_accept += 1
        elif accepted and should_refuse:
            fp_accept += 1
        elif (not accepted) and should_refuse:
            tn_refuse += 1
        else:
            fn_refuse += 1

        # coverage of query terms (proxy for support)
        if analyzer is not None:
            draft = Draft(answer=ans, citations=cites, confidence=score)
            cov, covered, missing = analyzer.analyze(q, draft)
        else:
            covered = _terms(q).intersection(_terms(ans + " " + " ".join(c.snippet for c in cites)))
            missing = _terms(q) - covered
            cov = min(1.0, len(covered) / max(1, len(covered) + len(missing)))
        sum_cov += cov

        examples.append(
            {
                "question": q,
                "accepted": accepted,
                "should_refuse": should_refuse,
                "score": score,
                "coverage": cov,
                "covered_terms": sorted(list(covered)),
                "missing_terms": sorted(list(missing)),
                "answer": ans,
                "citations": [
                    {
                        "source": c.source,
                        "snippet": c.snippet,
                        "score": c.score,
                    }
                    for c in cites
                ],
            }
        )

    # precision/recall (accept-as-positive)
    precision_den = tp_accept + fp_accept
    recall_den = tp_accept + fn_refuse
    precision = (tp_accept / precision_den) if precision_den else 0.0
    recall = (tp_accept / recall_den) if recall_den else 0.0
    # false acceptance rate among negatives (hallucination rate)
    total_neg = fp_accept + tn_refuse
    far = (fp_accept / total_neg) if total_neg else 0.0

    # 95% Wilson intervals
    precision_ci = _wilson_interval(tp_accept, precision_den)
    recall_ci = _wilson_interval(tp_accept, recall_den)
    far_ci = _wilson_interval(fp_accept, total_neg)

    return {
        "total": total,
        "accept_rate": accepts / total if total else 0.0,
        "refusal_rate": refusals / total if total else 0.0,
        "avg_score": sum_score / total if total else 0.0,
        "avg_query_coverage": sum_cov / total if total else 0.0,
        "precision_accept": precision,
        "precision_accept_ci": list(precision_ci),
        "recall_accept": recall,
        "recall_accept_ci": list(recall_ci),
        "false_accept_rate": far,
        "false_accept_rate_ci": list(far_ci),
        "confusion": {
            "tp_accept": tp_accept,
            "fp_accept": fp_accept,
            "tn_refuse": tn_refuse,
            "fn_refuse": fn_refuse,
            "total_positives": recall_den,
            "total_negatives": total_neg,
        },
        "examples": examples,
    }


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="alpha-evolve-eval", description="Evaluate the Alpha Evolve agent")
    p.add_argument("--dataset", type=Path, default=Path("data/eval.jsonl"), help="JSONL with {question, should_refuse?}")
    p.add_argument("--corpus", type=Path, default=Path("data/corpus"))
    p.add_argument("--iters", type=int, default=3)
    p.add_argument("--ideas", type=int, default=2)
    p.add_argument("--threshold", type=float, default=0.7)
    p.add_argument(
        "--sweep",
        type=str,
        default=None,
        help="Comma-separated thresholds (e.g., '0.5,0.6,0.7,0.8,0.9') to run a sweep",
    )
    p.add_argument("--out", type=Path, default=None, help="Write JSON report to this path")

    args = p.parse_args(argv)

    data = _load_dataset(args.dataset)

    if args.sweep:
        # Parse thresholds and run evaluate per threshold with a fresh agent
        try:
            thresholds = [float(x.strip()) for x in args.sweep.split(",") if x.strip()]
        except ValueError:
            raise SystemExit("--sweep must be a comma-separated list of floats, e.g., 0.5,0.6,0.7")
        sweep_reports: List[Dict[str, Any]] = []
        print("threshold\tprecision\tprecision_ci\trecall\trecall_ci\tFAR\tFAR_ci\taccept_rate\trefusal_rate")
        for th in thresholds:
            agent = build_agent(args.corpus, max_iters=args.iters, ideas=args.ideas, accept_threshold=th)
            rpt = evaluate(agent, data, threshold=th)
            sweep_reports.append({"threshold": th, **rpt})
            print(
                f"{th:.2f}\t{rpt['precision_accept']:.3f}\t{tuple(rpt['precision_accept_ci'])}"
                f"\t{rpt['recall_accept']:.3f}\t{tuple(rpt['recall_accept_ci'])}"
                f"\t{rpt['false_accept_rate']:.3f}\t{tuple(rpt['false_accept_rate_ci'])}"
                f"\t{rpt['accept_rate']:.3f}\t{rpt['refusal_rate']:.3f}"
            )
        out_obj = {"sweep": sweep_reports}
        text = json.dumps(out_obj, indent=2)
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text, encoding="utf-8")
            print(str(args.out))
        else:
            print(text)
    else:
        agent = build_agent(args.corpus, max_iters=args.iters, ideas=args.ideas, accept_threshold=args.threshold)
        report = evaluate(agent, data, threshold=args.threshold)
        text = json.dumps(report, indent=2)
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text, encoding="utf-8")
            print(str(args.out))
        else:
            print(text)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

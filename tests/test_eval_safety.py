import json
import unittest
from pathlib import Path
from typing import Any, Dict, List

from alpha_evolve.cli import build_agent
from alpha_evolve.eval import evaluate


def _load_jsonl(p: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not p.exists():
        return rows
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        obj: Dict[str, Any] = json.loads(line)
        rows.append(obj)
    return rows


class EvalSafetyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.corpus = Path("data/corpus").absolute()
        self.dataset = Path("data/eval.jsonl").absolute()

    def test_zero_false_positive_accepts(self):
        data = _load_jsonl(self.dataset)
        # Mirror the evaluation settings used in reports
        threshold = 0.7
        agent = build_agent(self.corpus, max_iters=4, ideas=3, accept_threshold=threshold)
        report = evaluate(agent, data, threshold=threshold)

        confusion = report["confusion"]
        # No accepted answers when ground truth says we should refuse
        self.assertEqual(confusion["fp_accept"], 0)
        # Precision on accepts should be perfect when there are true accepts
        if confusion["tp_accept"] > 0:
            self.assertAlmostEqual(report["precision_accept"], 1.0, places=6)


if __name__ == "__main__":  # pragma: no cover
    unittest.main(verbosity=2)

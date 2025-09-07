import unittest
from pathlib import Path

from alpha_evolve.cli import build_agent


class TestAlphaEvolve(unittest.TestCase):
    def setUp(self) -> None:
        self.corpus = Path("data/corpus").absolute()

    def test_accepts_when_terms_covered(self):
        agent = build_agent(self.corpus, max_iters=2, accept_threshold=0.4)
        answer, cites, score = agent.ask("What is alpha evolve?")
        self.assertGreaterEqual(score, 0.4)
        self.assertTrue(cites)
        self.assertIn("evidence", answer.lower())

    def test_refuses_when_no_evidence(self):
        agent = build_agent(self.corpus, max_iters=2, accept_threshold=0.8)
        answer, _, score = agent.ask("How to grow mangoes on Mars with lasers?")
        # High threshold means likely refusal
        self.assertLess(score, 0.8)
        self.assertIn("confident", answer.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)

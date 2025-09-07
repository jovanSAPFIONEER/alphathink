# alphathink v0.1.0

Alpha Evolve: evidence-first anti-hallucination agent.

Highlights
- Zero false-positive acceptances on the labeled dataset (precision=1.0; FAR=0.0) with Wilson 95% CIs.
- Threshold sweep shows precision stays at 1.0 while recall is tunable.
- Dependency-free Python; reproducible via scripts/reproduce.ps1.

Components
- Alpha Evolve (agent, retriever, verifier, CLI, eval harness)
- QuickCapture (notes/tasks CLI)

See docs/RESULTS.md for metrics and reproduction steps.
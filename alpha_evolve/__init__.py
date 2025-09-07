"""
Alpha Evolve: a minimal anti-hallucination agent.

It iterates: plan -> retrieve -> propose -> verify -> refine, and refuses to
answer when the evidence is insufficient. Pure standard library.
"""

from .version import __version__

__all__ = ["__version__"]

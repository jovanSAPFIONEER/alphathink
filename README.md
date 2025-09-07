# Alpha Evolve + QuickCapture

[![CI](https://github.com/jovanSAPFIONEER/alphathink/actions/workflows/ci.yml/badge.svg)](https://github.com/jovanSAPFIONEER/alphathink/actions/workflows/ci.yml)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17072907.svg)](https://doi.org/10.5281/zenodo.17072907)

This repo contains two small, dependency-free Python CLIs:

- Alpha Evolve: an evidence-first anti-hallucination agent that iterates retrieve → propose → verify → refine and refuses when support is weak.
- QuickCapture: a fast notes/tasks CLI backed by local SQLite.

Both run directly from source on any standard Python 3 environment.

## Alpha Evolve (anti-hallucination)

One-minute pitch: Avoid hallucinations by only accepting answers when they are supported by retrieved evidence; otherwise refuse. The loop generates multiple ideas, verifies (unigram+bigram coverage), and refines retrieval toward missing terms. All answers include citations; `--trace` prints per-iteration diagnostics.

Quick start:

```
python -m alpha_evolve --demo
python -m alpha_evolve "What is alpha evolve?" --corpus data/corpus --iters 4 --ideas 3 --threshold 0.7 --trace
```

Reproducible results: See `docs/RESULTS.md` for metrics (acceptance, coverage) and how to regenerate the reports.

## QuickCapture (notes/tasks)

Run directly from source:

```
python -m quickcapture --help
```

Install (editable):

```
python -m pip install -e .
```

Default DB location

- Windows: `%USERPROFILE%/.quickcapture/quickcapture.db`

Override with `--db PATH` on any command.

Commands

- add-note, add-task, list, complete-task, export

Examples

```
python -m quickcapture add-note "Meeting" --content "Discuss roadmap"
python -m quickcapture add-task "Pay bills" --due 2025-09-10
python -m quickcapture list --type all
python -m quickcapture complete-task 1
python -m quickcapture export --out data/export.json
```

## Testing

```
python -m unittest -v
```

## Releases and citation

- GitHub Releases: https://github.com/jovanSAPFIONEER/alphathink/releases
- Cite: see `CITATION.cff`
- Zenodo: enable GitHub -> Zenodo integration, then create a GitHub release tag (e.g., `v0.1.0`) to mint a DOI.

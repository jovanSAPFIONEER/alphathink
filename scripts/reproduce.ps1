# Reproducibility script for Windows PowerShell
# Usage: ./scripts/reproduce.ps1

$ErrorActionPreference = "Stop"

Write-Host "Running unit tests..."
python -m unittest -v

Write-Host "Running evaluations..."
python -m alpha_evolve.eval --dataset data/eval.jsonl --corpus data/corpus --iters 1 --ideas 1 --threshold 0.7 --out data/report_baseline.json
python -m alpha_evolve.eval --dataset data/eval.jsonl --corpus data/corpus --iters 4 --ideas 3 --threshold 0.7 --out data/report_rethink.json
python -m alpha_evolve.eval --dataset data/eval.jsonl --corpus data/corpus --iters 4 --ideas 3 --threshold 0.7 --out data/report_rethink_bm25.json

Write-Host "Running threshold sweep (precision/recall/FAR with Wilson CIs)..."
python -m alpha_evolve.eval --dataset data/eval.jsonl --corpus data/corpus --iters 4 --ideas 3 --sweep "0.5,0.6,0.7,0.8,0.9" --out data/report_sweep.json

Write-Host "Done. Reports: data/report_baseline.json, data/report_rethink.json, data/report_rethink_bm25.json, data/report_sweep.json"

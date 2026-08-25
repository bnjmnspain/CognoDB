#!/bin/bash
set -e
echo "Setting up Graph Database Benchmark..."
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
echo "Setup complete. Edit config/databases.yaml with your credentials, then run: python scripts/run_benchmark.py"

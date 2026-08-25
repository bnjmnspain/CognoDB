@echo off
echo Setting up Graph Database Benchmark...
python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt
echo Setup complete. Edit config\databases.yaml with your credentials, then run: python scripts\run_benchmark.py

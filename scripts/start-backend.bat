@echo off
echo Starting GARUDA Backend...
cd backend
python -m venv venv
call venv\Scripts\activate
pip install -e ".[dev]"
python migrate.py
uvicorn main:app --reload --host 0.0.0.0 --port 8000

@echo off
echo Running GARUDA Backend Tests...
cd backend
pytest -v --tb=short

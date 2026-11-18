@echo off
cd /d %~dp0
if exist .update (
  .venv\Scripts\python.exe core\updater.py %~dp0app.py
  exit /b
)
set OLLAMA_MODELS=%~dp0modelos
start "" .venv\Scripts\python.exe app.py

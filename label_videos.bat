@echo off
cd /d "%~dp0"
"%~dp0venv\Scripts\python.exe" "%~dp0tools\label_video.py"
if errorlevel 1 pause

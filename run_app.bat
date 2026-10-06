@echo off
cd /d "%~dp0"
if not exist "venv\Scripts\pythonw.exe" (
    echo Chua co venv. Xem huong dan cai dat trong README.md.
    pause
    exit /b 1
)
start "" "%~dp0venv\Scripts\pythonw.exe" "%~dp0python_app\gui.py"

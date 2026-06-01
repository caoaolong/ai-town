@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
  echo 未找到 .venv，请先执行: python -m venv .venv
  exit /b 1
)

call .venv\Scripts\activate.bat

echo Installing dependencies...
python -m pip install -r requirements.txt

echo.
echo Starting AI Town Server...
python main.py

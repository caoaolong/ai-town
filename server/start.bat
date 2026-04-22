@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Starting AI Town Server...
python main.py

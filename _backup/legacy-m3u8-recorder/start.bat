@echo off
cd /d "%~dp0"

if not exist venv (
    echo [Setup] Dang tao moi truong ao Python lan dau...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo [Setup] Dang kiem tra thu vien...
pip install -r requirements.txt -q

echo.
echo ============================================
echo   Bigo Recorder dang chay tai:
echo   http://127.0.0.1:5000
echo ============================================
echo.

start "" http://127.0.0.1:5000
python app.py

pause

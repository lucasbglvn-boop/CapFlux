@echo off
setlocal
cd /d "%~dp0"

rem UTF-8 so Vietnamese log messages don't blow up on a legacy code page
chcp 65001 >nul 2>nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo ============================================
echo   TOOL - Quay livestream Bigo ^& TikTok
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [LOI] Khong tim thay Python.
    echo       Tai Python 3.10 tro len tai: https://www.python.org/downloads/
    echo       Nho tich "Add Python to PATH" khi cai dat.
    echo.
    pause
    exit /b 1
)

if not exist "venv\Scripts\python.exe" (
    echo [Setup] Dang tao moi truong Python lan dau, co the mat 1-2 phut...
    python -m venv venv
)

call "venv\Scripts\activate.bat"

echo [Setup] Dang kiem tra thu vien...
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q

where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo.
    echo [CANH BAO] Khong tim thay ffmpeg trong PATH.
    echo             Bigo can ffmpeg de quay duoc video.
    echo             Tai tai: https://www.gyan.dev/ffmpeg/builds/
    echo             Giai nen, roi them thu muc "bin" vao PATH cua Windows.
    echo.
)

echo.
echo ============================================
echo   TOOL dang chay tai: http://127.0.0.1:5000
echo   De tat: dong cua so nay hoac bam Ctrl+C
echo ============================================
echo.

start "" http://127.0.0.1:5000
python -m uvicorn main:app --host 127.0.0.1 --port 5000

echo.
echo TOOL da dung.
pause

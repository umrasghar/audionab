@echo off
:: ============================================
::  AudioNab — Build standalone .exe
:: ============================================
::  Requirements: Python 3.8+
::  Output: dist\AudioNab.exe
:: ============================================

echo.
echo   AudioNab — Building standalone executable...
echo.

python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo   [ERROR] Python not found. Install from python.org
    pause
    exit /b 1
)

echo   [1/4] Installing build dependencies...
pip install -r requirements.txt pyinstaller --quiet

echo   [2/4] Downloading FFmpeg (if needed)...
python scripts/download_ffmpeg.py

echo   [3/4] Building AudioNab.exe...
set PYINSTALLER_ARGS=--onefile --windowed --name "AudioNab" --collect-all customtkinter --add-data "audionab;audionab" --clean

:: Include FFmpeg if downloaded
if exist ffmpeg\ffmpeg.exe (
    echo   Including bundled FFmpeg...
    set PYINSTALLER_ARGS=%PYINSTALLER_ARGS% --add-data "ffmpeg;ffmpeg"
)

pyinstaller %PYINSTALLER_ARGS% audionab.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo   [ERROR] Build failed!
    pause
    exit /b 1
)

echo   [4/4] Done!
echo.
echo   ============================================
echo    AudioNab.exe built successfully!
echo   ============================================
echo.
echo    Location: dist\AudioNab.exe
echo.
echo    Double-click to launch, or move it anywhere.
echo    Use Settings to install the right-click menu.
echo.
echo    To build installer: iscc installer.iss
echo.
pause

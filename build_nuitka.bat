@echo off
:: ============================================
::  AudioNab - Build standalone .exe (Nuitka)
:: ============================================
::  Requirements: Python 3.8+, C compiler (MSVC or MinGW)
::  Output: dist\AudioNab.exe
:: ============================================

echo.
echo   AudioNab - Building standalone executable (Nuitka)...
echo.

python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo   [ERROR] Python not found. Install from python.org
    pause
    exit /b 1
)

echo   [1/5] Installing build dependencies...
pip install -r requirements.txt nuitka ordered-set zstandard --quiet

echo   [2/5] Downloading FFmpeg (if needed)...
python scripts/download_ffmpeg.py

echo   [3/5] Generating app icons (if needed)...
python scripts/generate_icon.py

echo   [4/5] Building AudioNab.exe with Nuitka...

set NUITKA_ARGS=--standalone --onefile
set NUITKA_ARGS=%NUITKA_ARGS% --windows-console-mode=disable
set NUITKA_ARGS=%NUITKA_ARGS% --enable-plugin=tk-inter
set NUITKA_ARGS=%NUITKA_ARGS% --include-package=customtkinter
set NUITKA_ARGS=%NUITKA_ARGS% --include-package-data=customtkinter
set NUITKA_ARGS=%NUITKA_ARGS% --include-package=windnd
set NUITKA_ARGS=%NUITKA_ARGS% --include-package=pystray
set NUITKA_ARGS=%NUITKA_ARGS% --include-package=PIL
set NUITKA_ARGS=%NUITKA_ARGS% --include-package=watchdog
set NUITKA_ARGS=%NUITKA_ARGS% --include-package=httpx
set NUITKA_ARGS=%NUITKA_ARGS% --include-package=httpcore
set NUITKA_ARGS=%NUITKA_ARGS% --include-package=h11
set NUITKA_ARGS=%NUITKA_ARGS% --include-package=anyio
set NUITKA_ARGS=%NUITKA_ARGS% --include-package=sniffio
set NUITKA_ARGS=%NUITKA_ARGS% --include-package=certifi
set NUITKA_ARGS=%NUITKA_ARGS% --include-package=idna
set NUITKA_ARGS=%NUITKA_ARGS% --include-package=audionab
set NUITKA_ARGS=%NUITKA_ARGS% --include-data-dir=audionab=audionab
set NUITKA_ARGS=%NUITKA_ARGS% --include-data-dir=assets=assets
set NUITKA_ARGS=%NUITKA_ARGS% --output-dir=dist
set NUITKA_ARGS=%NUITKA_ARGS% --output-filename=AudioNab.exe
set NUITKA_ARGS=%NUITKA_ARGS% --remove-output
set NUITKA_ARGS=%NUITKA_ARGS% --assume-yes-for-downloads
set NUITKA_ARGS=%NUITKA_ARGS% --company-name=AudioNab
set NUITKA_ARGS=%NUITKA_ARGS% --product-name=AudioNab
set NUITKA_ARGS=%NUITKA_ARGS% --product-version=2.5.0
set NUITKA_ARGS=%NUITKA_ARGS% --file-description="AudioNab - Lightweight Audio Extractor"

:: Include app icon
if exist assets\icon.ico (
    set NUITKA_ARGS=%NUITKA_ARGS% --windows-icon-from-ico=assets/icon.ico
)

:: Include FFmpeg if downloaded
if exist ffmpeg\ffmpeg.exe (
    echo   Including bundled FFmpeg...
    set NUITKA_ARGS=%NUITKA_ARGS% --include-data-files=ffmpeg/ffmpeg.exe=ffmpeg/ffmpeg.exe
)
if exist ffmpeg\ffprobe.exe (
    set NUITKA_ARGS=%NUITKA_ARGS% --include-data-files=ffmpeg/ffprobe.exe=ffmpeg/ffprobe.exe
)

python -m nuitka %NUITKA_ARGS% audionab.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo   [ERROR] Nuitka build failed!
    echo.
    echo   Troubleshooting:
    echo     - Ensure a C compiler is installed (MSVC or MinGW-w64)
    echo     - Run: pip install nuitka --upgrade
    echo     - Try: python -m nuitka --help
    echo     - Fallback: build_pyinstaller.bat
    echo.
    pause
    exit /b 1
)

echo   [5/5] Done!
echo.
echo   ============================================
echo    AudioNab.exe built successfully! (Nuitka)
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

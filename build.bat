@echo off
:: Delegates to Nuitka build. Use build_pyinstaller.bat for PyInstaller fallback.
call "%~dp0build_nuitka.bat" %*

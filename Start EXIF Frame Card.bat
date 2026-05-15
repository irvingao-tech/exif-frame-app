@echo off
setlocal

cd /d "%~dp0"

set "PYTHONW=%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe"
if exist "%PYTHONW%" (
    start "EXIF Frame Card" "%PYTHONW%" "%~dp0main.py"
    exit /b 0
)

where py >nul 2>nul
if not errorlevel 1 (
    start "EXIF Frame Card" py -3 "%~dp0main.py"
    exit /b 0
)

where python >nul 2>nul
if not errorlevel 1 (
    start "EXIF Frame Card" python "%~dp0main.py"
    exit /b 0
)

echo Python was not found. Please install Python 3.11 or add Python to PATH.
pause
exit /b 1

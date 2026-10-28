@echo off
cd /d "%~dp0"

rem Launcher for VMD camera adjust tool (double-click to run)
rem UI language follows the Windows system language (Chinese / English).
rem To force a language, run: python vmd_camera_tool.py --lang en  (or --lang zh)

where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw vmd_camera_tool.py
    exit /b 0
)

where python >nul 2>nul
if %errorlevel%==0 (
    python vmd_camera_tool.py
    if errorlevel 1 pause
    exit /b 0
)

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 vmd_camera_tool.py
    if errorlevel 1 pause
    exit /b 0
)

echo [ERROR] Python not found. Please install Python 3 first.
pause

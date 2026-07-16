@echo off
title Employee Monitor - Master Build
color 0B
cls

echo ================================================
echo    Employee Monitor - Master Build Script
echo ================================================
echo.

echo [STEP 1/5] Cleaning old builds...
if exist "dist" rmdir /S /Q "dist"
if exist "build" rmdir /S /Q "build"
if exist "..\installer_output" rmdir /S /Q "..\installer_output"
mkdir "..\installer_output" 2>nul
echo [OK] Cleaned!

echo.
echo [STEP 2/5] Installing build tools...
pip install pyinstaller --quiet
echo [OK] Build tools ready!

echo.
echo [STEP 3/5] Building EmployeeMonitor_Setup.exe...
echo This will take 2-3 minutes...
echo.

pyinstaller --onefile --windowed --name "EmployeeMonitor_Setup" ^
    --hidden-import=pystray ^
    --hidden-import=PIL ^
    --hidden-import=PIL._tkinter_finder ^
    --hidden-import=pynput ^
    --hidden-import=pynput._util.win32 ^
    --hidden-import=psutil ^
    --hidden-import=mss ^
    --hidden-import=mss.tools ^
    --hidden-import=requests ^
    --hidden-import=engineio ^
    --hidden-import=engineio.async_drivers ^
    --hidden-import=socketio ^
    --collect-all pystray ^
    --collect-all PIL ^
    setup_gui.py

if %errorlevel% neq 0 (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)
echo [OK] EmployeeMonitor_Setup.exe built!

echo.
echo [STEP 4/5] Copying installer files...
copy /Y dist\EmployeeMonitor_Setup.exe "..\installer_output\" >nul
copy /Y install.bat "..\installer_output\" >nul
copy /Y uninstall.bat "..\installer_output\" >nul
echo [OK] Files copied!

echo.
echo [STEP 5/5] Creating distribution package...

cd "..\installer_output"

echo.
echo ================================================
echo    BUILD COMPLETE!
echo ================================================
echo.
echo Output files in: installer_output\
echo.
echo FOR EMPLOYEES (Simple - No Python needed):
echo   - EmployeeMonitor_Setup.exe (run this)
echo.
echo FOR IT TEAM (Manual install):
echo   - install.bat (auto-installs everything)
echo   - uninstall.bat (removes everything)
echo.
echo ================================================
echo.
echo Employee ko sirf EmployeeMonitor_Setup.exe dena hai!
echo.

cd "..\agent"
pause

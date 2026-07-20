@echo off
echo ==========================================
echo   Employee Monitor - Build .exe
echo ==========================================
echo.

echo [1/4] Installing PyInstaller...
pip install pyinstaller 2>nul

echo [2/4] Building setup_gui.exe (Setup Window)...
pyinstaller --onefile --windowed --name "EmployeeMonitor_Setup" ^
    --icon=NUL ^
    --add-data "config.json;." ^
    --hidden-import=pystray ^
    --hidden-import=PIL ^
    --hidden-import=pynput ^
    --hidden-import=psutil ^
    --hidden-import=mss ^
    --hidden-import=mss.tools ^
    --hidden-import=requests ^
    setup_gui.py

echo [3/4] Building monitor_agent.exe (Background Agent)...
pyinstaller --onefile --windowed --name "MonitorAgent" ^
    --icon=NUL ^
    --add-data "config.json;." ^
    --hidden-import=pystray ^
    --hidden-import=PIL ^
    --hidden-import=pynput ^
    --hidden-import=psutil ^
    --hidden-import=mss ^
    --hidden-import=mss.tools ^
    --hidden-import=requests ^
    main.py

echo [4/4] Creating installer folder...
mkdir "..\installer_output" 2>nul
copy dist\EmployeeMonitor_Setup.exe "..\installer_output\" 2>nul
copy dist\MonitorAgent.exe "..\installer_output\" 2>nul
copy config.json "..\installer_output\" 2>nul

echo.
echo ==========================================
echo   Build Complete!
echo ==========================================
echo.
echo Output files:
echo   - installer_output\EmployeeMonitor_Setup.exe
echo   - installer_output\MonitorAgent.exe
echo.
echo Employee ko sirf EmployeeMonitor_Setup.exe dena hai!
echo.
pause

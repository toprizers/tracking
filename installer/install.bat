@echo off
title Employee Monitor - Installer
color 0A
cls

echo ================================================
echo    Employee Monitor - Auto Installer
echo ================================================
echo.
echo This will install Employee Monitor on your system.
echo It will take 2-3 minutes.
echo.
echo Press any key to start...
pause >nul

echo.
echo [1/6] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found! Installing Python automatically...
    
    echo Downloading Python 3.11...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\python_installer.exe'}"
    
    echo Installing Python (this may take a minute)...
    %TEMP%\python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    timeout /t 60 /nobreak >nul
    
    echo Refreshing environment...
    set PATH=%PATH%;C:\Python311;C:\Python311\Scripts
    
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ERROR: Python installation failed.
        echo Please install Python manually from https://python.org
        echo Make sure to check "Add Python to PATH" during installation.
        pause
        exit /b 1
    )
)
echo [OK] Python is ready!

echo.
echo [2/6] Installing required libraries...
pip install mss Pillow pynput psutil requests pystray --quiet
echo [OK] Libraries installed!

echo.
echo [3/6] Creating application folder...
if not exist "%APPDATA%\EmployeeMonitor" mkdir "%APPDATA%\EmployeeMonitor"

echo.
echo [4/6] Copying files...
copy /Y "%~dp0main.py" "%APPDATA%\EmployeeMonitor\" >nul
copy /Y "%~dp0capture.py" "%APPDATA%\EmployeeMonitor\" >nul
copy /Y "%~dp0activity.py" "%APPDATA%\EmployeeMonitor\" >nul
copy /Y "%~dp0uploader.py" "%APPDATA%\EmployeeMonitor\" >nul
copy /Y "%~dp0tray.py" "%APPDATA%\EmployeeMonitor\" >nul
echo [OK] Files copied!

echo.
echo [5/6] Opening configuration...
echo.
echo ================================================
echo    Please enter your Server URL and Agent Key
echo ================================================
echo.

set /p SERVER_URL="Server URL (e.g., http://your-server.com:5000): "
set /p AGENT_KEY="Agent Key: "

echo.
echo Saving configuration...

(
echo {
echo     "server_url": "%SERVER_URL%",
echo     "agent_key": "%AGENT_KEY%",
echo     "screenshot_interval": 1800,
echo     "idle_threshold": 900,
echo     "activity_check_interval": 60,
echo     "input_test_interval": 300,
echo     "max_retries": 3,
echo     "retry_delay": 10
echo }
) > "%APPDATA%\EmployeeMonitor\config.json"

echo [OK] Configuration saved!

echo.
echo [6/6] Setting up auto-start...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "EmployeeMonitor" /t REG_SZ /d "pythonw \"%APPDATA%\EmployeeMonitor\main.py\"" /f >nul 2>&1
echo [OK] Auto-start enabled!

echo.
echo ================================================
echo    Installation Complete!
echo ================================================
echo.
echo Starting Employee Monitor...

start /B pythonw "%APPDATA%\EmployeeMonitor\main.py"

echo.
echo Employee Monitor is now running!
echo You will see a green icon in system tray.
echo.
echo You can close this window.
echo.
timeout /t 5 /nobreak >nul

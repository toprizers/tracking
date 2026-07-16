@echo off
title Employee Monitor - Uninstaller
color 0C
cls

echo ================================================
echo    Employee Monitor - Uninstaller
echo ================================================
echo.
echo This will completely remove Employee Monitor.
echo.
echo Press any key to uninstall...
pause >nul

echo.
echo [1/4] Stopping agent...
taskkill /F /IM MonitorAgent.exe >nul 2>&1
taskkill /F /IM main.py >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/4] Removing auto-start...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "EmployeeMonitor" /f >nul 2>&1

echo [3/4] Deleting files...
if exist "%APPDATA%\EmployeeMonitor" rmdir /S /Q "%APPDATA%\EmployeeMonitor"

echo [4/4] Cleanup complete!

echo.
echo ================================================
echo    Uninstall Complete!
echo ================================================
echo.
echo Employee Monitor has been removed from your system.
echo.
timeout /t 5 /nobreak >nul

@echo off
echo ========================================
echo   Employee Monitor - Local Setup
echo ========================================

echo [1/4] Creating virtual environment...
cd server
python -m venv venv
call venv\Scripts\activate

echo [2/4] Installing dependencies...
pip install -r requirements.txt

echo [3/4] Creating uploads directory...
mkdir uploads 2>nul

echo [4/4] Starting server...
echo.
echo Server will start at: http://localhost:5000
echo.
echo Default login:
echo   Username: admin
echo   Password: admin123
echo.
python app.py
pause

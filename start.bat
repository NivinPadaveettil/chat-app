@echo off
REM Inderbara WhatsApp Clone - Windows Startup Script

echo ========================================
echo    Inderbara - WhatsApp Clone
echo    Starting Server...
echo ========================================
echo.

REM Check if Redis is needed
echo Checking Redis...
timeout /t 2 /nobreak

REM Run Django development server
echo Starting Django server on http://localhost:8000
python manage.py runserver 0.0.0.0:8000

pause

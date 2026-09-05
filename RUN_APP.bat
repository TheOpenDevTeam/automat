@echo off
title AUTOMAT - Task Automation Manager
echo ========================================
echo AUTOMAT - Task Automation Manager
echo ========================================
echo.
echo Приложение запускается...
echo.
cd /d "%~dp0\automat"
set PYTHONIOENCODING=utf-8
python main.py
pause

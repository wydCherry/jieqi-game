@echo off
chcp 65001 >nul
cd /d "%~dp0"
python main.py
if %errorlevel% neq 0 pause
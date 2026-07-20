@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================
echo        揭棋对战 - 打包工具
echo ==========================================
echo.
echo 正在检查 PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller 未安装，正在安装...
    pip install pyinstaller -q
)

echo.
echo 正在打包游戏...
python build_exe.py

echo.
pause
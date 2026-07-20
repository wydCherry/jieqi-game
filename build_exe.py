# -*- coding: utf-8 -*-
"""
揭棋游戏打包脚本
使用 PyInstaller 打包成 Windows 可执行文件
"""

import PyInstaller.__main__
import os
import shutil

# 项目路径
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_FILE = os.path.join(PROJECT_DIR, 'main.py')

# 打包配置
PyInstaller.__main__.run([
    MAIN_FILE,
    '--name=揭棋对战',
    '--onefile',
    '--windowed',
    '--clean',
    '--noconfirm',
    f'--distpath={os.path.join(PROJECT_DIR, "dist")}',
    f'--workpath={os.path.join(PROJECT_DIR, "build")}',
    f'--specpath={PROJECT_DIR}',
])

print("\n" + "=" * 50)
print("打包完成!")
print(f"可执行文件位置: {os.path.join(PROJECT_DIR, 'dist', '揭棋对战.exe')}")
print("=" * 50)
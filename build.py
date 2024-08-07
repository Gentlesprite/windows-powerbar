# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/4/1 14:27
# File:build
import os
# 最好使用虚拟环境打包
import PyInstaller.__main__

py_name = "powerbar.py"
icon_path = r"img\powercfg.ico"
upx_dir = r"D:\env\upx\upx-4.2.3-win64"
version_file = os.path.join(os.getcwd(), 'file_version_info.txt')

PyInstaller.__main__.run([
    '--upx-dir', upx_dir,
    '-F',
    '-w',
    '-i', icon_path,
    '--version-file', version_file,
    py_name
])

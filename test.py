# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/3/29 19:04
# File:test

nuitka --windows-icon-from-ico="D:\files\Documents\study\python\Program\windows_power_manager\img\powercfg.ico" powerbar.py --disable-console --standalone --file-version=1.0 --onefile --enable-plugin=pyside2 --include-data-files="D:\files\Documents\study\python\Program\windows_power_manager\img\powercfg.ico=@powercfg.ico" --copyright="Copyright (C) 2024 Gentlesprite."

pyinstaller --upx-dir "D:\env\upx\upx-4.2.3-win64" -F -w -i "D:\files\Documents\study\python\Program\windows_power_manager\img\powercfg.ico" powerbar.py
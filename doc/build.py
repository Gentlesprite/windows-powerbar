# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/3/27 1:56
# File:build

cmd ="""

nuitka --windows-icon-from-ico="powercfg.ico" powerbar.py --disable-console --standalone --file-version=1.0 --onefile --enable-plugin=pyside2 --include-data-files="D:\files\Documents\study\python\Program\windows_power_manager\powercfg.ico=@powercfg.ico" --copyright="Copyright (C) 2024 Gentlesprite."

"""

import os
import sys
os.system(cmd)
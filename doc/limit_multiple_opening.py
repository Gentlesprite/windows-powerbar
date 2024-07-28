# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/7/28 19:53
# File:limit_multiple_opening
import sys
from PySide6.QtCore import QSharedMemory

share = QSharedMemory('powerbar')
if share.attach():
    print('软件已存在,不能多开!')
    "检测到多开时候的处理逻辑"
if share.create(1):
    "软件启动逻辑"

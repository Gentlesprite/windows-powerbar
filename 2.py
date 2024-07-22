# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/3/30 20:35
# File:2

import sys

from PyQt5.QtCore import QSharedMemory
from PyQt5.QtWidgets import *


def runWindow():
    app = QApplication(sys.argv)
    share = QSharedMemory()
    share.setKey("main_window")
    if share.attach():
        msg_box = QMessageBox()
        msg_box.setWindowTitle("提示")
        msg_box.setText("软件已在运行!")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.addButton("确定", QMessageBox.YesRole)
        msg_box.exec()
        sys.exit(-1)
    if share.create(1):
        win = QWidget()
        win.resize(450, 150)
        win.move(0, 300)
        win.setWindowTitle('测试')
        win.show()
        sys.exit(app.exec_())


if __name__ == '__main__':
    runWindow()
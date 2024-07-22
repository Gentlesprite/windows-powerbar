# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/3/30 20:35
# File:2
# from PySide2.QtWidgets import *
# from PySide2.QtGui import QIcon
# from qfluentwidgets import SystemTrayMenu,Action
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QHBoxLayout, QLabel

from qfluentwidgets import Action, SystemTrayMenu, MessageBox, setTheme, Theme
class SystemTrayIcon(QSystemTrayIcon):

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.setIcon(parent.windowIcon())

        self.menu = SystemTrayMenu(parent=parent)
        self.menu.addActions([
            Action('🎤   唱'),
            Action('🕺   跳'),
            Action('🤘🏼   RAP'),
            Action('🎶   Music'),
            Action('🏀   篮球', triggered=self.ikun),
        ])
        self.setContextMenu(self.menu)

    def ikun(self):
        print("""巅峰产生虚伪的拥护，黄昏见证真正的使徒 🏀

                       ⠰⢷⢿⠄
                   ⠀⠀⠀⠀⠀⣼⣷⣄
                   ⠀⠀⣤⣿⣇⣿⣿⣧⣿⡄
                   ⢴⠾⠋⠀⠀⠻⣿⣷⣿⣿⡀
                   ⠀⢀⣿⣿⡿⢿⠈⣿
                   ⠀⠀⠀⢠⣿⡿⠁⠀⡊⠀⠙
                   ⠀⠀⠀⢿⣿⠀⠀⠹⣿
                   ⠀⠀⠀⠀⠹⣷⡀⠀⣿⡄
                   ⠀⠀⠀⠀⣀⣼⣿⠀⢈⣧
        """)


class Demo(QWidget):

    def __init__(self):
        super().__init__()
        self.setLayout(QHBoxLayout())
        self.label = QLabel('Right-click system tray icon', self)
        self.layout().addWidget(self.label)

        self.resize(500, 500)
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))

        self.systemTrayIcon = SystemTrayIcon(self)
        self.systemTrayIcon.show()
if __name__ == '__main__':
    app = QApplication([])
    dm = Demo()
    dm.show()
    app.exec_()
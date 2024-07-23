# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/7/23 19:35
# File:read_res
"""
读取res资源文件中的内容转换为图片显示或生成文件路径
"""
from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import QMainWindow, QLabel
import PySide2


# 处理QIcon对象将它显示在窗口上,相当于打开编译好的资源进行读取查看
class ImageView(QMainWindow):
    def __init__(self, image: PySide2.QtGui.QIcon, title_icon: PySide2.QtGui.QPixmap.QIcon):
        super(ImageView, self).__init__()
        self.setWindowIcon(title_icon)
        self.setWindowTitle('窗口标题')
        self.label = QLabel(self)
        self.label.setScaledContents(True)  # 让图片自适应 QLabel 大小
        self.label.setPixmap(image)
        self.setCentralWidget(self.label)  # 将 QLabel 设置为主窗口的中央部件
        self.adjustSize()  # 调整窗口大小以适应图片大小
        self.show()


# 用法:
iv = ImageView(image_icon='需要显示图片', title_icon='标题图片')


# 也支持QPixmap对象的图片,传入时候转换即可
class ImageView(QMainWindow):
    def __init__(self, image: PySide2.QtGui.QPixmap, title_icon: PySide2.QtGui.QPixmap.QIcon):
        super(ImageView, self).__init__()
        pixmap = QPixmap()
        pixmap.loadFromData(image)
        self.setWindowIcon(title_icon)
        self.setWindowTitle('窗口标题')
        self.label = QLabel(self)
        self.label.setScaledContents(True)  # 让图片自适应 QLabel 大小
        self.label.setPixmap(image)
        self.setCentralWidget(self.label)  # 将 QLabel 设置为主窗口的中央部件
        self.adjustSize()  # 调整窗口大小以适应图片大小
        self.show()


iv = ImageView(image_icon='需要显示图片', title_icon='标题图片')

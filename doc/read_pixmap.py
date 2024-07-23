# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/7/23 19:29
# File:read_pixmap
"""
读取QPixmap对象的内容生成一个文件
https://blog.csdn.net/weixin_42579717/article/details/99319125
"""
import base64
import tempfile
from PySide2.QtWidgets import QApplication, QPushButton
from PySide2.QtGui import QPixmap
from PySide2.QtCore import QSize

# 首先将图片打印成二进制文件
# with open(r"图片路径", "rb") as f:  # 用 rb 模式（二进制）打开文件
#    # image = f.read()
#    # print(image)  # 打印一下
#
#    # b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x16\xd6 ...省略...'


image_data = b'获取的图片数据'


class PushButton(QPushButton):
    def __init__(self):
        super(PushButton, self).__init__()
        self.setIcon(icon)
        self.setIconSize(QSize(200, 200))
        self.show()


if __name__ == '__main__':
    app = QApplication([])
    # 创建QPixmap并加载图像数据
    icon = QPixmap()
    icon.loadFromData(image_data)
    # 保存图像到临时文件
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=True)
    icon.save(temp_file.name, 'PNG')  # 保存图像到临时文件
    print("Temporary file path:", temp_file.name)
    window = PushButton()
    app.exec_()


# 进阶版:使用base64缩短长度

# with open(r"D:\windowIcon.png", "rb") as f:
#    image = base64.b64encode(f.read())
#    print(image)
image_data = base64.b64decode('打印的内容需要的时候解码成图片数据')


class PushButton(QPushButton):
    def __init__(self):
        super(PushButton, self).__init__()
        self.setIcon(icon)
        self.setIconSize(QSize(200, 200))
        self.show()


if __name__ == '__main__':
    app = QApplication([])
    # 创建QPixmap并加载图像数据
    icon = QPixmap()
    icon.loadFromData(image_data)
    # 保存图像到临时文件
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=True)
    icon.save(temp_file.name, 'PNG')  # 保存图像到临时文件
    print("Temporary file path:", temp_file.name)
    win = PushButton()
    app.exec_()

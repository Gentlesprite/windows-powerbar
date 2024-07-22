# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/4/1 12:51
# File:2
import os
def get_target_path(shortcut_path):
    import win32com.client
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortcut(shortcut_path)
    target_path = shortcut.TargetPath
    return target_path
a = get_target_path(r'C:\Users\lzy\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\PowerBar.lnk')
print(a)

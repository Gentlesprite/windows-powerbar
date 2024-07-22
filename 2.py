# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/4/1 12:51
# File:2
import os
import win32com.client
def get_target_path(shortcut_path):
    import win32com.client
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortcut(shortcut_path)
    target_path = shortcut.TargetPath
    return target_path


def change_target_path(shortcut_path, new_target_path):
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortcut(shortcut_path)
    shortcut.TargetPath = new_target_path
    shortcut.Save()

# a = 'C:\\Users\\username\\Documents\\new_example.txt'
# change_target_path(r'C:\Users\lzy\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\PowerBar.lnk',a)

import sys
current_path = os.path.abspath(sys.argv[0])
software_path = os.path.dirname(current_path)
software_name = os.path.basename(current_path)

a = os.path.splitext(software_name)[0]

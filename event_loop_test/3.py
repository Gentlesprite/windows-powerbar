# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/4/2 14:50
# File:3
import time
from ctypes import Structure
from comtypes import GUID
from ctypes.wintypes import DWORD


# todo 1.0 解决了当软件移动时开机目标自动改变的功能
# todo 1.0plus 优化代码逻辑
# 软件启动时候不会自动勾选当前电源计划

class POWERBROADCAST_SETTING(Structure):
    _fields_ = [("PowerSetting", GUID),
                ("DataLength", DWORD),
                ("Data", DWORD)]


import re
import subprocess
from PySide2.QtCore import QThread, Signal
from loguru import logger

import win32con
import win32api
import win32gui
from ctypes import POINTER, windll, cast, CFUNCTYPE, c_int, c_uint, c_void_p, c_bool
from comtypes import GUID
from ctypes.wintypes import HANDLE, DWORD


# todo 1.0 解决了当软件移动时开机目标自动改变的功能
# todo 1.0plus 优化代码逻辑
# 软件启动时候不会自动勾选当前电源计划


class PowerEventListener:
    PBT_POWERSETTINGCHANGE = 0x8013
    GUID_POWERSCHEME_PERSONALITY = '{245D8541-3943-4422-B025-13A784F679B7}'

    def handle_power_setting_change(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_POWERBROADCAST and wparam == PowerEventListener.PBT_POWERSETTINGCHANGE:
            settings = cast(lparam, POINTER(POWERBROADCAST_SETTING)).contents
            power_setting = str(settings.PowerSetting)
            if power_setting == PowerEventListener.GUID_POWERSCHEME_PERSONALITY:
                pass

    def register_window_class(self):
        hinst = win32api.GetModuleHandle(None)
        wndclass = win32gui.WNDCLASS()
        wndclass.hInstance = hinst
        wndclass.lpszClassName = "testWindowClass"
        CMPFUNC = CFUNCTYPE(c_bool, c_int, c_uint, c_uint, c_void_p)
        wndproc_pointer = CMPFUNC(self.handle_power_setting_change)
        wndclass.lpfnWndProc = {win32con.WM_POWERBROADCAST: wndproc_pointer}

        try:
            return win32gui.RegisterClass(wndclass)
        except Exception as e:
            logger.error(f"Exception: {e}")
            raise

    def create_window(self):
        hwnd = None
        try:
            myWindowClass = self.register_window_class()
            if myWindowClass:
                hwnd = win32gui.CreateWindowEx(win32con.WS_EX_LEFT,
                                               myWindowClass,
                                               "testMsgWindow",
                                               0,
                                               0,
                                               0,
                                               win32con.CW_USEDEFAULT,
                                               win32con.CW_USEDEFAULT,
                                               0,
                                               0,
                                               win32api.GetModuleHandle(None),
                                               None)
        except Exception as e:
            logger.error(f"Exception: {e}")
            raise
        return hwnd

    def register_power_setting_notification(self, hwnd):
        if hwnd is None:
            logger.error("hwnd is none!")
            return

        result = windll.user32.RegisterPowerSettingNotification(HANDLE(hwnd),
                                                                GUID(PowerEventListener.GUID_POWERSCHEME_PERSONALITY),
                                                                DWORD(0))
        logger.info('registering power setting change notification')
        logger.info(f'result: {hex(result)}')

        if result == 0:
            logger.error(f"Error registering power setting notification: {win32api.GetLastError()}")
            raise Exception("Failed to register power setting notification.")

    def start_listening(self):
        hwnd = self.create_window()
        self.register_power_setting_notification(hwnd)
        logger.info('\n进入事件循环')
        while True:
            win32gui.PumpMessages()


class MyThread(QThread, PowerEventListener):
    power_plan_changed = Signal(tuple)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False

    def run(self):
        self.running = True
        hwnd = self.create_window()
        self.register_power_setting_notification(hwnd)
        logger.info('\n已开启监听')
        while self.running:
            win32gui.PumpMessages()


    def stop(self):
        self.running = False
        logger.error('\n监听已退出')

    def handle_power_setting_change(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_POWERBROADCAST and wparam == PowerEventListener.PBT_POWERSETTINGCHANGE:
            settings = cast(lparam, POINTER(POWERBROADCAST_SETTING)).contents
            power_setting = str(settings.PowerSetting)
            if power_setting == PowerEventListener.GUID_POWERSCHEME_PERSONALITY:
                print(getCurrentPlan())
                # self.power_plan_changed.emit(getCurrentPlan())


def getCurrentPlan() -> tuple:  # (name,guid)
    # 获取当前的电源方案
    try:
        result = subprocess.run(['powercfg', '/getactivescheme'], capture_output=True, text=True,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        pattern = re.compile(r'GUID:\s*([\w-]+)\s*\((.+)\)')
        match = pattern.search(result.stdout)
        if match:
            return match.group(2), match.group(1)
        else:
            return ()
    except Exception as e:
        logger.error(f'Error occurred:{e}')
    return ()
a = MyThread()
a.start()



time.sleep(10)

a.stop()
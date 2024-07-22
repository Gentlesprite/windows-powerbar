# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/4/1 22:57
# File:power_event_loop.py
import win32con
import win32api
import win32gui
from ctypes import POINTER, windll, Structure, cast, CFUNCTYPE, c_int, c_uint, c_void_p, c_bool
from comtypes import GUID
from ctypes.wintypes import HANDLE, DWORD
import logging
import time

PBT_POWERSETTINGCHANGE = 0x8013
GUID_POWERSCHEME_PERSONALITY = '{245D8541-3943-4422-B025-13A784F679B7}'
first_time = True


class POWERBROADCAST_SETTING(Structure):
    _fields_ = [("PowerSetting", GUID),
                ("DataLength", DWORD),
                ("Data", DWORD)]


def handle_power_setting_change(hwnd, msg, wparam, lparam):
    global first_time
    if msg == win32con.WM_POWERBROADCAST and wparam == PBT_POWERSETTINGCHANGE:
        settings = cast(lparam, POINTER(POWERBROADCAST_SETTING)).contents
        power_setting = str(settings.PowerSetting)
        if first_time:
            first_time = False
            return

        if power_setting == GUID_POWERSCHEME_PERSONALITY:
            logging.info(f'电源设置发生更改，更改的GUID类型为：{power_setting}')
            logging.info(f'主动电源方案个性已更改。{1}')


def register_window_class():
    hinst = win32api.GetModuleHandle(None)
    wndclass = win32gui.WNDCLASS()
    wndclass.hInstance = hinst
    wndclass.lpszClassName = "testWindowClass"
    CMPFUNC = CFUNCTYPE(c_bool, c_int, c_uint, c_uint, c_void_p)
    wndproc_pointer = CMPFUNC(handle_power_setting_change)
    wndclass.lpfnWndProc = {win32con.WM_POWERBROADCAST: wndproc_pointer}

    try:
        return win32gui.RegisterClass(wndclass)
    except Exception as e:
        logging.error(f"Exception: {e}")
        raise


def create_window():
    hwnd = None
    try:
        myWindowClass = register_window_class()
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
        logging.error(f"Exception: {e}")
        raise
    return hwnd


def register_power_setting_notification(hwnd):
    if hwnd is None:
        logging.error("hwnd is none!")
        return

    result = windll.user32.RegisterPowerSettingNotification(HANDLE(hwnd), GUID(GUID_POWERSCHEME_PERSONALITY), DWORD(0))
    logging.info('registering power setting change notification')
    logging.info(f'result: {hex(result)}')

    if result == 0:
        logging.error(f"Error registering power setting notification: {win32api.GetLastError()}")
        raise Exception("Failed to register power setting notification.")


def message_loop():
    logging.info('\n进入事件循环')
    while True:
        win32gui.PumpMessages()


def main():
    # first_time = True
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    hwnd = create_window()
    register_power_setting_notification(hwnd)
    message_loop()

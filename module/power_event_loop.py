# coding=UTF-8
# Author: Gentlesprite
# Software: PyCharm
# Time: 2024/4/1 22:57
# File: power_event_loop.py
import win32con
import win32api
import win32gui
from ctypes import POINTER, windll, Structure, cast, CFUNCTYPE, c_int, c_uint, c_void_p, c_bool
from comtypes import GUID
from ctypes.wintypes import HANDLE, DWORD
from loguru import logger

# todo 1.0 解决了当软件移动时开机目标自动改变的功能
# todo 1.0plus 优化代码逻辑和性能
HWND_NAME = 'PowerBar'


class POWERBROADCAST_SETTING(Structure):
    _fields_ = [("PowerSetting", GUID),
                ("DataLength", DWORD),
                ("Data", DWORD)]


class PowerEventListener:
    PBT_POWERSETTINGCHANGE = 0x8013
    GUID_POWERSCHEME_PERSONALITY = '{245D8541-3943-4422-B025-13A784F679B7}'

    def __init__(self):
        self.hwnd = self.create_window()

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
        wndclass.lpszClassName = HWND_NAME
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
                                               HWND_NAME,
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

    def register_power_setting_notification(self):
        try:
            if self.hwnd is None:
                self.hwnd = self.create_window()
        except AttributeError:
            self.hwnd = self.create_window()

        result = windll.user32.RegisterPowerSettingNotification(HANDLE(self.hwnd),
                                                                GUID(PowerEventListener.GUID_POWERSCHEME_PERSONALITY),
                                                                DWORD(0))
        logger.success('注册电源设置更改通知成功!')
        logger.info(f'结果码(HRESULT):"{hex(result)}"')

        if result == 0:
            logger.error(f"注册电源设置通知时出错: {win32api.GetLastError()}")
            raise Exception("无法注册电源设置通知。")

    def start_listening(self):
        self.register_power_setting_notification()
        logger.info('进入监听模式')
        while True:
            win32gui.PumpMessages()

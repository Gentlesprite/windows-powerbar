# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/4/1 22:45
# File:20
import win32con
import win32api
import win32gui
import time
from ctypes import POINTER, windll, Structure, cast, CFUNCTYPE, c_int, c_uint, c_void_p, c_bool
from comtypes import GUID
from ctypes.wintypes import HANDLE, DWORD


PBT_POWERSETTINGCHANGE = 0x8013
GUID_POWERSCHEME_PERSONALITY = '{245D8541-3943-4422-B025-13A784F679B7}'


class POWERBROADCAST_SETTING(Structure):
    _fields_ = [("PowerSetting", GUID),
                ("DataLength", DWORD),
                ("Data", DWORD)]
def wndproc(hwnd, msg, wparam, lparam):
    if msg == win32con.WM_POWERBROADCAST and wparam == PBT_POWERSETTINGCHANGE:
        settings = cast(lparam, POINTER(POWERBROADCAST_SETTING)).contents
        power_setting = str(settings.PowerSetting)
        if power_setting == GUID_POWERSCHEME_PERSONALITY:
            print('主动电源方案个性已更改。\n')


if __name__ == "__main__":
    hinst = win32api.GetModuleHandle(None)
    wndclass = win32gui.WNDCLASS()
    wndclass.hInstance = hinst
    wndclass.lpszClassName = "testWindowClass"
    CMPFUNC = CFUNCTYPE(c_bool, c_int, c_uint, c_uint, c_void_p)
    wndproc_pointer = CMPFUNC(wndproc)
    wndclass.lpfnWndProc = {win32con.WM_POWERBROADCAST: wndproc_pointer}

    try:
        myWindowClass = win32gui.RegisterClass(wndclass)
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
                                       hinst,
                                       None)
    except Exception as e:
        print("Exception: %s" % str(e))

    if hwnd is None:
        print("hwnd is none!")
    else:
        print("hwnd: %s" % hwnd)

    result = windll.user32.RegisterPowerSettingNotification(HANDLE(hwnd), GUID(GUID_POWERSCHEME_PERSONALITY), DWORD(0))
    print('registering power setting change notification')
    print('result:', hex(result))
    print('lastError:', win32api.GetLastError())

    print('\n进入时间循环')
    while True:
        print(win32gui.PumpWaitingMessages())
        win32gui.PumpWaitingMessages()
        time.sleep(1)

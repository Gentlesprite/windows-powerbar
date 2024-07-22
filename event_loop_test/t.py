# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/4/1 12:51
# File:2
import ctypes
import ctypes.wintypes

# 定义常量
HWND_BROADCAST = 0xFFFF
WM_POWERBROADCAST = 0x218
PBT_POWERSETTINGCHANGE = 0x8013

# 定义结构体
class POWERBROADCAST_SETTING(ctypes.Structure):
    _fields_ = [
        ("PowerSetting", ctypes.wintypes.GUID),
        ("DataLength", ctypes.wintypes.DWORD),
        ("Data", ctypes.c_byte * 1)  # 此处数据长度可能会变化
    ]

# 定义回调函数来处理电源管理事件
def power_setting_callback(hwnd, msg, wparam, lparam):
    if wparam == PBT_POWERSETTINGCHANGE:
        setting = ctypes.cast(lparam, ctypes.POINTER(POWERBROADCAST_SETTING)).contents
        print("Power Setting Changed:")
        print("  Power Setting GUID:", setting.PowerSetting)
        print("  Data Length:", setting.DataLength)
        # 处理数据...
    return True

# 注册电源设置通知
def register_power_setting_notification():
    user32 = ctypes.windll.user32
    user32.RegisterPowerSettingNotification.restype = ctypes.wintypes.HANDLE
    return user32.RegisterPowerSettingNotification(
        ctypes.wintypes.HANDLE(HWND_BROADCAST),
        ctypes.byref(ctypes.wintypes.GUID),
        0
    )

# 处理 WM_POWERBROADCAST 消息
def message_loop():
    user32 = ctypes.windll.user32
    msg = ctypes.wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))

# 注册回调函数
power_setting_callback_type = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.UINT, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM)
power_setting_callback_ptr = power_setting_callback_type(power_setting_callback)
notification_handle = register_power_setting_notification()

# 处理消息循环
message_loop()
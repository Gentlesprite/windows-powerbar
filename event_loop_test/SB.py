# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/4/1 23:00
# File:SB
import win32con
import win32api
import win32gui
import sys
import time
from ctypes import POINTER, windll
from comtypes import GUID
from ctypes.wintypes import HANDLE, DWORD

PBT_POWERSETTINGCHANGE = 0x8013

def log_info(msg):
    """ Prints """
    print(msg)
    f = open("../test.log", "a+")
    f.write(msg + "\n")
    f.close()

def wndproc(hwnd, msg, wparam, lparam):
    print('.')
    log_info("wndproc: %s\nw: %s\nl: %s" % (msg, wparam, lparam))
    if msg == win32con.WM_POWERBROADCAST:
        if wparam == win32con.PBT_APMPOWERSTATUSCHANGE:
            log_info('Power status has changed')
        if wparam == win32con.PBT_APMRESUMEAUTOMATIC:
            log_info('System resume')
        if wparam == win32con.PBT_APMRESUMESUSPEND:
            log_info('System resume by user input')
        if wparam == win32con.PBT_APMSUSPEND:
            log_info('System suspend')
        if wparam == PBT_POWERSETTINGCHANGE:
            log_info('Power setting changed...')
            #lparam is pointer to structure i need

if __name__ == "__main__":
    log_info("*** STARTING ***")
    hinst = win32api.GetModuleHandle(None)
    wndclass = win32gui.WNDCLASS()
    wndclass.hInstance = hinst
    wndclass.lpszClassName = "testWindowClass"
    messageMap = { win32con.WM_POWERBROADCAST : wndproc }

    wndclass.lpfnWndProc = messageMap

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
        log_info("Exception: %s" % str(e))


    if hwnd is None:
        log_info("hwnd is none!")
    else:
        log_info("hwnd: %s" % hwnd)

    register_function = windll.user32.RegisterPowerSettingNotification

    guids_info = {
                    'GUID_MONITOR_POWER_ON' : '{02731015-4510-4526-99e6-e5a17ebd1aea}',
                    'GUID_SYSTEM_AWAYMODE' : '{98a7f580-01f7-48aa-9c0f-44352c29e5C0}',
                    'fake' : '{98a7f580-01f7-48aa-9c0f-44352c29e555}' # just to see if I get an error or a different return from function
                 }

    hwnd_pointer = HANDLE(hwnd)
    for name, guid_info in guids_info.items():
        result = register_function(hwnd_pointer, GUID(guid_info), DWORD(0))
        print('registering', name)
        print('result:', result) # result is pointer to unregister function if I'm not mistaken
        print()

    print('\nEntering loop')
    while True:
        win32gui.PumpWaitingMessages()
        time.sleep(1)
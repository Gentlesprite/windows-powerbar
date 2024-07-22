# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/3/29 19:04
# File:test
#
#
# from subprocess import run, call, CREATE_NO_WINDOW
# from re import compile
#
# def getPowerConfig() -> dict:
#     # 执行命令并捕获输出
#     result = run(['powercfg', '/l'], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
#     # 使用正则表达式匹配电源方案的名称和对应的 GUID
#     pattern = compile(r'GUID:\s*([\w-]+)\s*\((.+)\)')
#     matches = pattern.findall(result.stdout)
#     power_cfg = {name: guid for guid, name in matches}
#     return power_cfg  # k0别名，v1 guid
# print(getPowerConfig()
# )
from winotify import Notification, audio
from enum import Enum


toast = Notification(app_id="电源计划",
                     title="电源计划调整",
                     msg=1,
                     icon=r'D:\files\Documents\study\python\Program\windows_power_manager\img\powercfg.ico',
                     duration='short')
"""type_attribute: dict = {AudioType.Default: audio.Default,
                        AudioType.IM: audio.IM,
                        AudioType.Mail: audio.Mail,
                        AudioType.Reminder: audio.Reminder,
                        AudioType.SMS: audio.SMS,
                        AudioType.Disabled: audio.Silent}"""

class Sound:
    def __init__(self, s):
        self.s = s

    def __str__(self):
        return self.s


Default = Sound("ms-winsoundevent:Notification.Default")
IM = Sound("ms-winsoundevent:Notification.IM")
Mail = Sound("ms-winsoundevent:Notification.Mail")
Reminder = Sound("ms-winsoundevent:Notification.Reminder")
SMS = Sound("ms-winsoundevent:Notification.SMS")
LoopingAlarm = Sound("ms-winsoundevent:Notification.Looping.Alarm")
LoopingAlarm2 = Sound("ms-winsoundevent:Notification.Looping.Alarm2")
LoopingAlarm3 = Sound("ms-winsoundevent:Notification.Looping.Alarm3")
LoopingAlarm4 = Sound("ms-winsoundevent:Notification.Looping.Alarm4")
LoopingAlarm6 = Sound("ms-winsoundevent:Notification.Looping.Alarm6")
LoopingAlarm8 = Sound("ms-winsoundevent:Notification.Looping.Alarm8")
LoopingAlarm9 = Sound("ms-winsoundevent:Notification.Looping.Alarm9")
LoopingAlarm10 = Sound("ms-winsoundevent:Notification.Looping.Alarm10")
LoopingCall = Sound("ms-winsoundevent:Notification.Looping.Call")
LoopingCall2 = Sound("ms-winsoundevent:Notification.Looping.Call2")
LoopingCall3 = Sound("ms-winsoundevent:Notification.Looping.Call3")
LoopingCall4 = Sound("ms-winsoundevent:Notification.Looping.Call4")
LoopingCall5 = Sound("ms-winsoundevent:Notification.Looping.Call5")
LoopingCall6 = Sound("ms-winsoundevent:Notification.Looping.Call6")
LoopingCall7 = Sound("ms-winsoundevent:Notification.Looping.Call7")
LoopingCall8 = Sound("ms-winsoundevent:Notification.Looping.Call8")
LoopingCall9 = Sound("ms-winsoundevent:Notification.Looping.Call9")
LoopingCall10 = Sound("ms-winsoundevent:Notification.Looping.Call10")
Silent = Sound("silent")

toast.set_audio(SMS, loop=False)
toast.show()

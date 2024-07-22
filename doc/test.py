# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/3/26 16:59
# File:TEST.py
import os
from enum import Enum

from winotify import Notification, audio


class AudioType(Enum):
    Default = 1
    IM = 2
    Mail = 3
    Reminder = 4
    SMS = 5
    Disabled = 6

    def text(self) -> str:
        audio_names = {
            AudioType.Default: '默认',
            AudioType.IM: '感应',
            AudioType.Mail: '邮件',
            AudioType.Reminder: '提醒',
            AudioType.SMS: '短讯',
            AudioType.Disabled: '禁用'
        }
        return str(audio_names[self])

    @property
    def attribute(self) -> audio.Sound:
        attribute_map: dict = {AudioType.Default: audio.Default,
                               AudioType.IM: audio.IM,
                               AudioType.Mail: audio.Mail,
                               AudioType.Reminder: audio.Reminder,
                               AudioType.SMS: audio.SMS,
                               AudioType.Disabled: audio.Silent}
        # return type(attribute_map[self])

        # return {self.value: str(attribute_map[self])}

        return {str(attribute_map[self]): self.value}


# for i in AudioType:
#     print(attribute_map[i])
# a = AudioType.Reminder.attribute
# b = audio.Silent.s
# print(a)
# print(b)

# a = AudioType.Mail.attribute
# print(a)
# for i in AudioType:
#     print(i.value)
# a = {'ms-winsoundevent:Notification.Default': 1}
# b = a['ms-winsoundevent:Notification.Default']
# print(b)

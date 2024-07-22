# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/3/29 19:04
# File:test
from subprocess import run, CREATE_NO_WINDOW
from re import compile

from enum import Enum
from winotify import Notification, audio


class AudioType(Enum):
    Default = 1
    IM = 2
    Mail = 3
    Reminder = 4
    SMS = 5
    Disabled = 6

    @staticmethod
    def valueGetAudioType(value):
        for i in AudioType:
            if i.value == value:
                return i
    @staticmethod
    def valueGetAudioTypeList():
        lst = []
        for i in range(AudioType.Default.value,AudioType.Disabled.value+1):
            lst.append(AudioType.valueGetAudioType(i))
        return lst
    def findAudioType(self, value):
        for audio_type in AudioType:
            if audio_type.value == value:
                return audio_type
        raise ValueError("No AudioType with value {}".format(value))

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
    @staticmethod
    def k0name_v1audiotype()->dict:
        k0name_v1audiotype_dict: dict = {}
        for i in AudioType.valueGetAudioTypeList():
            k0name_v1audiotype_dict[i.text()] = str(i)
        return k0name_v1audiotype_dict
    @property
    def attribute(self):
        attribute_map: dict = {AudioType.Default: audio.Default,
                               AudioType.IM: audio.IM,
                               AudioType.Mail: audio.Mail,
                               AudioType.Reminder: audio.Reminder,
                               AudioType.SMS: audio.SMS,
                               AudioType.Disabled: audio.Silent}
        # return (self, attribute_map[self])
        return {str(attribute_map[self]): self.value}

    @staticmethod
    def k0audio_v1num() -> dict:
        k0audio_v1num_dict: dict = {}
        for i in AudioType:
            for j in i.attribute.items():
                k0audio_v1num_dict[j[0]] = j[1]
        return k0audio_v1num_dict


# a = AudioType.findAudioType(1)
# print(a)
b = AudioType.k0name_v1audiotype()
print(b)

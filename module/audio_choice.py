# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/4/3 16:35
# File:audio_choice
from enum import Enum
from winotify import audio


class AudioType(Enum):
    Default = 1
    IM = 2
    Mail = 3
    Reminder = 4
    Disabled = 5

    def text(self) -> str:
        audio_names = {
            AudioType.Default: '默认',
            AudioType.IM: '感应',
            AudioType.Mail: '邮件',
            AudioType.Reminder: '提醒',
            AudioType.Disabled: '禁用'
        }
        return str(audio_names[self])

    @staticmethod
    def valueGetAudioType(value):
        for i in AudioType:
            if i.value == value:
                return i

    @staticmethod
    def valueGetAudioTypeList() -> list:
        lst = []
        for i in range(AudioType.Default.value, AudioType.Disabled.value + 1):
            lst.append(AudioType.valueGetAudioType(i))
        return lst

    @staticmethod
    def k0name_v1audiotype() -> dict:
        k0name_v1audiotype_dict: dict = {}
        for i in AudioType.valueGetAudioTypeList():
            k0name_v1audiotype_dict[i.text()] = i
        return k0name_v1audiotype_dict

    @property
    def attribute(self):
        attribute_map: dict = {AudioType.Default: audio.Default,
                               AudioType.IM: audio.IM,
                               AudioType.Mail: audio.Mail,
                               AudioType.Reminder: audio.Reminder,
                               AudioType.Disabled: audio.Silent}
        # return (self, attribute_map[self])
        return {str(attribute_map[self]): self.value}

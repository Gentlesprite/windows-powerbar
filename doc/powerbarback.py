# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/3/26 16:59
# File:powerbar.py

from functools import partial
from subprocess import run, call, CREATE_NO_WINDOW
from re import compile
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication
from winotify import Notification, audio
from PySide2.QtCore import QTimer
from enum import Enum
import win32com.client

import res_rc
import os
import json
import sys


class PowerMenu(QMenu):
    def __init__(self):
        super(PowerMenu, self).__init__()
        self.config = SaveUserConfig()
        self.quit_save_config = {}
        self.choice_actions = []  # 存储菜单中选项的内存地址
        self.initMenu()
        self.load_config()
        self.band()

    def load_config(self):
        config = self.config.getConfig()
        if isinstance(config, dict):
            try:
                if config['notice'] == True and config['type'] in range(AudioType.Default.value,
                                                                        AudioType.SMS.value + 1):  # 如果打开通知
                    self.is_notice_button.setChecked(True)  # 那么勾选通知菜单
                    self.is_notice_button.setMenu(self.voice_menu)  # 设置为提示音菜单
                    for i in AudioType:  # 遍历提示音种类
                        if config['type'] == i.value:  # 如果type的值等于音乐种类中的值
                            for key, value in self.voice_box.items():  # 对提示音字典进行遍历 key:type的
                                if key.value == config['type']:  # 如果提示音字典中的键等于配置文件中的值
                                    # print(value.data())
                                    # self.updateVoiceBoxState(data=(value.data()))
                                    value.setChecked(True)  # 勾选该选项
                elif config['notice'] == True and config['type'] == AudioType.Disabled.value:
                    config = self.config.configTemplate()
                    config['notice'] = False
                    config['type'] = AudioType.Disabled.value
                    self.config.createConfig(change_content=config)
            except:
                self.config.removeConfig()

    def band(self):
        self.icon.activated.connect(self.startPwoerConfigPanel)
        self.quit_button.triggered.connect(self.quit)
        self.is_notice_button.triggered.connect(
            lambda: self.updateVoiceBoxState(data=self.default_voice.data(), is_enabled=True))
        self.default_voice.triggered.connect(lambda: self.updateVoiceBoxState(data=self.default_voice.data()))
        self.im_voice.triggered.connect(lambda: self.updateVoiceBoxState(data=self.im_voice.data()))
        self.email_voice.triggered.connect(lambda: self.updateVoiceBoxState(data=self.email_voice.data()))
        self.reminder_voice.triggered.connect(lambda: self.updateVoiceBoxState(data=self.reminder_voice.data()))
        self.sms_voice.triggered.connect(lambda: self.updateVoiceBoxState(data=self.sms_voice.data()))
        self.disabled_voice.triggered.connect(lambda: self.updateVoiceBoxState(data=self.disabled_voice.data()))
        self.startup.toggled.connect(self.startWithWindows)

    def initMenu(self):
        self.taskBarMenu()

    def startWithWindows(self):
        current_path = os.path.abspath(sys.argv[0])
        software_path = os.path.dirname(current_path)
        software_name = os.path.basename(current_path)
        target = os.path.join(software_path, software_name)
        if self.startup.isChecked():
            startup = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
            current_path = os.path.abspath(sys.argv[0])
            software_path = os.path.dirname(current_path)
            print(software_path)
            # 创建快捷方式的名称
            link_name = SaveUserConfig.software_name
            # 在用户的启动目录中创建快捷方式
            shortcut_path = os.path.join(startup, link_name + '.lnk')
            shell = win32com.client.Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = target
            shortcut.save()
        else:
            os.remove(target)


    def quit(self):
        for key, value in self.voice_box.items():
            if value.isChecked():
                try:
                    if key.value in range(AudioType.Default.value, AudioType.SMS.value + 1):
                        self.quit_save_config['notice'] = True
                    elif key.value == AudioType.Disabled.value:
                        self.quit_save_config['notice'] = False
                except:
                    self.config.removeConfig()
                finally:
                    self.quit_save_config['type'] = key.value

        self.config.createConfig(change_content=self.quit_save_config)
        self.icon.deleteLater()  # 回收内存
        QApplication.quit()

    def cancelALLSelection(self) -> None:
        # 取消勾选所有选项框
        for _ in self.choice_actions:
            _.setChecked(False)

    def getPowerConfig(self) -> dict:
        # 执行命令并捕获输出
        result = run(['powercfg', '/l'], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
        # 使用正则表达式匹配电源方案的名称和对应的 GUID
        pattern = compile(r'GUID:\s*([\w-]+)\s*\((.+)\)')
        matches = pattern.findall(result.stdout)
        power_cfg = {name: guid for guid, name in matches}
        return power_cfg

    def setPlan(self, key, value, force=False) -> None:
        """设定当前系统电源方案
        key:
            电源计划的别称
        value:
            电源计划所对应的唯一的GUID
        force:
            是否无视当前状态是否一致，强制执行一次电源计划调整
            默认为否
        """
        current_plan = self.getCurrentPlan()
        if current_plan != value or force:
            # 设置用户选择的电源方案
            run(['powercfg', '/S', value], creationflags=CREATE_NO_WINDOW)
            print(f"电源方案调整为:{key}")
            self.powerChangeNotice(change_plan_content=key) if self.is_notice_button.isChecked() else None

    def powerChangeNotice(self, change_plan_content):

        toast = Notification(app_id="电源计划",
                             title="电源计划调整",
                             msg=change_plan_content,
                             icon=r'D:\files\Documents\study\python\Program\windows_power_manager\powercfg.ico',
                             duration='short')
        toast.set_audio(self.voice, loop=False) if self.voice else 0
        toast.show()

    def startPwoerConfigPanel(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:  # 单机左键打开控制面板的电源选项
            call(['control', 'powercfg.cpl'], creationflags=CREATE_NO_WINDOW)
        elif reason == QSystemTrayIcon.ActivationReason.Context:  # 目的在于处理用户从控制面板中改变电源计划(而非软件里面),对用户的选择进行实时匹配
            QTimer.singleShot(0, self.handleContextMenu)

    def handleContextMenu(self):
        # 在异步操作中获取当前电源计划
        key_word = {}  # 创建用于存储别称和内存相对应的字典
        power_cfg = self.getPowerConfig()  # 重新获取电源配置 key:人认识的(别称) value:电脑认识的(GUID)
        current_plan = self.getCurrentPlan()  # 获取当前电源选项的实际值
        for i in power_cfg.items():  # 遍历电源选项配置
            if i[1] == current_plan:  # 通过匹配GUID(value)来获取 来获取对应的键(key)
                key, value = i  # 获取到当前GUID对应的键 key:别称 value:GUID
                for j in self.choice_actions:  # 遍历存储菜单中所有选项的内存地址
                    key_word[str(j.text())] = j  # 将他们的别称和他们的内存地址一一对应 存入关键字字典 key:内存中的文本 value:内存地址
                    for k in key_word.items():  # 遍历这个内存和关键字对应的字典
                        if k[0] == key:  # 如果内存中的别称 匹配到了在前面获取到的 当前GUID对应的别称
                            self.cancelALLSelection()  # 取消以前所有勾选的
                            k[1].setChecked(True)  # 将匹配到的别称所对应的GUID进行勾选,那么必定就是当前所选择的电源计划

    def taskBarMenu(self):  # 定义任务栏右边的图标
        # 创建系统托盘图标和菜单
        self.icon = QSystemTrayIcon(QIcon(':powercfg.ico'), self)
        self.menu = QMenu(self)
        # 获取电源配置
        power_cfg = self.getPowerConfig()  # 重新获取电源配置
        # 匹配电源选项并为每个选项创建 QAction 对象
        current_plan = self.getCurrentPlan()  # 获取当前电源选项的实际值
        for index, (key, value) in enumerate(power_cfg.items()):
            self.action = QAction(key, self, checkable=True)  # 创建QAction对象，文本为电源选项名称
            self.choice_actions.append(self.action)
            self.menu.addAction(self.action)  # 将QAction对象添加到菜单中
            self.action.triggered.connect(
                partial(lambda k=key: self.setPlan(key=k, value=power_cfg[k])))
            self.value = value
            if self.value == current_plan:
                self.action.setChecked(True)  # 如果是当前的电源方案，则设置为选中状态
        # 将菜单设置为系统托盘图标的上下文菜单

        self.voice_box: dict = {}

        self.default_voice = QAction('默认', self, checkable=True, data=(audio.Default, '默认'))
        self.default_voice.isChecked()
        self.voice_box[AudioType.Default] = self.default_voice
        self.im_voice = QAction('感应', self, checkable=True, data=(audio.IM, '感应'))
        self.voice_box[AudioType.IM] = self.im_voice
        self.email_voice = QAction('邮件', self, checkable=True, data=(audio.Mail, '邮件'))
        self.voice_box[AudioType.Mail] = self.email_voice
        self.reminder_voice = QAction('提醒', self, checkable=True, data=(audio.Reminder, '提醒'))
        self.voice_box[AudioType.Reminder] = self.reminder_voice
        self.sms_voice = QAction('短讯', self, checkable=True, data=(audio.SMS, '短讯'))
        self.voice_box[AudioType.SMS] = self.sms_voice
        self.disabled_voice = QAction('禁用', self, checkable=True, data=(audio.Silent, '禁用'))
        self.voice_box[AudioType.Disabled] = self.disabled_voice
        self.voice_menu = QMenu("voice_selection")
        self.voice_box_list = []
        for i in self.voice_box.items():
            self.voice_box_list.append(i[1])
        menu_notice = self.voice_box_list[
                      :]  # [:] 常见的复制列表的方法，生成一个原列表的副本，而不是直接将原列表赋值给新列表变量。这样做的好处是，当修改 menu_notice 时不会影响原始的 self.voice_box_list，因为它们是两个独立的列表对象。
        menu_notice.insert(5, self.voice_menu.addSeparator())  # 在副本中插入分隔符
        self.voice_menu.addActions(menu_notice)
        self.icon.setContextMenu(self.menu)
        self.menu.addSeparator()
        self.startup = QAction('开机启动', self, checkable=True)
        self.menu.addAction(self.startup)

        self.is_notice_button = QAction('通知', self, checkable=True)

        self.menu.addAction(self.is_notice_button)
        self.menu.addSeparator()
        self.quit_button = QAction('退出', self)
        self.menu.addAction(self.quit_button)

        # 显示小图标
        self.icon.show()

    def getCurrentPlan(self) -> str:
        # 获取当前的电源方案
        result = run(['powercfg', '/getactivescheme'], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
        pattern = compile(r'GUID:\s*([\w-]+)')
        match = pattern.search(result.stdout)
        if match:
            return match.group(1)
        else:
            return ''

    def updateVoiceBoxState(self, data, is_enabled=False):
        voice, action = data
        self.voice = voice  # 设置提示音
        if is_enabled:
            self.is_notice_button.setMenu(self.voice_menu)
            self.default_voice.setChecked(True)
        else:
            for act in self.voice_box_list:
                if act.text() != action:
                    act.setChecked(False)
            if not voice:
                self.is_notice_button.setChecked(False)
                self.is_notice_button.setMenu(None)
                self.disabled_voice.setChecked(False)


class AudioType(Enum):
    Default = 1
    IM = 2
    Mail = 3
    Reminder = 4
    SMS = 5
    Disabled = 6


class SaveUserConfig:
    software_name = 'PowerBar'
    config_name = 'config.json'
    app_default_dir = os.path.join(os.getenv('APPDATA'), software_name)
    app_temp_dir = os.path.join(os.environ.get('TEMP'), software_name)
    default_config_path = os.path.join(app_default_dir, 'config.json')
    temp_config_path = os.path.join(app_temp_dir, 'config.json')

    def configTemplate(self):
        config = {
            "notice": True,
            "type": AudioType.Default.value
        }
        return config

    def readConfig(self):
        try:
            save_path = SaveUserConfig.default_config_path
            with open(save_path, 'r') as file:
                config = json.load(file)
        except FileNotFoundError:
            save_path = SaveUserConfig.temp_config_path
            with open(save_path, 'r') as file:
                config = json.load(file)
        except:
            return False
        finally:
            return config

    def createConfig(self, change_content=False):
        if not self.isExist() or change_content:
            save_path = ''
            try:
                save_path = SaveUserConfig.app_default_dir
                os.makedirs(save_path, exist_ok=True)
            except PermissionError:
                save_path = SaveUserConfig.app_temp_dir
                os.makedirs(save_path, exist_ok=True)
            finally:
                self.config_path = os.path.join(save_path, SaveUserConfig.config_name)
                with open(self.config_path, 'w') as file:
                    json.dump(self.configTemplate() if not change_content else change_content, file, indent=4)

    def isExist(self):
        if os.path.exists(SaveUserConfig.default_config_path) or os.path.exists(SaveUserConfig.temp_config_path):
            return True
        else:
            return False

    def getConfig(self):
        if not self.isExist():
            self.createConfig()
        config = self.readConfig() if self.readConfig() else False
        return config

    def removeConfig(self):
        try:
            os.remove(SaveUserConfig.default_config_path)
        except:
            os.remove(SaveUserConfig.temp_config_path)


if __name__ == '__main__':
    app = QApplication([])
    menu = PowerMenu()
    menu.show()
    app.exec_()

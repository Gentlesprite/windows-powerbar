# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/3/26 16:59
# File:powerbar.py

from functools import partial
from subprocess import run, call, CREATE_NO_WINDOW
from re import compile
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PySide2.QtCore import QTimer
from winotify import Notification, audio
from enum import Enum
import win32com.client

import res_rc
import os
import json
import sys
from loguru import logger

logger.add(
    os.path.join(os.getcwd(), "pb.log"),
    rotation="10 MB",
    retention="10 days",
    level="DEBUG",
)


class PowerMenu(QMenu):
    def __init__(self):
        super(PowerMenu, self).__init__()
        self.config = SaveUserConfig()
        self.config_content_dict = self.config.getConfig(exist_ok=True)[0]  # 加载配置
        self.choice_actions = []  # 存储菜单中选项的内存地址
        self.action = None
        self.initMenu()
        self.band()
        if self.loadConfig(only_check=True):  # 生成配置文件
            self.notice, self.dtype, self.start_with_windows = None, None, None
            self.pid = os.getpid()
            self.current_power_plan = PowerMenu.getCurrentPlan()
            self.config.updateConfig(config_dict=self.config_content_dict, pid=self.pid,
                                     current_power_plan=self.current_power_plan)
            logger.info(f'当前运行PID:{self.pid}')
            self.loadConfig()

    def loadConfig(self, only_check=False):
        if isinstance(self.config_content_dict, dict):  # 配置必须为字典
            if only_check:
                return only_check
            else:
                try:
                    if self.config_content_dict['notice'] == True and self.config_content_dict['type'] in range(
                            AudioType.Default.value,
                            AudioType.SMS.value + 1):  # 如果打开通知
                        self.is_notice_button.setChecked(True)  # 那么勾选通知菜单
                        self.is_notice_button.setMenu(self.voice_menu)  # 设置为提示音菜单
                        for i in AudioType:  # 遍历提示音种类
                            if self.config_content_dict['type'] == i.value:  # 如果type的值等于音乐种类中的值
                                for key, value in self.voice_box.items():  # 对提示音字典进行遍历 key:type的
                                    logger.error(f'key:{key}, value:{value}')
                                    if key.value == self.config_content_dict['type']:  # 如果提示音字典中的键等于配置文件中的值
                                        # print(value.data())
                                        # self.updateVoiceBoxState(data=(value.data()))
                                        value.setChecked(True)  # 勾选该选项
                    elif self.config_content_dict['notice'] == True and self.config_content_dict[
                        'type'] == AudioType.Disabled.value:
                        # self.config_content_dict = self.config.configTemplate()
                        self.notice = False
                        self.dtype = AudioType.Disabled.value
                    if self.islinkExists() == True:
                        self.start_with_windows = True
                        self.startup.setChecked(True)
                    elif self.islinkExists() == False:
                        self.start_with_windows = False
                        self.startup.setChecked(False)
                    # 匹配电源计划
                    # 获取电脑的所有的电源配置
                    power_cfg: dict = PowerMenu.getPowerConfig()  # 获取所以电源选项
                    k0guid_v1address: dict = {}  # 创建字典用于存储:k0 guid ,v1 控件地址
                    for pb_k0v1, pc_k0v1 in zip(self.power_box.items(), power_cfg.items()):
                        # 别名,控件地址  别名 GUID
                        if pb_k0v1[0] == pc_k0v1[0]:  # 将彼此的别名进行比较
                            k0guid_v1address[pc_k0v1[1]] = pb_k0v1[1]  # 生成{GUID:控件地址}
                    for k0guid, v1address in k0guid_v1address.items():  # 遍历{GUID:控件地址}
                        if k0guid_v1address[PowerMenu.getCurrentPlan()] == v1address:  # 与现在与当前电源的GUID字段进行匹配对应内存地址
                            v1address.setChecked(True)
                        for name, guid in power_cfg.items():
                            if k0guid == guid:
                                self.current_power_plan = k0guid
                    self.config.updateConfig(config_dict=self.config_content_dict,
                                             notice=self.notice,
                                             dtype=self.dtype,
                                             start_with_windows=self.start_with_windows,
                                             current_power_plan=self.current_power_plan)
                except Exception as e:
                    logger.error(f'错误:{e}')
                    self.config.removeConfig()

    def band(self):
        self.icon.activated.connect(self.startPwoerConfigPanel)
        self.quit_button.triggered.connect(self.quit)
        self.is_notice_button.triggered.connect(
            lambda: self.updateVoiceBoxState(data=self.default_voice.data()))
        self.default_voice.triggered.connect(lambda: self.updateVoiceBoxState(data=self.default_voice.data()))
        self.im_voice.triggered.connect(lambda: self.updateVoiceBoxState(data=self.im_voice.data()))
        self.email_voice.triggered.connect(lambda: self.updateVoiceBoxState(data=self.email_voice.data()))
        self.reminder_voice.triggered.connect(lambda: self.updateVoiceBoxState(data=self.reminder_voice.data()))
        self.sms_voice.triggered.connect(lambda: self.updateVoiceBoxState(data=self.sms_voice.data()))
        self.disabled_voice.triggered.connect(lambda: self.updateVoiceBoxState(data=self.disabled_voice.data()))
        self.startup.triggered.connect(self.startWithWindows)

        for i in self.power_box.items():
            self.choice_actions.append(i[1])
        for j in self.choice_actions:
            data = j.data()
            j.triggered.connect(partial(lambda d=data: self.updatePowerBoxState(data=d)))

    def initMenu(self):
        self.taskBarMenu()

    def startWithWindows(self):
        # TODO:根据配置打沟
        current_path = os.path.abspath(sys.argv[0])
        software_path = os.path.dirname(current_path)
        software_name = os.path.basename(current_path)
        target = os.path.join(software_path, software_name)
        link_name = SaveUserConfig.software_name  # 创建快捷方式的名称
        startup = SaveUserConfig.startup_dir
        shortcut_path = os.path.join(startup, link_name + '.lnk')  # 快捷方式地址
        if self.startup.isChecked():
            # 在用户的启动目录中创建快捷方式
            shell = win32com.client.Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = target
            shortcut.save()
            self.powerChangeNotice(change_plan_content='设置成功',
                                   title='设置开机自启') if self.is_notice_button.isChecked() else 0
            self.start_with_windows = False
            self.config.updateConfig(config_dict=self.config_content_dict, start_with_windows=self.start_with_windows)
        else:
            try:
                os.remove(shortcut_path)
                self.powerChangeNotice(change_plan_content='取消成功',
                                       title='设置开机自启') if self.is_notice_button.isChecked() else 0
                self.start_with_windows = False
                self.config.updateConfig(config_dict=self.config_content_dict,
                                         start_with_windows=self.start_with_windows)
                # self.config.createConfig()
            except:
                self.powerChangeNotice(change_plan_content='未知错误',
                                       title='设置开机自启') if self.is_notice_button.isChecked() else 0
                # todo

    def islinkExists(self) -> bool:
        return os.path.exists(os.path.join(SaveUserConfig.startup_dir, SaveUserConfig.software_name + '.lnk'))

    def quit(self):
        pid, notice, dtype, startWithWindows, current_power_plan = self.matchCurrentConfigFile()
        self.config.updateConfig(config_dict=self.config_content_dict, pid=pid, notice=notice, dtype=dtype,
                                 start_with_windows=startWithWindows, current_power_plan=current_power_plan)
        self.icon.deleteLater()  # 回收内存
        QApplication.quit()

    def cancelALLSelection(self) -> None:
        # 取消勾选所有选项框
        for _ in self.choice_actions:
            _.setChecked(False)

    @staticmethod
    def getPowerConfig() -> dict:
        # 执行命令并捕获输出
        result = run(['powercfg', '/l'], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
        # 使用正则表达式匹配电源方案的名称和对应的 GUID
        pattern = compile(r'GUID:\s*([\w-]+)\s*\((.+)\)')
        matches = pattern.findall(result.stdout)
        power_cfg = {name: guid for guid, name in matches}
        return power_cfg  # k0别名，v1 guid

    def setPlan(self, key, value) -> None:
        """设定当前系统电源方案
        key:
            电源计划的别称
        value:
            电源计划所对应的唯一的GUID
        force:
            是否无视当前状态是否一致，强制执行一次电源计划调整
            默认为否
        """
        # 设置用户选择的电源方案
        run(['powercfg', '/S', value], creationflags=CREATE_NO_WINDOW)
        logger.info(f"电源方案调整为:{key},GUID:{value}")
        self.powerChangeNotice(change_plan_content=key) if self.is_notice_button.isChecked() else None

    def matchCurrentConfigFile(self):  # 匹配软件状态的配置文件
        for key, value in self.voice_box.items():  # 遍历控件状态
            if value.isChecked():  # 找到打开状态的控件
                try:
                    if key.value in range(AudioType.Default.value, AudioType.SMS.value + 1):
                        self.notice = True
                    elif key.value == AudioType.Disabled.value:
                        self.notice = False
                except:
                    self.config.removeConfig()
                finally:
                    self.dtype = key.value
                if self.startup.isChecked() and self.islinkExists():
                    self.start_with_windows = True
                else:
                    self.start_with_windows = False
                # return self.pid, self.notice, self.dtype, self.start_with_windows
        # # 根据实际电源配置生成对应控件
        # power_cfg: dict = PowerMenu.getPowerConfig()
        # # check_current_power_plan: str = PowerMenu.getCurrentPlan()  # current guid
        # k0guid_v1address: dict = {}  # k0 guid ,v1 控件地址
        # for pb_k0v1, pc_k0v1 in zip(self.power_box.items(), power_cfg.items()):
        #     if pb_k0v1[0] == pc_k0v1[0]:
        #         k0guid_v1address[pc_k0v1[1]] = pb_k0v1[1]
        # for k0guid, v1address in k0guid_v1address.items():
        #     if v1address.isChecked():
        #         self.current_power_plan = k0guid
        self.current_power_plan = PowerMenu.getCurrentPlan()
        return self.pid, self.notice, self.dtype, self.start_with_windows, self.current_power_plan
        # if value.isChecked():
        #     try:
        #         if value == check_current_power_plan == self.config_content_dict['']

        #
        # self.power_box: dict = PowerMenu.getPowerConfig()# k0别名，v1 guid
        #
        # if check_current_power_plan == self.config_content_dict['currentPowerPlan']:
        #     self.current_power_plan =check_current_power_plan
        # else:
        #     self.current_power_plan = check_current_power_plan
        #
        # for key,value in self.power_box.items():

    def powerChangeNotice(self, change_plan_content, title=False):
        toast = Notification(app_id="电源计划",
                             title="电源计划调整" if not title else title,
                             msg=change_plan_content,
                             icon=r'D:\files\Documents\study\python\Program\windows_power_manager\img\powercfg.ico',
                             duration='short')
        # plan1
        # try:
        #     if self.voice:
        #         toast.set_audio(self.voice, loop=False)
        # except:
        # plan2
        # self.matchCurrentConfigFile()
        # self.config.createConfig(change_content=self.quit_save_config)
        # config = self.config.getConfig()
        # TODO:需要做到更新配置
        type_attribute: dict = {AudioType.Default: audio.Default,
                                AudioType.IM: audio.IM,
                                AudioType.Mail: audio.Mail,
                                AudioType.Reminder: audio.Reminder,
                                AudioType.SMS: audio.SMS,
                                AudioType.Disabled: audio.Silent}
        for i in AudioType:
            if self.config_content_dict['type'] == i.value:
                # print(i.value)
                toast.set_audio(type_attribute[i], loop=False) if self.config_content_dict['notice'] == True else 0
        # finally:
        #     self.updateConfig()
        toast.show()

    def startPwoerConfigPanel(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:  # 单机左键打开控制面板的电源选项
            call(['control', 'powercfg.cpl'], creationflags=CREATE_NO_WINDOW)
        elif reason == QSystemTrayIcon.ActivationReason.Context:  # 目的在于处理用户从控制面板中改变电源计划(而非软件里面),对用户的选择进行实时匹配
            QTimer.singleShot(0, self.handleContextMenu)

    def handleContextMenu(self):
        # 在异步操作中获取当前电源计划
        key_word = {}  # 创建用于存储别称和内存相对应的字典
        power_cfg = PowerMenu.getPowerConfig()  # 重新获取电源配置 key:人认识的(别称) value:电脑认识的(GUID)
        current_plan = PowerMenu.getCurrentPlan()  # 获取当前电源选项的实际值
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

        self.power_box: dict = {}  # 存储电源选项的字典 k0类型(别名)v1控件地址
        # 获取当前电源配置
        current_plan = PowerMenu.getCurrentPlan()
        power_cfg = PowerMenu.getPowerConfig()
        # 匹配电源选项并为每个选项创建 QAction 对象
        for index, (key, value) in enumerate(power_cfg.items()):
            self.action = QAction(key, self, checkable=True, data=(key, value, self.action))  # 创建QAction对象，文本为电源选项名称

            self.power_box[key] = self.action  # 存储电源选项的字典 k0类型(别名)v1控件地址
            self.menu.addAction(self.action)  # 将QAction对象添加到菜单中
            # self.action.triggered.connect(partial(lambda: self.matchCurrentConfigFile()))
            #
            # self.action.triggered.connect(
            #     partial(lambda k=key: self.setPlan(key=k, value=power_cfg[k])))
            # self.value = value
            # if self.value == power_cfg:
            #     self.action.setChecked(True)  # 如果是当前的电源方案，则设置为选中状态
        # 将菜单设置为系统托盘图标的上下文菜单

        self.voice_box: dict = {}  # 存储提示音选项的k0类型v1控件地址
        # todo:根据配置文件的dtype自动打沟
        self.default_voice = QAction(AudioType.Default.text(), self, checkable=True,
                                     data=(audio.Default, AudioType.Default))
        # logger.debug(f'测试{self.default_voice.data()}')
        self.default_voice.isChecked()
        self.voice_box[AudioType.Default] = self.default_voice
        self.im_voice = QAction(AudioType.IM.text(), self, checkable=True, data=(audio.IM, AudioType.IM))
        self.voice_box[AudioType.IM] = self.im_voice
        self.email_voice = QAction(AudioType.Mail.text(), self, checkable=True, data=(audio.Mail, AudioType.Mail))
        self.voice_box[AudioType.Mail] = self.email_voice
        self.reminder_voice = QAction(AudioType.Reminder.text(), self, checkable=True,
                                      data=(audio.Reminder, AudioType.Reminder))
        self.voice_box[AudioType.Reminder] = self.reminder_voice
        self.sms_voice = QAction(AudioType.SMS.text(), self, checkable=True, data=(audio.SMS, AudioType.SMS))
        self.voice_box[AudioType.SMS] = self.sms_voice
        self.disabled_voice = QAction(AudioType.Disabled.text(), self, checkable=True,
                                      data=(audio.Silent, AudioType.Disabled))
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

    @staticmethod
    def getCurrentPlan() -> str:
        # 获取当前的电源方案
        result = run(['powercfg', '/getactivescheme'], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
        pattern = compile(r'GUID:\s*([\w-]+)')
        match = pattern.search(result.stdout)
        if match:
            return match.group(1)
        else:
            return ''

    def updatePowerBoxState(self, data):
        name, guid, action_button_address = data
        self.setPlan(value=guid, key=name)
        self.current_power_plan = guid
        self.config.updateConfig(config_dict=self.config_content_dict, current_power_plan=self.current_power_plan)
        key_word = {}
        power_cfg = PowerMenu.getPowerConfig()  # 重新获取电源配置 key:人认识的(别称) value:电脑认识的(GUID)
        current_plan = PowerMenu.getCurrentPlan()
        for i in power_cfg.items():  # 遍历电源选项配置
            if i[1] == current_plan:  # 通过匹配GUID(value)来获取 来获取对应的键(key)
                key, value = i  # 获取到当前GUID对应的键 key:别称 value:GUID
                for j in self.choice_actions:  # 遍历存储菜单中所有选项的内存地址
                    key_word[str(j.text())] = j  # 将他们的别称和他们的内存地址一一对应 存入关键字字典 key:内存中的文本 value:内存地址
                    for k in key_word.items():  # 遍历这个内存和关键字对应的字典
                        if k[0] == key:  # 如果内存中的别称 匹配到了在前面获取到的 当前GUID对应的别称
                            self.cancelALLSelection()  # 取消以前所有勾选的
                            k[1].setChecked(True)  # 将匹配到的别称所对应的GUID进行勾选,那么必定就是当前所选择的电源计划

    def updateVoiceBoxState(self, data):
        voice, action = data
        # logger.debug(f'voice:{voice},action:{action.text()}')
        self.voice = voice  # 设置提示音
        # logger.warning(self.voice)
        notice_name = ''
        # if is_enabled:
        #     pass
        #     # self.is_notice_button.setMenu(self.voice_menu)
        #     # self.default_voice.setChecked(True)
        # else:
        # for act in self.voice_box_list:
        #     if act.text() != action.text():
        #         act.setChecked(False)
        # 分隔符
        # dic = {}
        # for i in AudioType:
        #     for j in i.attribute.items():
        #         dic[j[0]] = j[1]
        # for k in dic.items():
        #     if str(voice) == k[0]:
        #         self.dtype = k[1]
        #         notice_name = k[0]
        k0audio_v1num = AudioType.k0audio_v1num()
        for i in k0audio_v1num.items():
            if str(voice) == i[0]:
                self.dtype = i[1]
                notice_name = i[0]
                for j in self.voice_box.items():
                    res = ()
                    for k in j[0].attribute.items():
                        res = k
                    # logger.debug(res)
                    if res[0] == str(voice):
                        j[1].setChecked(True)
                    else:
                        j[1].setChecked(False)
                    # k0audio  v1
        if self.dtype == AudioType.Disabled.value:
            self.notice = False
            self.is_notice_button.setChecked(False)  # 那么勾选通知菜单
            self.is_notice_button.setMenu(None)  # 设置为提示音菜单
        elif self.is_notice_button.isChecked():
            self.notice = True
            self.is_notice_button.setChecked(True)
            self.is_notice_button.setMenu(self.voice_menu)

        # logger.debug(k0audio_v1num)
        logger.debug(f'提示音被更改为:{notice_name} 编号:{self.dtype}')
        self.config.updateConfig(config_dict=self.config_content_dict, dtype=self.dtype, notice=self.notice)

        # logger.error(i.attribute[str(voice)])
        # print(a)
        # for j in a:
        #     if voice == j.attribute[str(voice)]:
        #         logger.error(f'i的值为{j}')
        #         self.is_notice_button.setChecked(True)
        #         self.is_notice_button.setMenu(self.voice_menu)
        #         self.disabled_voice.setChecked(False)
        #         # config = self.config.getConfig()
        #         self.notice = True
        #         self.dtype = j.attribute
        #         self.config.updateConfig(config_dict=self.config_content_dict, notice=self.notice, dtype=self.dtype)
        #     else:
        #         pass
        # logger.warning(i.attribute[voice])
        # logger.warning('voice的值为',voice,f'({type(voice)})', 'exec的值为:',exec(f'{i}.attribute'),f'({type(exec(f"{i}.attribute"))})')
        #
        # if voice == audio.Silent:
        #     self.is_notice_button.setChecked(False)
        #     self.is_notice_button.setMenu(None)
        #     self.disabled_voice.setChecked(False)
        #     # config = self.config.getConfig()
        #     self.notice = False
        #     self.dtype = AudioType.Disabled.value
        #     self.config.updateConfig(config_dict=self.config_content_dict, notice=self.notice, dtype=self.dtype)


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
        """
        {'ms-winsoundevent:Notification.Default': 1, 
        'ms-winsoundevent:Notification.IM': 2, 
        'ms-winsoundevent:Notification.Mail': 3, 
        'ms-winsoundevent:Notification.Reminder': 4, 
        'ms-winsoundevent:Notification.SMS': 5, 
        'silent': 6}

        """


"""
audio.IM
voice:ms-winsoundevent:Notification.IM,action:感应

"""


class SaveUserConfig:
    software_name = 'PowerBar'
    config_name = 'config.json'
    app_default_dir = os.path.join(os.getenv('APPDATA'), software_name)
    app_temp_dir = os.path.join(os.environ.get('TEMP'), software_name)
    default_config_path = os.path.join(app_default_dir, 'config.json')
    temp_config_path = os.path.join(app_temp_dir, 'config.json')
    startup_dir = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs',
                               'Startup')  # 开机目录

    def __init__(self):
        self.current_plan = PowerMenu.getCurrentPlan()
        self.key_num = 5  # 配置文件中键的个数
        logger.debug(f'当前的电源计划为{self.current_plan}')
        try:
            self.config_path = self.getConfig(exist_ok=True)[1]
        except TypeError:
            self.removeConfig()
            self.config_path = self.getConfig(exist_ok=True)[1]
        finally:
            logger.info('配置加载成功！')

    def configTemplate(self):  # 配置模板
        config = {
            "notice": True,
            "type": AudioType.Default.value,
            "startWithWindows": False,
            "pid": os.getpid(),
            "currentPowerPlan": self.current_plan
        }
        return config

    def removeConfig(self):  # 删
        try:
            os.remove(SaveUserConfig.default_config_path)
        except:
            os.remove(SaveUserConfig.temp_config_path)

    def readConfig(self, save_path):
        try:
            with open(save_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            logger.error(f"Config file not found at {save_path}")
            raise
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {save_path}")
            raise

    def genConfigTemplate(self, save_path):
        try:
            with open(save_path, 'w') as file:
                json.dump(self.configTemplate(), file, indent=4)
        except FileNotFoundError:
            logger.error(f"Error creating config template at {save_path}")
            raise

    def getConfig(self, exist_ok=False):  # 查
        self.existOk() if exist_ok else 0  # 判断存在是否创建config.json存在
        save_path = SaveUserConfig.default_config_path
        try:
            config = self.readConfig(save_path=save_path)
        except FileNotFoundError:
            save_path = SaveUserConfig.temp_config_path
            config = self.readConfig(save_path=save_path)
        except:
            try:
                save_path = SaveUserConfig.default_config_path
                self.genConfigTemplate(save_path=save_path)
            except FileNotFoundError:
                save_path = SaveUserConfig.temp_config_path
                self.genConfigTemplate(save_path=save_path)
            try:
                save_path = SaveUserConfig.default_config_path
                config = self.readConfig(save_path=save_path)
            except FileNotFoundError:
                save_path = SaveUserConfig.temp_config_path
                config = self.readConfig(save_path=save_path)
        finally:
            # 回调必须保证路径正确并且内容合法
            try:
                if self.isConfigLegal(compare_dict=config):
                    return config, save_path
            except Exception as e:
                logger.error(f'{e}')

            return exist_ok

            # self.removeConfig()
            # self.existOk()
            # self.getConfig()
            # UnboundLocalError: local variable 'config' referenced before assignment
            # 改进后又会导致 如果第一次启动检测配置文件错误会报错，其删除生成的新配置文件在第二次启动的时候才生效
            # todo ：可能不能这样写，因为当已存在的配置文件内容格式错误，return self.getConfig(exist_ok=True) 会导致getConfig无限递归

        r"""
          File "D:\files\Documents\study\python\Program\windows_power_manager\powerbar_re.py", line 412 in getConfig
  File "D:\files\Documents\study\python\Program\windows_power_manager\powerbar_re.py", line 412 in getConfig
  File "D:\files\Documents\study\python\Program\windows_power_manager\powerbar_re.py", line 412 in getConfig
  ...

Process finished with exit code -1073740791 (0xC0000409)
        """

    # def updateConfig(self, config_dict,
    #                  pid=None,
    #                  notice=None,
    #                  dtype=None,
    #                  start_with_windows=None,
    #                  current_power_plan=None,
    #                  exist_ok=False):  # 改
    #     self.existOk() if exist_ok else 0
    #     logger.debug(f'更改前的配置:{config_dict}')
    #     # if pid is not None:
    #     #     config_dict['pid'] = pid
    #     # if notice is not None:
    #     #     config_dict['notice'] = notice
    #     # if dtype is not None:
    #     #     config_dict['type'] = dtype
    #     # if start_with_windows is not None:
    #     #     config_dict['startWithWindows'] = start_with_windows
    #     # if current_power_plan is not None:
    #     #     config_dict['currentPowerPlan'] = current_power_plan
    #     k0name_v1status = {'pid': pid, 'notice': notice, 'type': dtype, 'startWithWindows': start_with_windows,
    #                        'currentPowerPlan': current_power_plan}
    #     for k, v in k0name_v1status.items():
    #         if v is not None:
    #             config_dict[k] = v
    #             with open(self.config_path, 'w') as file:
    #                 json.dump(config_dict, file, indent=4)
    #     logger.success(f'更改后的配置:{config_dict}')
    def updateConfig(self, config_dict, pid=None, notice=None, dtype=None, start_with_windows=None,
                     current_power_plan=None,
                     exist_ok=False):  # 改
        self.existOk() if exist_ok else 0
        logger.info(f'更改前的配置:{config_dict}')
        if pid is not None:
            config_dict['pid'] = pid
        if notice is not None:
            config_dict['notice'] = notice
        if dtype is not None:
            config_dict['type'] = dtype
        if start_with_windows is not None:
            config_dict['startWithWindows'] = start_with_windows
        if current_power_plan is not None:
            config_dict['currentPowerPlan'] = current_power_plan
        with open(self.config_path, 'w') as file:
            json.dump(config_dict, file, indent=4)
        logger.success(f'更改后的配置:{config_dict}')

    def existOk(self):  # 判断存在是否创建config.json 判定存在必须合法
        save_path = SaveUserConfig.app_default_dir
        try:
            os.makedirs(save_path, exist_ok=True)
        except PermissionError:
            save_path = SaveUserConfig.app_temp_dir
            os.makedirs(save_path, exist_ok=True)
        finally:
            config_path = os.path.join(save_path, SaveUserConfig.config_name)
            if not os.path.exists(config_path):  # todo：如果是因为错误而程序发起的删除该判断可能导致问题
                with open(config_path, 'w') as file:
                    json.dump(self.configTemplate(), file, indent=4)
                logger.info('新模板创建成功')

        # # return config_path if callback else 0
        # if callback:
        #     # 回调必须保证路径正确并且内容合法
        #     try:
        #         with open(config_path, 'r') as file:
        #             compare_dict = json.load(file)
        #         if self.isConfigLegal(compare_dict=compare_dict):
        #             return config_path
        #         else:
        #             self.removeConfig()  # 不合法直接删除配置
        #             # TODO:可能还需要判断是否成功删除？感觉没必要
        #             self.existOk(callback=False)
        #             logger.info('不合法直接删除配置重新创建模板')
        #     except:
        #         logger('防止路径被删除的递归')
        #         self.removeConfig()  # 不合法直接删除配置
        #         self.existOk(callback=False)
        #
        #     finally:
        #         return config_path

    def isConfigLegal(self, compare_dict: dict) -> bool:  # 是否合法 :传入需要匹配键的字典
        key_name = []  # 创建列表存储键名
        # todo:加入try
        try:
            if isinstance(compare_dict, dict) and len(compare_dict) == self.key_num:
                for k0v1compare, k0v1template in zip(compare_dict.items(), self.configTemplate().items()):
                    if k0v1compare[0] == k0v1template[0]:
                        key_name.append(k0v1compare[0])
                return True if len(key_name) == self.key_num else False
            else:
                return False
        except:
            return False


if __name__ == '__main__':
    pid = os.getpid()
    from PySide2.QtWidgets import QApplication, QMessageBox

    app = QApplication([])
    menu = PowerMenu()
    if menu.config.getConfig()[0].get("pid") == pid:
        # QMessageBox.critical(None, '成功', f'当前PID:{menu.config.getConfig()[0].get("pid")}系统pid:{pid}')
        menu.show()
        app.exec_()
    else:
        menu.show()
        app.exec_()

        pass
        # QMessageBox.critical(None, '错误', '程序已存在，请勿重复运行！')

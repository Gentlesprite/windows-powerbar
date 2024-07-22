# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/3/26 16:59
# File:powerbar.py

from functools import partial
from subprocess import run, call, CREATE_NO_WINDOW
from re import compile
from PySide2.QtWidgets import QApplication, QMainWindow, QPushButton
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


# 1.短讯和感应声音相同故减少了一个重复提示音2.优化更新配置文件逻辑,值完全相同则不需要更新
# todo:优化方向：限制软件多开
class PowerMenu(QMenu):
    def __init__(self):
        super(PowerMenu, self).__init__()
        self.config = SaveUserConfig()
        self.config_content_dict = self.config.getConfig(exist_ok=True)[0]  # 加载配置
        self.choice_actions = []  # 存储菜单中选项的内存地址
        self.voice_choice_actions = []
        self.voice_buttons = None
        self.action = None
        self.initMenu()
        self.band()

        if self.loadConfig(only_check=True):  # 生成配置文件
            self.notice, self.dtype, self.start_with_windows = None, None, None
            self.pid = os.getpid()
            self.current_power_plan = PowerMenu.getCurrentPlan()
            self.config.updateConfig(config_dict=self.config_content_dict,
                                     current_power_plan=self.current_power_plan)
            logger.info(f'当前运行PID:{self.pid}')
            self.loadConfig()

    def isRunning(self):
        if self._instanceChecker is None:
            self._instanceChecker = self.findChild(QApplication, "instanceChecker")
        return self._instanceChecker is not None

    def band(self):
        self.icon.activated.connect(self.startPwoerConfigPanel)
        self.quit_button.triggered.connect(self.quit)

        self.is_notice_button.triggered.connect(
            lambda: self.updateVoiceBoxState(data=self.is_notice_button.data()))

        self.startup.triggered.connect(self.startWithWindows)

        for i in self.voice_box.items():
            self.voice_choice_actions.append(i[1])
        for j in self.voice_choice_actions:
            data = j.data()
            j.triggered.connect(partial(lambda d=data: self.updateVoiceBoxState(data=d)))

        for k in self.power_box.items():
            self.choice_actions.append(k[1])
        for l in self.choice_actions:
            data = l.data()
            l.triggered.connect(partial(lambda d=data: self.updatePowerBoxState(data=d)))

    def loadConfig(self, only_check=False):
        if isinstance(self.config_content_dict, dict):  # 配置必须为字典
            if only_check:
                return only_check
            else:
                try:
                    if self.config_content_dict['notice'] == True and self.config_content_dict['type'] in range(
                            AudioType.Default.value,
                            AudioType.Reminder.value + 1):  # 如果打开通知

                        self.is_notice_button.setChecked(True)  # 那么勾选通知菜单
                        self.is_notice_button.setMenu(self.voice_menu)  # 设置为提示音菜单
                        # 存储提示音选项的k0类型v1控件地址
                        # 还需要k0控件地址 v1 键
                        # for k0name_v1address, in zip(self.voice_box.items(),AudioType): #name ,address
                        # 拿到AudioType.Default : address
                        k0aduiotype_v1address = {}
                        for k0name_v1address, k0name_v1audiotype in zip(self.voice_box.items(),
                                                                        AudioType.k0name_v1audiotype().items()):
                            if k0name_v1address[0].text() == k0name_v1audiotype[0]:
                                k0aduiotype_v1address[k0name_v1audiotype[1]] = k0name_v1address[1]

                        for k0aduiotype, v1address in k0aduiotype_v1address.items():  # 对提示音字典进行遍历 key:type的
                            if k0aduiotype.value == self.config_content_dict['type']:  # 如果提示音字典中的键等于配置文件中的值
                                v1address.setChecked(True)  # 勾选该选项


                    elif self.config_content_dict['notice'] == True and self.config_content_dict[
                        'type'] == AudioType.Disabled.value:
                        self.notice = False
                        self.dtype = AudioType.Disabled.value
                    if self.islinkExists() == True:
                        self.start_with_windows = True
                        self.startup.setChecked(True)
                    elif self.islinkExists() == False:
                        self.start_with_windows = False
                        self.startup.setChecked(False)
                    self.pid = os.getpid()
                    # 匹配电源计划
                    self.current_power_plan = PowerMenu.getCurrentPlan()
                    # compare_dict: dict = {
                    #     "notice": self.notice,
                    #     "type": self.dtype,
                    #     "startWithWindows": self.start_with_windows,
                    #     "pid": self.pid,
                    #     "currentPowerPlan": self.current_power_plan
                    # }
                    # truth_table: list = [] # 创建真值表
                    # for k0name_v1value_0, k0name_v1value_1 in zip(self.config_content_dict.items(),
                    #                                               compare_dict.items()):
                    #     if k0name_v1value_0[0] == k0name_v1value_1[0] and k0name_v1value_1[1] is not None:
                    #         truth_table.append(k0name_v1value_0[1] == k0name_v1value_1[1])
                    #         # logger.debug(
                    #         #     f'{k0name_v1value_0[0]}原本的值：{k0name_v1value_0[1]}，{k0name_v1value_1[0]}现在的值：{k0name_v1value_1[1]}')
                    # if not all(truth_table):  # 全部一样(都为True)就不需要更新一遍配置了
                    self.config.updateConfig(config_dict=self.config_content_dict,
                                             notice=self.notice,
                                             dtype=self.dtype,
                                             start_with_windows=self.start_with_windows,
                                             current_power_plan=self.current_power_plan, pid=self.pid
                                             )
                except Exception as e:
                    logger.error(f'错误:{e.with_traceback()}')
                    self.config.removeConfig()

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
            self.start_with_windows = True
            self.config.updateConfig(config_dict=self.config_content_dict, start_with_windows=self.start_with_windows)
            logger.success('设置开机自启')
        else:
            try:
                os.remove(shortcut_path)
                self.powerChangeNotice(change_plan_content='取消成功',
                                       title='设置开机自启') if self.is_notice_button.isChecked() else 0
                self.start_with_windows = False
                self.config.updateConfig(config_dict=self.config_content_dict,
                                         start_with_windows=self.start_with_windows)
                logger.success('取消开机自启')
            except:
                self.powerChangeNotice(change_plan_content='未知错误',
                                       title='设置开机自启') if self.is_notice_button.isChecked() else 0
                logger.error('未找到文件,可能已删除,取消开机自启失败')
                # todo

    def islinkExists(self) -> bool:
        return os.path.exists(os.path.join(SaveUserConfig.startup_dir, SaveUserConfig.software_name + '.lnk'))

    def unknowQuit(self):
        pid, notice, dtype, startWithWindows, current_power_plan = self.matchCurrentConfigFile()
        pid = 0
        logger.debug('success')
        self.config.updateConfig(config_dict=self.config_content_dict, pid=pid, notice=notice, dtype=dtype,
                                 start_with_windows=startWithWindows, current_power_plan=current_power_plan)

    def quit(self):
        pid, notice, dtype, startWithWindows, current_power_plan = self.matchCurrentConfigFile()
        pid = 0

        self.config.updateConfig(config_dict=self.config_content_dict, pid=pid, notice=notice, dtype=dtype,
                                 start_with_windows=startWithWindows, current_power_plan=current_power_plan)

        self.icon.deleteLater()  # 回收内存
        self.close()
        sys.exit()

    # def closeEvent(self,event):
    #     self.quit_button.triggered.connect(self.quit)

    # 通知服务器的代码省略，这里不是重点...
    # else:
    #     event.ignore()

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
        logger.info(f"电源方案调整为:{key} GUID:{value}")
        self.powerChangeNotice(change_plan_content=key) if self.is_notice_button.isChecked() else None

    def matchCurrentConfigFile(self):  # 匹配软件状态的配置文件
        for key, value in self.voice_box.items():  # 遍历控件状态
            if value.isChecked():  # 找到打开状态的控件
                try:
                    if key.value in range(AudioType.Default.value, AudioType.Reminder.value + 1):
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
        self.current_power_plan = PowerMenu.getCurrentPlan()
        return self.pid, self.notice, self.dtype, self.start_with_windows, self.current_power_plan

    def powerChangeNotice(self, change_plan_content, title=False):
        toast = Notification(app_id="电源计划",
                             title="电源计划调整" if not title else title,
                             msg=change_plan_content,
                             icon=r'D:\files\Documents\study\python\Program\windows_power_manager\img\powercfg.ico',
                             duration='short')

        # TODO:需要做到更新配置
        type_attribute: dict = {AudioType.Default: audio.Default,
                                AudioType.IM: audio.IM,
                                AudioType.Mail: audio.Mail,
                                AudioType.Reminder: audio.Reminder,
                                AudioType.Disabled: audio.Silent}
        for i in AudioType:
            if self.config_content_dict['type'] == i.value:
                toast.set_audio(type_attribute[i], loop=False) if self.config_content_dict['notice'] == True else 0
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
                            if self.current_power_plan != i[1]:  # 如果现在的GUID不等于软件的GUID
                                self.current_power_plan = i[1]  # 说明GUID已经从非软件的地方发生了改变 赋值新的GUID然后更新配置文件
                                self.config.updateConfig(config_dict=self.config_content_dict,
                                                         current_power_plan=self.current_power_plan)

    def taskBarMenu(self):  # 定义任务栏右边的图标
        # 创建系统托盘图标和菜单
        self.icon = QSystemTrayIcon(QIcon(':powercfg.ico'), self)
        self.menu = QMenu(self)
        self.voice_menu = QMenu("voice_selection")
        self.power_box: dict = {}  # 存储电源选项的字典 k0类型(别名)v1控件地址
        self.voice_box: dict = {}  # 存储提示音选项的k0类型v1控件地址
        # 获取当前电源配置

        power_cfg = PowerMenu.getPowerConfig()
        # 匹配电源选项并为每个选项创建 QAction 对象
        for key, value in power_cfg.items():
            self.action = QAction(key, self, checkable=True)  # 创建QAction对象，文本为电源选项名称
            # name,guid,address
            self.power_box[key] = self.action  # 存储电源选项的字典 k0类型(别名)v1控件地址
            self.menu.addAction(self.action)  # 将QAction对象添加到菜单中
            self.action.setData((key, value, self.action))

        # 将菜单设置为系统托盘图标的上下文菜单

        voice_cfg = {}
        for i in AudioType:
            voice_cfg[i] = i.value

        for key, value in voice_cfg.items():
            self.voice_buttons = QAction(key.text(), self, checkable=True)
            self.voice_box[key] = self.voice_buttons
            self.voice_menu.addAction(self.voice_buttons)
            self.voice_buttons.setData((key.text(), value, self.voice_buttons))

        self.icon.setContextMenu(self.menu)
        self.menu.addSeparator()
        self.startup = QAction('开机启动', self, checkable=True)
        self.menu.addAction(self.startup)
        self.is_notice_button = QAction('通知', self, checkable=True)
        self.menu.addAction(self.is_notice_button)
        self.is_notice_button.setData(self.is_notice_button)
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
        if data == self.is_notice_button.data():
            self.notice = True
            self.dtype = AudioType.Default.value
            self.is_notice_button.data().setChecked(True)
            self.is_notice_button.setMenu(self.voice_menu)
            for k0audiotype_v2address in self.voice_box.items():
                if k0audiotype_v2address[0].value == AudioType.Default.value:
                    k0audiotype_v2address[1].setChecked(True)
            self.config.updateConfig(config_dict=self.config_content_dict, dtype=self.dtype, notice=self.notice)

        else:
            voice, action, address = data  # attribute,id,address
            logger.debug(f'当前提示音:{voice} 编号:{action}')
            address.setChecked(True)
            self.dtype = action
            if self.dtype == AudioType.Disabled.value:
                self.notice = False
                self.is_notice_button.setChecked(False)  # 那么勾选通知菜单
                self.is_notice_button.setMenu(None)  # 设置为提示音菜单

            self.config.updateConfig(config_dict=self.config_content_dict, dtype=self.dtype, notice=self.notice)

            # 初始化一个空字典用于存储特定数据结构
            key_word = {}
            # 遍历voice_choice_actions列表，并以其中data方法返回值的第二个元素为键，整个对象为值，填充字典
            for i in self.voice_choice_actions:
                key_word[i.data()[1]] = i
            # 记录debug信息，输出key_word字典内容
            # 遍历key_word字典的每一个键值对
            for k0valuev1_address in key_word.items():
                # 检查当前配置类型是否与字典键相匹配
                if self.config_content_dict['type'] == k0valuev1_address[0]:
                    # 如果配置类型匹配到的是禁用音频，则取消所有音频选项的选中状态
                    if k0valuev1_address[0] == AudioType.Disabled.value:
                        for j in self.voice_choice_actions:
                            j.setChecked(False)
                    # 如果配置类型不是禁用音频，则取消所有选项的选中状态，并选中与配置类型匹配的选项
                    else:
                        for j in self.voice_choice_actions:
                            j.setChecked(False)
                        k0valuev1_address[1].setChecked(True)
                        self.dtype = k0valuev1_address[0]
                        self.config.updateConfig(config_dict=self.config_content_dict, dtype=self.dtype,
                                                 notice=self.notice)


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

    @staticmethod
    def k0audio_v1num() -> dict:
        k0audio_v1num_dict: dict = {}
        for i in AudioType:
            for j in i.attribute.items():
                k0audio_v1num_dict[j[0]] = j[1]
        return k0audio_v1num_dict


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
        self.power_cfg = PowerMenu.getPowerConfig()
        for i in self.power_cfg.items():
            if i[1] == self.current_plan:
                logger.info(f'当前的电源计划为:{i[0]} GUID:{self.current_plan}')
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
            "pid": 0,
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

            # return exist_ok

    def updateConfig(self, config_dict, pid=None, notice=None, dtype=None, start_with_windows=None,
                     current_power_plan=None, last_ptime=None,
                     exist_ok=False):  # 改
        self.existOk() if exist_ok else 0
        compare_dict: dict = {
            "notice": notice,
            "type": dtype,
            "startWithWindows": start_with_windows,
            "pid": pid,
            "currentPowerPlan": current_power_plan
        }
        truth_table: list = []  # 创建真值表
        for k0name_v1value_0, k0name_v1value_1 in zip(config_dict.items(),
                                                      compare_dict.items()):
            if k0name_v1value_0[0] == k0name_v1value_1[0] and k0name_v1value_1[1] is not None:
                truth_table.append(k0name_v1value_0[1] == k0name_v1value_1[1])
        if not all(truth_table):
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
            # for i in compare_dict.items():
            #     if i[1] is not None:
            #         logger.info(f'更改前的配置:{config_dict}')
            #         config_dict[i[0]] = i[1]
            #         with open(self.config_path, 'w') as file:
            #             json.dump(config_dict, file, indent=4)
            #         logger.success(f'更改后的配置:{config_dict}')
        #
        #
        #
        # truth_table = [pid, notice, dtype, start_with_windows, current_power_plan]
        #
        #
        # if any(truth_table):
        #     logger.info(f'更改前的配置:{config_dict}')
        #     if pid is not None:
        #         config_dict['pid'] = pid
        #     if notice is not None:
        #         config_dict['notice'] = notice
        #     if dtype is not None:
        #         config_dict['type'] = dtype
        #     if start_with_windows is not None:
        #         config_dict['startWithWindows'] = start_with_windows
        #     if current_power_plan is not None:
        #         config_dict['currentPowerPlan'] = current_power_plan
        #     with open(self.config_path, 'w') as file:
        #         json.dump(config_dict, file, indent=4)
        #     logger.success(f'更改后的配置:{config_dict}')

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


import psutil

if __name__ == '__main__':
    suc = SaveUserConfig()
    pid = suc.getConfig()[0].get('pid')
    if pid == 0:
        app = QApplication([])
        menu = PowerMenu()
        menu.show()
        app.aboutToQuit.connect(menu.unknowQuit)
        print(1)
        app.exec_()
    else:
        if pid in psutil.pids():
            logger.error(f'pid已经在:{pid}列表{psutil.pids()}中')
        else:
            logger.error(f'pid:{pid}不在列表{psutil.pids()}')
            app = QApplication([])
            menu = PowerMenu()
            menu.show()
            app.aboutToQuit.connect(menu.unknowQuit)
            app.exec_()

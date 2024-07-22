# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/3/26 16:59
# File:powerbar.py
import base64
import os
import sys
import win32com.client
import psutil
from PIL import Image
from io import BytesIO
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QThread, Signal, QTimer, QByteArray, QBuffer, QIODevice
from winotify import Notification, audio
from functools import partial
from module import res_rc
from loguru import logger
from module.power_event_loop import PowerEventListener, POWERBROADCAST_SETTING, win32gui, win32con, cast, POINTER
from module.cmd_task import CmdTask
from module.user_config import SaveUserConfig
from module.audio_choice import AudioType


class PowerMenu(QMenu):
    startup_dir = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs',
                               'Startup')  # 开机目录
    current_path = os.path.abspath(sys.argv[0])
    software_path = os.path.dirname(current_path)
    software_name = os.path.basename(current_path)
    target = os.path.join(software_path, software_name)
    link_name = os.path.splitext(software_name)[0]
    shortcut_path = os.path.join(startup_dir, link_name + '.lnk')

    def __init__(self):
        super(PowerMenu, self).__init__()
        self.config = SaveUserConfig()
        self.thread = PowerEventTimer()
        self.config_content_dict = self.config.getConfig(exist_ok=True)[0]  # 加载配置
        self.guid = CmdTask.getCurrentPlan()
        self.power_choice_actions = []  # 存储菜单中选项的内存地址
        self.voice_choice_actions = []
        self.voice_buttons = None
        self.action = None
        self.notice, self.dtype, self.start_with_windows = None, None, None
        self.pid = os.getpid()
        self.power_cfg: dict = {}
        # 创建系统托盘图标和菜单
        self.icon = QSystemTrayIcon(QIcon(':powercfg.ico'), self)
        self.menu = QMenu(self)
        self.voice_menu = QMenu("voice_selection")

        self.power_box: dict = {}  # 存储电源选项的字典 k0类型(别名)v1控件地址
        self.voice_box: dict = {}  # 存储提示音选项的k0类型v1控件地址
        self.initMenu()  # 初始化操作
        self.band()  # 绑定按键

    def initMenu(self):
        self.power_cfg: dict = CmdTask.getPowerConfig()  # 获取所有电源选项
        self.taskBarMenu()
        if self.loadConfig(only_check=True):  # 生成配置文件
            logger.info(f'当前运行PID:{self.pid}')
            self.loadConfig()
        self.thread.start()  # 启动获取电源改变循环

    def band(self):
        for i in self.voice_box.items():
            self.voice_choice_actions.append(i[1])
        for j in self.voice_choice_actions:
            data = j.data()
            j.triggered.connect(partial(lambda d=data: self.updateVoiceBoxState(data=d)))
        for m in self.power_box.items():
            self.power_choice_actions.append(m[1])
        for n in self.power_choice_actions:
            data = n.data()
            n.triggered.connect(partial(lambda d=data: self.updatePowerBoxState(powercfg=None, data=d)))
        self.icon.activated.connect(self.startPwoerConfigPanel)
        self.quit_button.triggered.connect(self.quit)
        self.is_notice_button.triggered.connect(
            lambda: self.updateVoiceBoxState(data=self.is_notice_button.data()))
        self.startup.triggered.connect(self.startWithWindows)
        self.thread.power_plan_changed.connect(self.updatePowerBoxState)

    def show_pay_dialog(self):
        pay_image = QIcon(':pay.png')
        pixmap = pay_image.pixmap(pay_image.availableSizes()[0])  # 获取 QIcon 的原始大小
        # 将 QPixmap 转换为字节数组
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.WriteOnly)
        pixmap.save(buffer, 'PNG')  # 将 QPixmap 以 PNG 格式保存到缓冲区
        buffer.close()
        # 将字节流转换为 PIL Image
        image = Image.open(BytesIO(byte_array))
        image.show()

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
                    if self.islinkExists():
                        self.start_with_windows = True
                        self.startup.setChecked(True)
                    else:
                        self.start_with_windows = False
                        self.startup.setChecked(False)
                    self.pid = os.getpid()
                    self.config.updateConfig(config_dict=self.config_content_dict,
                                             notice=self.notice,
                                             dtype=self.dtype,
                                             start_with_windows=self.start_with_windows,
                                             pid=self.pid
                                             )
                except Exception as e:
                    logger.error(f'错误:{e.with_traceback()}')
                    self.config.removeConfig()

    @staticmethod
    def get_target_path(shortcut_path):  # lnk的地址
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(shortcut_path)
        target_path = shortcut.TargetPath
        return target_path

    @staticmethod
    def change_target_path(shortcut_path, new_target_path):  # lnk地址,新的实际软件地址
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(shortcut_path)
            shortcut.TargetPath = new_target_path
            shortcut.Save()
            return True
        except:
            os.remove(shortcut_path)
            return False

    def startWithWindows(self):
        # TODO:根据配置打沟
        if self.startup.isChecked():
            # 在用户的启动目录中创建快捷方式
            shell = win32com.client.Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(PowerMenu.shortcut_path)
            shortcut.Targetpath = PowerMenu.target
            shortcut.save()
            self.powerChangeNotice(change_plan_content='设置成功',
                                   title='设置开机自启') if self.is_notice_button.isChecked() else 0
            self.start_with_windows = True
            self.config.updateConfig(config_dict=self.config_content_dict, start_with_windows=self.start_with_windows)
            logger.success('设置开机自启')
        else:
            try:
                os.remove(PowerMenu.shortcut_path)
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
        shortcut_path = PowerMenu.shortcut_path  # 获取快捷方式地址
        if os.path.exists(shortcut_path):  # 判断快捷方式是否存在
            link_target = PowerMenu.get_target_path(shortcut_path)  # 得到存在的快捷方式的目标地址
            actual_software_target = PowerMenu.target
            res = True
            if link_target != actual_software_target:  # 如果目标地址不等于软件现在的地址
                res = PowerMenu.change_target_path(shortcut_path=shortcut_path,
                                                   new_target_path=actual_software_target)  # 重新更改目标地址以为现在的软件地址
                if res:
                    logger.warning(f'快捷方式目标地址与软件地址不一致 已自动更新为:{actual_software_target}')
                else:
                    logger.error(f'快捷方式目标地址与软件地址不一致 更新失败 已删除快捷方式')
            return res  # 并返回True
        else:
            return False  # 不存在返回False

    def quit(self):
        _pid, notice, dtype, startWithWindows = self.matchCurrentConfigFile()
        pid = 0  # 正常退出的标识0
        self.config.updateConfig(config_dict=self.config_content_dict, pid=pid, notice=notice, dtype=dtype,
                                 start_with_windows=startWithWindows)
        self.thread.stop()
        QApplication.quit()

    @staticmethod
    def cancelALLSelection(address_lst: list) -> None:
        # 取消勾选所有选项框
        for _ in address_lst:
            _.setChecked(False)

    def setPlan(self, name, guid) -> None:
        """设定当前系统电源方案
        key:
            电源计划的别称
        value:
            电源计划所对应的唯一的GUID
        """

        # 设置用户选择的电源方案
        CmdTask.setPlan(name, guid)
        logger.info(f"电源方案调整为:{name} GUID:{guid}")
        self.powerChangeNotice(change_plan_content=name) if self.is_notice_button.isChecked() else None

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

        return self.pid, self.notice, self.dtype, self.start_with_windows

    def updatePowerBoxState(self, powercfg, data=False):  # 处理在非本软件改变的电源计划

        if data:
            name, guid, address = data

        elif powercfg:
            name, guid = powercfg
        self._updatePowerPlanMenu()
        self.setPlan(name=name, guid=guid)

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

    @staticmethod
    def startPwoerConfigPanel(reason):
        if reason == QSystemTrayIcon.DoubleClick:  # 双击左键打开控制面板的电源选项
            CmdTask.startPwoerConfigPanel()

    def _updatePowerPlanMenu(self):
        current_guid = CmdTask.getCurrentPlan()[1]
        key_word = {str(action.text()): action for action in self.power_choice_actions}
        power_cfg = CmdTask.getPowerConfig()
        # 获取当前电源计划
        # 创建别称和内存地址的字典
        # 获取当前电源选项的实际值
        # 遍历电源选项配置
        # todo : 找出实际勾选的进行判断，而不是一味地无脑勾选
        # res = [i.isChecked() for i in self.power_choice_actions]
        # print(res)
        for key, compare_guid in power_cfg.items():
            if compare_guid == current_guid:
                # 如果当前GUID对应的别称在菜单中，则选中该菜单项
                # logger.error(key_word)
                action = key_word.get(key)
                if action:
                    PowerMenu.cancelALLSelection(self.power_choice_actions)
                    action.setChecked(True)
                    # self.setPlan(value=getCurrentPlan()[1], key=key)
                    self.icon.setToolTip(f'当前电源方案:{key}')
                    logger.success(f'已更新')
                    # 返回当前电源计划的值
                    return compare_guid
        return None

    def taskBarMenu(self):  # 定义任务栏右边的图标

        # 创建系统托盘图标和菜单
        self.icon = QSystemTrayIcon(QIcon(':powercfg.ico'), self)
        self.menu = QMenu(self)
        self.voice_menu = QMenu("voice_selection")
        self.power_box: dict = {}  # 存储电源选项的字典 k0类型(别名)v1控件地址
        self.voice_box: dict = {}  # 存储提示音选项的k0类型v1控件地址
        # 获取当前电源配置

        power_cfg = CmdTask.getPowerConfig()
        # 匹配电源选项并为每个选项创建 QAction 对象
        for key, value in power_cfg.items():
            self.action = QAction(key, self, checkable=True)  # 创建QAction对象，文本为电源选项名称
            # name,guid,address
            self.power_box[key] = self.action  # 存储电源选项的字典 k0类型(别名)v1控件地址
            self.menu.addAction(self.action)  # 将QAction对象添加到菜单中
            self.action.setData((key, value, self.action))
        # 将菜单设置为系统托盘图标的上下文菜单

        voice_cfg = {}
        for i in AudioType:  # 改为字典推导式
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

        self.pay_to_writer = QAction('捐赠作者:我不是盘神', self, checkable=False, triggered=self.show_pay_dialog)

        self.menu.addAction(self.pay_to_writer)
        self.menu.addSeparator()

        self.quit_button = QAction('退出', self)
        self.menu.addAction(self.quit_button)
        self.icon.setToolTip(f'当前电源方案:{CmdTask.getCurrentPlan()[0]}')
        # 显示小图标
        self.icon.show()

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
                        PowerMenu.cancelALLSelection(self.voice_choice_actions)
                    # 如果配置类型不是禁用音频，则取消所有选项的选中状态，并选中与配置类型匹配的选项
                    else:
                        PowerMenu.cancelALLSelection(self.voice_choice_actions)
                        k0valuev1_address[1].setChecked(True)
                        self.dtype = k0valuev1_address[0]
                        self.config.updateConfig(config_dict=self.config_content_dict, dtype=self.dtype,
                                                 notice=self.notice)


class PowerEventTimer(QThread, PowerEventListener):
    power_plan_changed = Signal(tuple)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False

    def run(self):
        self.running = True
        hwnd = self.create_window()
        self.register_power_setting_notification(hwnd)
        logger.info('已开启监听')
        self.timer = QTimer()
        self.timer.timeout.connect(win32gui.PumpMessages())
        self.timer.start(500)

    def stop(self):
        self.timer.stop()
        self.quit()
        logger.success('\n监听已退出')

    def handle_power_setting_change(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_POWERBROADCAST and wparam == PowerEventListener.PBT_POWERSETTINGCHANGE:
            settings = cast(lparam, POINTER(POWERBROADCAST_SETTING)).contents
            power_setting = str(settings.PowerSetting)
            if power_setting == PowerEventListener.GUID_POWERSCHEME_PERSONALITY:
                self.power_plan_changed.emit(CmdTask.getCurrentPlan())


def run_menu():
    app = QApplication(sys.argv)
    menu = PowerMenu()
    menu.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    suc = SaveUserConfig()
    pid = suc.getConfig()[0].get('pid')
    if pid == 0:
        run_menu()
        logger.success('通过初始化配置或者正常退出打开')
    else:
        pid_lst: list = psutil.pids()
        if pid in pid_lst:
            logger.success('软件已存在，不能多开')
            logger.error(f'pid已经在:{pid}在列表{pid_lst.index(pid)}中')
            CmdTask.startPwoerConfigPanel()
        else:
            run_menu()
            logger.success('通过异常退出打开')
            logger.info(f'pid:{pid}不在进程列表中')

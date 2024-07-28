# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/3/26 16:59
# File:powerbar.py
import os
import sys
import win32com.client
from PySide6.QtGui import QIcon, QAction, QActionGroup
from PySide6.QtCore import QThread, Signal, QTimer, QSize, QSharedMemory
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from winotify import Notification, audio
import module
from module import res_rc
from loguru import logger
from module.cmd_task import CmdTask
from module.audio_choice import AudioType
from module.user_config import SaveUserConfig, ImageView, setup_logger_config
from module.power_event_loop import PowerEventListener, POWERBROADCAST_SETTING, win32gui, win32con, cast, POINTER


class PowerMenu(QMenu):
    startup_dir = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs',
                               'Startup')  # 开机目录
    current_path = os.path.abspath(sys.argv[0])
    software_path = os.path.dirname(current_path)
    software_name = os.path.basename(current_path)
    target = os.path.join(software_path, software_name)
    link_name = os.path.splitext(software_name)[0]
    shortcut_path = os.path.join(startup_dir, link_name + '.lnk')
    version = module.version
    icon_path = os.path.join(SaveUserConfig.app_default_dir, 'powercfg.png')
    log_path = os.path.join(SaveUserConfig.app_default_dir, 'powerbar.log')
    setup_logger_config(log_path=log_path)

    def __init__(self):
        super(PowerMenu, self).__init__()
        self.config = SaveUserConfig()
        self.thread = PowerEventTimer()
        self.config_content_dict = self.config.getConfig(exist_ok=True)[0]  # 加载配置
        self.guid = CmdTask.getCurrentPlan()
        self.power_choice_actions = QActionGroup(self)
        self.voice_choice_actions = QActionGroup(self)
        self.voice_buttons = None
        self.power_buttons = None
        self.notice, self.dtype, self.start_with_windows = None, None, None
        self.pid = app_pid
        self.power_cfg: dict = {}
        # 创建系统托盘图标和菜单
        self.icon = QSystemTrayIcon(QIcon(':powercfg.ico'), self)
        self.menu = QMenu(self)
        self.voice_menu = QMenu("voice_selection")
        self.power_box: dict = {}  # 存储电源选项的字典 k0类型(别名)v1控件地址
        self.voice_box: dict = {}  # 存储提示音选项的k0类型v1控件地址
        self.initMenu()  # 初始化操作
        self.band()  # 绑定按键
        self.pay_dialog = ImageView

    def initMenu(self):
        self.power_cfg: dict = CmdTask.getPowerConfig()  # 获取所有电源选项
        self.taskBarMenu()
        if self.loadConfig(only_check=True):  # 生成配置文件
            logger.info(f'当前运行PID:{self.pid}。')
            self.loadConfig()
        self.thread.start()  # 启动获取电源改变循环

    def band(self):
        self.power_choice_actions.triggered.connect(self.updatePowerBoxState)
        self.voice_choice_actions.triggered.connect(self.updateVoiceBoxState)
        self.icon.activated.connect(self.startPwoerConfigPanel)
        self.quit_button.triggered.connect(self.quit)
        self.is_notice_button.triggered.connect(
            lambda: self.updateVoiceBoxState(data=self.is_notice_button.data()))
        self.startup.triggered.connect(self.startWithWindows)
        self.thread.power_plan_changed.connect(self.updatePowerBoxState)

    def showPayDialog(self):
        image_pay: QIcon = QIcon(':pay.png')
        self.pay_dialog: ImageView = ImageView(image_pay, QIcon(':powercfg.ico'), parent=self)

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
                    self.config.updateConfig(config_dict=self.config_content_dict,
                                             notice=self.notice,
                                             dtype=self.dtype,
                                             start_with_windows=self.start_with_windows
                                             )
                except Exception as e:
                    logger.error(f'错误:{e.with_traceback()}。')
                    self.config.removeConfig()

    def taskBarMenu(self):  # 定义任务栏右边的图标
        # 创建系统托盘图标和菜单
        self.icon = QSystemTrayIcon(QIcon(':powercfg.ico'), self)
        self.menu = QMenu(self)
        self.voice_menu = QMenu("voice_selection")
        self.power_box: dict = {}  # 存储电源选项的字典 k0类型(别名)v1控件地址
        self.voice_box: dict = {}  # 存储提示音选项的k0类型v1控件地址
        # 获取当前电源配置
        # 匹配电源选项并为每个选项创建 QAction 对象
        for name, guid in CmdTask.getPowerConfig().items():
            self.power_buttons = QAction(name, self, checkable=True)  # 创建QAction对象，文本为电源选项名称
            self.power_box[name] = self.power_buttons  # 存储电源选项的字典 k0类型(别名)v1控件地址
            self.menu.addAction(self.power_buttons)  # 将QAction对象添加到菜单中
            self.power_buttons.setData((name, guid))
            self.power_choice_actions.addAction(self.power_buttons)
        for name, dtype in {i: i.value for i in AudioType}.items():
            self.voice_buttons = QAction(name.text(), self, checkable=True)
            self.voice_box[name] = self.voice_buttons
            self.voice_menu.addAction(self.voice_buttons)
            self.voice_buttons.setData((name.text(), dtype))
            self.voice_choice_actions.addAction(self.voice_buttons)
        self.icon.setContextMenu(self.menu)
        self.menu.addSeparator()
        self.startup = QAction('开机启动', self, checkable=True)
        self.menu.addAction(self.startup)
        self.is_notice_button = QAction('通知', self, checkable=True)
        self.menu.addSeparator()
        self.menu.addAction(self.is_notice_button)
        self.is_notice_button.setData(self.is_notice_button)
        self.menu.addSeparator()
        self.pay_to_writer = QAction('捐赠作者:我不是盘神', self, checkable=False, triggered=self.showPayDialog)
        self.menu.addAction(self.pay_to_writer)
        self.menu.addSeparator()
        self.quit_button = QAction('退出', self)
        self.menu.addAction(self.quit_button)
        self.icon.setToolTip(f'当前电源方案:{CmdTask.getCurrentPlan()[0]}')
        # 显示小图标
        self.icon.show()

    def startWithWindows(self):
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
            logger.success('设置开机自启。')
        else:
            try:
                os.remove(PowerMenu.shortcut_path)
                self.powerChangeNotice(change_plan_content='取消成功',
                                       title='设置开机自启') if self.is_notice_button.isChecked() else 0
                self.start_with_windows = False
                self.config.updateConfig(config_dict=self.config_content_dict,
                                         start_with_windows=self.start_with_windows)
                logger.success('取消开机自启。')
            except:
                self.powerChangeNotice(change_plan_content='未知错误',
                                       title='设置开机自启') if self.is_notice_button.isChecked() else 0
                logger.error('未找到文件,可能已删除,取消开机自启失败!')

    def islinkExists(self) -> bool:
        shortcut_path = PowerMenu.shortcut_path  # 获取快捷方式地址
        if os.path.exists(shortcut_path):  # 判断快捷方式是否存在
            link_target = PowerMenu.get_target_path(shortcut_path)  # 得到存在的快捷方式的目标地址
            actual_software_target = PowerMenu.target
            res = True
            if link_target != actual_software_target:  # 如果目标地址不等于软件现在的地址
                res = PowerMenu.changeTargetPath(shortcut_path=shortcut_path,
                                                 new_target_path=actual_software_target)  # 重新更改目标地址以为现在的软件地址
                if res:
                    logger.warning(f'快捷方式目标地址与软件地址不一致,已自动更新为:{actual_software_target}。')
                else:
                    logger.error(f'快捷方式目标地址与软件地址不一致,更新失败,已删除快捷方式!')
            return res  # 并返回True
        else:
            return False  # 不存在返回False

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

        return self.notice, self.dtype, self.start_with_windows

    def updatePowerBoxState(self, data, force=False):
        inner = False
        self.thread.pause()
        if isinstance(data, QAction):
            inner = True
            self.thread.power_plan_changed.disconnect(self.updatePowerBoxState)
            # 内部触发,外部触发控件已暂时解绑
            name, guid = data.data()
        elif isinstance(data, tuple):
            force = True
            name, guid = data
        else:
            return
        current_guid = CmdTask.getCurrentPlan()[1]
        [i.setChecked(True) for i in self.power_choice_actions.actions() if force and i.text() == name]
        CmdTask.setPlan(name, guid) if guid != current_guid or force else 0
        self.icon.setToolTip(f'当前电源方案:{name}。')
        self.powerChangeNotice(change_plan_content=name) if self.is_notice_button.isChecked() else None
        if inner:
            QTimer().singleShot(200,
                                lambda: self.thread.power_plan_changed.connect(self.updatePowerBoxState))
        QTimer().singleShot(200,
                            lambda: self.thread.restore())

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
            name, self.dtype = data.data()
            logger.debug(f'当前提示音:{name},编号:{self.dtype}。')
            if self.dtype == AudioType.Disabled.value:
                self.notice = False
                self.is_notice_button.setChecked(False)  # 那么勾选通知菜单
                self.is_notice_button.setMenu(None)  # 设置为提示音菜单
            self.config.updateConfig(config_dict=self.config_content_dict, dtype=self.dtype, notice=self.notice)

    def powerChangeNotice(self, change_plan_content, title=False):
        icon_path = PowerMenu.icon_path
        if not os.path.exists(icon_path):
            logger.info(f'通知图标文件不存在,正在重新生成图标文件!')
            icon = QIcon(':powercfg.png')
            pixmap_icon = icon.pixmap(QSize(256, 256))
            pixmap_icon.save(PowerMenu.icon_path)
        toast = Notification(app_id="电源选项",
                             title="电源选项调整" if not title else title,
                             msg=change_plan_content,
                             icon=icon_path,
                             duration='short')
        type_attribute: dict = {AudioType.Default: audio.Default,
                                AudioType.IM: audio.IM,
                                AudioType.Mail: audio.Mail,
                                AudioType.Reminder: audio.Reminder,
                                AudioType.Disabled: audio.Silent}
        for i in AudioType:
            if self.config_content_dict['type'] == i.value:
                toast.set_audio(type_attribute[i], loop=False) if self.config_content_dict['notice'] == True else 0
        toast.show()

    def quit(self):
        notice, dtype, startWithWindows = self.matchCurrentConfigFile()
        self.config.updateConfig(config_dict=self.config_content_dict, notice=notice, dtype=dtype,
                                 start_with_windows=startWithWindows)
        self.thread.stop()
        # v2.0/v2.0-noad修复原本从配置文件读取的pid存在退出前篡改pid弊端
        logger.success(f'程序退出,PID:{app_pid}。')
        try:
            CmdTask.killPidToExit(app_pid)
        except Exception as e:
            logger.error(e)
            exit()

    @staticmethod
    def startPwoerConfigPanel(reason):
        if reason == QSystemTrayIcon.DoubleClick:  # 双击左键打开控制面板的电源选项
            CmdTask.startPwoerConfigPanel()

    @staticmethod
    def get_target_path(shortcut_path):  # lnk的地址
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(shortcut_path)
        target_path = shortcut.TargetPath
        return target_path

    @staticmethod
    def changeTargetPath(shortcut_path, new_target_path):  # lnk地址,新的实际软件地址
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(shortcut_path)
            shortcut.TargetPath = new_target_path
            shortcut.Save()
            return True
        except:
            os.remove(shortcut_path)
            return False


class PowerEventTimer(QThread, PowerEventListener):
    power_plan_changed = Signal(tuple)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self.delay = 1
        self.timer = QTimer()

    def run(self):
        self.running = True
        self.register_power_setting_notification()
        self.timer.timeout.connect(win32gui.PumpMessages())
        logger.info('监听已开启!')
        self.timer.start(self.delay)

    def pause(self):
        logger.info('监听已暂停!')
        self.timer.stop()

    def restore(self):
        logger.info('监听已恢复!')
        self.timer.start(self.delay)

    def stop(self):
        self.timer.stop()
        self.running = False
        self.quit()
        logger.success('监听已退出。')

    def handle_power_setting_change(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_POWERBROADCAST and wparam == PowerEventListener.PBT_POWERSETTINGCHANGE:
            settings = cast(lparam, POINTER(POWERBROADCAST_SETTING)).contents
            power_setting = str(settings.PowerSetting)
            if power_setting == PowerEventListener.GUID_POWERSCHEME_PERSONALITY:
                name, guid = CmdTask.getCurrentPlan()
                self.power_plan_changed.emit((name, guid))
                logger.info(f"电源方案调整为:{name},GUID:{guid}。")


if __name__ == '__main__':  # v2.1/v2.1noad解决了异常退出时,误检测为多开而导致可能打不开的问题
    # v2.1/v2.1noad解决启动时配置文件读取两次的问题
    share = QSharedMemory('powerbar')
    if share.attach():
        logger.success('软件已存在,不能多开!')
        CmdTask.startPwoerConfigPanel()
    if share.create(1):
        app = QApplication(sys.argv)
        app_pid = app.applicationPid()
        menu = PowerMenu()
        menu.show()
        logger.success('软件启动成功!')
        app.exec()
        sys.exit(app.exec())

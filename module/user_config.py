# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/4/3 16:26
# File:user_config
import os
import json
from Powerbar.module.cmd_task import CmdTask
from loguru import logger
from Powerbar.module.audio_choice import AudioType



class SaveUserConfig:
    config_name = 'config.json'
    without_ext_software_name = 'PowerBar'
    app_default_dir = os.path.join(os.getenv('APPDATA'), without_ext_software_name)
    app_temp_dir = os.path.join(os.environ.get('TEMP'), without_ext_software_name)
    default_config_path = os.path.join(app_default_dir, config_name)
    temp_config_path = os.path.join(app_temp_dir, config_name)

    def __init__(self):
        self.current_plan = CmdTask.getCurrentPlan()[1]
        self.key_num = 4  # 配置文件中键的个数
        self.power_cfg = CmdTask.getPowerConfig()
        for i in self.power_cfg.items():
            if i[1] == self.current_plan:
                logger.info(f'当前的电源计划为:{i[0]} GUID:{self.current_plan}')
        try:
            self.config_path = self.getConfig(exist_ok=True)[1]
        except TypeError:
            self.removeConfig()
            self.config_path = self.getConfig(exist_ok=True)[1]
        finally:
            logger.info(f'配置文件路径:{self.getConfig(exist_ok=True)[1]}配置加载成功！')

    def configTemplate(self):  # 配置模板
        config = {
            "notice": True,
            "type": AudioType.Default.value,
            "startWithWindows": False,
            "pid": 0
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

    def updateConfig(self, config_dict, pid=None,
                     notice=None,
                     dtype=None,
                     start_with_windows=None,
                     exist_ok=False):  # 改
        self.existOk() if exist_ok else 0
        compare_dict: dict = {
            "notice": notice,
            "type": dtype,
            "startWithWindows": start_with_windows,
            "pid": pid
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




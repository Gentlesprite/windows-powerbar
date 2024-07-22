# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/4/3 16:03
# File:task_mission
import re
import subprocess
from loguru import logger


class CmdTask:
    @staticmethod
    def startPwoerConfigPanel():
        subprocess.call(['control', 'powercfg.cpl'], creationflags=subprocess.CREATE_NO_WINDOW)

    @staticmethod
    def getPowerConfig() -> dict:
        # 执行命令并捕获输出
        try:
            result = subprocess.run(['powercfg', '/l'], capture_output=True, text=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
            # 使用正则表达式匹配电源方案的名称和对应的 GUID
            pattern = re.compile(r'GUID:\s*([\w-]+)\s*\((.+)\)')
            matches = pattern.findall(result.stdout)
            power_cfg = {name: guid for guid, name in matches}
            return power_cfg  # k0别名，v1 guid
        except Exception as e:
            print("Error occurred:", e)
        return ''

    @staticmethod
    def getCurrentPlan() -> tuple:  # (name,guid)
        # 获取当前的电源方案
        try:
            result = subprocess.run(['powercfg', '/getactivescheme'], capture_output=True, text=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
            pattern = re.compile(r'GUID:\s*([\w-]+)\s*\((.+)\)')
            match = pattern.search(result.stdout)
            if match:
                return match.group(2), match.group(1)
            else:
                return ()
        except Exception as e:
            logger.error(f'Error occurred:{e}')
        return ()
    @staticmethod
    def setPlan(name,guid) -> None:
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
        subprocess.run(['powercfg', '/S', guid], creationflags=subprocess.CREATE_NO_WINDOW)



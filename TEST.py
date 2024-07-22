# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/7/21 12:25
# File:TEST
import wmi
import re

def getCurrentPlan():
    try:
        c = wmi.WMI(namespace='root\cimv2\power')
        power_plans = c.ExecQuery('SELECT * FROM Win32_PowerPlan WHERE IsActive=True')

        for plan in power_plans:
            instance_id = re.search(r'{(.*?)}', plan.InstanceID).group(1)  # 使用正则表达式提取 GUID
            return (plan.ElementName, instance_id)

    except Exception as e:
        print(f"Error: {e}")
        return None



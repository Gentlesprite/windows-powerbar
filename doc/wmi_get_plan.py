# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/7/24 11:08
# File:wmi_get_plan
# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/7/21 12:03
# File:tests
import wmi
import re
from module.cmd_task import CmdTask
def get_power_plans():
    c = wmi.WMI(namespace='root\cimv2\power')

    power_plans = c.ExecQuery('SELECT * FROM Win32_PowerPlan')

    plans = {}
    for plan in power_plans:
        plans[plan.ElementName] = plan.InstanceID

    return plans


def get_active_power_scheme_guid():
    try:
        c = wmi.WMI(namespace='root\cimv2\power')
        power_plans = c.ExecQuery('SELECT * FROM Win32_PowerPlan WHERE IsActive=True')

        for plan in power_plans:
            return plan.InstanceID

    except Exception as e:
        print(f"Error: {e}")
        return None

def get_active_power_scheme():
    try:
        c = wmi.WMI(namespace='root\cimv2\power')
        power_plans = c.ExecQuery('SELECT * FROM Win32_PowerPlan WHERE IsActive=True')

        for plan in power_plans:
            instance_id = re.search(r'{(.*?)}', plan.InstanceID).group(1)  # 使用正则表达式提取 GUID
            return (plan.ElementName, instance_id)

    except Exception as e:
        print(f"Error: {e}")
        return None


def set_active_power_scheme(scheme_guid):
    try:
        c = wmi.WMI(namespace='root\cimv2\power')
        power_plans = c.ExecQuery('SELECT * FROM Win32_PowerPlan')

        for plan in power_plans:

            if plan.InstanceID.endswith(scheme_guid):
                plan.SetActive()
                print(f"Successfully set power scheme to {plan.ElementName}")
                return True

        print(f"Power scheme with GUID {scheme_guid} not found.")
        return False

    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    print(get_active_power_scheme_guid())
    for i in CmdTask.getPowerConfig().items():
        print(i[0],':',i[1])
    success = set_active_power_scheme('Microsoft:PowerPlan\{381b4222-f694-41f0-9685-ff5bb260df2e}')
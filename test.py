# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/3/29 19:04
# File:test
from subprocess import run,CREATE_NO_WINDOW
from re import compile



def getPowerConfig() -> dict:
    # 执行命令并捕获输出
    result = run(['powercfg', '/l'], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
    # 使用正则表达式匹配电源方案的名称和对应的 GUID
    pattern = compile(r'GUID:\s*([\w-]+)\s*\((.+)\)')
    matches = pattern.findall(result.stdout)
    power_cfg = {name: guid for guid, name in matches}
    return power_cfg  # k0别名，v1 guid
a = getPowerConfig()
for i in a.items():
    print(i)
('平衡', '381b4222-f694-41f0-9685-ff5bb260df2e')
('GameTurbo (High Performance)', '4b07589d-18e8-44f1-b457-2577cd9d948b')
('高性能', '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c')
('节能', 'a1841308-3541-4fab-bc81-f71556f20b4a')
('卓越性能', 'bf8ebe4b-d3d0-4448-af53-f0148d10d76d')
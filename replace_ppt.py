#!/usr/bin/env python3
"""
替换 config.plist 中 PP_PhmSoftPowerPlayTable 的 base64 数据
精确匹配旧 base64，替换为新 base64（MCLK State 3: 800MHz → 500MHz）
"""
import re

config_path = '/Volumes/NO NAME/EFI/OC/config.plist'
new_b64 = open('/Users/qian/Downloads/1/vega56_pp_table_mclk_capped.b64', 'r').read().strip()

# 读取 config.plist
with open(config_path, 'r') as f:
    content = f.read()

# 用正则提取 <data>...</data> 中的旧 PPT base64
# PP_PhmSoftPowerPlayTable 紧跟在下一行的 <data> 标签中
pattern = r'(<key>PP_PhmSoftPowerPlayTable</key>\s*<data>)([A-Za-z0-9+/=]+)(</data>)'
match = re.search(pattern, content)
if not match:
    print("ERROR: 未找到 PP_PhmSoftPowerPlayTable 数据！")
    exit(1)

old_b64 = match.group(2)
print(f"旧 base64 长度: {len(old_b64)}")
print(f"新 base64 长度: {len(new_b64)}")
print(f"旧 base64 前 40 字符: {old_b64[:40]}")
print(f"新 base64 前 40 字符: {new_b64[:40]}")

# 确认旧 base64 开头和结尾匹配
assert old_b64[:20] == new_b64[:20], "新旧 base64 开头不一致！"
assert old_b64[-20:] == new_b64[-20:], "新旧 base64 结尾不一致！"

# 执行替换
new_content = content[:match.start(2)] + new_b64 + content[match.end(2):]

# 写回
with open(config_path, 'w') as f:
    f.write(new_content)

print("\n替换完成！")

# 验证
with open(config_path, 'r') as f:
    verify = f.read()
verify_match = re.search(pattern, verify)
if verify_match:
    verify_b64 = verify_match.group(2)
    if verify_b64 == new_b64:
        print("验证通过：config.plist 中的 PPT 已更新为新版本")
    else:
        print("ERROR: 验证失败，PPT 数据不匹配！")
        print(f"期望前 40: {new_b64[:40]}")
        print(f"实际前 40: {verify_b64[:40]}")
else:
    print("ERROR: 验证失败，未找到 PPT 数据！")

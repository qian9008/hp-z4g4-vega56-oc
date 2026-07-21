#!/usr/bin/env python3
"""验证 config.plist 中注入的 PPT 数据是否正确"""
import base64
import struct

# 从 config.plist 提取注入的 PPT data
with open('/Volumes/NO NAME/EFI/OC/config.plist', 'r') as f:
    content = f.read()

start = content.find('<key>PP_PhmSoftPowerPlayTable</key>')
data_start = content.find('<data>', start) + 6
data_end = content.find('</data>', data_start)
injected_b64 = content[data_start:data_end].strip()

# 我们提取的完整 PPT
with open('/Users/qian/Downloads/1/vega56_pp_table_complete.b64', 'r') as f:
    expected_b64 = f.read().strip()

print(f"注入的 Base64 长度: {len(injected_b64)}")
print(f"预期的 Base64 长度: {len(expected_b64)}")
print(f"匹配: {injected_b64 == expected_b64}")

# 解码验证
injected_data = base64.b64decode(injected_b64)
print(f"解码后大小: {len(injected_data)} 字节")
print(f"Revision: 0x{injected_data[0]:02X}")

declared = struct.unpack_from('<H', injected_data, 1)[0]
print(f"声明大小: {declared} 字节")
print(f"实际大小: {len(injected_data)} 字节")
print(f"完整性: {'完整' if len(injected_data) == declared else '不完整'}")

# 显示 GPU 属性区域的三个 PP_ 参数
print()
print("=== config.plist GPU 属性确认 ===")
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'PP_' in line or 'PP_PhmSoftPowerPlayTable' in line:
        print(f"  行 {i+1}: {line.strip()}")

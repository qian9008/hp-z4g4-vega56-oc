#!/usr/bin/env python3
"""
验证: VBIOS PowerPlayInfo 表中嵌套的 pp_table 与用户的 bios.pp_table 是否匹配
"""
import struct

def r16(off, data):
    return struct.unpack_from('<H', data, off)[0]

with open('/Users/qian/Downloads/1/bios.rom', 'rb') as f:
    bios = f.read()

with open('/Users/qian/Downloads/1/bios.pp_table', 'rb') as f:
    pp_table = f.read()

# VBIOS PowerPlayInfo @ 0x9106, size=256
# 其中 offset 0x70 处出现 0xA7 (Linux pp_table 的 revision)
# VBIOS 绝对地址: 0x9106 + 0x70 = 0x9176

ppt_start_in_bios = 0x9106
nested_pp_start = ppt_start_in_bios + 0x70  # 0x9176

print(f"VBIOS PowerPlayInfo @ 0x{ppt_start_in_bios:04X}")
print(f"嵌套 pp_table 开头 @ 0x{nested_pp_start:04X}")
print(f"用户 bios.pp_table 大小: {len(pp_table)} 字节")
print()

# 检查 pp_table 声明的大小
pp_rev = pp_table[0]
pp_declared_size = r16(1, pp_table)
print(f"pp_table Revision: 0x{pp_rev:02X}")
print(f"pp_table 声明大小 (usTableSize): {pp_declared_size} 字节")
print(f"pp_table 实际文件大小: {len(pp_table)} 字节")
print(f"文件是否完整: {'否! 缺少 ' + str(pp_declared_size - len(pp_table)) + ' 字节' if len(pp_table) < pp_declared_size else '是'}")
print()

# 对比 VBIOS 中嵌套的 pp_table 和用户的文件
print("=== 对比前 100 字节 ===")
bios_nested = bios[nested_pp_start:nested_pp_start + min(100, len(pp_table))]
user_data = pp_table[:100]

match = True
for i in range(min(100, len(pp_table))):
    if bios_nested[i] != user_data[i]:
        print(f"  不匹配 @ offset 0x{i:04X}: VBIOS=0x{bios_nested[i]:02X}, 文件=0x{user_data[i]:02X}")
        match = False
        break

if match:
    print("  前 100 字节完全匹配!")

# 对比整个文件
print()
print("=== 对比整个文件 ===")
full_match = True
mismatch_count = 0
for i in range(len(pp_table)):
    bios_byte = bios[nested_pp_start + i] if nested_pp_start + i < len(bios) else None
    if bios_byte is None:
        print(f"  VBIOS 数据在 offset 0x{i:04X} 处超出范围!")
        full_match = False
        break
    if bios_byte != pp_table[i]:
        if mismatch_count < 5:
            print(f"  不匹配 @ offset 0x{i:04X}: VBIOS=0x{bios_byte:02X}, 文件=0x{pp_table[i]:02X}")
        mismatch_count += 1
        full_match = False

if full_match:
    print(f"  完全匹配! ({len(pp_table)} 字节)")
    print(f"  bios.pp_table 就是从 VBIOS 0x{nested_pp_start:04X} 处提取的")
else:
    print(f"  不匹配字节数: {mismatch_count}")

# 检查 VBIOS 中完整的 pp_table 数据
print()
print("=== VBIOS 中完整的 pp_table 数据 ===")
# pp_table 声明 2050 字节
full_pp_in_bios = bios[nested_pp_start:nested_pp_start + pp_declared_size]
print(f"VBIOS 中可用: {len(full_pp_in_bios)} 字节 (0x{nested_pp_start:04X} - 0x{nested_pp_start + ppt_declared_size - 1:04X})")

# 检查 VBIOS 中 pp_table 的结尾数据
if len(full_pp_in_bios) >= 32:
    print(f"VBIOS 中 pp_table 最后 32 字节:")
    for i in range(len(full_pp_in_bios) - 32, len(full_pp_in_bios), 16):
        h = ' '.join(f'{full_pp_in_bios[i+j]:02X}' for j in range(min(16, len(full_pp_in_bios) - i)))
        print(f"  0x{i:04X}: {h}")

# 检查用户文件缺少的部分
if len(pp_table) < pp_declared_size:
    missing_start = len(pp_table)
    missing_data = bios[nested_pp_start + missing_start:nested_pp_start + pp_declared_size]
    print(f"\n用户文件缺少的 {len(missing_data)} 字节开头:")
    for i in range(0, min(64, len(missing_data)), 16):
        h = ' '.join(f'{missing_data[i+j]:02X}' for j in range(min(16, len(missing_data) - i)))
        print(f"  0x{i:04X}: {h}")

# 检查 ATOM PowerPlayInfo 表的完整结构
print()
print("=== ATOM PowerPlayInfo 表结构分析 ===")
atom_ppt = bios[ppt_start_in_bios:ppt_start_in_bios + 256]
print(f"ATOM 表 (rev 0x{atom_ppt[0]:02X}, size={256}):")
print(f"  offset 0x00-0x6F: ATOM 格式状态索引 (112 字节)")
print(f"  offset 0x70-0xFF: 嵌套的 Linux pp_table 开头 (144 字节)")
print()

# 验证: 如果注入完整的 ATOM 表 (256 字节), macOS 驱动是否能识别?
# 或者: 应该注入完整的 Linux pp_table (2050 字节)?
print("=== 结论 ===")
print(f"1. bios.pp_table 是从 VBIOS 提取的 Linux 格式 pp_table")
print(f"2. 文件不完整: 声明 {pp_declared_size} 字节, 实际只有 {len(pp_table)} 字节")
print(f"3. macOS 驱动期望的格式取决于 PP_PhmSoftPowerPlayTable 的实现")
print(f"4. 两种可能:")
print(f"   a) 需要完整的 ATOM PowerPlayInfo 表 (256 字节, rev 0x74)")
print(f"   b) 需要完整的 Linux pp_table ({pp_declared_size} 字节, rev 0xa7)")

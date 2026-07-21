#!/usr/bin/env python3
"""修正版：验证 bios.pp_table 与 VBIOS 0x917A 处的数据是否匹配"""
import struct
import base64

def r16(off, data):
    return struct.unpack_from('<H', data, off)[0]

with open('/Users/qian/Downloads/1/bios.rom', 'rb') as f:
    bios = f.read()

with open('/Users/qian/Downloads/1/bios.pp_table', 'rb') as f:
    pp_table = f.read()

# 正确的嵌套 pp_table 开头位置: VBIOS 0x9106 + 0x74 = 0x917A
nested_start = 0x917A

print(f"VBIOS 嵌套 pp_table 开头: 0x{nested_start:04X}")
print(f"用户 bios.pp_table 大小: {len(pp_table)} 字节")
print()

# pp_table 声明大小
pp_rev = pp_table[0]
pp_declared_size = r16(1, pp_table)
print(f"pp_table Revision: 0x{pp_rev:02X}")
print(f"pp_table 声明大小 (usTableSize): {pp_declared_size} 字节")
print(f"pp_table 实际文件大小: {len(pp_table)} 字节")
if len(pp_table) < pp_declared_size:
    print(f"⚠️  文件不完整! 缺少 {pp_declared_size - len(pp_table)} 字节")
print()

# 对比 VBIOS 0x917A 开始的数据和用户的文件
print("=== 对比验证 ===")
match_count = 0
mismatch_count = 0
for i in range(len(pp_table)):
    bios_byte = bios[nested_start + i] if nested_start + i < len(bios) else None
    if bios_byte is None:
        print(f"VBIOS 数据在 offset 0x{i:04X} 超出范围")
        break
    if bios_byte == pp_table[i]:
        match_count += 1
    else:
        if mismatch_count < 3:
            print(f"  不匹配 @ 0x{i:04X}: VBIOS=0x{bios_byte:02X}, 文件=0x{pp_table[i]:02X}")
        mismatch_count += 1

print(f"  匹配: {match_count}/{len(pp_table)} 字节")
print(f"  不匹配: {mismatch_count}/{len(pp_table)} 字节")

# 提取完整的 pp_table (2050 字节)
print()
print("=== 从 VBIOS 提取完整的 pp_table ===")
full_pp = bios[nested_start:nested_start + pp_declared_size]
print(f"完整大小: {len(full_pp)} 字节")
print(f"VBIOS 地址范围: 0x{nested_start:04X} - 0x{nested_start + pp_declared_size - 1:04X}")

# 验证完整 pp_table 的内容
print(f"\n完整 pp_table 前 64 字节:")
for i in range(0, 64, 16):
    h = ' '.join(f'{full_pp[i+j]:02X}' for j in range(min(16, len(full_pp) - i)))
    print(f"  0x{i:04X}: {h}")

print(f"\n完整 pp_table 最后 48 字节:")
start = len(full_pp) - 48
for i in range(start, len(full_pp), 16):
    h = ' '.join(f'{full_pp[i+j]:02X}' for j in range(min(16, len(full_pp) - i)))
    print(f"  0x{i:04X}: {h}")

# 保存完整的 pp_table
out_bin = '/Users/qian/Downloads/1/vega56_pp_table_complete.bin'
with open(out_bin, 'wb') as f:
    f.write(full_pp)
print(f"\n已保存完整 pp_table: {out_bin} ({len(full_pp)} 字节)")

# 生成 Base64
b64 = base64.b64encode(full_pp).decode('ascii')
out_b64 = '/Users/qian/Downloads/1/vega56_pp_table_complete.b64'
with open(out_b64, 'w') as f:
    f.write(b64)
print(f"已保存 Base64: {out_b64} ({len(b64)} 字符)")

# 同时提取完整的 ATOM PowerPlayInfo 表 (256 字节, rev 0x74)
print()
print("=== ATOM PowerPlayInfo 表 (256 字节, rev 0x74) ===")
atom_ppt = bios[0x9106:0x9106 + 256]
atom_b64 = base64.b64encode(atom_ppt).decode('ascii')
print(f"大小: {len(atom_ppt)} 字节")
print(f"Base64 长度: {len(atom_b64)} 字符")
atom_out = '/Users/qian/Downloads/1/vega56_atom_powerplay.b64'
with open(atom_out, 'w') as f:
    f.write(atom_b64)
print(f"已保存: {atom_out}")

# 总结
print()
print("=" * 70)
print("总结")
print("=" * 70)
print(f"""
1. bios.pp_table (679 字节, rev 0xa7):
   - 来源: VBIOS 0x{nested_start:04X} 处的嵌套 Linux pp_table
   - 问题: 声明 {pp_declared_size} 字节但只有 {len(pp_table)} 字节 → 不完整
   - 格式: Linux amdgpu 驱动的 pp_table 格式

2. VBIOS 中的完整 pp_table ({pp_declared_size} 字节, rev 0xa7):
   - 已提取到 vega56_pp_table_complete.bin
   - 格式: 同上, 但完整

3. VBIOS 中的 ATOM PowerPlayInfo (256 字节, rev 0x74):
   - 已提取到 vega56_atom_powerplay.b64
   - 格式: ATOM 格式 (macOS 驱动原生支持的格式)
   - 包含状态索引 + 嵌套的 pp_table 开头

关键问题: macOS 驱动的 PP_PhmSoftPowerPlayTable 需要哪种格式?
""")

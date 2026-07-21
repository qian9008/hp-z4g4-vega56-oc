#!/usr/bin/env python3
"""
对比分析:
1. VBIOS 中的 ATOM PowerPlayInfo (256 字节, rev 0x74)
2. VBIOS 中的 ATOM PowerPlayInfo_V2 (515 字节, rev 0x27)
3. 用户的 bios.pp_table (679 字节, rev 0xa7, Linux 格式)
"""
import struct
import base64

def r16(off, data):
    return struct.unpack_from('<H', data, off)[0]

# 读取 VBIOS
with open('/Users/qian/Downloads/1/bios.rom', 'rb') as f:
    bios = f.read()

# 读取用户的 pp_table
with open('/Users/qian/Downloads/1/bios.pp_table', 'rb') as f:
    pp_table = f.read()

print("=" * 70)
print("1. VBIOS PowerPlayInfo (索引13) @ 0x9106")
print("=" * 70)
pp1_off = 0x9106
pp1_rev = bios[pp1_off]
pp1_size = r16(pp1_off + 1, bios)
pp1_data = bios[pp1_off:pp1_off + pp1_size]
print(f"  Revision: 0x{pp1_rev:02X} ({pp1_rev})")
print(f"  Size: {pp1_size} 字节")
print(f"  完整十六进制 dump:")
for i in range(0, pp1_size, 16):
    h = ' '.join(f'{pp1_data[i+j]:02X}' for j in range(min(16, pp1_size - i)))
    print(f"    0x{i:04X}: {h}")

print()
print("=" * 70)
print("2. VBIOS PowerPlayInfo_V2 (索引28) @ 0x94E4")
print("=" * 70)
pp2_off = 0x94E4
pp2_rev = bios[pp2_off]
pp2_size = r16(pp2_off + 1, bios)
pp2_data = bios[pp2_off:pp2_off + pp2_size]
print(f"  Revision: 0x{pp2_rev:02X} ({pp2_rev})")
print(f"  Size: {pp2_size} 字节")
print(f"  完整十六进制 dump:")
for i in range(0, pp2_size, 16):
    h = ' '.join(f'{pp2_data[i+j]:02X}' for j in range(min(16, pp2_size - i)))
    print(f"    0x{i:04X}: {h}")

print()
print("=" * 70)
print("3. 用户的 bios.pp_table (Linux 格式)")
print("=" * 70)
pp_rev = pp_table[0]
# Linux pp_table 的 size 在不同位置
print(f"  Revision: 0x{pp_rev:02X} ({pp_rev})")
print(f"  Size: {len(pp_table)} 字节")
print(f"  前 4 字节: {pp_table[:4].hex()}")
print(f"  完整十六进制 dump:")
for i in range(0, len(pp_table), 16):
    h = ' '.join(f'{pp_table[i+j]:02X}' for j in range(min(16, len(pp_table) - i)))
    a = ''.join(chr(pp_table[i+j]) if 32 <= pp_table[i+j] < 127 else '.' for j in range(min(16, len(pp_table) - i)))
    print(f"    0x{i:04X}: {h}  {a}")

# 分析 Linux pp_table 的结构
print()
print("=" * 70)
print("4. Linux pp_table 结构分析 (Vega 10, rev 0xa7)")
print("=" * 70)

# Vega 10 pp_table 结构 (Linux amdgpu):
# header (rev, size 等)
# 后面是各种 power state 数据

# 尝试解析已知的字段
# 参考: Linux kernel drivers/gpu/drm/amd/powerplay/hwmgr/vega10_pptable.h

# ATOM_Vega10_POWERPLAYTABLE 结构:
# +0: ucTableRevision (0xa7)
# +1: usTableSize (uint16)
# +3: ulGoldenPPTableSize (uint32)
# ...

rev = pp_table[0]
table_size = r16(1, pp_table)
print(f"  ucTableRevision: 0x{rev:02X}")
print(f"  usTableSize: {table_size} (0x{table_size:04X})")

if len(pp_table) >= 7:
    golden_size = struct.unpack_from('<I', pp_table, 3)[0]
    print(f"  ulGoldenPPTableSize: {golden_size}")

if len(pp_table) >= 9:
    # 更多字段
    print(f"  字节 [7-8]: {pp_table[7]:02X} {pp_table[8]:02X}")

# 搜索频率值 (10MHz 单位)
# Vega 56 基础频率约 1156-1271 MHz → 0x0484-0x04F7
# 显存频率约 800 MHz → 0x0320
print()
print("  === 搜索已知频率值 ===")
# 800 MHz = 0x0320 (显存基础频率)
# 167 MHz = 0x00A7 (显存 ULV 频率? 不对, 167MHz = 0x00A7? 不, 0x00A7=167 但这是十进制)
# 实际上频率以 10MHz 为单位: 800MHz = 80 = 0x0050, 167MHz = 16.7 ≈ 17 = 0x11

# 或者频率以 MHz 为单位: 800 = 0x0320, 167 = 0x00A7
for freq_mhz in [167, 500, 800, 852, 900, 1000, 1138, 1156, 1200, 1271, 1400, 1442, 1500, 1600]:
    freq_le = struct.pack('<H', freq_mhz)
    positions = []
    for i in range(len(pp_table) - 1):
        if pp_table[i:i+2] == freq_le:
            positions.append(i)
    if positions:
        print(f"  {freq_mhz} MHz (0x{freq_mhz:04X}) 出现在: {', '.join(f'0x{p:04X}' for p in positions)}")

# 对比两个表中的共同频率值
print()
print("  === VBIOS PowerPlayInfo 末尾频率值 ===")
# 最后 32 字节中有频率值
freqs = []
for i in range(pp1_size - 16, pp1_size, 2):
    v = r16(i, pp1_data)
    if 100 < v < 3000:  # 合理的 MHz 范围
        freqs.append(v)
if freqs:
    print(f"  频率值: {freqs} MHz")

# 检查 Linux pp_table 中 0x70-0x80 区域的频率值
print()
print("  === bios.pp_table 0x70-0x90 区域 ===")
for i in range(0x70, min(0x90, len(pp_table)), 2):
    v = r16(i, pp_table)
    if 100 < v < 3000:
        print(f"  0x{i:04X}: {v} MHz (0x{v:04X})")

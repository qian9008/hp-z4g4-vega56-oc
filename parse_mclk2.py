#!/usr/bin/env python3
"""搜索 PPT 中的 MCLK DPM 状态，包括 800MHz"""
import base64, struct

b64 = open('/Users/qian/Downloads/1/vega56_pp_table_complete.b64','r').read().strip()
data = base64.b64decode(b64)

# 已知频率 (10kHz 单位, LE32)
freqs = {16700: '167MHz', 50000: '500MHz', 60000: '600MHz', 70000: '700MHz', 80000: '800MHz'}

print("=== 搜索所有已知 MCLK 频率 (LE32) ===")
for val, label in sorted(freqs.items()):
    needle = struct.pack('<I', val)
    pos = 0
    found = []
    while True:
        idx = data.find(needle, pos)
        if idx == -1:
            break
        found.append(idx)
        pos = idx + 1
    if found:
        for off in found:
            # 显示前后 16 字节上下文
            ctx_start = max(0, off - 4)
            ctx_end = min(len(data), off + 12)
            ctx = data[ctx_start:ctx_end].hex()
            print(f'  {label}: offset 0x{off:04x}, context: {ctx}')
    else:
        print(f'  {label}: 未找到 ✗')

# 重点: 从 offset 0x0188 开始 dump MCLK DPM 表区域
print()
print("=== Hex dump 0x0180-0x0260 (MCLK DPM 区域) ===")
for base in range(0x0180, min(0x0260, len(data)), 16):
    hex_str = data[base:base+16].hex(' ')
    # 尝试解析每 4 字节为 LE32 频率值
    vals = []
    for i in range(0, 16, 4):
        if base + i + 4 <= len(data):
            v = struct.unpack_from('<I', data, base + i)[0]
            if 1000 < v < 200000:  # 合理频率范围 (10MHz-2000MHz)
                vals.append(f'{v/100:.0f}MHz')
            else:
                vals.append(f'0x{v:08x}')
        else:
            vals.append('--------')
    print(f'  0x{base:04x}: {hex_str}  | {" ".join(vals)}')

# 解析 MCLK dependency table
# 从搜索结果看，MCLK 状态从 0x0191 开始 (167MHz)
# 如果每条记录 8 字节: clock(4) + vddci(2) + vdd(2)
# 或 12 字节: clock(4) + vddInd(2) + vddciInd(2) + vddMemInd(2) + phase(2)
print()
print("=== 尝试按 8 字节记录解析 MCLK DPM (从 0x0191) ===")
base = 0x0191
for i in range(8):
    off = base + i * 8
    if off + 8 <= len(data):
        clock = struct.unpack_from('<I', data, off)[0]
        v1 = struct.unpack_from('<H', data, off + 4)[0]
        v2 = struct.unpack_from('<H', data, off + 6)[0]
        if clock == 0:
            break
        mhz = clock / 100 if clock < 200000 else 0
        print(f'  State {i} @0x{off:04x}: clock={clock} ({mhz:.0f}MHz), v1={v1}, v2={v2}')

print()
print("=== 尝试按 12 字节记录解析 MCLK DPM (从 0x0191) ===")
base = 0x0191
for i in range(8):
    off = base + i * 12
    if off + 12 <= len(data):
        clock = struct.unpack_from('<I', data, off)[0]
        v1 = struct.unpack_from('<H', data, off + 4)[0]
        v2 = struct.unpack_from('<H', data, off + 6)[0]
        v3 = struct.unpack_from('<H', data, off + 8)[0]
        v4 = struct.unpack_from('<H', data, off + 10)[0]
        if clock == 0:
            break
        mhz = clock / 100 if clock < 200000 else 0
        print(f'  State {i} @0x{off:04x}: clock={clock} ({mhz:.0f}MHz), vddInd={v1}, vddciInd={v2}, vddMemInd={v3}, phase={v4}')

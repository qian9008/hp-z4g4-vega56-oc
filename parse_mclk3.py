#!/usr/bin/env python3
"""精确解析 Vega10 PPT 中的 MCLK DPM 表"""
import base64, struct

b64 = open('/Users/qian/Downloads/1/vega56_pp_table_complete.b64','r').read().strip()
data = base64.b64decode(b64)

print(f"PPT 总长度: {len(data)} 字节")
print()

# 从之前的分析，167MHz (0x413c) 在 offset 0x0191
# 0x0190 处的值是 0x04，可能是 count=4
# 每条记录 7 字节: ulMCLK(4) + ucVddInd(1) + ucVddciInd(1) + ucPhaseShed(1)

# 验证：从 0x0190 开始解析
print("=== MCLK DPM 表 (从 offset 0x0190 开始) ===")
mclk_table_offset = 0x0190
count = data[mclk_table_offset]
print(f"状态数: {count}")
print(f"{'State':>6} {'Offset':>8} {'MCLK(raw)':>12} {'MCLK(MHz)':>10} {'byte5':>6} {'byte6':>6} {'byte7':>6}")

mclk_states = []
for i in range(count):
    rec_off = mclk_table_offset + 1 + i * 7
    if rec_off + 7 <= len(data):
        ulMCLK = struct.unpack_from('<I', data, rec_off)[0]
        b5 = data[rec_off + 4]
        b6 = data[rec_off + 5]
        b7 = data[rec_off + 6]
        mhz = ulMCLK / 100
        mclk_states.append((rec_off, ulMCLK, mhz))
        print(f"{i:>6} 0x{rec_off:04x}   {ulMCLK:>12}   {mhz:>8.0f}   0x{b5:02x}   0x{b6:02x}   0x{b7:02x}")

print()
print("=== 验证：原始 hex dump 0x0190-0x01b0 ===")
for base in range(0x0190, 0x01b0, 16):
    hex_str = ' '.join(f'{b:02x}' for b in data[base:base+16])
    print(f"  0x{base:04x}: {hex_str}")

print()
print("=== MCLK DPM 状态总结 ===")
for i, (off, raw, mhz) in enumerate(mclk_states):
    print(f"  MCLK State {i}: {mhz:.0f}MHz @ offset 0x{off:04x} (raw bytes: {data[off:off+4].hex()})")

# 确认修改方案
if len(mclk_states) >= 4:
    target_off = mclk_states[-1][0]  # 最高状态 (800MHz)
    print()
    print(f"=== 修改方案 ===")
    print(f"  目标: MCLK State {len(mclk_states)-1} @ 0x{target_off:04x}")
    print(f"  原始: {data[target_off:target_off+4].hex()} = {mclk_states[-1][2]:.0f}MHz")
    # 500MHz = 50000 = 0x0000c350
    new_bytes = struct.pack('<I', 50000)
    print(f"  修改为: {new_bytes.hex()} = 500MHz")
    print(f"  影响: 高负载时显存带宽从 410GB/s 降到 256GB/s")
    print(f"  好处: 退出 UVD 后 MCLK 从 800MHz 降到 500MHz")

#!/usr/bin/env python3
"""解析 Vega10 PPT 中的 MCLK DPM 状态表"""
import base64, struct

# 读取完整 PPT
b64 = open('/Users/qian/Downloads/1/vega56_pp_table_complete.b64','r').read().strip()
data = base64.b64decode(b64)

print(f'PPT 总长度: {len(data)} 字节')
print(f'Revision: 0x{data[0]:02x}, ContentSize: 0x{data[1]:02x}')

# Vega10 pp_table header offset 指针
# +0x0C: usStateArrayOffset
# +0x12: usSclkDependencyTableOffset
# +0x14: usMclkDependencyTableOffset  ← 关键
state_offset = struct.unpack_from('<H', data, 0x0C)[0]
sclk_dep_offset = struct.unpack_from('<H', data, 0x12)[0]
mclk_dep_offset = struct.unpack_from('<H', data, 0x14)[0]

print(f'StateArrayOffset:      0x{state_offset:04x}')
print(f'SclkDependencyOffset:  0x{sclk_dep_offset:04x}')
print(f'MclkDependencyOffset:  0x{mclk_dep_offset:04x}')

# 解析 MCLK Dependency Table
# 每条记录 12 字节: ulClock(4) + usVddInd(2) + usVddciInd(2) + usVddMemInd(2) + usPhase(2)
if mclk_dep_offset > 0 and mclk_dep_offset < len(data):
    num_entries = data[mclk_dep_offset]
    print(f'\n=== MCLK DPM 状态表 (共 {num_entries} 个状态) ===')
    for i in range(min(num_entries, 10)):
        rec_off = mclk_dep_offset + 1 + i * 12
        if rec_off + 12 <= len(data):
            ulClock = struct.unpack_from('<I', data, rec_off)[0]
            usVddInd = struct.unpack_from('<H', data, rec_off + 4)[0]
            usVddciInd = struct.unpack_from('<H', data, rec_off + 6)[0]
            usVddMemInd = struct.unpack_from('<H', data, rec_off + 8)[0]
            usPhase = struct.unpack_from('<H', data, rec_off + 10)[0]
            print(f'  MCLK State {i}: {ulClock/100:.0f}MHz (raw={ulClock}), VddInd={usVddInd}, VddciInd={usVddciInd}, VddMemInd={usVddMemInd}, Phase={usPhase}')

# 解析 StateArray (性能状态组合)
if state_offset > 0 and state_offset < len(data):
    num_states = data[state_offset]
    print(f'\n=== Performance States (共 {num_states} 个) ===')
    # 每条 state entry 是变长的，包含 a SCLK/MCLK state indices
    # ATOM_Vega10_State: nonClockInfoIndex(1) + clockInfoIndex array (每个2字节)
    # 让我先 dump 每个状态的 SCLK/MCLK 索引
    # 实际格式: count(1) + entries, 每个 entry 大小取决于版本
    # Vega10: 每个 state entry = 2字节 (nonClockInfoIndex(1) + clockInfoIndex(1))... 不对
    # 实际: usNonClockInfoIndex(2) + usClockInfoIndex(2) per clock domain
    # 让我 hex dump 这部分看看
    print(f'  (raw hex at state_offset 0x{state_offset:04x}:)')
    chunk = data[state_offset:state_offset+min(num_states*6+1, 60)]
    print(f'  {chunk.hex()}')

    # 尝试按 Vega10 state 格式解析
    # ATOM_Vega10_State: 4 bytes (usNonClockInfoIndex(2) + usClockInfoIndex(2))
    # 不对，让我看 Linux 源码格式
    # 实际格式: 每条 state = 1 byte count + clockInfoIndices
    # 先尝试 4 字节一条
    print(f'\n  按每条 4 字节解析:')
    for i in range(min(num_states, 8)):
        off = state_offset + 1 + i * 4
        if off + 4 <= len(data):
            ncidx = struct.unpack_from('<H', data, off)[0]
            cidx = struct.unpack_from('<H', data, off + 2)[0]
            print(f'    State {i}: nonClockInfoIndex={ncidx}, clockInfoIndex={cidx}')

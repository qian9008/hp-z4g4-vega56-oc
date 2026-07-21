#!/usr/bin/env python3
"""在 PPT 二进制中搜索已知的 MCLK 频率值"""
import base64, struct

b64 = open('/Users/qian/Downloads/1/vega56_pp_table_complete.b64','r').read().strip()
data = base64.b64decode(b64)

print(f'PPT 总长度: {len(data)} 字节')
print(f'前 64 字节 hex: {data[:64].hex()}')
print()

# 已知频率值 (10kHz 单位)
targets = {
    16700: '167MHz (ULV)',
    50000: '500MHz',
    60000: '600MHz', 
    80000: '800MHz',
    74000: '740MHz',
    1670: '16.7MHz',
    167: '1.67MHz',
    # 也试试 MHz 直接值
    167: '167 (直接?)',
    500: '500 (直接?)',
    800: '800 (直接?)',
}

print("=== 搜索已知频率值 (4字节 little-endian) ===")
for val, label in targets.items():
    needle_le = struct.pack('<I', val)
    needle_be = struct.pack('>I', val)
    # 也搜索 2 字节
    needle_le2 = struct.pack('<H', val)
    
    pos = 0
    found = []
    while True:
        idx = data.find(needle_le, pos)
        if idx == -1:
            break
        found.append((idx, 'LE32'))
        pos = idx + 1
    
    pos = 0
    while True:
        idx = data.find(needle_le2, pos)
        if idx == -1:
            break
        found.append((idx, 'LE16'))
        pos = idx + 1
    
    if found:
        for off, fmt in found:
            context = data[max(0,off-4):off+8].hex()
            print(f'  {label}: offset 0x{off:04x} ({fmt}), context: ...{context}...')
    else:
        print(f'  {label}: 未找到')

# 也尝试搜索 10kHz 的其他表示
# 167MHz 在某些表中可能是 0x41 0x3C (16700) 或其他编码
print()
print("=== 搜索 0x413C (16700=167MHz in 10kHz, LE16) ===")
needle = b'\x3c\x41'
pos = 0
while True:
    idx = data.find(needle, pos)
    if idx == -1:
        break
    context = data[max(0,idx-4):idx+8].hex()
    print(f'  offset 0x{idx:04x}, context: {context}')
    pos = idx + 1

print()
print("=== 搜索 0xC350 (50000=500MHz in 10kHz, LE16) ===")
needle = b'\x50\xc3'
pos = 0
while True:
    idx = data.find(needle, pos)
    if idx == -1:
        break
    context = data[max(0,idx-4):idx+8].hex()
    print(f'  offset 0x{idx:04x}, context: {context}')
    pos = idx + 1

print()
print("=== 搜索 0x3880 0x0001 (80000=800MHz in 10kHz, LE32) ===")
needle = b'\x80\x38\x01\x00'
pos = 0
while True:
    idx = data.find(needle, pos)
    if idx == -1:
        break
    context = data[max(0,idx-8):idx+12].hex()
    print(f'  offset 0x{idx:04x}, context: {context}')
    pos = idx + 1

# dump offset 0x14 附近的数据看看
print()
print(f"=== offset 0x10-0x30 hex dump ===")
for i in range(0x10, min(0x30, len(data)), 2):
    val = struct.unpack_from('<H', data, i)[0]
    print(f'  0x{i:04x}: 0x{val:04x} ({val})')

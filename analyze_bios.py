#!/usr/bin/env python3
"""分析 VBIOS 结构，搜索 ATOM 签名和 PowerPlay Table"""
import struct

with open('/Users/qian/Downloads/1/AMD Radeon RX Vega 56.bios', 'rb') as f:
    data = f.read()

print(f"VBIOS 大小: {len(data)} 字节")

# 1. 搜索 'ATOM' 签名
print('\n=== 搜索 ATOM 签名 ===')
for i in range(len(data) - 4):
    if data[i:i+4] == b'ATOM':
        print(f'  找到 ATOM @ 0x{i:04X}: {data[i:i+16].hex()}')

# 2. 搜索 'PCIR' 签名
print('\n=== 搜索 PCIR 签名 ===')
for i in range(len(data) - 4):
    if data[i:i+4] == b'PCIR':
        print(f'  找到 PCIR @ 0x{i:04X}: {data[i:i+24].hex()}')

# 3. 搜索 'ATOMBIOS' 字符串
print('\n=== 搜索 ATOMBIOS 字符串 ===')
for i in range(len(data) - 8):
    if data[i:i+8] == b'ATOMBIOS':
        print(f'  找到 ATOMBIOS @ 0x{i:04X}')

# 4. 查看 0x0274 处的数据
print(f'\n=== 0x0274 处数据 ===')
for i in range(0x0274, min(0x0274 + 80, len(data)), 16):
    hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
    print(f'  0x{i:04X}: {hex_str}  {ascii_str}')

# 5. 查看 0x029C 处的数据
print(f'\n=== 0x029C 处数据 (0x18 指针) ===')
for i in range(0x029C, min(0x029C + 80, len(data)), 16):
    hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
    print(f'  0x{i:04X}: {hex_str}  {ascii_str}')

# 6. 宽泛搜索 PowerPlay Table
print('\n=== 宽泛搜索 PowerPlay Table ===')
for i in range(len(data) - 3):
    rev = data[i]
    size = struct.unpack_from('<H', data, i + 1)[0]
    if 1500 <= size <= 3000:
        if i + size <= len(data):
            non_zero = sum(1 for b in data[i+3:i+min(100, size)] if b != 0)
            if non_zero > 40:
                print(f'  候选: offset=0x{i:04X}, rev=0x{rev:02X}, size={size}, non_zero={non_zero}/97')

# 7. 查看 0x60-0x70 区域 (BIOS 信息区)
print(f'\n=== 0x60-0x80 区域 ===')
for i in range(0x60, 0x80, 16):
    hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
    print(f'  0x{i:04X}: {hex_str}  {ascii_str}')

# 8. 搜索 ATOM_ROM_HEADER 的正确方法
# ATOM BIOS Header 通常在 offset 0x48 有指针
# 但也可能在其他位置
# ATOM_ROM_HEADER 以 ucFirmwareType=0x01 开始，后面是 revision
# 签名 "AT" (0x4154) 通常在 offset +2
print('\n=== 搜索可能的 ATOM_ROM_HEADER ===')
for i in range(len(data) - 10):
    if data[i] == 0x01:  # ucFirmwareType = 1 (AtomBios)
        sig = struct.unpack_from('<H', data, i + 2)[0]
        if sig == 0x4154:  # "AT" in little-endian
            print(f'  可能的 ATOM_ROM_HEADER @ 0x{i:04X}')
            for j in range(i, min(i + 48, len(data)), 16):
                hex_str = ' '.join(f'{b:02X}' for b in data[j:j+16])
                print(f'    0x{j:04X}: {hex_str}')

# 9. 也尝试搜索 0x0274 附近的结构
# 如果 ATOM_ROM_HEADER 在 0x0274，它的格式可能不同
print(f'\n=== 0x0260-0x02C0 区域 (0x0274 附近) ===')
for i in range(0x0260, 0x02C0, 16):
    hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
    print(f'  0x{i:04X}: {hex_str}  {ascii_str}')

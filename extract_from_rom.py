#!/usr/bin/env python3
"""
从 bios.rom (256KB 完整 VBIOS) 中提取 ATOM 格式 PowerPlay Table
"""
import struct
import base64

def read_u16(data, off):
    return struct.unpack_from('<H', data, off)[0]

def read_u32(data, off):
    return struct.unpack_from('<I', data, off)[0]

# 读取完整的 256KB VBIOS
with open('/Users/qian/Downloads/1/bios.rom', 'rb') as f:
    data = f.read()

print(f"VBIOS 大小: {len(data)} 字节 ({len(data)/1024:.1f} KB)")

# 验证签名
print(f"签名: {data[0]:02X} {data[1]:02X}")

# 1. 找到 ATOM_ROM_HEADER
rom_header_off = read_u16(data, 0x48)
print(f"\nATOM_ROM_HEADER @ 0x{rom_header_off:04X}")

# 打印 header 数据
print("\n=== ATOM_ROM_HEADER 原始数据 ===")
for i in range(rom_header_off, rom_header_off + 48, 16):
    hex_str = ' '.join(f'{data[j]:02X}' for j in range(i, min(i+16, len(data))))
    ascii_str = ''.join(chr(data[j]) if 32 <= data[j] < 127 else '.' for j in range(i, min(i+16, len(data))))
    print(f"  0x{i:04X}: {hex_str}  {ascii_str}")

# 验证 ATOM 签名 (在 header + 4)
sig = data[rom_header_off + 4 : rom_header_off + 8]
print(f"\nFirmwareSignature: {sig} ({sig.hex()})")

# 2. 尝试多种偏移读取 MasterDataTable
# 标准 ATOM_ROM_HEADER V2:
#   +0x00: ATOM_COMMON_HEADER (4 bytes)
#   +0x04: uaFirmwareSignature "ATOM" (4 bytes)
#   +0x08: usBiosRuntimeSegAddress
#   +0x0A: usProtectedModeInfoOffset
#   +0x0C: usConfigFilenameOffset
#   +0x0E: usConfigFilenameSize
#   +0x10: usMCIOffset
#   +0x12: usPciIOffset
#   +0x14: usVbeInfoOffset
#   +0x16: usThermalControllerOffset
#   +0x18: usPreviouslyLinkOffset
#   +0x1A: usMasterCommandTableOffset
#   +0x1C: usMasterDataTableOffset

print("\n=== 尝试不同偏移读取 MasterDataTable ===")
for off in [0x1C, 0x1E, 0x20, 0x22, 0x24, 0x26, 0x28]:
    val = read_u16(data, rom_header_off + off)
    # 检查这个偏移指向的地方是否像 MasterDataTable
    # MasterDataTable 应该以 ATOM_COMMON_HEADER 开头
    if val > 0 and val < len(data) - 4:
        first_bytes = data[val:val+4]
        is_pcir = data[val:val+4] == b'PCIR'
        print(f"  +0x{off:02X}: 0x{val:04X} -> bytes: {first_bytes.hex()} {'(PCIR!)' if is_pcir else ''}")

# 3. 搜索 ATOM_MASTER_DATA_TABLE 的特征
# MasterDataTable 以 ATOM_COMMON_HEADER 开头，后面是 ListOfDataTables
# ListOfDataTables 中的指针应该指向 VBIOS 内的合理地址
print("\n=== 搜索可能的 MasterDataTable ===")
# MasterDataTable 的特征：开头 4 bytes 是 header，后续是 uint16 指针列表
# 这些指针应该在 0x0000-0xFFFF 范围内，且非零的应该指向有效数据
for i in range(0x0100, len(data) - 80, 2):
    # 检查是否可能是 MasterDataTable
    # 跳过 PCIR 和已知区域
    if data[i:i+4] == b'PCIR' or data[i:i+4] == b'ATOM':
        continue
    
    # 检查后续的 uint16 值是否像表指针
    vals = [read_u16(data, i + 4 + j*2) for j in range(15)]
    non_zero = sum(1 for v in vals if v > 0)
    reasonable = sum(1 for v in vals if 0 < v < len(data))
    
    # MasterDataTable 应该有多个非零指针
    if non_zero >= 5 and reasonable >= 5:
        # 进一步检查：这些指针指向的位置不应该都是 ASCII 文本
        valid_ptrs = 0
        for v in vals:
            if 0 < v < len(data) - 4:
                # 检查指针指向的地方是否有合理的数据（非全零、非纯 ASCII）
                target = data[v:v+4]
                if target != b'\x00\x00\x00\x00':
                    valid_ptrs += 1
        
        if valid_ptrs >= 5:
            print(f"  候选 @ 0x{i:04X}: non_zero={non_zero}, reasonable={reasonable}, valid_ptrs={valid_ptrs}")
            print(f"    指针: {[f'0x{v:04X}' for v in vals[:10]]}")

# 4. 直接搜索 PowerPlay Table
# Vega 10 ATOM PPT 的特征：revision=0x0a 后跟合理的 table_size
print("\n=== 搜索 PowerPlay Table (revision=0x0a) ===")
for i in range(len(data) - 3):
    if data[i] == 0x0a:
        size = read_u16(data, i + 1)
        if 1500 <= size <= 3000 and i + size <= len(data):
            # 检查内容是否非全零
            non_zero = sum(1 for b in data[i+3:i+min(100, size)] if b != 0)
            if non_zero > 40:
                print(f"  候选 @ 0x{i:04X}: rev=0x0a, size={size}, non_zero={non_zero}/97")
                # 打印前 32 字节
                hex_str = ' '.join(f'{data[i+j]:02X}' for j in range(min(32, size)))
                print(f"    {hex_str}")

# 5. 也搜索其他常见 revision
print("\n=== 搜索 PowerPlay Table (其他 revision) ===")
for i in range(len(data) - 3):
    rev = data[i]
    size = read_u16(data, i + 1)
    if 1500 <= size <= 3000 and i + size <= len(data):
        non_zero = sum(1 for b in data[i+3:i+min(100, size)] if b != 0)
        if non_zero > 50 and rev != 0x0a:
            # 额外检查：后续数据不应该是代码/文本
            print(f"  候选 @ 0x{i:04X}: rev=0x{rev:02X}, size={size}, non_zero={non_zero}/97")

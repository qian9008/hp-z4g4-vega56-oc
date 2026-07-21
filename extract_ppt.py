#!/usr/bin/env python3
"""
从 AMD Vega 56 VBIOS 中提取完整的 ATOM 格式 PowerPlay Table (PPT)。

ATOM BIOS 结构解析流程：
  1. 0x48 处的 16-bit 指针 → ATOM_ROM_HEADER
  2. ATOM_ROM_HEADER + 0x20 → ATOM_MASTER_COMMAND_TABLE
  3. ATOM_ROM_HEADER + 0x22 → ATOM_MASTER_DATA_TABLE
  4. ATOM_MASTER_DATA_TABLE 中的 ListOfDataTables 包含各数据表指针
  5. PowerPlayInfo 是其中一个表，包含 GPU 频率/电压/DPM 状态

输出：Base64 编码的 PPT，可直接注入 config.plist 的 PP_PhmSoftPowerPlayTable。
"""

import struct
import sys
import base64

def read_u16(data, offset):
    """读取小端 16 位无符号整数"""
    return struct.unpack_from('<H', data, offset)[0]

def read_u32(data, offset):
    """读取小端 32 位无符号整数"""
    return struct.unpack_from('<I', data, offset)[0]

def parse_atom_bios(data):
    """
    解析 ATOM BIOS 结构，返回 PowerPlayInfo 表的偏移量和大小。
    """
    print("=" * 60)
    print("ATOM BIOS 结构解析")
    print("=" * 60)

    # 1. 验证 BIOS 签名 (0x55 0xAA)
    if data[0] != 0x55 or data[1] != 0xAA:
        print(f"[错误] BIOS 签名无效: {data[0]:02X} {data[1]:02X}")
        return None

    print(f"[OK] BIOS 签名: 55 AA")

    # 2. 读取 ATOM_ROM_HEADER 指针 (位于 offset 0x48)
    #    注意：有些 VBIOS 在 0x48 处直接是 16-bit offset
    atom_rom_header_off = read_u16(data, 0x48)
    print(f"[信息] ATOM_ROM_HEADER 偏移: 0x{atom_rom_header_off:04X}")

    if atom_rom_header_off == 0 or atom_rom_header_off >= len(data):
        print("[错误] ATOM_ROM_HEADER 偏移无效")
        return None

    # 3. 解析 ATOM_ROM_HEADER
    #    验证签名 "ATOM" (0x41544F4D) 或检查结构
    header = data[atom_rom_header_off:]
    # ATOM_ROM_HEADER 结构：
    #   +0x00: ucFirmwareType (1=AtomBios)
    #   +0x01: ucFirmwareRevision
    #   +0x02: usFirmwareSignature (应该是 "AT" = 0x5441)
    #   实际上，不同版本的结构布局不同

    # 通用方法：在 0x48 指向的位置附近找 "ATOM" 签名
    # 或者直接使用已知的偏移读取 MasterDataTable

    # 标准 ATOM_ROM_HEADER:
    #   offset 0:  uint8  ucFirmwareType
    #   offset 1:  uint8  ucFirmwareRevision
    #   offset 2:  uint16 usFirmwareSignature
    #   offset 4:  uint16 usBiosRuntimeSegAddress
    #   offset 6:  uint16 usProtectedModeInfoOffset
    #   offset 8:  uint16 usConfigFilenameOffset
    #   offset 10: uint16 usConfigFilenameSize
    #   offset 12: uint16 usMCIOffset
    #   offset 14: uint16 usPciIOffset
    #   offset 16: uint16 usVbeInfoOffset (AtomBiosExtension)
    #   offset 18: uint16 usThermalControllerOffset
    #   offset 20: uint16 usPreviouslyLinkOffset
    #   offset 22: uint16 usMasterCommandTableOffset  <-- 关键
    #   offset 24: uint16 usMasterDataTableOffset     <-- 关键
    #   offset 26: uint16 usExtendedFunctionTableOffset
    #   ...etc

    # 但实际上偏移可能不同。让我检查多种可能性。
    # 首先尝试标准偏移 (0x22 for MasterDataTable)

    # 检查 ATOM_ROM_HEADER 是否以特定签名开始
    fw_type = data[atom_rom_header_off]
    fw_rev = data[atom_rom_header_off + 1]
    fw_sig = read_u16(data, atom_rom_header_off + 2)
    print(f"[信息] FirmwareType: 0x{fw_type:02X}, Revision: 0x{fw_rev:02X}, Signature: 0x{fw_sig:04X}")

    # 尝试标准偏移读取 MasterDataTable
    # 在一些 ATOM BIOS 中，MasterDataTable 在 header+0x22
    master_data_off = read_u16(data, atom_rom_header_off + 0x22)
    master_cmd_off = read_u16(data, atom_rom_header_off + 0x20)
    print(f"[信息] MasterCommandTable 偏移: 0x{master_cmd_off:04X}")
    print(f"[信息] MasterDataTable 偏移: 0x{master_data_off:04X}")

    if master_data_off == 0 or master_data_off >= len(data):
        # 尝试备用偏移
        print("[警告] 标准偏移无效，尝试备用偏移...")
        # 在一些 VBIOS 中可能在 0x20
        master_data_off = read_u16(data, atom_rom_header_off + 0x20)
        print(f"[信息] 尝试 0x20 偏移: 0x{master_data_off:04X}")

    if master_data_off == 0 or master_data_off >= len(data):
        print("[错误] 无法找到 MasterDataTable")
        return None

    # 4. 解析 ATOM_MASTER_DATA_TABLE
    #    结构:
    #      offset 0:  ucTableType (1=AtomData)
    #      offset 1:  ucTableSize
    #      offset 2:  uint16 usStructureSize
    #      offset 4:  ListOfDataTables (连续的 uint16 offset)

    print(f"\n[信息] ATOM_MASTER_DATA_TABLE @ 0x{master_data_off:04X}:")
    table_type = data[master_data_off]
    table_size = data[master_data_off + 1]
    struct_size = read_u16(data, master_data_off + 2)
    print(f"  TableType: 0x{table_type:02X}, TableSize: 0x{table_size:02X}, StructureSize: 0x{struct_size:04X}")

    # ListOfDataTables 从 master_data_off + 4 开始
    # 每个表项是 16-bit offset
    # PowerPlayInfo 的索引在标准 ATOM BIOS 中通常是已知的
    # 但不同版本的索引可能不同

    # 标准 ATOM_MASTER_DATA_TABLE 中的表索引：
    # 0x00: UtilityPipeline
    # 0x02: MultimediaCapabilityInfo
    # 0x04: MultimediaConfigInfo
    # 0x06: StandardVESA_Timing
    # 0x08: FirmwareInfo
    # 0x0A: PaletteData
    # 0x0C: LVDS_Info
    # 0x0E: TMDS_Info
    # 0x10: AnalogTV_Info
    # 0x12: SupportedDevicesInfo
    # 0x14: GPIO_I2C_Info
    # 0x16: VRAM_UsageByFirmware
    # 0x18: GPIO_PinConfigInfo
    # 0x1A: PowerPlayInfo        <-- 这个！
    # 0x1C: GPUVirtualizationInfo
    # ...etc

    # PowerPlayInfo 在 ListOfDataTables 中的偏移是 0x1A (索引 13)
    # 即 master_data_off + 4 + 0x1A = master_data_off + 0x1E
    powerplay_off_in_list = master_data_off + 4 + 0x1A
    powerplay_table_off = read_u16(data, powerplay_off_in_list)
    print(f"\n[信息] PowerPlayInfo 指针位置: 0x{powerplay_off_in_list:04X}")
    print(f"[信息] PowerPlayInfo 表偏移: 0x{powerplay_table_off:04X}")

    if powerplay_table_off == 0 or powerplay_table_off >= len(data):
        print("[错误] PowerPlayInfo 表偏移无效")
        # 备用方案：直接搜索 PowerPlay Table
        return search_powerplay_table(data)

    # 5. 解析 PowerPlayInfo 表
    return parse_powerplay_table(data, powerplay_table_off)

def parse_powerplay_table(data, offset):
    """
    解析 PowerPlayInfo 表。
    对于 Vega 10 (revision 0x0a)：
      offset 0:  ucTableRevision (应为 0x0a)
      offset 1:  uint16 usTableSize
      offset 3:  uint16 usGoldenPPTableSize
      ...其余是频率/电压/DPM 状态数据
    """
    print(f"\n{'=' * 60}")
    print(f"PowerPlayInfo 表解析 @ 0x{offset:04X}")
    print(f"{'=' * 60}")

    revision = data[offset]
    table_size = read_u16(data, offset + 1)

    print(f"[信息] ucTableRevision: 0x{revision:02X} ({revision})")
    print(f"[信息] usTableSize: {table_size} (0x{table_size:04X})")

    # Vega 10 的 ATOM PPT revision 应该是 0x0a (10)
    if revision != 0x0a:
        print(f"[警告] 预期 revision 0x0a，但得到 0x{revision:02X}")
        # 仍然继续，可能是其他版本

    # 验证表大小是否合理
    # Vega 56/64 的完整 PPT 通常在 2000-2200 字节左右
    if table_size < 500:
        print(f"[警告] 表大小 {table_size} 字节过小，可能不是完整的 PPT")
    elif table_size > 4096:
        print(f"[警告] 表大小 {table_size} 字节过大，可能有问题")

    if offset + table_size > len(data):
        print(f"[错误] 表数据超出 VBIOS 范围 (offset={offset}, size={table_size}, bios_size={len(data)})")
        return None

    # 提取完整的 PPT 数据
    ppt_data = data[offset:offset + table_size]

    # 打印更多结构信息用于验证
    if table_size >= 8:
        golden_size = read_u16(data, offset + 3)
        print(f"[信息] usGoldenPPTableSize: {golden_size}")

    # 打印前 64 字节的十六进制
    print(f"\n[信息] PPT 前 64 字节十六进制:")
    for i in range(0, min(64, len(ppt_data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in ppt_data[i:i+16])
        print(f"  0x{i:04X}: {hex_str}")

    # 打印后 32 字节的十六进制
    if table_size > 64:
        print(f"\n[信息] PPT 最后 32 字节十六进制:")
        start = table_size - 32
        for i in range(start, table_size, 16):
            hex_str = ' '.join(f'{b:02X}' for b in ppt_data[i:i+16])
            print(f"  0x{i:04X}: {hex_str}")

    return {
        'offset': offset,
        'revision': revision,
        'size': table_size,
        'data': ppt_data,
    }

def search_powerplay_table(data):
    """
    备用方案：在 VBIOS 中搜索 PowerPlay Table。
    搜索特征：revision=0x0a 开头，后面跟着合理的 table_size。
    """
    print("\n[备用] 在 VBIOS 中搜索 PowerPlay Table...")

    candidates = []
    for i in range(len(data) - 4):
        if data[i] == 0x0a:  # revision
            size = read_u16(data, i + 1)
            # Vega 56/64 的 PPT 大小通常在 1900-2300 之间
            if 1900 <= size <= 2500:
                # 进一步验证：检查后续字节是否有合理的内容
                if i + size <= len(data):
                    candidates.append((i, size))

    if not candidates:
        print("[错误] 未找到符合特征的 PowerPlay Table")
        return None

    print(f"[信息] 找到 {len(candidates)} 个候选位置:")
    for offset, size in candidates:
        print(f"  - offset=0x{offset:04X}, size={size}")

    # 选择第一个候选
    best = candidates[0]
    print(f"\n[信息] 选择第一个候选: offset=0x{best[0]:04X}")
    return parse_powerplay_table(data, best[0])

def main():
    bios_path = "/Users/qian/Downloads/1/AMD Radeon RX Vega 56.bios"

    print(f"读取 VBIOS: {bios_path}")
    with open(bios_path, 'rb') as f:
        data = f.read()

    print(f"VBIOS 大小: {len(data)} 字节 ({len(data)/1024:.1f} KB)")

    result = parse_atom_bios(data)

    if result is None:
        print("\n[失败] 无法提取 PowerPlay Table")
        sys.exit(1)

    ppt_data = result['data']
    table_size = result['size']

    print(f"\n{'=' * 60}")
    print("提取结果")
    print(f"{'=' * 60}")
    print(f"偏移量: 0x{result['offset']:04X}")
    print(f"Revision: 0x{result['revision']:02X}")
    print(f"表大小: {table_size} 字节")

    # 保存原始二进制
    out_bin = "/Users/qian/Downloads/1/vega56_powerplay_table.bin"
    with open(out_bin, 'wb') as f:
        f.write(ppt_data)
    print(f"\n[已保存] 二进制文件: {out_bin}")

    # 生成 Base64 (用于 config.plist 的 PP_PhmSoftPowerPlayTable)
    b64 = base64.b64encode(ppt_data).decode('ascii')
    print(f"\n[信息] Base64 长度: {len(b64)} 字符")

    # 保存 Base64 到文件
    out_b64 = "/Users/qian/Downloads/1/vega56_powerplay_table.b64"
    with open(out_b64, 'w') as f:
        f.write(b64)
    print(f"[已保存] Base64 文件: {out_b64}")

    # 打印 Base64（前 200 字符和后 100 字符）
    if len(b64) > 300:
        print(f"\nBase64 预览:")
        print(f"  开头: {b64[:200]}...")
        print(f"  结尾: ...{b64[-100:]}")
    else:
        print(f"\nBase64:\n{b64}")

    print(f"\n{'=' * 60}")
    print("✅ 提取完成！")
    print(f"{'=' * 60}")

if __name__ == '__main__':
    main()

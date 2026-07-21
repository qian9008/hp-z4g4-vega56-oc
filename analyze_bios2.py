#!/usr/bin/env python3
"""
修正版：正确解析 ATOM_ROM_HEADER 结构
ATOM_ROM_HEADER 的字段偏移（相对于 header 起始）：
  +0x00: ATOM_COMMON_HEADER (4 bytes)
  +0x04: uaFirmwareSignature "ATOM" (4 bytes)
  +0x08: usBiosRuntimeSegAddress (2 bytes)
  +0x0A: usProtectedModeInfoOffset (2 bytes)
  +0x0C: usConfigFilenameOffset (2 bytes)
  +0x0E: usConfigFilenameSize (2 bytes)
  +0x10: usMCIOffset (2 bytes)
  +0x12: usPciIOffset (2 bytes)
  +0x14: usVbeInfoOffset (2 bytes)
  +0x16: usThermalControllerOffset (2 bytes)
  +0x18: usPreviouslyLinkOffset (2 bytes)
  +0x1A: usMasterCommandTableOffset (2 bytes) ← 关键
  +0x1C: usMasterDataTableOffset (2 bytes) ← 关键
"""
import struct
import base64

def read_u16(data, off):
    return struct.unpack_from('<H', data, off)[0]

with open('/Users/qian/Downloads/1/AMD Radeon RX Vega 56.bios', 'rb') as f:
    data = f.read()

# 1. ATOM_ROM_HEADER 在 0x0274 (0x48 处的指针)
rom_header_off = read_u16(data, 0x48)
print(f"ATOM_ROM_HEADER offset: 0x{rom_header_off:04X}")

# 打印完整的 ATOM_ROM_HEADER
print("\n=== ATOM_ROM_HEADER 完整数据 ===")
for i in range(rom_header_off, rom_header_off + 48, 16):
    hex_str = ' '.join(f'{data[j]:02X}' for j in range(i, min(i+16, len(data))))
    ascii_str = ''.join(chr(data[j]) if 32 <= data[j] < 127 else '.' for j in range(i, min(i+16, len(data))))
    print(f"  0x{i:04X}: {hex_str}  {ascii_str}")

# 验证 "ATOM" 签名在 header + 0x04
sig = data[rom_header_off + 4 : rom_header_off + 8]
print(f"\nFirmwareSignature: {sig} ({sig.hex()})")
if sig == b'ATOM':
    print("[OK] ATOM 签名验证通过")

# 读取关键字段
print(f"\n=== ATOM_ROM_HEADER 字段 ===")
fields = [
    (0x08, "usBiosRuntimeSegAddress"),
    (0x0A, "usProtectedModeInfoOffset"),
    (0x0C, "usConfigFilenameOffset"),
    (0x0E, "usConfigFilenameSize"),
    (0x10, "usMCIOffset"),
    (0x12, "usPciIOffset"),
    (0x14, "usVbeInfoOffset"),
    (0x16, "usThermalControllerOffset"),
    (0x18, "usPreviouslyLinkOffset"),
    (0x1A, "usMasterCommandTableOffset"),
    (0x1C, "usMasterDataTableOffset"),
]

master_cmd_off = 0
master_data_off = 0

for foff, fname in fields:
    val = read_u16(data, rom_header_off + foff)
    print(f"  +0x{foff:02X} {fname}: 0x{val:04X}")
    if fname == "usMasterCommandTableOffset":
        master_cmd_off = val
    elif fname == "usMasterDataTableOffset":
        master_data_off = val

print(f"\nMasterCommandTable: 0x{master_cmd_off:04X}")
print(f"MasterDataTable: 0x{master_data_off:04X}")

# 2. 解析 ATOM_MASTER_DATA_TABLE
if master_data_off > 0 and master_data_off < len(data):
    print(f"\n=== ATOM_MASTER_DATA_TABLE @ 0x{master_data_off:04X} ===")
    for i in range(master_data_off, master_data_off + 64, 16):
        hex_str = ' '.join(f'{data[j]:02X}' for j in range(i, min(i+16, len(data))))
        ascii_str = ''.join(chr(data[j]) if 32 <= data[j] < 127 else '.' for j in range(i, min(i+16, len(data))))
        print(f"  0x{i:04X}: {hex_str}  {ascii_str}")

    # MasterDataTable 结构:
    # +0x00: ATOM_COMMON_HEADER (4 bytes)
    # +0x04: ListOfDataTables (连续的 uint16 offset)
    #
    # PowerPlayInfo 在 ListOfDataTables 中的索引:
    # 索引 0: UtilityPipeline (0x04)
    # 索引 1: MultimediaCapabilityInfo (0x06)
    # 索引 2: MultimediaConfigInfo (0x08)
    # 索引 3: StandardVESA_Timing (0x0A)
    # 索引 4: FirmwareInfo (0x0C)
    # 索引 5: PaletteData (0x0E)
    # 索引 6: LVDS_Info (0x10)
    # 索引 7: TMDS_Info (0x12)
    # 索引 8: AnalogTV_Info (0x14)
    # 索引 9: SupportedDevicesInfo (0x16)
    # 索引 10: GPIO_I2C_Info (0x18)
    # 索引 11: VRAM_UsageByFirmware (0x1A)
    # 索引 12: GPIO_PinConfigInfo (0x1C)
    # 索引 13: PowerPlayInfo (0x1E) ← 关键
    # 索引 14: GPUVirtualizationInfo (0x20)

    # 但不同版本的索引可能不同
    # 让我列出所有表项
    print("\n=== ListOfDataTables ===")
    table_names = [
        "UtilityPipeline", "MultimediaCapabilityInfo", "MultimediaConfigInfo",
        "StandardVESA_Timing", "FirmwareInfo", "PaletteData",
        "LVDS_Info", "TMDS_Info", "AnalogTV_Info", "SupportedDevicesInfo",
        "GPIO_I2C_Info", "VRAM_UsageByFirmware", "GPIO_PinConfigInfo",
        "PowerPlayInfo", "GPUVirtualizationInfo", "SaveRestoreInfo",
        "OemInfo", "XtalInfo", "I2CConfigInfo", "ClockSourceInfo",
        "SclkMclkDependTableInfo", "Gpio_LcdInfo", "MemoryTrainingInfo",
        "FirmwareInfo_V2", "GPIO_PinConfigInfo_V2", "PowerSourceInfo",
        "VramInfo_V2", "OemInfo_V2", "PowerPlayInfo_V2", "SclkMclkDependTableInfo_V2",
    ]

    list_start = master_data_off + 4
    for idx in range(30):
        off_pos = list_start + idx * 2
        if off_pos + 2 > len(data):
            break
        val = read_u16(data, off_pos)
        name = table_names[idx] if idx < len(table_names) else f"Unknown_{idx}"
        print(f"  [{idx:2d}] @ 0x{off_pos:04X}: 0x{val:04X} ({name})")

    # 读取 PowerPlayInfo 偏移 (索引 13)
    powerplay_list_off = list_start + 13 * 2
    powerplay_table_off = read_u16(data, powerplay_list_off)
    print(f"\nPowerPlayInfo (索引 13) 偏移: 0x{powerplay_table_off:04X}")

    # 也检查 PowerPlayInfo_V2 (索引 28)
    if list_start + 28 * 2 + 2 <= len(data):
        powerplay_v2_list_off = list_start + 28 * 2
        powerplay_v2_off = read_u16(data, powerplay_v2_list_off)
        print(f"PowerPlayInfo_V2 (索引 28) 偏移: 0x{powerplay_v2_off:04X}")

    # 3. 解析 PowerPlayInfo 表
    if powerplay_table_off > 0 and powerplay_table_off < len(data):
        print(f"\n=== PowerPlayInfo 表 @ 0x{powerplay_table_off:04X} ===")
        rev = data[powerplay_table_off]
        size = read_u16(data, powerplay_table_off + 1)
        print(f"  Revision: 0x{rev:02X} ({rev})")
        print(f"  TableSize: {size} (0x{size:04X})")

        # 打印前 64 字节
        print(f"\n  前 64 字节:")
        for i in range(0, min(64, size), 16):
            hex_str = ' '.join(f'{data[powerplay_table_off+i+j]:02X}' for j in range(min(16, size-i)))
            print(f"    0x{i:04X}: {hex_str}")

        # 如果表大小合理，提取并保存
        if size > 100 and powerplay_table_off + size <= len(data):
            ppt_data = data[powerplay_table_off:powerplay_table_off + size]
            b64 = base64.b64encode(ppt_data).decode('ascii')

            # 保存二进制
            with open('/Users/qian/Downloads/1/vega56_powerplay_table.bin', 'wb') as f:
                f.write(ppt_data)
            print(f"\n  [已保存] 二进制: vega56_powerplay_table.bin ({size} 字节)")

            # 保存 Base64
            with open('/Users/qian/Downloads/1/vega56_powerplay_table.b64', 'w') as f:
                f.write(b64)
            print(f"  [已保存] Base64: vega56_powerplay_table.b64 ({len(b64)} 字符)")

            print(f"\n  Base64 前 100 字符: {b64[:100]}...")
            print(f"  Base64 后 100 字符: ...{b64[-100:]}")
        else:
            print(f"\n  [警告] 表大小 {size} 不合理或超出范围")

# 也检查 PowerPlayInfo_V2
if powerplay_v2_off > 0 and powerplay_v2_off < len(data):
    print(f"\n=== PowerPlayInfo_V2 表 @ 0x{powerplay_v2_off:04X} ===")
    rev = data[powerplay_v2_off]
    size = read_u16(data, powerplay_v2_off + 1)
    print(f"  Revision: 0x{rev:02X} ({rev})")
    print(f"  TableSize: {size} (0x{size:04X})")
    if size > 100 and powerplay_v2_off + size <= len(data):
        print(f"  [注意] 这个表也可能是正确的 PPT")

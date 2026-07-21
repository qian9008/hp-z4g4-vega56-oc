#!/usr/bin/env python3
import struct

with open('/Users/qian/Downloads/1/bios.rom', 'rb') as f:
    data = f.read()

def r16(off):
    return struct.unpack_from('<H', data, off)[0]

# 检查 0x8E9C 是否是 MasterDataTable
print('=== 0x8E9C 处 (可能是 MasterDataTable) ===')
for i in range(0x8E9C, 0x8E9C + 80, 16):
    h = ' '.join(f'{data[j]:02X}' for j in range(i, min(i+16, len(data))))
    a = ''.join(chr(data[j]) if 32 <= data[j] < 127 else '.' for j in range(i, min(i+16, len(data))))
    print(f'  0x{i:04X}: {h}  {a}')

# ListOfDataTables 从 0x8EA0 开始
print()
print('=== ListOfDataTables (从 0x8EA0 开始) ===')
names = [
    'UtilityPipeline', 'MultimediaCapabilityInfo', 'MultimediaConfigInfo',
    'StandardVESA_Timing', 'FirmwareInfo', 'PaletteData',
    'LVDS_Info', 'TMDS_Info', 'AnalogTV_Info', 'SupportedDevicesInfo',
    'GPIO_I2C_Info', 'VRAM_UsageByFirmware', 'GPIO_PinConfigInfo',
    'PowerPlayInfo', 'GPUVirtualizationInfo', 'SaveRestoreInfo',
    'OemInfo', 'XtalInfo', 'I2CConfigInfo', 'ClockSourceInfo',
    'SclkMclkDependTableInfo', 'Gpio_LcdInfo', 'MemoryTrainingInfo',
    'FirmwareInfo_V2', 'GPIO_PinConfigInfo_V2', 'PowerSourceInfo',
    'VramInfo_V2', 'OemInfo_V2', 'PowerPlayInfo_V2',
    'SclkMclkDependTableInfo_V2'
]
for idx in range(30):
    off = 0x8EA0 + idx * 2
    val = r16(off)
    nm = names[idx] if idx < len(names) else f'Unknown_{idx}'
    print(f'  [{idx:2d}] @ 0x{off:04X}: 0x{val:04X} ({nm})')

# 检查 PowerPlayInfo 偏移 (索引 13)
pp_off = r16(0x8EA0 + 13 * 2)
print(f'\nPowerPlayInfo (索引13) 偏移: 0x{pp_off:04X}')
if 0 < pp_off < len(data):
    rev = data[pp_off]
    sz = r16(pp_off + 1)
    print(f'  Revision: 0x{rev:02X}')
    print(f'  TableSize: {sz}')
    if sz > 0 and sz < 5000 and pp_off + sz <= len(data):
        print(f'  前 64 字节:')
        for i in range(0, min(64, sz), 16):
            h = ' '.join(f'{data[pp_off+i+j]:02X}' for j in range(min(16, sz-i)))
            print(f'    0x{i:04X}: {h}')
        print(f'  最后 32 字节:')
        start = sz - 32
        for i in range(start, sz, 16):
            h = ' '.join(f'{data[pp_off+i+j]:02X}' for j in range(min(16, sz-i)))
            print(f'    0x{i:04X}: {h}')
    else:
        print(f'  [警告] 表大小 {sz} 不合理')

# 也检查 PowerPlayInfo_V2 (索引 28)
pp_v2_off = r16(0x8EA0 + 28 * 2)
if pp_v2_off > 0:
    print(f'\nPowerPlayInfo_V2 (索引28) 偏移: 0x{pp_v2_off:04X}')
    rev = data[pp_v2_off]
    sz = r16(pp_v2_off + 1)
    print(f'  Revision: 0x{rev:02X}, TableSize: {sz}')

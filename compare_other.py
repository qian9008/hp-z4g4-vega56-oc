#!/usr/bin/env python3
"""
对比分析用户提供的别人的 PPT 和我们的完整 pp_table
"""
import base64
import struct

def r16(off, data):
    return struct.unpack_from('<H', data, off)[0]

def r32(off, data):
    return struct.unpack_from('<I', data, off)[0]

# 用户提供的别人的 PPT (Base64)
other_b64 = "tgIIAQBcAOEGAADuKwAAGwBIAAAAgKkDAPBJAgCOAAgAAAAAAAAAAAAAAAAAAAIBXABPAkYClACeAb4AKAF6AIwAvAEAAAAAcgIAAJAAqAJtAUMBlwHwSQIAcQICAgAAAAAAAAgAAAAAAAAABQAHAAMABQAAAAAAAAABCIQDhAOEA4QDhAOEA7YDMwQBATMEAQGEAwAIYOoAAABAGQEAAYA4AQAC3EoBAAOQXwEABAB3AQAFkJEBAAZQvQEABwEI0EwBAAAAgAAAAAAAAByDAQABAAAAAAAAAABwpwEAAgAAAAAAAAAAiLwBAAMAAAAAAAAAADjBAQAEAAAAAAAAAACI1QEABQAAAAABAAAAmPwBAAYAAAAAAQAAAEgzAgAHAAAAAAEAAAAABWDqAAAAQBkBAACAOAEAANxKAQAAkF8BAAAACChuAAAALMkAAAH4CwEAAoA4AQADkF8BAAT0kQEABdCwAQAGOMEBAAcACGw5AAAAJF4AAAH8hQAAAqy8AAADNNAAAARobgEABQiXAQAGsK0BAAcAAWg8AQAAAQQ8QQAAAAAAUMMAAAAAAIA4AQACAAA0mAEABAAAAQgAmIUAAEC1AABg6gAAUMMAAAGAuwAAYOoAAJQLAQBQwwAAAgDhAACUCwEAQBkBAFDDAAADeP8AAEAZAQCIJgEAUMMAAARAGQEAgDgBAIA4AQBQwwAABYA4AQDcSgEA3EoBAFDDAAAGAHcBAAB3AQCQXwEAUMMAAAeQkQEAkJEBAAB3AQBQwwAAARgAAAAAAAAACwAAvAJIJkYACgBUA5ABkAGQAZABkAGQAZABAAAAAAACBDEH3ADcANwAkAEAAFkAaQBKAEoAXwBzAHMAZABAAJCSl2CWAJBVAAAAAAAAAAAAAAAAAAAAAAACAtQwAAACEGDqAAACEA=="

other_data = base64.b64decode(other_b64)

print("=" * 70)
print("别人的 PPT 分析")
print("=" * 70)
print(f"Base64 长度: {len(other_b64)} 字符")
print(f"解码后大小: {len(other_data)} 字节")
print(f"Revision: 0x{other_data[0]:02X} ({other_data[0]})")

declared_size = r16(1, other_data)
print(f"声明大小 (usTableSize): {declared_size} 字节")
print(f"实际大小: {len(other_data)} 字节")
print(f"完整性: {'完整' if len(other_data) >= declared_size else '不完整! 缺少 ' + str(declared_size - len(other_data)) + ' 字节'}")

# 对比我们的完整 pp_table
print()
print("=" * 70)
print("对比: 我们的完整 pp_table vs 别人的 PPT")
print("=" * 70)

with open('/Users/qian/Downloads/1/vega56_pp_table_complete.bin', 'rb') as f:
    our_data = f.read()

print(f"我们的: {len(our_data)} 字节, rev=0x{our_data[0]:02X}, 声明={r16(1, our_data)}")
print(f"别人的: {len(other_data)} 字节, rev=0x{other_data[0]:02X}, 声明={r16(1, other_data)}")

# 检查两者前缀是否相同
print()
print("=== 前 32 字节对比 ===")
print("我们的:", our_data[:32].hex(' '))
print("别人的:", other_data[:32].hex(' '))

# 详细解析别人的 PPT 结构
print()
print("=" * 70)
print("别人的 PPT 详细解析")
print("=" * 70)
print(f"全十六进制 dump ({len(other_data)} 字节):")
for i in range(0, len(other_data), 16):
    h = ' '.join(f'{other_data[i+j]:02X}' for j in range(min(16, len(other_data) - i)))
    a = ''.join(chr(other_data[i+j]) if 32 <= other_data[i+j] < 127 else '.' for j in range(min(16, len(other_data) - i)))
    print(f"  0x{i:04X}: {h}  {a}")

# 搜索频率值
print()
print("=== 搜索频率值 ===")
for freq_mhz in [167, 500, 800, 852, 900, 1000, 1138, 1156, 1200, 1271, 1400, 1442, 1500, 1600]:
    freq_le = struct.pack('<H', freq_mhz)
    positions = []
    for i in range(len(other_data) - 1):
        if other_data[i:i+2] == freq_le:
            positions.append(i)
    if positions:
        print(f"  {freq_mhz} MHz (0x{freq_mhz:04X}) @ {', '.join(f'0x{p:04X}' for p in positions)}")

# 也检查 ATOM PowerPlayInfo (256字节, rev 0x74) 的 Base64
print()
print("=" * 70)
print("三种选项对比")
print("=" * 70)

# 选项1: ATOM PowerPlayInfo (256字节)
atom_b64 = base64.b64encode(open('/Users/qian/Downloads/1/vega56_atom_powerplay.b64', 'rb').read()).decode()
print(f"选项1 - ATOM PowerPlayInfo (rev 0x74):")
print(f"  大小: 256 字节, Base64: {len(atom_b64)} 字符")

# 但这实际上是 b64 文件再编码... 让我直接从 bios 读取
bios = open('/Users/qian/Downloads/1/bios.rom', 'rb').read()
atom_ppt = bios[0x9106:0x9106+256]
atom_b64 = base64.b64encode(atom_ppt).decode('ascii')
print(f"  (修正) 大小: 256 字节, Base64: {len(atom_b64)} 字符")

print(f"选项2 - 完整 Linux pp_table (rev 0xa7):")
print(f"  大小: {len(our_data)} 字节, Base64: {len(base64.b64encode(our_data).decode())} 字符")

print(f"选项3 - 别人的 PPT (rev 0xb6):")
print(f"  大小: {len(other_data)} 字节, Base64: {len(other_b64)} 字符")

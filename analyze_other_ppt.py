#!/usr/bin/env python3
"""
深入对比三个 PPT 选项，确定 macOS 驱动实际需要什么
"""
import base64
import struct

def r16(off, data):
    return struct.unpack_from('<H', data, off)[0]

def r32(off, data):
    return struct.unpack_from('<I', data, off)[0]

# === 三个 PPT ===

# 1. 我们的完整 pp_table (从 VBIOS 提取, rev 0xa7, 2050字节)
with open('/Users/qian/Downloads/1/vega56_pp_table_complete.bin', 'rb') as f:
    ours_full = f.read()

# 2. 用户的 bios.pp_table (从 Windows 导出, rev 0xa7, 679字节)
with open('/Users/qian/Downloads/1/bios.pp_table', 'rb') as f:
    user_partial = f.read()

# 3. 别人的 PPT (rev 0xb6, 694字节)
other_b64 = "tgIIAQBcAOEGAADuKwAAGwBIAAAAgKkDAPBJAgCOAAgAAAAAAAAAAAAAAAAAAAIBXABPAkYClACeAb4AKAF6AIwAvAEAAAAAcgIAAJAAqAJtAUMBlwHwSQIAcQICAgAAAAAAAAgAAAAAAAAABQAHAAMABQAAAAAAAAABCIQDhAOEA4QDhAOEA7YDMwQBATMEAQGEAwAIYOoAAABAGQEAAYA4AQAC3EoBAAOQXwEABAB3AQAFkJEBAAZQvQEABwEI0EwBAAAAgAAAAAAAAByDAQABAAAAAAAAAABwpwEAAgAAAAAAAAAAiLwBAAMAAAAAAAAAADjBAQAEAAAAAAAAAACI1QEABQAAAAABAAAAmPwBAAYAAAAAAQAAAEgzAgAHAAAAAAEAAAAABWDqAAAAQBkBAACAOAEAANxKAQAAkF8BAAAACChuAAAALMkAAAH4CwEAAoA4AQADkF8BAAT0kQEABdCwAQAGOMEBAAcACGw5AAAAJF4AAAH8hQAAAqy8AAADNNAAAARobgEABQiXAQAGsK0BAAcAAWg8AQAAAQQ8QQAAAAAAUMMAAAAAAIA4AQACAAA0mAEABAAAAQgAmIUAAEC1AABg6gAAUMMAAAGAuwAAYOoAAJQLAQBQwwAAAgDhAACUCwEAQBkBAFDDAAADeP8AAEAZAQCIJgEAUMMAAARAGQEAgDgBAIA4AQBQwwAABYA4AQDcSgEA3EoBAFDDAAAGAHcBAAB3AQCQXwEAUMMAAAeQkQEAkJEBAAB3AQBQwwAAARgAAAAAAAAACwAAvAJIJkYACgBUA5ABkAGQAZABkAGQAZABAAAAAAACBDEH3ADcANwAkAEAAFkAaQBKAEoAXwBzAHMAZABAAJCSl2CWAJBVAAAAAAAAAAAAAAAAAAAAAAACAtQwAAACEGDqAAACEA=="
other_data = base64.b64decode(other_b64)

print("=" * 70)
print("三个 PPT 对比总览")
print("=" * 70)
print(f"{'属性':<25} {'我们的完整版':<20} {'用户文件':<20} {'别人的':<20}")
print("-" * 85)
print(f"{'Revision':<25} {'0x' + format(ours_full[0], '02X'):<20} {'0x' + format(user_partial[0], '02X'):<20} {'0x' + format(other_data[0], '02X'):<20}")
print(f"{'声明大小 (usTableSize)':<25} {r16(1, ours_full):<20} {r16(1, user_partial):<20} {r16(1, other_data):<20}")
print(f"{'实际文件大小':<25} {len(ours_full):<20} {len(user_partial):<20} {len(other_data):<20}")
print(f"{'完整性':<25} {'✓ 完整':<20} {'✗ 缺1371字节':<20} {'✗ 缺1356字节':<20}")

# 关键对比：别人的和我们的完整版，实际数据内容是否一样？
print()
print("=" * 70)
print("别人的 PPT vs 我们的完整 pp_table - 结构对比")
print("=" * 70)

# 两个都声明 2050 字节，但实际都更小
# 问题：macOS 驱动到底用了多少？

# 检查别人的 PPT 结构
print("\n别人的 PPT (rev 0xb6) 关键区域:")
print(f"  0x00: Revision = 0x{other_data[0]:02X}")
print(f"  0x01: usTableSize = {r16(1, other_data)}")
print(f"  0x03: ulGoldenPPTableSize = {r32(3, other_data)}")

# 0x70-0x90 处的 SCLK 频率数组
print(f"\n  0x7C-0x8E SCLK 频率数组 (MHz):")
freqs = []
for i in range(0x7C, 0x90, 2):
    v = r16(i, other_data)
    if v > 0:
        freqs.append(v)
print(f"    {freqs}")

# 对比频率数组
print(f"\n我们的 pp_table (rev 0xa7) 0x7C-0x8E:")
our_freqs = []
for i in range(0x7C, 0x90, 2):
    v = r16(i, ours_full)
    if v > 0:
        our_freqs.append(v)
print(f"    {our_freqs}")

# 重要：别人的 PPT 在 0x90 之后还有数据，但我们的在 0x90 之后也有
# 让我们看看别人的 PPT 中实际包含多少有效的数据
print()
print("=" * 70)
print("别人的 PPT 完整内容分析 (694 字节)")
print("=" * 70)

# 检查最后部分是否有数据
last_nonzero = 0
for i in range(len(other_data) - 1, -1, -1):
    if other_data[i] != 0:
        last_nonzero = i
        break
print(f"最后非零字节位置: 0x{last_nonzero:04X} (第 {last_nonzero+1} 字节)")
print(f"有效数据长度: {last_nonzero + 1} 字节")

# 关键问题：别人也是不完整的！声明 2050 但只有 694 字节
# 但如果别人能正常工作，说明 macOS 驱动可能只用了前面的部分？

# 让我们看看哪个区域是实际必需的
# pp_table 结构通常分为几个块：
# 1. Header (0x00-0x0F)
# 2. State arrays
# 3. SCLK/MCLK dependency tables
# 4. Overdrive limits
# 5. Thermal limits
# 6. Fan control

# 让我们检查别人和我们的 PPT 在共同区域的结构
print()
print("=" * 70)
print("逐字节对比前 100 字节")
print("=" * 70)
print(f"{'Offset':<10} {'我们的':<8} {'别人的':<8} {'差异':<8}")
print("-" * 36)
for i in range(min(100, len(other_data), len(ours_full))):
    diff = "相同" if ours_full[i] == other_data[i] else "*** 不同"
    if diff == "*** 不同":
        print(f"0x{i:04X}     0x{ours_full[i]:02X}      0x{other_data[i]:02X}      {diff}")

# 统计前 694 字节（别人有的部分）的匹配度
match = sum(1 for i in range(len(other_data)) if i < len(ours_full) and ours_full[i] == other_data[i])
print(f"\n前 {len(other_data)} 字节匹配度: {match}/{len(other_data)} ({match*100//len(other_data)}%)")

# 检查最后一个区域（0x280-0x2B6 别人的结尾部分）
print()
print("=" * 70)
print("别人 PPT 结尾部分 (0x240-0x2B6)")
print("=" * 70)
for i in range(0x240, len(other_data), 16):
    end = min(i + 16, len(other_data))
    h = ' '.join(f'{other_data[i+j]:02X}' for j in range(end - i))
    a = ''.join(chr(other_data[i+j]) if 32 <= other_data[i+j] < 127 else '.' for j in range(end - i))
    print(f"  0x{i:04X}: {h}  {a}")

# 我们的完整版对应区域
print()
print("我们完整版对应区域 (0x240-0x2C0)")
for i in range(0x240, min(0x2C0, len(ours_full)), 16):
    end = min(i + 16, len(ours_full))
    h = ' '.join(f'{ours_full[i+j]:02X}' for j in range(end - i))
    a = ''.join(chr(ours_full[i+j]) if 32 <= ours_full[i+j] < 127 else '.' for j in range(end - i))
    print(f"  0x{i:04X}: {h}  {a}")

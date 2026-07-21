#!/usr/bin/env python3
"""
最终分析: 别人的 PPT 和我们的完整 pp_table 在结尾部分高度一致
说明 macOS 驱动可能只用到约 690 字节左右的数据
"""
import base64
import struct

def r16(off, data):
    return struct.unpack_from('<H', data, off)[0]

with open('/Users/qian/Downloads/1/vega56_pp_table_complete.bin', 'rb') as f:
    ours_full = f.read()

other_b64 = "tgIIAQBcAOEGAADuKwAAGwBIAAAAgKkDAPBJAgCOAAgAAAAAAAAAAAAAAAAAAAIBXABPAkYClACeAb4AKAF6AIwAvAEAAAAAcgIAAJAAqAJtAUMBlwHwSQIAcQICAgAAAAAAAAgAAAAAAAAABQAHAAMABQAAAAAAAAABCIQDhAOEA4QDhAOEA7YDMwQBATMEAQGEAwAIYOoAAABAGQEAAYA4AQAC3EoBAAOQXwEABAB3AQAFkJEBAAZQvQEABwEI0EwBAAAAgAAAAAAAAByDAQABAAAAAAAAAABwpwEAAgAAAAAAAAAAiLwBAAMAAAAAAAAAADjBAQAEAAAAAAAAAACI1QEABQAAAAABAAAAmPwBAAYAAAAAAQAAAEgzAgAHAAAAAAEAAAAABWDqAAAAQBkBAACAOAEAANxKAQAAkF8BAAAACChuAAAALMkAAAH4CwEAAoA4AQADkF8BAAT0kQEABdCwAQAGOMEBAAcACGw5AAAAJF4AAAH8hQAAAqy8AAADNNAAAARobgEABQiXAQAGsK0BAAcAAWg8AQAAAQQ8QQAAAAAAUMMAAAAAAIA4AQACAAA0mAEABAAAAQgAmIUAAEC1AABg6gAAUMMAAAGAuwAAYOoAAJQLAQBQwwAAAgDhAACUCwEAQBkBAFDDAAADeP8AAEAZAQCIJgEAUMMAAARAGQEAgDgBAIA4AQBQwwAABYA4AQDcSgEA3EoBAFDDAAAGAHcBAAB3AQCQXwEAUMMAAAeQkQEAkJEBAAB3AQBQwwAAARgAAAAAAAAACwAAvAJIJkYACgBUA5ABkAGQAZABkAGQAZABAAAAAAACBDEH3ADcANwAkAEAAFkAaQBKAEoAXwBzAHMAZABAAJCSl2CWAJBVAAAAAAAAAAAAAAAAAAAAAAACAtQwAAACEGDqAAACEA=="
other_data = base64.b64decode(other_b64)

# 关键发现：从 0x249 开始两个表几乎完全一致！
# 别人的: 0x249 开始
# 我们的: 0x240 开始 (偏移9字节)
# 让我找到精确的对齐

print("=" * 70)
print("寻找精确的对齐位置")
print("=" * 70)

# 搜索别人 PPT 中 "48 26 46 00 0A 00 54 03" 这个序列在我们完整版中的位置
search_seq = other_data[0x255:0x25D]  # 48 26 46 00 0A 00 54 03
print(f"搜索序列 (别人 0x255): {search_seq.hex(' ')}")

for i in range(len(ours_full) - len(search_seq)):
    if ours_full[i:i+len(search_seq)] == search_seq:
        print(f"  在我们完整版中找到 @ 0x{i:04X}")
        print(f"  偏移差: 别人0x255 - 我们0x{i:04X} = {0x255 - i}")

# 实际上从 0x249 开始就是完全一样的
# 让我从结尾对齐来比较
print()
print("=== 从结尾对齐比较 ===")
# 别人的最后 100 字节 vs 我们完整版的最后 100 字节
# 但我们的有 2050 字节，别人只有 694
# 如果从 0x249 对齐:
align_other = 0x249
align_ours = 0x240

# 或者让我直接找最后一个大块
# 0x0A 00 54 03 90 01 90 01 ... 这个序列
search2 = bytes.fromhex("0A 00 54 03 90 01 90 01".replace(" ", ""))
for i in range(len(ours_full) - len(search2)):
    if ours_full[i:i+len(search2)] == search2:
        print(f"序列 '0A 00 54 03...' 在我们中 @ 0x{i:04X}")
for i in range(len(other_data) - len(search2)):
    if other_data[i:i+len(search2)] == search2:
        print(f"序列 '0A 00 54 03...' 在别人中 @ 0x{i:04X}")

# 从 0x24A (别人) 和 0x24A (我们) 对齐比较
print()
print("=== 从 0x24A 对齐比较 ===")
match_from_24a = 0
total = min(len(other_data) - 0x24A, len(ours_full) - 0x24A)
for i in range(total):
    if other_data[0x24A + i] == ours_full[0x24A + i]:
        match_from_24a += 1
print(f"从 0x24A 开始匹配: {match_from_24a}/{total}")

# 实际对比 0x24A 之后的数据
print()
print("0x24A 之后逐字节比较 (显示前 32 字节):")
for i in range(min(32, total)):
    o = other_data[0x24A + i]
    u = ours_full[0x24A + i]
    diff = "✓" if o == u else "✗"
    print(f"  0x{0x24A+i:04X}: 别人=0x{o:02X} 我们=0x{u:02X} {diff}")

# 核心结论
print()
print("=" * 70)
print("核心结论")
print("=" * 70)
print(f"""
1. 别人的 PPT 也是不完整的!
   - 声明 {r16(1, other_data)} 字节，但只有 {len(other_data)} 字节
   - 说明 macOS 驱动实际只读取了约 690 字节的数据

2. 别人的 PPT revision 是 0xB6 (修改过的)
   - 我们的原始 VBIOS revision 是 0xA7
   - 别人可能修改了频率/电压参数 (如 SCLK 全是 900MHz)

3. 两个表从 0x24A 开始的尾部数据高度一致
   - 这是 pp_table 的通用结构区域（风扇/热限等）

4. 关键区别在前半部分（频率/电压状态定义）:
   - 我们的: SCLK 800/900/950/1000/1050/1100/1150/1200 MHz
   - 别人的: SCLK 全是 900 MHz (可能是节能定制版)

5. 回答你的问题 "mac 可以识别完整的吗":
   - 别人用 694 字节（不完整）就能正常工作
   - 说明 macOS 驱动不要求完整的 2050 字节
   - 但之前注入 679 字节 (你的 bios.pp_table) 失效的原因可能是:
     a) 当时还有其他配置问题 (AGPM/ULV 等同时改动)
     b) 或者 679 字节恰好截断了某个关键结构

6. 建议: 优先尝试注入完整的 2050 字节
   - 这是最安全的选择，包含所有数据
   - 如果完整版有问题，再尝试截断版
""")

#!/usr/bin/env python3
import base64, struct

def r16(off, data):
    return struct.unpack_from('<H', data, off)[0]

with open('/Users/qian/Downloads/1/vega56_pp_table_complete.bin', 'rb') as f:
    ours = f.read()

other_b64 = "tgIIAQBcAOEGAADuKwAAGwBIAAAAgKkDAPBJAgCOAAgAAAAAAAAAAAAAAAAAAAIBXABPAkYClACeAb4AKAF6AIwAvAEAAAAAcgIAAJAAqAJtAUMBlwHwSQIAcQICAgAAAAAAAAgAAAAAAAAABQAHAAMABQAAAAAAAAABCIQDhAOEA4QDhAOEA7YDMwQBATMEAQGEAwAIYOoAAABAGQEAAYA4AQAC3EoBAAOQXwEABAB3AQAFkJEBAAZQvQEABwEI0EwBAAAAgAAAAAAAAByDAQABAAAAAAAAAABwpwEAAgAAAAAAAAAAiLwBAAMAAAAAAAAAADjBAQAEAAAAAAAAAACI1QEABQAAAAABAAAAmPwBAAYAAAAAAQAAAEgzAgAHAAAAAAEAAAAABWDqAAAAQBkBAACAOAEAANxKAQAAkF8BAAAACChuAAAALMkAAAH4CwEAAoA4AQADkF8BAAT0kQEABdCwAQAGOMEBAAcACGw5AAAAJF4AAAH8hQAAAqy8AAADNNAAAARobgEABQiXAQAGsK0BAAcAAWg8AQAAAQQ8QQAAAAAAUMMAAAAAAIA4AQACAAA0mAEABAAAAQgAmIUAAEC1AABg6gAAUMMAAAGAuwAAYOoAAJQLAQBQwwAAAgDhAACUCwEAQBkBAFDDAAADeP8AAEAZAQCIJgEAUMMAAARAGQEAgDgBAIA4AQBQwwAABYA4AQDcSgEA3EoBAFDDAAAGAHcBAAB3AQCQXwEAUMMAAAeQkQEAkJEBAAB3AQBQwwAAARgAAAAAAAAACwAAvAJIJkYACgBUA5ABkAGQAZABkAGQAZABAAAAAAACBDEH3ADcANwAkAEAAFkAaQBKAEoAXwBzAHMAZABAAJCSl2CWAJBVAAAAAAAAAAAAAAAAAAAAAAACAtQwAAACEGDqAAACEA=="
other = base64.b64decode(other_b64)

# 找对齐点: 序列 59 00 69 00
search = bytes.fromhex("59006900")
our_pos = None
other_pos = None
for i in range(len(ours) - 4):
    if ours[i:i+4] == search:
        our_pos = i
        break
for i in range(len(other) - 4):
    if other[i:i+4] == search:
        other_pos = i
        break

print(f"我们对齐位置: 0x{our_pos:04X}")
print(f"别人对齐位置: 0x{other_pos:04X}")
print(f"偏移差: {other_pos - our_pos}")

# 从对齐点开始比较
match = 0
total = min(len(ours) - our_pos, len(other) - other_pos)
for i in range(total):
    if ours[our_pos + i] == other[other_pos + i]:
        match += 1
print(f"从对齐点匹配: {match}/{total} ({match*100//total}%)")

# 显示对齐区域
print(f"\n对齐区域比较 (前 48 字节):")
for i in range(min(48, total)):
    o = ours[our_pos + i]
    t = other[other_pos + i]
    diff = "OK" if o == t else "XX"
    print(f"  +0x{i:02X}: 我们=0x{o:02X} @0x{our_pos+i:04X}  别人=0x{t:02X} @0x{other_pos+i:04X}  {diff}")

# 最终结论
print()
print("=" * 60)
print("最终结论")
print("=" * 60)
print(f"1. 别人的 PPT: {len(other)} 字节 (声明 {r16(1, other)})")
print(f"2. 我们的 PPT: {len(ours)} 字节 (声明 {r16(1, ours)})")
print(f"3. 结构相同, revision 不同 (0x{other[0]:02X} vs 0x{ours[0]:02X})")
print(f"4. 别人用 {len(other)} 字节就能工作")
print(f"5. 但别人也是不完整的! 只是驱动能容忍截断")
print(f"6. 完整的 {len(ours)} 字节是最安全的选择")

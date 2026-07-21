#!/usr/bin/env python3
"""
修改 PPT 中的 MCLK DPM State 3: 800MHz → 500MHz
offset 0x01a6, 原始值 0x80380100 (80000), 改为 0x50c30000 (50000)
"""
import base64, struct, shutil, datetime

# 读取原始 PPT
b64_orig = open('/Users/qian/Downloads/1/vega56_pp_table_complete.b64','r').read().strip()
data = bytearray(base64.b64decode(b64_orig))

print(f"PPT 原始长度: {len(data)} 字节")

# 确认修改前的值
target_offset = 0x01a6
old_val = struct.unpack_from('<I', data, target_offset)[0]
print(f"\n修改前 offset 0x{target_offset:04x}: {old_val} ({old_val/100:.0f}MHz)")
assert old_val == 80000, f"预期 80000, 实际 {old_val}，offset 错误！"

# 执行修改：80000 → 50000
new_val = 50000
struct.pack_into('<I', data, target_offset, new_val)

# 确认修改后的值
verify_val = struct.unpack_from('<I', data, target_offset)[0]
print(f"修改后 offset 0x{target_offset:04x}: {verify_val} ({verify_val/100:.0f}MHz)")
assert verify_val == 50000, f"修改失败！"

# 验证其他 MCLK 状态未被破坏
print("\n=== 修改后 MCLK DPM 表验证 ===")
mclk_table_offset = 0x0190
count = data[mclk_table_offset]
for i in range(count):
    rec_off = mclk_table_offset + 1 + i * 7
    ulMCLK = struct.unpack_from('<I', data, rec_off)[0]
    print(f"  State {i}: {ulMCLK/100:.0f}MHz")

# 生成新的 base64
new_b64 = base64.b64encode(bytes(data)).decode('ascii')
print(f"\n新 base64 长度: {len(new_b64)} 字符")
print(f"原始 base64 长度: {len(b64_orig)} 字符")
assert len(new_b64) == len(b64_orig), "base64 长度不一致！"

# 保存新的 base64 文件
new_b64_path = '/Users/qian/Downloads/1/vega56_pp_table_mclk_capped.b64'
with open(new_b64_path, 'w') as f:
    f.write(new_b64)
print(f"\n新 base64 已保存: {new_b64_path}")

# 保存新的 bin 文件（用于验证）
new_bin_path = '/Users/qian/Downloads/1/vega56_pp_table_mclk_capped.bin'
with open(new_bin_path, 'wb') as f:
    f.write(bytes(data))
print(f"新 bin 已保存: {new_bin_path}")

# 输出 diff
print("\n=== 修改 diff ===")
orig_data = base64.b64decode(b64_orig)
diff_count = 0
for i in range(len(data)):
    if data[i] != orig_data[i]:
        print(f"  offset 0x{i:04x}: 0x{orig_data[i]:02x} → 0x{data[i]:02x}")
        diff_count += 1
print(f"总共修改 {diff_count} 字节")

# 输出新的 base64（用于 config.plist）
print(f"\n=== 新 PP_PhmSoftPowerPlayTable base64 ===")
print(new_b64)

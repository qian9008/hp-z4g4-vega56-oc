#!/usr/bin/env python3
"""
验证 AppleAHCIPort binary patch 位置
分析 AHCI-Ejectable 设置逻辑，确定 patch 方案
"""

import struct
import os

BINARY = "/Volumes/ramdisk/AppleAHCIPort.kext.binary"
TEXT_VMADDR = 0xffffff8001498000

def main():
    with open(BINARY, "rb") as f:
        data = f.read()

    print("=" * 70)
    print("AppleAHCIPort Binary Patch 分析 (macOS 15.7 / Sequoia)")
    print("=" * 70)

    # ============================================================
    # 第一处引用: 偏移 0x1748
    # ============================================================
    print("\n【第一处引用】偏移 0x1748 - AppleAHCI 控制器级别")
    print("-" * 50)

    # 提取 0x16F0 - 0x1780 的代码
    start = 0x16F0
    end = 0x1780
    chunk = data[start:end]

    print(f"代码区域 0x{start:x} - 0x{end:x}:")
    for i in range(0, len(chunk), 16):
        addr = start + i
        hexbytes = ' '.join(f'{b:02x}' for b in chunk[i:i+16])
        print(f"  0x{addr:05x}: {hexbytes}")

    # 关键 patch 位置: 0x1704 处的 je 指令
    # 0x1701: 48 85 c0       test rax, rax
    # 0x1704: 74 07          je   0x170d          <-- PATCH: 改为 90 90 (nop nop)
    # 0x1706: c6 83 b4 00 00 00 01   mov byte [rbx+0xb4], 1  (设置 Ejectable=1)

    patch_offset = 0x1704
    find_bytes = data[patch_offset:patch_offset+9]
    print(f"\n  Patch 位置: 0x{patch_offset:x}")
    print(f"  Find    : {' '.join(f'{b:02x}' for b in find_bytes)}")
    print(f"           (je +7; mov byte [rbx+0xb4], 1)")

    replace_bytes = b'\x90\x90' + find_bytes[2:]
    print(f"  Replace : {' '.join(f'{b:02x}' for b in replace_bytes)}")
    print(f"           (nop; nop; mov byte [rbx+0xb4], 1)")

    # 验证唯一性
    find_hex = find_bytes
    count = 0
    pos = 0
    while True:
        idx = data.find(find_hex, pos)
        if idx == -1:
            break
        count += 1
        print(f"  匹配位置 {count}: 0x{idx:x}")
        pos = idx + 1

    print(f"  唯一性: {'✅ 唯一' if count == 1 else f'❌ 出现 {count} 次'}")

    # ============================================================
    # 第三处引用: 偏移 0x39a4 (AppleIntelPchSeriesAHCI 端口级别)
    # ============================================================
    print("\n【第三处引用】偏移 0x39a4 - AppleIntelPchSeriesAHCI 端口级别")
    print("-" * 50)

    start3 = 0x3960
    end3 = 0x3A20
    chunk3 = data[start3:end3]

    print(f"代码区域 0x{start3:x} - 0x{end3:x}:")
    for i in range(0, len(chunk3), 16):
        addr = start3 + i
        hexbytes = ' '.join(f'{b:02x}' for b in chunk3[i:i+16])
        print(f"  0x{addr:05x}: {hexbytes}")

    # ============================================================
    # 总结 patch 方案
    # ============================================================
    print("\n" + "=" * 70)
    print("Patch 方案总结")
    print("=" * 70)

    print("""
方案: NOP 掉条件跳转，强制设置 AHCI-Ejectable = 1

原始逻辑:
  test rax, rax
  je   skip          ← 如果条件不满足(rax==0)，跳过设置
  mov  byte [rbx+0xb4], 1   ← 设置 Ejectable=1 (被跳过了)
skip:
  movzbl edx, byte [rbx+0xb4]  ← 读取 0xb4 作为 AHCI-Ejectable 值
  setProperty("AHCI-Ejectable", value)

Patch 后:
  test rax, rax
  nop                 ← 无操作
  nop                 ← 无操作
  mov  byte [rbx+0xb4], 1   ← 总是执行，强制设置 Ejectable=1
  movzbl edx, byte [rbx+0xb4]  ← 读取 0xb4 = 1
  setProperty("AHCI-Ejectable", 1)
""")

    print("OpenCore config.plist Kernel → Patch 配置:")
    print(f"  Identifier : com.apple.driver.AppleAHCIPort")
    print(f"  Find       : {' '.join(f'{b:02x}' for b in find_hex)}")
    print(f"  Replace    : {' '.join(f'{b:02x}' for b in replace_bytes)}")
    print(f"  Mask        : (无)")
    print(f"  ReplaceMask : (无)")

if __name__ == "__main__":
    main()

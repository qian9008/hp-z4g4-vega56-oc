#!/usr/bin/env python3
"""
完整分析 AppleAHCIPort 中所有 AHCI-Ejectable 相关代码
确定所有需要 patch 的位置
"""

import struct

BINARY = "/Volumes/ramdisk/AppleAHCIPort.kext.binary"
TEXT_VMADDR = 0xffffff8001498000

def main():
    with open(BINARY, "rb") as f:
        data = f.read()

    print("=" * 70)
    print("AppleAHCIPort 全部 AHCI-Ejectable Patch 分析")
    print("=" * 70)

    # ============================================================
    # Patch 1: 第一处 - AppleAHCI 类 (偏移 0x1704)
    # ============================================================
    print("\n【Patch 1】AppleAHCI 控制器级别 (偏移 0x1704)")
    print("-" * 50)

    # 原始代码:
    # 0x1701: 48 85 c0              test rax, rax
    # 0x1704: 74 07                 je   skip        ← 条件跳转
    # 0x1706: c6 83 b4 00 00 00 01  mov byte [rbx+0xb4], 1  ← 设置 Ejectable=1
    # skip:
    # 0x170d: ... (后续读取 0xb4 作为属性值)

    find1 = bytes.fromhex("7407c683b400000001")
    replace1 = bytes.fromhex("9090c683b400000001")

    count1 = data.count(find1)
    print(f"  逻辑: 条件跳转 je 跳过设置 Ejectable=1")
    print(f"  Patch: je → nop nop (强制执行设置)")
    print(f"  Find    : {find1.hex(' ')}")
    print(f"  Replace : {replace1.hex(' ')}")
    print(f"  唯一性  : {'✅' if count1 == 1 else '❌'} ({count1} 次)")

    # ============================================================
    # Patch 2: 第三处 - AppleIntelPchSeriesAHCI 端口级别 (偏移 0x399b)
    # ============================================================
    print("\n【Patch 2】AppleIntelPchSeriesAHCI 端口级别 (偏移 ~0x399b)")
    print("-" * 50)

    # 原始代码:
    # mov edx, [rbx+0x16d]     8b 93 6d 01 00 00  (读取端口能力字段)
    # shr edx, 14              c1 ea 0e           (右移14位, 取 bit 14)
    # and edx, 1               83 e2 01           (取最低位)
    # mov rax, [rbx]           48 8b 03
    # lea rsi, "AHCI-Ejectable" 48 8d 35 ...

    # Patch: and edx,1 → or edx,1 (强制为1)
    # 83 e2 01 → 83 ca 01

    find2 = bytes.fromhex("c1ea0e83e201")
    replace2 = bytes.fromhex("c1ea0e83ca01")

    count2 = data.count(find2)
    print(f"  逻辑: 从端口能力字段提取 bit 14 作为 Ejectable 值")
    print(f"  Patch: and edx,1 → or edx,1 (强制 Ejectable=1)")
    print(f"  Find    : {find2.hex(' ')}")
    print(f"  Replace : {replace2.hex(' ')}")
    print(f"  唯一性  : {'✅' if count2 == 1 else '❌'} ({count2} 次)")

    # 验证找到的位置
    pos = 0
    locations = []
    while True:
        idx = data.find(find2, pos)
        if idx == -1:
            break
        locations.append(idx)
        pos = idx + 1
    for loc in locations:
        print(f"  匹配位置: 0x{loc:x}")

    # ============================================================
    # 第二处引用分析 (偏移 0x36a1)
    # ============================================================
    print("\n【第二处引用分析】偏移 0x36a1")
    print("-" * 50)

    start2 = 0x3680
    end2 = 0x3700
    chunk2 = data[start2:end2]
    print(f"代码区域 0x{start2:x} - 0x{end2:x}:")
    for i in range(0, len(chunk2), 16):
        addr = start2 + i
        hexbytes = ' '.join(f'{b:02x}' for b in chunk2[i:i+16])
        print(f"  0x{addr:05x}: {hexbytes}")

    # ============================================================
    # 总结
    # ============================================================
    print("\n" + "=" * 70)
    print("最终 Patch 方案")
    print("=" * 70)
    print(f"""
用户 SATA 控制器使用 AppleAHCI 类 (从 ioreg 确认)
建议应用 Patch 1 (必须) 和 Patch 2 (可选, 覆盖 Intel PCH 路径)

Patch 1 (必须 - AppleAHCI):
  Identifier: com.apple.driver.AppleAHCIPort
  Find      : {find1.hex()}
  Replace   : {replace1.hex()}

Patch 2 (可选 - AppleIntelPchSeriesAHCI):
  Identifier: com.apple.driver.AppleAHCIPort
  Find      : {find2.hex()}
  Replace   : {replace2.hex()}
""")

if __name__ == "__main__":
    main()

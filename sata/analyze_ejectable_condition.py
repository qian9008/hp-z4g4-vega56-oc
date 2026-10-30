#!/usr/bin/env python3
"""
分析 AppleAHCIPort 中决定 Ejectable 的条件
找到 getProperty 调用引用的属性名 —— 如果能通过 ACPI _DSM 注入该属性，
就不需要 binary patch
"""

BINARY = "/Volumes/ramdisk/AppleAHCIPort.kext.binary"

def main():
    with open(BINARY, "rb") as f:
        data = f.read()

    # ============================================================
    # 第一处引用前的代码: getProperty 调用分析
    # 0x16f0: 3e 48 8b 07           mov rax, [rdi]  (DS: vtable)
    # 0x16f4: 48 8d 35 d8 bc 00 00  lea rsi, [rip+0xbcd8]  (属性名)
    # 0x16fb: ff 90 b8 02 00 00     call [rax+0x2b8]  (getProperty)
    # 0x1701: 48 85 c0              test rax, rax
    # 0x1704: 74 07                 je skip
    # 0x1706: c6 83 b4 00 00 00 01  mov byte [rbx+0xb4], 1  (Ejectable=1)
    # ============================================================

    # 计算 LEA 引用的属性名地址
    # instruction_end = 0x16fb, disp = 0xbcd8
    name_offset = 0x16fb + 0xbcd8  # = 0xd3d3
    print(f"属性名偏移: 0x{name_offset:x}")

    # 读取该偏移处的 C 字符串
    name_end = data.index(b'\x00', name_offset)
    name = data[name_offset:name_end].decode('utf-8', errors='replace')
    print(f"属性名: '{name}'")
    print()

    # 打印 0xd3c0 - 0xd420 范围的所有字符串
    print("0xd3c0 - 0xd420 范围内的字符串:")
    region = data[0xd3c0:0xd420]
    i = 0
    while i < len(region):
        if 0x20 <= region[i] < 0x7f:
            s = []
            j = i
            while j < len(region) and 0x20 <= region[j] < 0x7f:
                s.append(chr(region[j]))
                j += 1
            if len(s) >= 3:
                print(f"  0x{0xd3c0+i:x}: '{''.join(s)}'")
            i = j
        else:
            i += 1

    # ============================================================
    # 分析: 如果属性名是某个可通过 _DSM 注入的字符串
    # 那么通过 SSDT 注入该属性就能让 Ejectable=1
    # ============================================================
    print()
    print("=" * 60)
    print(f"关键发现: 代码调用 getProperty(\"{name}\")")
    print(f"  如果返回非空 → 设置 AHCI-Ejectable = 1")
    print(f"  如果返回空 → 跳过, AHCI-Ejectable = 0 (内置)")
    print()

    # 检查这个属性名在二进制中是否还出现在其他地方
    name_bytes = name.encode('utf-8')
    count = 0
    pos = 0
    while True:
        idx = data.find(name_bytes, pos)
        if idx == -1:
            break
        count += 1
        # 看看前后字节确认是独立字符串
        print(f"  字符串出现位置 {count}: 0x{idx:x}")
        pos = idx + 1

    # ============================================================
    # 检查 ASMediaAppleAHCI 类是否有不同的 ejectable 逻辑
    # 搜索 ASMedia 相关代码
    # ============================================================
    print()
    print("=" * 60)
    print("ASMedia 相关分析:")
    asm_offsets = []
    pos = 0
    while True:
        idx = data.find(b'ASMedia', pos)
        if idx == -1:
            break
        asm_offsets.append(idx)
        pos = idx + 1
    print(f"  'ASMedia' 出现 {len(asm_offsets)} 次")
    for off in asm_offsets:
        # 读取完整字符串
        end = data.index(b'\x00', off)
        s = data[off:end].decode('utf-8', errors='replace')
        print(f"    0x{off:x}: '{s}'")

if __name__ == "__main__":
    main()

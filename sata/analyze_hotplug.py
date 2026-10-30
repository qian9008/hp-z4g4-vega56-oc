#!/usr/bin/env python3
"""分析修改版 AppleAHCIPortHotplug.kext，找到 AHCI-Ejectable 相关代码"""

import struct
import os

BINARY = "/Volumes/ramdisk/AppleAHCIPortHotplug.kext/Contents/MacOS/AppleAHCIPort"

# 修改版 kext 的 __TEXT 段: vmaddr=0, fileoff=0
TEXT_VMADDR = 0x0000000000000000

def find_lea_references(data, target_vmaddr, text_vmaddr):
    """搜索所有 LEA reg, [RIP+disp32] 指令"""
    results = []
    reg_names = {
        0: "rax", 1: "rcx", 2: "rdx", 3: "rbx",
        4: "rsp", 5: "rbp", 6: "rsi", 7: "rdi"
    }
    for i in range(len(data) - 7):
        if data[i] in (0x48, 0x4C) and data[i+1] == 0x8D:
            modrm = data[i+2]
            mod = (modrm >> 6) & 0x3
            reg = (modrm >> 3) & 0x7
            rm = modrm & 0x7
            if mod == 0 and rm == 5:
                disp32 = struct.unpack("<i", data[i+3:i+7])[0]
                instruction_end = text_vmaddr + i + 7
                target = instruction_end + disp32
                if target == target_vmaddr:
                    rex = data[i]
                    reg_name = f"r{8+reg}" if rex == 0x4C else reg_names[reg]
                    results.append({
                        'offset': i,
                        'vmaddr': text_vmaddr + i,
                        'reg': reg_name,
                        'disp32': disp32,
                        'target': hex(target)
                    })
    return results

def main():
    with open(BINARY, "rb") as f:
        data = f.read()

    # 查找 "AHCI-Ejectable" 字符串
    str_offset = data.find(b"AHCI-Ejectable")
    if str_offset < 0:
        print("未找到 AHCI-Ejectable 字符串")
        return

    str_vmaddr = TEXT_VMADDR + str_offset
    print(f"'AHCI-Ejectable' 字符串:")
    print(f"  文件偏移: 0x{str_offset:x} ({str_offset})")
    print(f"  虚拟地址: 0x{str_vmaddr:x}")
    print()

    refs = find_lea_references(data, str_vmaddr, TEXT_VMADDR)
    print(f"找到 {len(refs)} 处 LEA 引用:")
    for ref in refs:
        print(f"  偏移 0x{ref['offset']:x}  VMAddr 0x{ref['vmaddr']:x}  "
              f"LEA {ref['reg']}, [RIP+0x{ref['disp32']:x}]")

    # 对比：原版 kernelcache 中的引用在偏移 0x1748, 0x36a1, 0x39a4
    # 修改版中的引用位置
    print()

    # 提取每个引用点前后的代码字节
    for ref in refs:
        off = ref['offset']
        # 提取前 48 字节和后 48 字节
        start = max(0, off - 48)
        end = min(len(data), off + 55)
        chunk = data[start:end]
        print(f"\n--- 引用点 0x{off:x} (前后代码) ---")
        for j in range(0, len(chunk), 16):
            addr = start + j
            hexbytes = ' '.join(f'{b:02x}' for b in chunk[j:j+16])
            print(f"  0x{addr:05x}: {hexbytes}")

if __name__ == "__main__":
    main()

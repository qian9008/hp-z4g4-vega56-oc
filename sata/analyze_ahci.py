#!/usr/bin/env python3
"""分析 AppleAHCIPort 二进制，找到设置 AHCI-Ejectable 属性的代码位置"""

import struct
import os

BINARY = "/Volumes/ramdisk/AppleAHCIPort.kext.binary"

# AppleAHCIPort 在 kernelcache 中的信息
# vmaddr(__TEXT) = 0xffffff8001498000
# fileoff in kernelcache = 0x1398000
TEXT_VMADDR = 0xffffff8001498000
TEXT_FILEOFF_KC = 0x1398000

def find_string_offset(data, pattern):
    """在二进制中搜索字符串，返回偏移"""
    idx = data.find(pattern.encode())
    return idx

def find_lea_references(data, target_vmaddr, text_vmaddr):
    """搜索所有 LEA reg, [RIP+disp32] 指令，
    计算目标地址是否指向 target_vmaddr"""

    results = []
    # x86_64 LEA 指令: REX.W 8D ModRM disp32
    # REX.W = 0x48 (或 0x4C for r8-r15)
    # ModRM: mod=00, reg=目标寄存器, r/m=101 (RIP-relative)
    # ModRM = 0b00_reg_101
    # reg: RDI=111(0x3D), RSI=110(0x35), RDX=010(0x15),
    #      RCX=001(0x0D), R8=000(0x05 with REX 0x4C),
    #      RAX=000(0x05 with REX 0x48)

    reg_names = {
        0: "rax", 1: "rcx", 2: "rdx", 3: "rbx",
        4: "rsp", 5: "rbp", 6: "rsi", 7: "rdi"
    }

    # 搜索 LEA 指令
    for i in range(len(data) - 7):
        # REX.W prefix: 0x48 or 0x4C
        if data[i] in (0x48, 0x4C) and data[i+1] == 0x8D:
            modrm = data[i+2]
            mod = (modrm >> 6) & 0x3
            reg = (modrm >> 3) & 0x7
            rm = modrm & 0x7

            # RIP-relative: mod=00, rm=101
            if mod == 0 and rm == 5:
                # 读取 disp32 (little-endian)
                disp32 = struct.unpack("<i", data[i+3:i+7])[0]

                # 计算目标地址
                # 指令长度 = 7 bytes (REX + opcode + ModRM + disp32)
                # instruction_end = text_vmaddr + i + 7
                instruction_end = text_vmaddr + i + 7
                target = instruction_end + disp32

                if target == target_vmaddr:
                    rex = data[i]
                    if rex == 0x4C:
                        reg_name = f"r{8+reg}"
                    else:
                        reg_name = reg_names[reg]

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
    str_offset = find_string_offset(data, "AHCI-Ejectable")
    if str_offset < 0:
        print("未找到 AHCI-Ejectable 字符串")
        return

    str_vmaddr = TEXT_VMADDR + str_offset
    print(f"'AHCI-Ejectable' 字符串:")
    print(f"  文件偏移: 0x{str_offset:x} ({str_offset})")
    print(f"  虚拟地址: 0x{str_vmaddr:x}")
    print()

    # 搜索引用此字符串的 LEA 指令
    refs = find_lea_references(data, str_vmaddr, TEXT_VMADDR)

    print(f"找到 {len(refs)} 处 LEA 引用:")
    for ref in refs:
        print(f"  偏移 0x{ref['offset']:x}  VMAddr 0x{ref['vmaddr']:x}  "
              f"LEA {ref['reg']}, [RIP+0x{ref['disp32']:x}]  ->  {ref['target']}")

    # 也搜索 "Ejectable" (不含 AHCI- 前缀)
    eject_offset = find_string_offset(data, "Ejectable\x00")
    if eject_offset >= 0:
        eject_vmaddr = TEXT_VMADDR + eject_offset
        print(f"\n'Ejectable' 字符串 (null-terminated):")
        print(f"  文件偏移: 0x{eject_offset:x}")
        print(f"  虚拟地址: 0x{eject_vmaddr:x}")

        refs2 = find_lea_references(data, eject_vmaddr, TEXT_VMADDR)
        print(f"找到 {len(refs2)} 处 LEA 引用:")
        for ref in refs2:
            print(f"  偏移 0x{ref['offset']:x}  VMAddr 0x{ref['vmaddr']:x}  "
                  f"LEA {ref['reg']}, [RIP+0x{ref['disp32']:x}]  ->  {ref['target']}")

    # 搜索 "External SATA" 和 "HotPlug"
    for s in ["External SATA", "HotPlug"]:
        off = find_string_offset(data, s)
        if off >= 0:
            vmaddr = TEXT_VMADDR + off
            print(f"\n'{s}' 字符串: 偏移 0x{off:x}  VMAddr 0x{vmaddr:x}")
            refs3 = find_lea_references(data, vmaddr, TEXT_VMADDR)
            print(f"  {len(refs3)} 处引用:")
            for ref in refs3:
                print(f"    偏移 0x{ref['offset']:x}  LEA {ref['reg']}")

if __name__ == "__main__":
    main()

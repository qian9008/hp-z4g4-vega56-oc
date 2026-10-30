#!/usr/bin/env python3
"""从 MH_FILESET 格式的 kernelcache 中提取 AppleAHCIPort 二进制
   LC_FILESET_ENTRY = 0x80000035
"""

import struct
import os

KCACHE = "/System/Library/KernelCollections/BootKernelExtensions.kc"
OUTPUT_DIR = "/Volumes/ramdisk"

# LC_FILESET_ENTRY = 0x35 | LC_REQ_DYLD
LC_FILESET_ENTRY = 0x80000035

def extract():
    with open(KCACHE, "rb") as f:
        data = f.read()

    magic = struct.unpack("<I", data[:4])[0]
    filetype = struct.unpack("<I", data[12:16])[0]
    ncmds = struct.unpack("<I", data[16:20])[0]
    print(f"Magic: 0x{magic:08x}  Filetype: {filetype}  ncmds: {ncmds}")

    offset = 32  # mach_header_64 size
    entries = []

    for i in range(ncmds):
        if offset + 8 > len(data):
            break
        cmd, cmdsize = struct.unpack("<II", data[offset:offset+8])

        if cmd == LC_FILESET_ENTRY:
            # struct entry_command:
            #   uint32_t cmd
            #   uint32_t cmdsize
            #   uint64_t vmaddr
            #   uint64_t fileoff
            #   uint32_t entry_id  (字符串偏移，相对于 load command 起始)
            #   uint32_t reserved
            vmaddr, fileoff = struct.unpack("<QQ", data[offset+8:offset+24])
            entry_id_offset = struct.unpack("<I", data[offset+24:offset+28])[0]
            # entry_id 是字符串偏移，相对于 load command 起始位置
            name_start = offset + entry_id_offset
            name_end = data.index(b"\x00", name_start)
            name = data[name_start:name_end].decode("utf-8", errors="replace")
            entries.append((name, vmaddr, fileoff))

        offset += cmdsize

    print(f"\nLC_FILESET_ENTRY 数量: {len(entries)}")

    # 列出包含 AHCI 的条目
    ahci_entries = [(n, v, f) for n, v, f in entries if "AHCI" in n.upper() or "AHCI" in n]
    print(f"AHCI 相关条目: {len(ahci_entries)}")
    for name, vmaddr, fileoff in ahci_entries:
        print(f"  {name}  vmaddr=0x{vmaddr:x}  fileoff=0x{fileoff:x}")

    # 提取 AppleAHCIPort
    for idx, (name, vmaddr, fileoff) in enumerate(entries):
        if "AppleAHCIPort" in name:
            # 下一个 entry 的 fileoff 来确定大小
            sorted_entries = sorted(entries, key=lambda x: x[2])  # 按 fileoff 排序
            sidx = [i for i, e in enumerate(sorted_entries) if e[2] == fileoff][0]
            if sidx + 1 < len(sorted_entries):
                next_fileoff = sorted_entries[sidx + 1][2]
            else:
                next_fileoff = len(data)
            size = next_fileoff - fileoff

            outpath = os.path.join(OUTPUT_DIR, "AppleAHCIPort.kext.binary")
            with open(outpath, "wb") as f:
                f.write(data[fileoff:fileoff + size])
            print(f"\n提取完成: {outpath}")
            print(f"  名称: {name}")
            print(f"  fileoff=0x{fileoff:x}  size=0x{size:x} ({size} bytes)")
            return outpath

    print("\n未找到 AppleAHCIPort，列出前 20 个条目:")
    for name, vmaddr, fileoff in entries[:20]:
        print(f"  {name}")

    return None

if __name__ == "__main__":
    extract()

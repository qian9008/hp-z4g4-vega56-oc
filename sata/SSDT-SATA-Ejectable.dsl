// SSDT-SATA-Ejectable.dsl
// 通过 _DSM 注入 IOPCIEjectable 属性, 让 macOS 将 SATA 视为可移动设备
// 
// 原理: AppleAHCIPort 驱动调用 getProperty("IOPCIEjectable")
//   如果该属性存在(非空) → 设置 AHCI-Ejectable=1 → 磁盘显示为"外置"
//   如果该属性不存在 → AHCI-Ejectable=0 → 磁盘显示为"内置"
//
// ACPI 路径: \_SB.PC00.SAT1 (通过 ioreg 确认)
// PCI 路径:  PciRoot(0x0)/Pci(0x17,0x0)
// 编译命令:  iasl -tc SSDT-SATA-Ejectable.dsl

DefinitionBlock ("", "SSDT", 2, "HACK", "SATAEJ", 0x00000000)
{
    // 外部引用: SATA 控制器在 ACPI 中的实际路径
    External (\_SB.PC00.SAT1, DeviceObj)

    Scope (\_SB.PC00.SAT1)
    {
        // _DSM 方法: 设备特定方法 (Device-Specific Method)
        // macOS 通过 UUID + Arg2=0 调用, 返回属性字典
        // Arg0 = UUID, Arg1 = Revision, Arg2 = Function, Arg3 = Arg3
        Method (_DSM, 4, NotSerialized)
        {
            // Apple Device Properties UUID
            // macOS 使用此 UUID 注入设备属性
            If (LEqual (Arg2, Zero))
            {
                // 返回属性包 (Package)
                // 格式: { "属性名", 属性值, ... }
                // IOPCIEjectable = 1 (One) → 告诉驱动此设备可移动
                Return (Package (0x02)
                {
                    "IOPCIEjectable",
                    One
                })
            }

            // 其他 function 返回空
            Return (Zero)
        }
    }
}

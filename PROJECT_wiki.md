# PROJECT_wiki.md — Vega 56 Hackintosh GPU 电源管理项目

## 项目概述

在 macOS (Hackintosh/OpenCore) 上为 **AMD Radeon RX Vega 56** 实现 GPU 电源管理：

- 待机时：GfxOff 工作 → ULV → MCLK=167MHz ✓
- 播放视频：UVD 专用 → MCLK=500MHz ✓
- 退出视频后：MCLK≤500MHz（PPT State 3 封顶 500MHz）✓

## 硬件环境

- GPU: AMD Radeon RX Vega 56 (Device ID: `0x687f`)
- VBIOS: `D0500300.101` (113-D0500300-101), 256KB
- 系统: macOS (OpenCore 引导)

## 核心文件

### EFI 分区 (`/Volumes/NO NAME/EFI/OC/`)

| 文件 | 说明 |
|------|------|
| `config.plist` | OpenCore 主配置，包含 GPU DeviceProperties 和 Kext 注册 |
| `config.plist.bak.*` | 历史备份 |
| `Kexts/AGPMInjector.kext` | AGPM 注入器，让 AppleGraphicsPowerManagement 匹配 Vega 56 |

### 工作目录 (`/Users/qian/Downloads/1/`)

| 文件 | 说明 |
|------|------|
| `AMD Radeon RX Vega 56.bios` | 64KB VBIOS dump |
| `bios.rom` | 256KB 完整 VBIOS dump |
| `bios.pp_table` | Windows 导出的 Linux 格式 pp_table (679 字节, **不完整**) |
| `vega56_pp_table_complete.bin` | 从 VBIOS 提取的完整 pp_table (2050 字节, 原始) |
| `vega56_pp_table_complete.b64` | 完整 pp_table 的 Base64 编码 (2736 字符, 原始) |
| `vega56_pp_table_mclk_capped.bin` | MCLK State 3 封顶 500MHz 的 pp_table (2050 字节) ✓ |
| `vega56_pp_table_mclk_capped.b64` | MCLK 封顶版 pp_table 的 Base64 (2736 字符) ✓ |
| `patch_mclk.py` | PPT MCLK 修改脚本 (800MHz→500MHz) |
| `replace_ppt.py` | 将新 PPT base64 写入 config.plist 的脚本 |
| `vega56_atom_powerplay.b64` | ATOM PowerPlayInfo 表 Base64 (256 字节, rev 0x74) |
| `extract_ppt.py` | VBIOS 解析脚本 (从 64KB bios 提取) |
| `extract_from_rom.py` | VBIOS 解析脚本 (从 256KB rom 提取) |
| `verify_match.py` / `verify_match2.py` | 验证 pp_table 与 VBIOS 数据匹配 |
| `compare_other.py` | 对比别人的 PPT (694 字节, rev 0xb6) |
| `verify_injection.py` | 验证 config.plist 注入正确性 |

## 关键技术决策

### 1. AGPMInjector.kext (已部署)

**问题**: macOS 系统 AGPM 默认不匹配 Vega 56 (`0x687f`)，导致 P-state 无法切换。
**方案**: 使用 AGPMInjector.kext 注册 `0x687f` 到 AGPM 的设备列表。
**注意**: 不能用 `Kernel->Block` 禁用系统 AGPM（会导致内核崩溃），因为 AGPM 是 plist-only kext，代码在内核集合中。

### 2. PowerPlay Table (PPT) 格式选择

**VBIOS 中存在两个表**:
- `PowerPlayInfo` (索引 13): 256 字节, revision `0x74` — ATOM 格式状态索引
- `PowerPlayInfo_V2` (索引 28): 515 字节, revision `0x27`

**实际使用的 PPT**:
- 从 VBIOS `0x917A` 处提取的 **Linux 格式 pp_table** (revision `0xa7`)
- 完整大小: **2050 字节** (声明大小 = 实际大小)
- macOS AMD 驱动可识别 revision `0xa7` 格式

**VBIOS 结构解析路径**:
```
0x48 → ATOM_ROM_HEADER @ 0x0274
  +0x04: "ATOM" 签名
  +0x20: MasterCommandTable @ 0x0B36
  +0x20 (备用偏移): MasterDataTable @ 0x8E9C
    +0x04: ListOfDataTables
      [13] → PowerPlayInfo @ 0x9106 (rev 0x74, 256 字节)
        +0x74: 嵌套 Linux pp_table @ 0x917A (rev 0xa7, 2050 字节) ← 实际注入的
```

### 3. PP_PhmSoftPowerPlayTable 注入

**config.plist DeviceProperties 中的 GPU 属性**:
```xml
<key>PP_DisableULV</key>
<integer>0</integer>                    <!-- 启用 ULV (167MHz) -->
<key>PP_GfxOffControl</key>
<integer>1</integer>                    <!-- 启用 GfxOff -->
<key>PP_PhmSoftPowerPlayTable</key>
<data>pwIIAQBcAO8G...（2050 字节 Base64, 2736 字符）</data>
```

**注意事项**:
- `PP_DisableULV=0`：AMD 驱动默认 `PP_DisableULV=1`（硬编码），注入 0 尝试启用 ULV
- `PP_GfxOffControl=1`：驱动可能覆盖此值，但保留作为尝试
- PPT 必须完整：之前注入 679 字节（截断）导致传感器失效

### 6. 驱动 aty_properties 覆盖问题（关键修复）

**问题**: 在 config.plist DeviceProperties 中注入的 `PP_DisableULV=0` 和 `PP_GfxOffControl=1` 被驱动运行时覆盖：
- `PP_DisableULV` 被覆盖为 **1**（禁用 ULV，阻止 167MHz）
- `PP_GfxOffControl` 被覆盖为 **0**（禁用 GfxOff）

**根因**: `AMD10000Controller.kext` 的 Info.plist 中：
- 默认 `aty_properties` 硬编码 `PP_DisableULV=1, PP_GfxOffControl=0`
- `ATY,Kamarang` personality 的 `aty_properties` 未定义这两个属性，继承了默认值
- 驱动初始化时用 personality 的 aty_properties 覆盖了 DeviceProperties 注入值

**解决方案**: 修改 `AMD10000Controller.kext`（plist-only kext，无可执行文件）：
1. 复制到 `EFI/OC/Kexts/AMD10000Controller.kext/`
2. 在 `ATY,Kamarang` 的 `aty_properties` 中显式添加 `PP_DisableULV=0` 和 `PP_GfxOffControl=1`
3. 通过 OpenCore `Kernel->Add` 注入，替换系统 KC 中的版本

**修改内容**:
```xml
<!-- ATY,Kamarang 的 aty_properties 修改前 -->
<key>aty_properties</key>
<dict>
    <key>PP_ACDCGpioDisabled</key>
    <integer>0</integer>
    <key>PP_DisablePCCLimitControl</key>
    <integer>1</integer>
</dict>

<!-- 修改后（新增 PP_DisableULV, PP_GfxOffControl, 及防止 MCLK 锁死的 UVD/VCE 握手禁用）-->
<key>aty_properties</key>
<dict>
    <key>PP_ACDCGpioDisabled</key>
    <integer>0</integer>
    <key>PP_DisablePCCLimitControl</key>
    <integer>1</integer>
    <key>PP_DisableULV</key>
    <integer>0</integer>
    <key>PP_DisableUVDHandshake</key>
    <integer>1</integer>
    <key>PP_DisableVCEHandshake</key>
    <integer>1</integer>
    <key>PP_GfxOffControl</key>
    <integer>1</integer>
</dict>
```

**ioreg 验证方法**:
```
ioreg -l | grep "PP_Disable"
```
修改后应显示 `PP_DisableULV = 0`, `PP_DisableUVDHandshake = 1` 等属性生效（不再是驱动的默认值）。

### 4. bios.pp_table 不完整问题

| 属性 | bios.pp_table | 完整版 |
|------|--------------|--------|
| Revision | 0xa7 | 0xa7 |
| 声明大小 (usTableSize) | 2050 字节 | 2050 字节 |
| 实际大小 | **679 字节** ✗ | **2050 字节** ✓ |
| 数据来源 | VBIOS 0x917A | VBIOS 0x917A |
| 数据正确性 | 679/679 匹配 ✓ | 2050/2050 完整 ✓ |

Windows 下导出的 `bios.pp_table` 数据正确但不完整（缺少 1371 字节）。
别人使用的 694 字节 PPT (rev 0xb6) 同样不完整但能工作——说明 macOS 驱动对截断有容忍度，
但完整版是最安全的选择。



### 7. MCLK DPM State 3 封顶（退出视频后频率修复）

**问题**: 待机 167MHz 已修复，但退出视频播放后 MCLK 永久锁死在 800MHz（DPM 最高状态），
GfxOff 无法重新触发。这是 macOS AMD 驱动的 bug——UVD 退出后 DPM 状态机不回退。

**验证过程**:
1. 杀掉 VTDecoderXPCService / VTEncoderXPCService → MCLK 不变（排除进程持有上下文）
2. 显示器休眠/唤醒 → MCLK 不变（排除显示管线状态）
3. PP_GfxOffControl=1 已生效 → 排除 GfxOff 配置问题
4. 结论：驱动 DPM 状态机 bug，退出 UVD 后永久锁定在最高 MCLK DPM 状态

**解决方案**: 直接修改 PPT 中的 MCLK DPM State 3，从 800MHz 降为 500MHz。
这样退出 UVD 后即使锁在最高状态，也只有 500MHz（和播放视频时一样）。

**PPT MCLK DPM 表 (offset 0x0190, 4 个状态)**:

| State | offset | 原始频率 | 修改后 | 用途 |
|-------|--------|---------|--------|------|
| 0 | 0x0191 | 167MHz | 167MHz | ULV（待机）|
| 1 | 0x0198 | 500MHz | 500MHz | UVD 视频解码 |
| 2 | 0x019f | 700MHz | 700MHz | 中间过渡 |
| 3 | 0x01a6 | **800MHz** | **500MHz** | 最高（退出 UVD 后锁死在这里）|

**修改详情**: 仅改 3 字节
- offset 0x01a6: 0x80 → 0x50
- offset 0x01a7: 0x38 → 0xc3
- offset 0x01a8: 0x01 → 0x00

**副作用**: 高负载时显存带宽从 410GB/s 降到 256GB/s。对日常使用无影响，
游戏或 GPU 计算密集型任务会受影响。

## 当前配置状态 (2026-07-21)

### config.plist GPU 属性 (PciRoot(0x2C)/Pci(0x0,0x0)/Pci(0x0,0x0))

- ✅ `PP_DisableULV = 0`
- ✅ `PP_GfxOffControl = 1`
- ✅ `PP_PhmSoftPowerPlayTable` = 2050 字节 (rev 0xa7, MCLK State 3 封顶 500MHz)
- ✅ `device_type = ATY,KamarangParent`
- ✅ `model = AMD Radeon Pro Vega 56`

### Kext 状态

- ✅ `AGPMInjector.kext` — 启用
- ✅ `RadeonSensor.kext` — 启用
- ✅ `AMD10000Controller.kext` — 启用 (修改版，覆盖系统 kext)

### 备份

- `config.plist.bak.mclk_cap.*` — MCLK 封顶修改前的备份

## 验证清单

重启后需检查:

1. ✅ 空闲时显存频率降至 167MHz — 已修复
2. ⏳ 退出视频播放后 MCLK ≤ 500MHz（不再卡 800MHz）— 待重启验证
3. 命令行查看频率: `ioreg -l -c IOService -r -d 6 | grep "Memory Clock"`

### 8. 不兼容 NVMe (海力士 PC601) 的屏蔽 (2026-07-25 修复)

**背景**: 系统中插有海力士 PC601 NVMe 硬盘，其固件与 macOS `IONVMeController` 原生驱动不兼容，导致加载时内核崩溃或启动自检时严重卡顿。

**发现的错误**: 
- 之前 `DeviceProperties` 注入的 `PciRoot` 路径不准确（照搬了网上的 `PciRoot(0x2C)`）。
- 同时启用了互相冲突的 ACPI 补丁：`SSDT-PC03-BR3C-NVME.aml` (用于补全节点) 和 `SSDT-NVMe-disable.aml` (暴力关闭整个 `BR3C` 桥，导致 ACPI 冲突和启动卡顿)。
- 查阅 IOReg 后确认，真实的设备路径为 `IOService:/AppleACPIPlatformExpert/PC03@0/AppleACPIPCI/pci-bridge@2/IOPP/pci1c5c,1627@0`，其对应的 EFI 路径实为 **`PciRoot(0x3)/Pci(0x2,0x0)/Pci(0x0,0x0)`**。

**最终屏蔽方案**:
1. **DeviceProperties 注入 (config.plist)**: 在正确的路径 `PciRoot(0x3)/Pci(0x2,0x0)/Pci(0x0,0x0)` 下，注入 `class-code = FFFFFFFF`（Base64: `/////w==`），强制 macOS 将其识别为未分配类别的未知设备，从而跳过驱动加载。
2. **ACPI (SSDT) 配合**: 
   - **保留** `SSDT-PC03-BR3C-NVME.aml`（此补丁在 `_SB.PC03.BR3C` 下定义了 `ANS1` 节点，为上面的属性注入提供了挂载点，因为部分高端主板原始 DSDT 下缺少该节点，如果不加此“锚点”，DeviceProperties 属性可能无法成功挂载到物理设备上）。
   - **彻底禁用/删除** 任何试图通过 `_STA=0` 直接隐藏设备的补丁（如 `SSDT-NVMe-disable.aml` 或带有 `CORRECT` 字样的补丁），以避免与节点补全补丁发生抢占冲突，同时防止 macOS 强行物理扫描总线带来的识别崩溃。
